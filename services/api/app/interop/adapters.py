"""State adapters (PRD §20-22, §40): state-specific records -> canonical schema.

Each state is described declaratively in data/adapters/<state>.json (field mappings, code tables,
unit conversions, date formats, districts). This one generic engine applies any state's config, so
onboarding a new state is a config + sample-data change, not a code change.
"""

import json
from datetime import datetime
from functools import lru_cache
from typing import Any

from app.canonical.models import Crop, Farmer, Field_, GeoPoint, SoilObservation
from app.config import DATA_DIR, REPO_ROOT
from app.farms import geo
from app.sample_data import sample_provenance

ADAPTERS_DIR = DATA_DIR / "adapters"


class AdapterError(ValueError):
    pass


@lru_cache
def state_configs() -> dict[str, dict[str, Any]]:
    configs = {}
    for path in sorted(ADAPTERS_DIR.glob("*.json")):
        cfg = json.loads(path.read_text())
        configs[cfg["state_id"]] = cfg
    return configs


def state_config(state_id: str) -> dict[str, Any]:
    try:
        return state_configs()[state_id.upper()]
    except KeyError:
        raise AdapterError(f"unknown state '{state_id}'") from None


def resolve_district(cfg: dict[str, Any], name: str) -> dict[str, Any]:
    needle = name.strip().lower()
    for d in cfg["districts"]:
        if needle in {d["name"].lower(), d["id"].lower(), *(a.lower() for a in d.get("aliases", []))}:
            return d
    raise AdapterError(f"district '{name}' is not configured for {cfg['state_id']}")


def _get(record: dict[str, Any], path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _apply(spec: str | dict[str, Any], record: dict[str, Any], cfg: dict[str, Any]) -> Any:
    if isinstance(spec, str):
        return _get(record, spec)
    value = _get(record, spec["path"])
    if value is None:
        return None
    match spec.get("transform"):
        case "language":
            return cfg["language_map"].get(value, cfg["default_language"])
        case "district":
            return resolve_district(cfg, value)["name"]
        case "code":
            table = cfg[spec["table"]]
            if value not in table:
                raise AdapterError(f"{cfg['state_id']}: unknown code '{value}' for {spec['table']}")
            return table[value]
        case "scale":
            return round(float(value) * float(spec["factor"]), 3)
        case "date":
            return datetime.strptime(value, spec["format"]).date()
        case "prefix":
            return f"{spec['prefix']}{value}".replace("/", "-")
        case "season":
            low = str(value).lower()
            return next((s for s in ("kharif", "rabi", "zaid") if s in low), None)
        case None:
            return value
        case other:
            raise AdapterError(f"unsupported transform '{other}'")


def map_record(state_id: str, entity: str, record: dict[str, Any]) -> dict[str, Any]:
    """Apply the declarative mapping for one entity and return a nested canonical dict."""
    cfg = state_config(state_id)
    out: dict[str, Any] = {}
    for target, spec in cfg["records"][entity]["fields"].items():
        value = _apply(spec, record, cfg)
        node = out
        *parents, leaf = target.split(".")
        for p in parents:
            node = node.setdefault(p, {})
        node[leaf] = value
    return out


def adapt_farmer(state_id: str, record: dict[str, Any], source_system: str) -> Farmer:
    return Farmer(**map_record(state_id, "farmers", record), state=state_id.upper(), source_system=source_system, is_sample=True)


def adapt_field(state_id: str, record: dict[str, Any], farmer: Farmer, source_system: str) -> Field_:
    data = map_record(state_id, "fields", record)
    geometry = geo.normalize(data.pop("geometry"))
    lat, lon = geo.centroid(geometry)
    crop = Crop(**data.pop("crop"))
    return Field_(
        **data,
        crop=crop,
        geometry=geometry,
        centroid=GeoPoint(lat=lat, lon=lon),
        state=state_id.upper(),
        district=farmer.district,
        block=farmer.block,
        village=farmer.village,
        name=f"{farmer.village or farmer.district} field {data.get('local_ref') or ''}".strip(),
        source_system=source_system,
        is_sample=True,
    )


def adapt_soil(state_id: str, record: dict[str, Any], meta: dict[str, Any]) -> tuple[dict[str, Any], SoilObservation]:
    data = map_record(state_id, "soil", record)
    location = {"district": data.pop("district"), "block": data.pop("block", None)}
    return location, SoilObservation(**data, provenance=sample_provenance(meta, note="Soil Health Card style record mapped by the state adapter"))


@lru_cache
def load_state_dataset(state_id: str) -> dict[str, Any]:
    """Run the adapter over the state's sample export. Returns canonical farmers/fields/soil."""
    cfg = state_config(state_id)
    raw = json.loads((REPO_ROOT / cfg["source_file"]).read_text())
    meta = raw["_meta"]
    source_system = cfg["source_system"]
    recs = cfg["records"]
    farmers = {f.farmer_id: f for f in (adapt_farmer(state_id, r, source_system) for r in raw[recs["farmers"]["collection"]])}
    fields = [
        adapt_field(state_id, r, farmers[_get(r, recs["fields"]["fields"]["farmer_id"])], source_system)
        for r in raw[recs["fields"]["collection"]]
    ]
    soil = [adapt_soil(state_id, r, meta) for r in raw[recs["soil"]["collection"]]]
    return {"meta": meta, "raw": raw, "farmers": list(farmers.values()), "fields": fields, "soil": soil}


def soil_for(state_id: str, district: str, block: str | None) -> SoilObservation | None:
    """Best matching soil record for a location: same block, else same district, else state-level."""
    try:
        soil = load_state_dataset(state_id)["soil"]
    except AdapterError:
        return None
    for loc, obs in soil:
        if block and loc.get("block") == block and loc["district"] == district:
            return obs
    for loc, obs in soil:
        if loc["district"] == district:
            return obs.model_copy(update={"provenance": obs.provenance.model_copy(
                update={"note": f"Nearest available record: {loc['district']} / {loc.get('block')} (not this exact field)"})})
    if soil:
        loc, obs = soil[0]
        return obs.model_copy(update={"provenance": obs.provenance.model_copy(
            update={"note": f"No record for {district}; using state sample from {loc['district']} (indicative only)"})})
    return None


def adapter_demo(state_id: str) -> dict[str, Any]:
    """Raw state record side by side with its canonical mapping (for the interoperability demo)."""
    cfg = state_config(state_id)
    ds = load_state_dataset(state_id)
    raw = ds["raw"]
    recs = cfg["records"]
    return {
        "state_id": cfg["state_id"],
        "state_name": cfg["state_name"],
        "adapter_version": cfg["adapter_version"],
        "source_system": cfg["source_system"],
        "source_meta": ds["meta"],
        "examples": [
            {"entity": "farmer", "raw": raw[recs["farmers"]["collection"]][0],
             "mapping": recs["farmers"]["fields"], "canonical": ds["farmers"][0].model_dump(mode="json")},
            {"entity": "field", "raw": {k: v for k, v in raw[recs["fields"]["collection"]][0].items() if k not in ("boundary", "geometry", "polygon")},
             "mapping": recs["fields"]["fields"],
             "canonical": ds["fields"][0].model_dump(mode="json", exclude={"geometry"})},
            {"entity": "soil", "raw": raw[recs["soil"]["collection"]][0],
             "mapping": recs["soil"]["fields"], "canonical": ds["soil"][0][1].model_dump(mode="json")},
        ],
    }

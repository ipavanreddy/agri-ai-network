"use client";

import { useMemo, useState } from "react";
import { Loader2, MapPin, Plus, Search, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { FieldMap, useMapProvider, type LatLng } from "@/components/field-map";
import { apiGet, apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Crop, Farmer, Field, GeocodeResult, StateConfig } from "@/lib/types";

const IRRIGATION = ["rainfed", "supplemental", "borewell", "canal", "drip", "tank"];
const selectCls = "h-8 w-full rounded-lg border border-input bg-transparent px-2 text-sm";

type Props = {
  states: StateConfig[];
  crops: Crop[];
  farmers: Farmer[];
  fields: Field[];
  selectedFieldId: string | null;
  onSelectField: (id: string) => void;
  onCreated: (farmer: Farmer, field: Field) => void;
};

export function FieldSetup({ states, crops, farmers, fields, selectedFieldId, onSelectField, onCreated }: Props) {
  const { t, lang } = useI18n();
  const mapProvider = useMapProvider();
  const [drawing, setDrawing] = useState(false);
  const [points, setPoints] = useState<LatLng[]>([]);
  const [form, setForm] = useState({ name: "", state: "AP", district: "", village: "", crop: "", sowing: "", irrigation: "rainfed" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [found, setFound] = useState<GeocodeResult | null>(null);
  const [searchNote, setSearchNote] = useState<string | null>(null);

  const selected = fields.find((f) => f.field_id === selectedFieldId) ?? null;
  const stateCfg = states.find((s) => s.state_id === form.state) ?? states[0];
  const district = stateCfg?.districts.find((d) => d.name === form.district) ?? stateCfg?.districts[0];
  const stateCrops = crops.filter((c) => stateCfg?.supported_crops.includes(c.crop_id));
  const center = useMemo<LatLng>(() => {
    if (drawing && found) return [found.lat, found.lon];
    if (drawing && district) return [district.lat, district.lon];
    if (selected) return [selected.centroid.lat, selected.centroid.lon];
    return [20.5, 78.9];
  }, [drawing, found, district, selected]);
  const zoom = drawing ? (found ? 15 : 13) : selected ? 16 : 5;

  async function search() {
    if (query.trim().length < 2) return;
    setSearchNote(null);
    try {
      const res = await apiGet<{ results: GeocodeResult[]; mode: string; note?: string }>(`/api/geocode?q=${encodeURIComponent(query.trim())}`);
      const hit = res.results[0];
      if (!hit) {
        setSearchNote(res.note ?? "No match - pick the district below instead.");
        return;
      }
      setFound(hit);
      setSearchNote(`${hit.label} · Google Maps Geocoding`);
      const st = states.find((s) => s.state_name.toLowerCase() === (hit.state ?? "").toLowerCase());
      const d = st?.districts.find((x) => [hit.district, hit.village].some((n) => n && n.toLowerCase().startsWith(x.name.toLowerCase().slice(0, 5))));
      setForm((f) => ({ ...f, state: st?.state_id ?? f.state, district: d?.name ?? (st ? "" : f.district), village: f.village || hit.village || "" }));
    } catch (e) {
      setSearchNote((e as Error).message);
    }
  }

  async function save() {
    if (points.length < 3) {
      setError(t("draw_hint"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const farmer = await apiPost<Farmer>("/api/farmers", {
        name: form.name || "Demo farmer",
        preferred_language: lang,
        state: stateCfg.state_id,
        district: district?.name,
        village: form.village || null,
      });
      const ring = [...points, points[0]].map(([lat, lon]) => [lon, lat]);
      const field = await apiPost<Field>("/api/fields", {
        farmer_id: farmer.farmer_id,
        geometry: { type: "Polygon", coordinates: [ring] },
        crop_name: form.crop || stateCfg.primary_crop,
        sowing_date: form.sowing || null,
        irrigation: form.irrigation,
      });
      setPoints([]);
      setDrawing(false);
      onCreated(farmer, field);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("step_field")}</CardTitle>
        <CardDescription>Map: {mapProvider.label}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div>
          <p className="mb-2 text-sm font-medium">{t("demo_farmers")}</p>
          <div className="flex flex-wrap gap-2">
            {fields.map((f) => {
              const farmer = farmers.find((x) => x.farmer_id === f.farmer_id);
              return (
                <Button
                  key={f.field_id}
                  size="sm"
                  variant={f.field_id === selectedFieldId ? "default" : "outline"}
                  onClick={() => {
                    setDrawing(false);
                    onSelectField(f.field_id);
                  }}
                >
                  <MapPin /> {farmer?.name ?? f.farmer_id} · {crops.find((c) => c.crop_id === f.crop.crop_name)?.names[lang] ?? f.crop.crop_name} · {f.state}
                  {f.is_sample ? <Badge variant="secondary" className="ml-1">sample</Badge> : null}
                </Button>
              );
            })}
            <Button size="sm" variant={drawing ? "default" : "secondary"} onClick={() => setDrawing((d) => !d)}>
              <Plus /> {t("new_field")}
            </Button>
          </div>
        </div>

        <FieldMap
          fields={fields}
          selectedId={selectedFieldId}
          onSelect={(id) => !drawing && onSelectField(id)}
          drawing={drawing}
          points={points}
          onAddPoint={(p) => setPoints((prev) => [...prev, p])}
          center={center}
          zoom={zoom}
        />

        {drawing ? (
          <div className="flex flex-col gap-3 rounded-lg border p-3">
            <form
              className="flex flex-wrap items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                void search();
              }}
            >
              <Input className="max-w-xs" placeholder={t("find_village")} value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button type="submit" size="sm" variant="outline">
                <Search /> {t("find_village")}
              </Button>
              {searchNote ? <span className="text-xs text-muted-foreground">{searchNote}</span> : null}
            </form>
            <p className="text-sm text-muted-foreground">
              {t("draw_hint")} ({points.length})
              <Button size="xs" variant="ghost" onClick={() => setPoints([])} className="ml-2">
                <Trash2 /> {t("clear")}
              </Button>
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <label className="text-xs">
                {t("name")}
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </label>
              <label className="text-xs">
                {t("state")}
                <select className={selectCls} value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value, district: "", crop: "" })}>
                  {states.map((s) => (
                    <option key={s.state_id} value={s.state_id}>
                      {s.state_name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs">
                {t("district")}
                <select className={selectCls} value={district?.name ?? ""} onChange={(e) => setForm({ ...form, district: e.target.value })}>
                  {stateCfg?.districts.map((d) => (
                    <option key={d.id} value={d.name}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs">
                {t("village")}
                <Input value={form.village} onChange={(e) => setForm({ ...form, village: e.target.value })} />
              </label>
              <label className="text-xs">
                {t("crop")}
                <select className={selectCls} value={form.crop || stateCfg?.primary_crop} onChange={(e) => setForm({ ...form, crop: e.target.value })}>
                  {stateCrops.map((c) => (
                    <option key={c.crop_id} value={c.crop_id}>
                      {c.names[lang]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs">
                {t("sowing_date")}
                <Input type="date" value={form.sowing} onChange={(e) => setForm({ ...form, sowing: e.target.value })} />
              </label>
              <label className="text-xs">
                {t("irrigation")}
                <select className={selectCls} value={form.irrigation} onChange={(e) => setForm({ ...form, irrigation: e.target.value })}>
                  {IRRIGATION.map((i) => (
                    <option key={i} value={i}>
                      {i}
                    </option>
                  ))}
                </select>
              </label>
              <div className="flex items-end">
                <Button onClick={save} disabled={busy || points.length < 3} className="w-full">
                  {busy ? <Loader2 className="animate-spin" /> : null} {t("save_field")}
                </Button>
              </div>
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

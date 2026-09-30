"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Droplets, Leaf, Sprout, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ModeBadge } from "@/components/mode-badge";
import { RegionMap, mapProvider, type RegionMarker } from "@/components/region-map";
import { apiGet } from "@/lib/api";
import type { DistrictRisks, Overview, StateAnalytics } from "@/lib/types";

const RISK_COLOR = { high: "#dc2626", medium: "#f59e0b", low: "#16a34a" } as const;
const healthColor = (h: number) => (h >= 70 ? "#16a34a" : h >= 60 ? "#f59e0b" : "#dc2626");
const CROP_COLORS = ["#15803d", "#0ea5e9", "#a855f7", "#f59e0b", "#ef4444", "#64748b", "#14b8a6", "#84cc16"];

function Kpi({ icon: Icon, label, value, hint }: { icon: typeof Users; label: string; value: string; hint?: string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-lg border p-3">
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Icon className="size-3.5" /> {label}
      </span>
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  );
}

function CropBars({ dist }: { dist: Record<string, number> }) {
  const entries = Object.entries(dist);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex h-4 w-full overflow-hidden rounded-full">
        {entries.map(([crop, pct], i) => (
          <div key={crop} title={`${crop}: ${pct}%`} style={{ width: `${pct}%`, background: CROP_COLORS[i % CROP_COLORS.length] }} />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {entries.map(([crop, pct], i) => (
          <span key={crop} className="flex items-center gap-1">
            <span className="inline-block size-2.5 rounded-sm" style={{ background: CROP_COLORS[i % CROP_COLORS.length] }} />
            {crop.replaceAll("_", " ")} {pct}%
          </span>
        ))}
      </div>
    </div>
  );
}

export function RegionalView({ overview }: { overview: Overview }) {
  const [stateId, setStateId] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<StateAnalytics | null>(null);
  const [districtId, setDistrictId] = useState<string | null>(null);
  const [district, setDistrict] = useState<DistrictRisks | null>(null);

  useEffect(() => {
    if (!stateId) return;
    let cancelled = false;
    apiGet<StateAnalytics>(`/api/states/${stateId}/analytics`).then((a) => !cancelled && setAnalytics(a));
    return () => {
      cancelled = true;
    };
  }, [stateId]);

  useEffect(() => {
    if (!districtId) return;
    let cancelled = false;
    apiGet<DistrictRisks>(`/api/districts/${districtId}/risks`).then((d) => !cancelled && setDistrict(d));
    return () => {
      cancelled = true;
    };
  }, [districtId]);

  const view = stateId && analytics?.state_id === stateId ? analytics : null;
  const markers = useMemo<RegionMarker[]>(() => {
    if (view) {
      return view.districts.map((d) => ({
        id: d.district_id,
        lat: d.lat,
        lon: d.lon,
        color: RISK_COLOR[d.weather_risk],
        radius: 8 + Math.min(14, d.disease_alerts / 2),
        tooltip: `${d.district}: health ${d.avg_farm_health}, weather risk ${d.weather_risk}, ${d.disease_alerts} disease/stress alerts`,
      }));
    }
    return overview.states.map((s) => ({
      id: s.state_id,
      lat: s.lat,
      lon: s.lon,
      color: healthColor(s.avg_farm_health),
      radius: 14,
      tooltip: `${s.state_name}: avg farm health ${s.avg_farm_health}, ${s.disease_alerts} alerts`,
    }));
  }, [view, overview]);
  const center = useMemo<[number, number]>(() => {
    if (view && view.districts.length) {
      return [view.districts.reduce((a, d) => a + d.lat, 0) / view.districts.length, view.districts.reduce((a, d) => a + d.lon, 0) / view.districts.length];
    }
    return [22.5, 79];
  }, [view]);

  const selectState = (id: string) => {
    setStateId(id);
    setDistrictId(null);
    setDistrict(null);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Button size="sm" variant={stateId ? "outline" : "default"} onClick={() => { setStateId(null); setDistrictId(null); }}>
          India
        </Button>
        {overview.states.map((s) => (
          <Button key={s.state_id} size="sm" variant={stateId === s.state_id ? "default" : "outline"} onClick={() => selectState(s.state_id)}>
            {s.state_name} · {s.primary_crop}
          </Button>
        ))}
        {district && districtId ? <Badge variant="secondary">District: {district.district}</Badge> : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              {view ? `${view.state_name}: district risk map` : "India: state overview"}
              <ModeBadge demo={view ? view.provenance.is_sample : overview.demo_mode} />
            </CardTitle>
            <CardDescription>
              {view ? "Colour = weather risk, size = disease/stress alerts. Click a district." : "Colour = average Farm Health. Click a state."} Map: {mapProvider}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RegionMap markers={markers} center={center} zoom={view ? 7 : 4} onSelect={(id) => (view ? setDistrictId(id) : selectState(id))} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{view ? view.state_name : "All states"}</CardTitle>
            <CardDescription>
              {view ? `${view.provenance.source}${view.provenance.note ? ` - ${view.provenance.note}` : ""}` : "Aggregated from state analytics"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {view ? (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <Kpi icon={Users} label="Farmers represented" value={view.totals.farmers_represented.toLocaleString("en-IN")} hint={`${view.totals.fields_represented.toLocaleString("en-IN")} fields`} />
                  <Kpi icon={Leaf} label="Avg Farm Health" value={`${view.totals.avg_farm_health}`} hint={`${view.totals.active_crops} active crops`} />
                  <Kpi icon={Droplets} label="Water stress index" value={view.totals.avg_water_stress_index.toFixed(2)} hint="0 = none, 1 = severe" />
                  <Kpi icon={AlertTriangle} label="Disease / stress alerts" value={`${view.totals.disease_alerts}`} hint={`${view.totals.high_weather_risk_districts} high weather-risk districts`} />
                </div>
                <div>
                  <p className="mb-1 text-sm font-medium">Crop distribution (area share)</p>
                  <CropBars dist={view.crop_distribution_pct} />
                </div>
                <div>
                  <p className="mb-1 text-sm font-medium">Disease / stress hotspots</p>
                  <ul className="flex flex-col gap-1 text-sm">
                    {view.hotspots.map((h) => (
                      <li key={h.district_id} className="flex items-start justify-between gap-2">
                        <button className="text-left underline-offset-2 hover:underline" onClick={() => setDistrictId(h.district_id)}>
                          {h.district}: {h.top_issues.join("; ")}
                        </button>
                        <Badge variant={h.weather_risk === "high" ? "destructive" : "secondary"}>{h.disease_alerts}</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-md border p-2 text-xs">
                  <p className="font-medium">Live platform activity (this demo)</p>
                  <p className="text-muted-foreground">
                    {view.platform_activity.registered_fields} fields · {view.platform_activity.advisories_generated} advisories ·{" "}
                    {view.platform_activity.diagnoses} Crop Doctor checks · {view.platform_activity.pending_reviews} awaiting review
                  </p>
                </div>
              </>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>State</TableHead>
                    <TableHead className="text-right">Farmers</TableHead>
                    <TableHead className="text-right">Health</TableHead>
                    <TableHead className="text-right">Alerts</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {overview.states.map((s) => (
                    <TableRow key={s.state_id} className="cursor-pointer" onClick={() => selectState(s.state_id)}>
                      <TableCell>{s.state_name}</TableCell>
                      <TableCell className="text-right tabular-nums">{s.farmers_represented.toLocaleString("en-IN")}</TableCell>
                      <TableCell className="text-right tabular-nums">{s.avg_farm_health}</TableCell>
                      <TableCell className="text-right tabular-nums">{s.disease_alerts}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {view ? (
        <Card>
          <CardHeader>
            <CardTitle>Districts</CardTitle>
            <CardDescription>Crop health, weather risk, water stress and disease/stress alerts per district. Click a row for blocks.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>District</TableHead>
                  <TableHead className="text-right">Farmers</TableHead>
                  <TableHead className="text-right">Farm Health</TableHead>
                  <TableHead>Weather risk</TableHead>
                  <TableHead className="text-right">Water stress</TableHead>
                  <TableHead className="text-right">Alerts</TableHead>
                  <TableHead className="text-right">Advisories (7d)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {view.districts.map((d) => (
                  <TableRow key={d.district_id} className="cursor-pointer" data-state={districtId === d.district_id ? "selected" : undefined} onClick={() => setDistrictId(d.district_id)}>
                    <TableCell className="font-medium">{d.district}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.farmers_represented.toLocaleString("en-IN")}</TableCell>
                    <TableCell className="text-right tabular-nums" style={{ color: healthColor(d.avg_farm_health) }}>{d.avg_farm_health}</TableCell>
                    <TableCell>
                      <Badge variant={d.weather_risk === "high" ? "destructive" : d.weather_risk === "medium" ? "outline" : "secondary"} title={d.weather_risk_reason}>
                        {d.weather_risk}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{d.water_stress_index.toFixed(2)}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.disease_alerts}</TableCell>
                    <TableCell className="text-right tabular-nums">{d.advisories_issued_7d}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {view && district && districtId === district.district_id ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sprout className="size-4" /> {district.district}: risks and blocks
              <ModeBadge demo={district.provenance.is_sample} />
            </CardTitle>
            <CardDescription>Reference date {district.reference_date}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <ul className="flex flex-col gap-2 text-sm">
              {district.risks.map((r, i) => (
                <li key={i} className="flex items-center gap-2">
                  <Badge variant={r.level === "high" ? "destructive" : "outline"}>{r.type.replaceAll("_", " ")}</Badge> {r.detail}
                </li>
              ))}
              <li className="text-xs text-muted-foreground">
                Platform (live): {district.platform_activity.registered_fields} registered fields, {district.platform_activity.diagnoses} Crop Doctor checks
                {district.platform_activity.recent_diagnoses.length
                  ? ` - latest: ${district.platform_activity.recent_diagnoses[0].potential_condition} (${district.platform_activity.recent_diagnoses[0].severity})`
                  : ""}
              </li>
            </ul>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Block</TableHead>
                  <TableHead className="text-right">Health</TableHead>
                  <TableHead className="text-right">Water stress</TableHead>
                  <TableHead className="text-right">Alerts</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {district.blocks.map((b) => (
                  <TableRow key={b.block}>
                    <TableCell>{b.block}</TableCell>
                    <TableCell className="text-right tabular-nums" style={{ color: healthColor(b.avg_farm_health) }}>{b.avg_farm_health}</TableCell>
                    <TableCell className="text-right tabular-nums">{b.water_stress_index.toFixed(2)}</TableCell>
                    <TableCell className="text-right tabular-nums">{b.disease_alerts}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

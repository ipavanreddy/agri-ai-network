"use client";

import { CloudRain, Droplets, Leaf, Satellite, Thermometer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { HealthScore } from "@/components/health-score";
import { ModeBadge, SourceLine } from "@/components/mode-badge";
import { fmt } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Intelligence } from "@/lib/types";

function NdviChart({ series, expected }: { series: Intelligence["satellite"]["series"]; expected: number | null }) {
  if (series.length < 2) return <p className="text-sm text-muted-foreground">Not enough observations.</p>;
  const w = 280;
  const h = 90;
  const xs = series.map((p) => new Date(p.date).getTime());
  const [x0, x1] = [Math.min(...xs), Math.max(...xs)];
  const x = (t: number) => ((t - x0) / Math.max(1, x1 - x0)) * (w - 8) + 4;
  const y = (v: number) => h - 4 - v * (h - 8);
  const path = series.map((p, i) => `${i ? "L" : "M"}${x(xs[i]).toFixed(1)},${y(p.ndvi).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-24 w-full" role="img" aria-label="NDVI time series">
      <line x1={0} x2={w} y1={y(0.5)} y2={y(0.5)} className="stroke-muted-foreground/30" strokeDasharray="3 3" />
      {expected ? <line x1={0} x2={w} y1={y(expected)} y2={y(expected)} stroke="#16a34a" strokeOpacity={0.6} strokeDasharray="6 3" /> : null}
      <path d={path} fill="none" stroke="#15803d" strokeWidth={2} />
      {series.map((p, i) => (
        <circle key={p.date} cx={x(xs[i])} cy={y(p.ndvi)} r={2.5} fill="#15803d">
          <title>{`${p.date}: NDVI ${p.ndvi.toFixed(2)}`}</title>
        </circle>
      ))}
    </svg>
  );
}

function RainBars({ daily }: { daily: Intelligence["weather"]["daily"] }) {
  const max = Math.max(5, ...daily.map((d) => d.rain_mm ?? 0));
  return (
    <div className="flex h-16 items-end gap-0.5" aria-label="Daily rainfall, past 14 days and 7-day forecast">
      {daily.map((d) => (
        <div
          key={d.date}
          title={`${d.date}: ${fmt(d.rain_mm, 1)} mm${d.is_forecast ? " (forecast)" : ""}`}
          className={d.is_forecast ? "flex-1 rounded-t bg-sky-300 dark:bg-sky-700" : "flex-1 rounded-t bg-sky-600"}
          style={{ height: `${Math.max(2, ((d.rain_mm ?? 0) / max) * 100)}%` }}
        />
      ))}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function IntelligencePanel({ intel }: { intel: Intelligence }) {
  const { t, lang } = useI18n();
  const { weather: w, soil, satellite: sat } = intel;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2">
            {intel.crop.names?.[lang] ?? intel.crop.name} · {intel.field.area_acres} {t("acres")} · {intel.field.district}
            <ModeBadge demo={intel.demo_mode} />
          </CardTitle>
          <CardDescription>
            {t("stage")}: {intel.current_stage.stage.replaceAll("_", " ")}
            {intel.current_stage.days_after_sowing !== null ? ` · ${intel.current_stage.days_after_sowing} ${t("days_after_sowing")}` : ""}
            {" · "}
            {intel.field.irrigation} · {intel.field.farming_practice.replaceAll("_", " ")}
            {intel.scenario_note ? <span className="block text-amber-700 dark:text-amber-400">{intel.scenario_note}</span> : null}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <HealthScore health={intel.health} />
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CloudRain className="size-4" /> {t("weather")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-2">
              <Stat label={t("temperature")} value={fmt(w.temperature_c, 1, " °C")} />
              <Stat label={t("humidity")} value={fmt(w.humidity_pct, 0, "%")} />
              <Stat label={t("rain_14d")} value={fmt(w.rain_past_14d_mm, 0, " mm")} />
              <Stat label={t("rain_3d")} value={fmt(w.rain_next_3d_mm, 0, " mm")} />
            </div>
            <RainBars daily={w.daily} />
            <div className="flex flex-wrap gap-1">
              {w.alerts.map((a) => (
                <Badge key={a.code} variant={a.severity === "high" ? "destructive" : "secondary"} title={a.message}>
                  {a.message}
                </Badge>
              ))}
            </div>
            <SourceLine p={w.provenance} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Leaf className="size-4" /> {t("soil")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {soil ? (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <Stat label="pH" value={fmt(soil.ph, 1)} />
                  <Stat label={t("organic_carbon")} value={fmt(soil.organic_carbon_pct, 2, "%")} />
                  <Stat label="N / P / K (kg/ha)" value={`${fmt(soil.nitrogen_kg_ha)} / ${fmt(soil.phosphorus_kg_ha)} / ${fmt(soil.potassium_kg_ha)}`} />
                  <Stat label="Clay / sand / silt" value={`${fmt(soil.clay_pct)} / ${fmt(soil.sand_pct)} / ${fmt(soil.silt_pct)}%`} />
                </div>
                <SourceLine p={soil.provenance} label="NPK, pH, OC" />
                {soil.texture_provenance ? <SourceLine p={soil.texture_provenance} label="Texture" /> : null}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No soil record for this location.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Satellite className="size-4" /> {t("satellite")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-2">
              <Stat label={t("ndvi")} value={fmt(sat.latest_ndvi, 2)} />
              <Stat label="Δ 30 days" value={sat.ndvi_change_30d === null ? "n/a" : `${sat.ndvi_change_30d > 0 ? "+" : ""}${sat.ndvi_change_30d.toFixed(2)}`} />
            </div>
            <NdviChart series={sat.series} expected={intel.current_stage.expected_ndvi} />
            {sat.thumbnail_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={sat.thumbnail_url} alt="NDVI image of the field" className="h-32 w-32 rounded border" />
            ) : null}
            <SourceLine p={sat.provenance} />
          </CardContent>
        </Card>
      </div>
      <p className="flex items-center gap-1 text-xs text-muted-foreground">
        <Thermometer className="size-3" /> <Droplets className="size-3" /> Weather, soil and satellite inputs are combined into the
        Farm Health score and passed as structured context to the AI advisory.
      </p>
    </div>
  );
}

"use client";

import { useI18n, type StringKey } from "@/lib/i18n";
import type { FarmHealth } from "@/lib/types";
import { cn } from "@/lib/utils";

const BAND_STYLE = {
  Good: "text-emerald-700 dark:text-emerald-400",
  Moderate: "text-amber-700 dark:text-amber-400",
  Poor: "text-red-700 dark:text-red-400",
} as const;

const BAR = { good: "bg-emerald-500", moderate: "bg-amber-500", poor: "bg-red-500", missing: "bg-muted" } as const;

export function HealthScore({ health }: { health: FarmHealth }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
      <div className="flex min-w-36 flex-col items-center rounded-xl border p-4">
        <span className="text-sm text-muted-foreground">{t("farm_health")}</span>
        <span className={cn("text-5xl font-semibold tabular-nums", BAND_STYLE[health.band])}>{health.score}</span>
        <span className="text-xs text-muted-foreground">/ 100</span>
        <span className={cn("mt-1 font-medium", BAND_STYLE[health.band])}>{health.band}</span>
      </div>
      <ul className="flex flex-1 flex-col gap-2.5">
        {health.factors.map((f) => (
          <li key={f.key} className="flex flex-col gap-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">
                {t(f.key as StringKey)} <span className="text-xs text-muted-foreground">({Math.round(f.weight * 100)}%)</span>
              </span>
              <span className="tabular-nums">{f.score === null ? "missing" : Math.round(f.score)}</span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div className={cn("h-2 rounded-full", BAR[f.status])} style={{ width: `${f.score ?? 0}%` }} />
            </div>
            <p className="text-xs text-muted-foreground">{f.drivers.join(" · ")}</p>
          </li>
        ))}
        <li className="text-xs text-muted-foreground">
          Method {health.method}: weighted sum of observed factors; missing factors are re-weighted, never imputed.
        </li>
      </ul>
    </div>
  );
}

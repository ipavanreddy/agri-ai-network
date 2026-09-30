import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/format";
import type { Provenance } from "@/lib/types";

const DEMO = "border-amber-300 bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100";
const LIVE = "border-emerald-300 bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100";

/** Visible "Demo mode / sample data" marker required whenever fallbacks or sample data are shown. */
export function ModeBadge({ demo, label }: { demo: boolean; label?: string }) {
  return (
    <Badge variant="outline" className={demo ? DEMO : LIVE}>
      {label ?? (demo ? "Demo mode · sample data" : "Live data")}
    </Badge>
  );
}

export function AiBadge({ mode, model }: { mode: "live" | "demo"; model: string }) {
  return (
    <Badge variant="outline" className={mode === "demo" ? DEMO : LIVE}>
      {mode === "demo" ? "Demo AI (rules, no Gemini call)" : `Gemini · ${model}`}
    </Badge>
  );
}

/** Source + freshness line for one data block (PRD §36). */
export function SourceLine({ p, label }: { p: Provenance; label?: string }) {
  const demo = p.mode === "demo" || p.is_sample;
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
      {label ? <span className="font-medium text-foreground">{label}:</span> : null}
      <span>{p.source}</span>
      <span>· observed {timeAgo(p.reference_timestamp)}</span>
      {demo ? <ModeBadge demo label={p.is_synthetic ? "Sample · synthetic" : "Sample"} /> : <ModeBadge demo={false} label="Live" />}
      {p.note ? <span className="w-full italic">{p.note}</span> : null}
    </div>
  );
}

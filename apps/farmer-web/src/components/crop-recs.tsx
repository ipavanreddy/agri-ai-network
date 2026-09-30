"use client";

import { useState } from "react";
import { Loader2, Wheat } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AiBadge, ModeBadge } from "@/components/mode-badge";
import { ReviewStatus } from "@/components/review-status";
import { apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { CropRecommendation } from "@/lib/types";

const SUIT = {
  High: "bg-emerald-600 text-white",
  Moderate: "bg-amber-500 text-white",
  Low: "bg-muted text-muted-foreground",
} as const;

export function CropRecs({ fieldId, useSample }: { fieldId: string; useSample: boolean }) {
  const { t, lang } = useI18n();
  const [rec, setRec] = useState<CropRecommendation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setRec(await apiPost<CropRecommendation>("/api/crop-recommendation", { field_id: fieldId, use_sample: useSample }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          {t("step_crops")}
          {rec ? <AiBadge mode={rec.ai.mode} model={rec.ai.model_name} /> : null}
          {rec ? <ModeBadge demo={rec.demo_mode} /> : null}
        </CardTitle>
        <CardDescription>Transparent rule scores (pH, temperature, water, climate risk, rotation value), explained by Gemini.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Button onClick={run} disabled={busy} className="w-fit">
          {busy ? <Loader2 className="animate-spin" /> : <Wheat />} {t("get_recommendations")}
        </Button>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {rec ? (
          <>
            <ReviewStatus review={rec.review} />
            <p className="text-sm">{rec.summary}</p>
            <ol className="grid gap-3 md:grid-cols-2">
              {rec.options.map((o, i) => (
                <li key={o.crop_id} className="flex flex-col gap-1.5 rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">
                      {i + 1}. {o.names?.[lang] ?? o.crop_id}
                    </span>
                    <Badge className={SUIT[o.suitability]}>
                      {t("suitability")}: {o.suitability}
                    </Badge>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-muted">
                    <div className="h-1.5 rounded-full bg-emerald-600" style={{ width: `${o.score}%` }} />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Rule score {o.score}/100 ({Object.entries(o.breakdown).map(([k, v]) => `${k.replace("_", " ")} ${v}`).join(", ")})
                  </span>
                  <ul className="list-disc pl-4 text-sm">
                    {o.reasons.map((r, j) => <li key={j}>{r}</li>)}
                  </ul>
                  {o.risks.length ? (
                    <ul className="list-disc pl-4 text-xs text-amber-800 dark:text-amber-300">
                      {o.risks.map((r, j) => <li key={j}>{r}</li>)}
                    </ul>
                  ) : null}
                  {o.regenerative_role ? <p className="text-xs text-emerald-800 dark:text-emerald-300">♻ {o.regenerative_role}</p> : null}
                </li>
              ))}
            </ol>
            <p className="text-sm">
              <span className="font-semibold">{t("rotation_plan")}:</span> {rec.rotation_plan}
            </p>
            <p className="text-xs text-muted-foreground">
              Not considered: {rec.missing_information.join("; ")} · model {rec.ai.model_name} · prompt {rec.ai.prompt_version}
            </p>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

"use client";

import { useState } from "react";
import { Camera, ImageIcon, Loader2, Stethoscope } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AiBadge } from "@/components/mode-badge";
import { NearbySupport } from "@/components/nearby-support";
import { ReviewStatus } from "@/components/review-status";
import { API_URL, apiUpload } from "@/lib/api";
import { pct } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Diagnosis } from "@/lib/types";

const SAMPLE_URL = `${API_URL}/samples/leaf_spot_synthetic.png`;

export function CropDoctor({ fieldId, onDiagnosed }: { fieldId: string; onDiagnosed: () => void }) {
  const { t } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Diagnosis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function choose(f: File | null) {
    setFile(f);
    setResult(null);
    setPreview(f ? URL.createObjectURL(f) : null);
  }

  async function loadSample() {
    const blob = await (await fetch(SAMPLE_URL)).blob();
    choose(new File([blob], "leaf_spot_synthetic.png", { type: "image/png" }));
  }

  async function analyse() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("image", file);
      form.append("field_id", fieldId);
      setResult(await apiUpload<Diagnosis>("/api/diagnosis", form));
      onDiagnosed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const r = result?.result;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          {t("step_doctor")}
          {result ? <AiBadge mode={result.ai.mode} model={result.ai.model_name} /> : null}
        </CardTitle>
        <CardDescription>AI-assisted preliminary assessment from a photo - not a certified diagnosis.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-sm hover:bg-muted">
            <Camera className="size-4" /> {t("upload_photo")}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              capture="environment"
              className="sr-only"
              onChange={(e) => choose(e.target.files?.[0] ?? null)}
            />
          </label>
          <Button variant="outline" onClick={loadSample}>
            <ImageIcon /> {t("use_sample_photo")}
          </Button>
          <Button onClick={analyse} disabled={!file || busy}>
            {busy ? <Loader2 className="animate-spin" /> : <Stethoscope />} {t("analyse")}
          </Button>
        </div>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <div className="flex flex-col gap-4 md:flex-row">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Selected crop photo" className="h-48 w-48 rounded-lg border object-cover" />
          ) : null}
          {result && r ? (
            <div className="flex flex-1 flex-col gap-3 text-sm">
              {result.demo_mode ? (
                <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
                  Demo mode: example output for this crop - the photo was not analysed. Set GEMINI_API_KEY for real analysis.
                </p>
              ) : null}
              {!r.image_usable ? <p className="text-destructive">Image problem: {r.image_issue}</p> : null}
              <div>
                <span className="text-xs text-muted-foreground">{t("potential_condition")}</span>
                <p className="text-lg font-medium">{result.potential_condition}</p>
                <div className="mt-1 flex flex-wrap gap-2">
                  <Badge variant="outline">
                    {t("confidence")}: {pct(result.confidence)}
                  </Badge>
                  <Badge variant={result.severity === "high" ? "destructive" : "secondary"}>
                    {t("severity")}: {result.severity}
                  </Badge>
                  <Badge variant="outline">{r.plant_part}</Badge>
                </div>
              </div>
              <div>
                <p className="font-semibold">{t("visible_symptoms")}</p>
                <ul className="list-disc pl-5">{r.visible_symptoms.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
              {r.potential_conditions.length > 1 ? (
                <div className="text-xs text-muted-foreground">
                  Other possibilities:{" "}
                  {r.potential_conditions.slice(1).map((c) => `${c.name} (${pct(c.likelihood)})`).join("; ")}
                </div>
              ) : null}
              <div>
                <p className="font-semibold">{t("next_steps")}</p>
                <ol className="list-decimal pl-5">{r.recommended_next_actions.map((s, i) => <li key={i}>{s}</li>)}</ol>
              </div>
              <NearbySupport fieldId={fieldId} />
              <ReviewStatus review={result.review} />
              <p className="text-xs text-muted-foreground">{result.disclaimer}</p>
              <p className="text-xs text-muted-foreground">
                {result.diagnosis_id} · model {result.ai.model_name} · prompt {result.ai.prompt_version} · {r.explanation}
              </p>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

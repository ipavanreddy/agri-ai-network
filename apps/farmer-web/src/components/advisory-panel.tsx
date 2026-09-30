"use client";

import { useEffect, useState } from "react";
import { Loader2, Sprout, Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AiBadge, ModeBadge } from "@/components/mode-badge";
import { ReviewStatus } from "@/components/review-status";
import { apiGet, apiPost } from "@/lib/api";
import { pct } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { speak } from "@/lib/speech";
import type { Advisory, AdvisoryContent, Lang } from "@/lib/types";

const RISK_VARIANT = { low: "secondary", medium: "outline", high: "destructive" } as const;

export function AdvisoryPanel({ fieldId, useSample }: { fieldId: string; useSample: boolean }) {
  const { t, lang } = useI18n();
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [localized, setLocalized] = useState<Record<string, { content: AdvisoryContent; method: string }>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voice, setVoice] = useState<string | null>(null);

  // Present the SAME advisory in the selected language (no re-analysis, FR-07).
  useEffect(() => {
    if (!advisory || lang === "en" || localized[lang]) return;
    let cancelled = false;
    apiPost<{ content: AdvisoryContent; method: string }>(`/api/advisories/${advisory.advisory_id}/localize`, { language: lang })
      .then((r) => !cancelled && setLocalized((prev) => ({ ...prev, [lang]: r })))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [advisory, lang, localized]);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const a = await apiPost<Advisory>("/api/advisory/generate", { field_id: fieldId, language: lang, use_sample: useSample });
      setAdvisory(a);
      setLocalized(Object.fromEntries(Object.entries(a.localized ?? {}).map(([k, v]) => [k, { content: v.content, method: v.method }])));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function refreshReview() {
    if (!advisory) return;
    const fresh = await apiGet<Advisory>(`/api/advisories/${advisory.advisory_id}`);
    setAdvisory((a) => (a ? { ...a, review: fresh.review } : a));
  }

  const view: AdvisoryContent | null = advisory ? (lang === "en" ? advisory.content : localized[lang]?.content ?? null) : null;
  const method = lang === "en" ? "original" : localized[lang]?.method;

  async function listen() {
    if (!view) return;
    const text = [view.summary, ...view.recommendations.map((r) => r.action), view.regenerative_practice.action].join(" ");
    const mode = await speak(text, lang as Lang);
    setVoice(mode === "cloud" ? "Cloud Text-to-Speech" : mode === "browser" ? "Browser voice (demo fallback)" : "No voice available");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          {t("step_advisory")}
          {advisory ? <AiBadge mode={advisory.ai.mode} model={advisory.ai.model_name} /> : null}
          {advisory ? <ModeBadge demo={advisory.demo_mode} /> : null}
        </CardTitle>
        <CardDescription>Gemini reasons over the structured field context only; observations, interpretation and actions are kept separate.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-2">
          <Button onClick={generate} disabled={busy}>
            {busy ? <Loader2 className="animate-spin" /> : <Sprout />} {t("generate_advisory")}
          </Button>
          {view ? (
            <Button variant="outline" onClick={listen}>
              <Volume2 /> {t("listen")}
            </Button>
          ) : null}
          {voice ? <span className="self-center text-xs text-muted-foreground">{voice}</span> : null}
        </div>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {advisory && !view ? <p className="text-sm text-muted-foreground">{t("loading")}</p> : null}
        {advisory && view ? (
          <div className="flex flex-col gap-4">
            <ReviewStatus review={advisory.review} onRefresh={refreshReview} />
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-lg font-medium">{view.summary}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <Badge variant={RISK_VARIANT[view.risk_level]}>
                  {t("risk")}: {view.risk_level}
                </Badge>
                <Badge variant="outline">{view.time_sensitivity.replaceAll("_", " ")}</Badge>
                <Badge variant="outline">
                  {t("confidence")}: {pct(view.confidence)}
                </Badge>
                {method && method !== "original" ? <Badge variant="outline">translation: {method.replaceAll("_", " ")}</Badge> : null}
              </div>
            </div>
            <section>
              <h3 className="mb-1 text-sm font-semibold">① {t("observed")}</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {view.observations.map((o, i) => (
                  <li key={i}>
                    {o.fact} <span className="text-xs text-muted-foreground">({o.category} · {o.source})</span>
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="mb-1 text-sm font-semibold">② {t("interpretation")}</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {view.interpretations.map((x, i) => (
                  <li key={i}>
                    {x.statement} <span className="text-xs text-muted-foreground">(uncertainty: {x.uncertainty}; based on {x.based_on.join(", ")})</span>
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="mb-1 text-sm font-semibold">③ {t("recommendation")}</h3>
              <ol className="space-y-2 text-sm">
                {view.recommendations.map((r, i) => (
                  <li key={i} className="rounded-md border p-2">
                    <div className="flex flex-wrap items-center gap-2 font-medium">
                      <Badge variant={r.priority === "high" ? "destructive" : "secondary"}>{r.priority}</Badge>
                      {r.action}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {r.timeframe} · {r.reason}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
            <section className="rounded-lg border border-emerald-300 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950/40">
              <h3 className="mb-1 text-sm font-semibold">{t("regenerative")}</h3>
              <p className="text-sm font-medium">{view.regenerative_practice.action}</p>
              <p className="text-xs text-muted-foreground">
                {view.regenerative_practice.reason} (evidence: {view.regenerative_practice.evidence.join(", ")})
              </p>
            </section>
            <div className="grid gap-3 text-xs text-muted-foreground md:grid-cols-2">
              <div>
                <p className="font-semibold text-foreground">{t("missing_info")}</p>
                <ul className="list-disc pl-4">{view.missing_information.map((m, i) => <li key={i}>{m}</li>)}</ul>
              </div>
              <div>
                <p className="font-semibold text-foreground">{t("freshness")}</p>
                <ul className="list-disc pl-4">{view.data_freshness_notes.map((m, i) => <li key={i}>{m}</li>)}</ul>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {advisory.advisory_id} · model {advisory.ai.model_name} ({advisory.ai.model_version}) · prompt {advisory.ai.prompt_version}
              {advisory.ai.fallback_reason ? ` · ${advisory.ai.fallback_reason}` : ""}
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

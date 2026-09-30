"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { AdvisoryPanel } from "@/components/advisory-panel";
import { CropDoctor } from "@/components/crop-doctor";
import { CropRecs } from "@/components/crop-recs";
import { useMapProvider } from "@/components/field-map";
import { FieldSetup } from "@/components/field-setup";
import { IntelligencePanel } from "@/components/intelligence-panel";
import { ModeBadge } from "@/components/mode-badge";
import { VoiceAssistant } from "@/components/voice-assistant";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet, apiPatch } from "@/lib/api";
import { I18nProvider, LANG_LABELS, useI18n } from "@/lib/i18n";
import type { Crop, Farmer, Field, Intelligence, Lang, StateConfig, SystemStatus } from "@/lib/types";

function Shell() {
  const { live: MAPS_LIVE, label: mapLabel } = useMapProvider();
  const { t, lang, setLang } = useI18n();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [states, setStates] = useState<StateConfig[]>([]);
  const [crops, setCrops] = useState<Crop[]>([]);
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [fieldId, setFieldId] = useState<string | null>(null);
  const [intel, setIntel] = useState<Intelligence | null>(null);
  const [loadingIntel, setLoadingIntel] = useState(false);
  const [intelError, setIntelError] = useState<string | null>(null);
  const [useSample, setUseSample] = useState(false);

  useEffect(() => {
    Promise.all([
      apiGet<SystemStatus>("/api/system/status"),
      apiGet<StateConfig[]>("/api/states"),
      apiGet<{ crops: Crop[] }>("/api/crops"),
      apiGet<Farmer[]>("/api/farmers"),
      apiGet<Field[]>("/api/fields"),
    ])
      .then(([s, st, c, fa, fi]) => {
        setStatus(s);
        setStates(st);
        setCrops(c.crops);
        setFarmers(fa);
        setFields(fi);
        setFieldId((cur) => cur ?? fi[0]?.field_id ?? null);
      })
      .catch(() => setApiDown(true));
  }, []);

  const loadIntel = useCallback(async (id: string, sample: boolean) => {
    setLoadingIntel(true);
    setIntelError(null);
    try {
      setIntel(await apiGet<Intelligence>(`/api/fields/${id}/intelligence?sample=${sample}`));
    } catch (e) {
      setIntelError((e as Error).message);
    } finally {
      setLoadingIntel(false);
    }
  }, []);

  useEffect(() => {
    if (!fieldId) return;
    let cancelled = false;
    apiGet<Intelligence>(`/api/fields/${fieldId}/intelligence?sample=${useSample}`)
      .then((d) => !cancelled && setIntel(d))
      .catch((e: Error) => !cancelled && setIntelError(e.message));
    return () => {
      cancelled = true;
    };
  }, [fieldId, useSample]);

  function changeLang(l: Lang) {
    setLang(l);
    const farmerId = intel?.farmer.farmer_id;
    if (farmerId) apiPatch(`/api/farmers/${farmerId}`, { preferred_language: l }).catch(() => undefined);
  }

  const cloudSpeech = status?.integrations.find((i) => i.key === "speech")?.mode === "live";
  // The browser Maps key is baked into this app at build time, so only the app can report it.
  const integrations = (status?.integrations ?? []).map((i) =>
    i.key === "maps" ? { ...i, mode: MAPS_LIVE ? ("live" as const) : ("demo" as const), detail: MAPS_LIVE ? "Satellite basemap" : mapLabel } : i,
  );
  const demoIntegrations = integrations.filter((i) => i.mode === "demo");
  const liveIntegrations = integrations.filter((i) => i.mode === "live");

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-4 sm:p-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-1">
          <Badge variant="secondary" className="w-fit">Farmer</Badge>
          <h1 className="text-3xl font-semibold tracking-tight">{t("app_title")}</h1>
          <p className="text-muted-foreground">{t("tagline")}</p>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <div className="flex items-center gap-1" role="group" aria-label={t("language")}>
            {(Object.keys(LANG_LABELS) as Lang[]).map((l) => (
              <button
                key={l}
                onClick={() => changeLang(l)}
                className={`rounded-md border px-2.5 py-1 text-sm ${l === lang ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
              >
                {LANG_LABELS[l]}
              </button>
            ))}
          </div>
          {apiDown ? <Badge variant="destructive">API unreachable on {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8040"}</Badge> : null}
          {status ? (
            <div className="flex flex-wrap gap-1" title={integrations.map((i) => `${i.mode === "live" ? "LIVE" : "DEMO"} ${i.label}: ${i.detail}`).join("\n")}>
              <ModeBadge demo={false} label={`${liveIntegrations.length} Google/public integrations live`} />
              {demoIntegrations.length ? <ModeBadge demo label={`Demo mode · ${demoIntegrations.length} on fallback`} /> : null}
            </div>
          ) : null}
        </div>
      </header>

      {status && demoIntegrations.length ? (
        <details className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
          <summary className="cursor-pointer font-medium">Demo mode: some Google integrations are using labelled fallbacks</summary>
          <p className="mt-2">
            <span className="font-medium">Live:</span> {liveIntegrations.map((i) => i.label).join(" · ")}
          </p>
          <p className="mt-1 font-medium">On fallback:</p>
          <ul className="list-disc pl-5">
            {demoIntegrations.map((i) => (
              <li key={i.key}>
                <span className="font-medium">{i.label}</span>: {i.detail} <span className="text-xs">(enable with {i.env})</span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <FieldSetup
        states={states}
        crops={crops}
        farmers={farmers}
        fields={fields}
        selectedFieldId={fieldId}
        onSelectField={setFieldId}
        onCreated={(farmer, field) => {
          setFarmers((f) => [...f, farmer]);
          setFields((f) => [...f, field]);
          setFieldId(field.field_id);
        }}
      />

      <label className="flex w-fit items-center gap-2 text-sm">
        <input type="checkbox" checked={useSample} onChange={(e) => setUseSample(e.target.checked)} />
        {t("sample_toggle")}
      </label>

      {!fieldId ? (
        <p className="text-muted-foreground">{t("select_field_first")}</p>
      ) : (
        <>
          <section className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold">{t("step_intel")}</h2>
            {intelError ? <p className="text-sm text-destructive">{intelError}</p> : null}
            {loadingIntel || !intel || intel.field.field_id !== fieldId ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Loader2 className="size-4 animate-spin" /> {t("loading")}
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">Fetching weather, soil and satellite signals...</CardContent>
              </Card>
            ) : (
              <IntelligencePanel intel={intel} />
            )}
          </section>
          <AdvisoryPanel key={`adv-${fieldId}-${useSample}`} fieldId={fieldId} useSample={useSample} />
          <CropRecs key={`rec-${fieldId}-${useSample}`} fieldId={fieldId} useSample={useSample} />
          <CropDoctor key={`dx-${fieldId}`} fieldId={fieldId} onDiagnosed={() => loadIntel(fieldId, useSample)} />
          <VoiceAssistant key={`va-${fieldId}`} fieldId={fieldId} useSample={useSample} cloudSpeech={cloudSpeech} />
        </>
      )}
      <footer className="pb-6 text-xs text-muted-foreground">
        AI outputs are drafts for human review. Sample and synthetic data are labelled wherever shown. Map data © OpenStreetMap contributors
        (when the Google Maps key is not set).
      </footer>
    </main>
  );
}

export default function FarmerApp() {
  return (
    <I18nProvider>
      <Shell />
    </I18nProvider>
  );
}

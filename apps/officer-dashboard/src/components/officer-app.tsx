"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InteropView } from "@/components/interop-view";
import { ModeBadge } from "@/components/mode-badge";
import { RegionalView } from "@/components/regional-view";
import { ReviewQueue } from "@/components/review-queue";
import { apiGet } from "@/lib/api";
import type { Integration, Overview } from "@/lib/types";

export default function OfficerApp() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [apiDown, setApiDown] = useState(false);

  const refresh = useCallback(() => {
    apiGet<Overview>("/api/overview").then(setOverview).catch(() => setApiDown(true));
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([apiGet<Overview>("/api/overview"), apiGet<{ integrations: Integration[] }>("/api/system/status")])
      .then(([o, s]) => {
        if (cancelled) return;
        setOverview(o);
        setIntegrations(s.integrations);
      })
      .catch(() => !cancelled && setApiDown(true));
    return () => {
      cancelled = true;
    };
  }, []);

  const demo = integrations.filter((i) => i.mode === "demo");
  const pending = overview?.platform_activity.pending_reviews ?? 0;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 sm:p-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-1">
          <Badge variant="secondary" className="w-fit">Agriculture Officer</Badge>
          <h1 className="text-3xl font-semibold tracking-tight">Agri AI Network: regional intelligence</h1>
          <p className="text-muted-foreground">India → State → District → Block, built on one canonical agriculture data model.</p>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          {apiDown ? <Badge variant="destructive">API unreachable</Badge> : null}
          {overview ? <ModeBadge demo={overview.demo_mode || demo.length > 0} label={demo.length ? `Demo mode · ${demo.length} integrations on fallback` : undefined} /> : null}
        </div>
      </header>

      {demo.length ? (
        <details className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
          <summary className="cursor-pointer font-medium">Demo mode: regional indicators are synthetic samples; some Google integrations use fallbacks</summary>
          <ul className="mt-2 list-disc pl-5">
            {demo.map((i) => (
              <li key={i.key}>
                <span className="font-medium">{i.label}</span>: {i.detail} <span className="text-xs">(enable with {i.env})</span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <Tabs defaultValue="regional">
        <TabsList>
          <TabsTrigger value="regional">Regional risks</TabsTrigger>
          <TabsTrigger value="review">
            Review queue {pending ? <Badge className="ml-1">{pending}</Badge> : null}
          </TabsTrigger>
          <TabsTrigger value="interop">Interoperability</TabsTrigger>
        </TabsList>
        <TabsContent value="regional" className="pt-2">
          {overview ? <RegionalView overview={overview} /> : <p className="text-muted-foreground">Loading...</p>}
        </TabsContent>
        <TabsContent value="review" className="pt-2">
          <ReviewQueue onChange={refresh} />
        </TabsContent>
        <TabsContent value="interop" className="pt-2">
          <InteropView />
        </TabsContent>
      </Tabs>
    </main>
  );
}

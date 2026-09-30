"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ModeBadge } from "@/components/mode-badge";
import { apiGet } from "@/lib/api";
import type { AdapterDemo } from "@/lib/types";

const STATES = ["AP", "MH", "PB"];

function Json({ value }: { value: unknown }) {
  return <pre className="max-h-80 overflow-auto rounded-md bg-muted p-2 text-[11px] leading-snug">{JSON.stringify(value, null, 2)}</pre>;
}

/** "State-specific data, common interfaces": raw state record -> declarative mapping -> canonical record. */
export function InteropView() {
  const [state, setState] = useState("AP");
  const [demo, setDemo] = useState<AdapterDemo | null>(null);
  const [entity, setEntity] = useState("field");

  useEffect(() => {
    let cancelled = false;
    apiGet<AdapterDemo>(`/api/states/${state}/adapter-demo`).then((d) => !cancelled && setDemo(d));
    return () => {
      cancelled = true;
    };
  }, [state]);

  const example = demo?.state_id === state ? demo.examples.find((e) => e.entity === entity) : null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Interoperability: state adapters → canonical schema
          <ModeBadge demo label="Sample state exports (synthetic)" />
        </CardTitle>
        <CardDescription>
          Each state keeps its own formats (codes, units, date formats, language). A declarative adapter (data/adapters/&lt;state&gt;.json)
          maps them into one canonical model that every shared service - Farm Health, advisory, crop recommendation, Crop Doctor - consumes.
        </CardDescription>
        <div className="flex flex-wrap gap-2">
          {STATES.map((s) => (
            <Button key={s} size="sm" variant={s === state ? "default" : "outline"} onClick={() => setState(s)}>
              {s}
            </Button>
          ))}
          <span className="mx-2 border-l" />
          {["farmer", "field", "soil"].map((e) => (
            <Button key={e} size="sm" variant={e === entity ? "secondary" : "ghost"} onClick={() => setEntity(e)}>
              {e}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {demo && demo.state_id === state ? (
          <p className="text-sm">
            <span className="font-medium">{demo.state_name}</span> · {demo.source_system} · adapter v{demo.adapter_version}{" "}
            <Badge variant="outline">{String((demo.source_meta as { dataset_version?: string }).dataset_version ?? "")}</Badge>
          </p>
        ) : null}
        {example ? (
          <div className="grid items-start gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr]">
            <div>
              <p className="mb-1 text-xs font-semibold">State record ({state} format)</p>
              <Json value={example.raw} />
            </div>
            <ArrowRight className="mt-10 hidden size-5 lg:block" />
            <div>
              <p className="mb-1 text-xs font-semibold">Adapter mapping</p>
              <Json value={example.mapping} />
            </div>
            <ArrowRight className="mt-10 hidden size-5 lg:block" />
            <div>
              <p className="mb-1 text-xs font-semibold">Canonical record (same for every state)</p>
              <Json value={example.canonical} />
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Loading...</p>
        )}
      </CardContent>
    </Card>
  );
}

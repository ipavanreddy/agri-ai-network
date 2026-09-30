"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, RefreshCw, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ModeBadge } from "@/components/mode-badge";
import { apiGet, apiPost } from "@/lib/api";
import type { ReviewItem } from "@/lib/types";

const KIND_LABEL = { advisories: "Advisory", diagnoses: "Crop Doctor", crop_recommendations: "Crop recommendation" } as const;

function Detail({ item }: { item: ReviewItem }) {
  const d = item.detail as Record<string, unknown>;
  if (item.kind === "advisories") {
    const c = d.content as { recommendations: { action: string; priority: string }[]; regenerative_practice: { action: string }; observations: { fact: string }[] };
    return (
      <div className="grid gap-2 text-sm md:grid-cols-2">
        <div>
          <p className="font-medium">Observed data</p>
          <ul className="list-disc pl-4 text-xs">{c.observations.map((o, i) => <li key={i}>{o.fact}</li>)}</ul>
        </div>
        <div>
          <p className="font-medium">Recommended actions</p>
          <ul className="list-disc pl-4 text-xs">
            {c.recommendations.map((r, i) => <li key={i}>[{r.priority}] {r.action}</li>)}
            <li>Regenerative: {c.regenerative_practice.action}</li>
          </ul>
        </div>
      </div>
    );
  }
  if (item.kind === "diagnoses") {
    const r = d.result as { visible_symptoms: string[]; recommended_next_actions: string[]; explanation: string };
    return (
      <div className="flex flex-col gap-2 text-sm md:flex-row">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8040"}/api/diagnoses/${item.id}/image`} alt="Uploaded crop photo" className="h-28 w-28 rounded border object-cover" />
        <div className="text-xs">
          <p>Confidence {Math.round((d.confidence as number) * 100)}% · symptoms: {r.visible_symptoms.join(", ")}</p>
          <p>Next actions: {r.recommended_next_actions.join("; ")}</p>
          <p className="text-muted-foreground">{r.explanation}</p>
        </div>
      </div>
    );
  }
  const opts = d.options as { crop_id: string; suitability: string; score: number }[];
  return <p className="text-xs">{opts.map((o) => `${o.crop_id} (${o.suitability}, ${o.score})`).join(" · ")}</p>;
}

export function ReviewQueue({ onChange }: { onChange: () => void }) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [filter, setFilter] = useState<"pending_officer_review" | "">("pending_officer_review");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    apiGet<ReviewItem[]>(`/api/review-queue?status=${filter}`).then(setItems).catch((e: Error) => setError(e.message));
  }, [filter]);

  useEffect(() => {
    let cancelled = false;
    apiGet<ReviewItem[]>(`/api/review-queue?status=${filter}`)
      .then((d) => !cancelled && setItems(d))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [filter]);

  async function decide(item: ReviewItem, decision: "approve" | "reject") {
    const verb = decision === "approve" ? "Approve" : "Reject";
    if (!window.confirm(`${verb} this ${KIND_LABEL[item.kind].toLowerCase()} for the farmer?`)) return;
    try {
      await apiPost(`/api/reviews/${item.kind}/${item.id}`, { decision, note: notes[item.id] || null, reviewer: "Agriculture Officer (demo)" });
      load();
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          Human review of AI outputs
          <Badge variant="secondary">{items.length}</Badge>
          <Button size="icon-sm" variant="ghost" onClick={load} aria-label="Refresh">
            <RefreshCw />
          </Button>
        </CardTitle>
        <CardDescription>Advisories, crop recommendations and Crop Doctor results stay AI drafts until an Agriculture Officer approves them.</CardDescription>
        <div className="flex gap-2 text-sm">
          <Button size="sm" variant={filter ? "default" : "outline"} onClick={() => setFilter("pending_officer_review")}>Pending</Button>
          <Button size="sm" variant={filter ? "outline" : "default"} onClick={() => setFilter("")}>All</Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {items.length === 0 ? <p className="text-sm text-muted-foreground">Nothing to review. Generate an advisory or run Crop Doctor in the farmer app.</p> : null}
        {items.map((item) => (
          <div key={`${item.kind}-${item.id}`} className="flex flex-col gap-2 rounded-lg border p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{KIND_LABEL[item.kind]}</Badge>
              {item.severity ? <Badge variant={item.severity === "high" ? "destructive" : "secondary"}>{item.severity}</Badge> : null}
              <span className="font-medium">{item.title}</span>
              {item.demo_mode ? <ModeBadge demo label="Demo AI / sample data" /> : null}
            </div>
            <p className="text-xs text-muted-foreground">
              {item.id} · {item.state}/{item.district} · field {item.field_id} · {item.model_name} · {item.prompt_version} ·{" "}
              {new Date(item.created_at).toLocaleString()} · {item.requires_review_reason}
            </p>
            <Detail item={item} />
            {item.review.status === "pending_officer_review" ? (
              <div className="flex flex-wrap items-center gap-2">
                <Input
                  className="max-w-md"
                  placeholder="Note to farmer (optional)"
                  value={notes[item.id] ?? ""}
                  onChange={(e) => setNotes({ ...notes, [item.id]: e.target.value })}
                />
                <Button size="sm" onClick={() => decide(item, "approve")}>
                  <Check /> Approve
                </Button>
                <Button size="sm" variant="destructive" onClick={() => decide(item, "reject")}>
                  <X /> Reject
                </Button>
              </div>
            ) : (
              <p className="text-sm">
                {item.review.status} by {item.review.reviewer}
                {item.review.note ? ` - "${item.review.note}"` : ""}
              </p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

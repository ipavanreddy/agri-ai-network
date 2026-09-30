"use client";

import { RefreshCw, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import type { Review } from "@/lib/types";

/** Human-approval status of an AI output (consequential actions need Agriculture Officer review). */
export function ReviewStatus({ review, onRefresh }: { review: Review; onRefresh?: () => void }) {
  const { t } = useI18n();
  const map = {
    pending_officer_review: { icon: ShieldAlert, cls: "border-amber-300 bg-amber-50 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100", text: t("pending_review") },
    approved: { icon: ShieldCheck, cls: "border-emerald-300 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100", text: t("approved") },
    rejected: { icon: ShieldX, cls: "border-red-300 bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100", text: t("rejected") },
  } as const;
  const s = map[review.status];
  const Icon = s.icon;
  return (
    <div className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${s.cls}`}>
      <Icon className="size-4 shrink-0" />
      <span className="flex-1">
        {s.text}
        {review.note ? ` - "${review.note}"` : ""}
      </span>
      {onRefresh ? (
        <Button size="icon-sm" variant="ghost" onClick={onRefresh} aria-label="Refresh review status">
          <RefreshCw />
        </Button>
      ) : null}
    </div>
  );
}

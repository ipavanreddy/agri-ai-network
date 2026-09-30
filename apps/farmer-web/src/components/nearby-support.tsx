"use client";

import { useEffect, useState } from "react";
import { MapPinned } from "lucide-react";
import { ModeBadge } from "@/components/mode-badge";
import { apiGet } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { NearbySupport as Nearby } from "@/lib/types";

/** Nearest KVK / agriculture office with real drive time (Google Maps Places + Routes via the API). */
export function NearbySupport({ fieldId }: { fieldId: string }) {
  const { t } = useI18n();
  const [data, setData] = useState<Nearby | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<Nearby>(`/api/fields/${fieldId}/nearby-support`)
      .then((d) => !cancelled && setData(d))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [fieldId]);

  if (!data) return null;
  return (
    <div className="rounded-lg border p-3 text-sm">
      <p className="mb-2 flex flex-wrap items-center gap-2 font-semibold">
        <MapPinned className="size-4" /> {t("nearest_help")}
        <ModeBadge demo={data.mode !== "live"} label={data.mode === "live" ? "Google Maps · live" : undefined} />
      </p>
      {data.places.length ? (
        <ul className="flex flex-col gap-1.5">
          {data.places.map((p) => (
            <li key={p.maps_url}>
              <a href={p.maps_url} target="_blank" rel="noreferrer" className="font-medium underline-offset-2 hover:underline">
                {p.name}
              </a>{" "}
              <span className="text-xs text-muted-foreground">
                · {p.kind} ·{" "}
                {p.distance_km != null ? `${p.distance_km} km by road, ~${p.duration_min} min drive` : `${p.straight_km} km away`}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground">{data.note ?? "No agriculture office found within 80 km."}</p>
      )}
      {data.source ? <p className="mt-1 text-xs text-muted-foreground">{data.source}</p> : null}
    </div>
  );
}

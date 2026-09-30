"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import type * as Leaflet from "leaflet";
import type { Field } from "@/lib/types";

export type LatLng = [number, number];

type Props = {
  fields: Field[];
  selectedId: string | null;
  onSelect: (fieldId: string) => void;
  drawing: boolean;
  points: LatLng[];
  onAddPoint: (p: LatLng) => void;
  center: LatLng;
  zoom?: number;
};

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

/** Google Maps (satellite) when NEXT_PUBLIC_MAPS_API_KEY is set; Leaflet + OpenStreetMap otherwise. */
export function FieldMap(props: Props) {
  return MAPS_KEY ? <GoogleFieldMap {...props} /> : <LeafletFieldMap {...props} />;
}

export const mapProvider = MAPS_KEY ? "Google Maps" : "OpenStreetMap (Leaflet) · demo fallback";

const ringLatLngs = (f: Field): LatLng[] => f.geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);

function useLatest<T>(value: T) {
  const ref = useRef(value);
  useEffect(() => {
    ref.current = value;
  });
  return ref;
}

function LeafletFieldMap({ fields, selectedId, onSelect, drawing, points, onAddPoint, center, zoom = 16 }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const L = useRef<typeof Leaflet | null>(null);
  const layer = useRef<Leaflet.LayerGroup | null>(null);
  const [ready, setReady] = useState(false);
  const cb = useLatest({ onSelect, onAddPoint, drawing });

  useEffect(() => {
    let cancelled = false;
    import("leaflet").then((mod) => {
      if (cancelled || !el.current || map.current) return;
      const lib = (mod as unknown as { default?: typeof Leaflet }).default ?? (mod as unknown as typeof Leaflet);
      L.current = lib;
      const m = lib.map(el.current, { zoomControl: true }).setView(center, zoom);
      lib.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(m);
      m.on("click", (e: Leaflet.LeafletMouseEvent) => {
        if (cb.current.drawing) cb.current.onAddPoint([e.latlng.lat, e.latlng.lng]);
      });
      layer.current = lib.layerGroup().addTo(m);
      map.current = m;
      setReady(true);
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (ready) map.current?.setView(center, zoom);
  }, [ready, center, zoom]);

  useEffect(() => {
    const lib = L.current;
    const group = layer.current;
    if (!ready || !lib || !group) return;
    group.clearLayers();
    for (const f of fields) {
      const selected = f.field_id === selectedId;
      lib.polygon(ringLatLngs(f), { color: selected ? "#16a34a" : "#2563eb", weight: selected ? 3 : 2, fillOpacity: selected ? 0.35 : 0.15 })
        .bindTooltip(`${f.name ?? f.field_id} · ${f.crop.crop_name} · ${f.area_acres} ac`)
        .on("click", () => cb.current.onSelect(f.field_id))
        .addTo(group);
    }
    if (points.length) {
      lib.polyline(points.length >= 3 ? [...points, points[0]] : points, { color: "#f59e0b", dashArray: "4 4" }).addTo(group);
      points.forEach((p) => lib.circleMarker(p, { radius: 5, color: "#f59e0b", fillOpacity: 1 }).addTo(group));
    }
  }, [ready, fields, selectedId, points, cb]);

  return <div ref={el} className="h-80 w-full overflow-hidden rounded-lg border" style={{ cursor: drawing ? "crosshair" : undefined }} />;
}

let googleLoader: Promise<typeof google> | null = null;
function loadGoogleMaps(key: string): Promise<typeof google> {
  if (googleLoader) return googleLoader;
  googleLoader = new Promise((resolve, reject) => {
    const cbName = "__agriMapsReady";
    (window as unknown as Record<string, () => void>)[cbName] = () => resolve(window.google);
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly&loading=async&callback=${cbName}`;
    s.async = true;
    s.onerror = () => reject(new Error("Google Maps failed to load"));
    document.head.appendChild(s);
  });
  return googleLoader;
}

function GoogleFieldMap({ fields, selectedId, onSelect, drawing, points, onAddPoint, center, zoom = 16 }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<google.maps.Map | null>(null);
  const overlays = useRef<{ setMap: (m: google.maps.Map | null) => void }[]>([]);
  const [ready, setReady] = useState(false);
  const cb = useLatest({ onSelect, onAddPoint, drawing });

  useEffect(() => {
    loadGoogleMaps(MAPS_KEY).then((g) => {
      if (!el.current || map.current) return;
      const m = new g.maps.Map(el.current, { center: { lat: center[0], lng: center[1] }, zoom, mapTypeId: "hybrid", tilt: 0 });
      m.addListener("click", (e: google.maps.MapMouseEvent) => {
        if (cb.current.drawing && e.latLng) cb.current.onAddPoint([e.latLng.lat(), e.latLng.lng()]);
      });
      map.current = m;
      setReady(true);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (ready) {
      map.current?.setCenter({ lat: center[0], lng: center[1] });
      map.current?.setZoom(zoom);
    }
  }, [ready, center, zoom]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    overlays.current.forEach((o) => o.setMap(null));
    overlays.current = [];
    for (const f of fields) {
      const selected = f.field_id === selectedId;
      const poly = new google.maps.Polygon({
        paths: ringLatLngs(f).map(([lat, lng]) => ({ lat, lng })),
        strokeColor: selected ? "#22c55e" : "#60a5fa",
        strokeWeight: selected ? 3 : 2,
        fillOpacity: selected ? 0.3 : 0.12,
        map: m,
      });
      poly.addListener("click", () => cb.current.onSelect(f.field_id));
      overlays.current.push(poly);
    }
    if (points.length) {
      const path = (points.length >= 3 ? [...points, points[0]] : points).map(([lat, lng]) => ({ lat, lng }));
      overlays.current.push(new google.maps.Polyline({ path, strokeColor: "#f59e0b", map: m }));
    }
  }, [ready, fields, selectedId, points, cb]);

  return <div ref={el} className="h-80 w-full overflow-hidden rounded-lg border" style={{ cursor: drawing ? "crosshair" : undefined }} />;
}

"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import type * as Leaflet from "leaflet";

export type RegionMarker = { id: string; lat: number; lon: number; color: string; radius: number; tooltip: string };
type Props = { markers: RegionMarker[]; center: [number, number]; zoom: number; onSelect: (id: string) => void };

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";
export const mapProvider = MAPS_KEY ? "Google Maps" : "OpenStreetMap (Leaflet) · demo fallback";

function useLatest<T>(value: T) {
  const ref = useRef(value);
  useEffect(() => {
    ref.current = value;
  });
  return ref;
}

/** Regional risk map: Google Maps when NEXT_PUBLIC_MAPS_API_KEY is set, Leaflet + OpenStreetMap otherwise. */
export function RegionMap(props: Props) {
  return MAPS_KEY ? <GoogleRegionMap {...props} /> : <LeafletRegionMap {...props} />;
}

function LeafletRegionMap({ markers, center, zoom, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const L = useRef<typeof Leaflet | null>(null);
  const layer = useRef<Leaflet.LayerGroup | null>(null);
  const [ready, setReady] = useState(false);
  const cb = useLatest(onSelect);

  useEffect(() => {
    let cancelled = false;
    import("leaflet").then((mod) => {
      if (cancelled || !el.current || map.current) return;
      const lib = (mod as unknown as { default?: typeof Leaflet }).default ?? (mod as unknown as typeof Leaflet);
      L.current = lib;
      const m = lib.map(el.current).setView(center, zoom);
      lib.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(m);
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
    for (const mk of markers) {
      lib.circleMarker([mk.lat, mk.lon], { radius: mk.radius, color: mk.color, fillColor: mk.color, fillOpacity: 0.55, weight: 2 })
        .bindTooltip(mk.tooltip)
        .on("click", () => cb.current(mk.id))
        .addTo(group);
    }
  }, [ready, markers, cb]);

  return <div ref={el} className="h-96 w-full overflow-hidden rounded-lg border" />;
}

let googleLoader: Promise<typeof google> | null = null;
function loadGoogleMaps(key: string): Promise<typeof google> {
  if (googleLoader) return googleLoader;
  googleLoader = new Promise((resolve, reject) => {
    const cbName = "__agriOfficerMapsReady";
    (window as unknown as Record<string, () => void>)[cbName] = () => resolve(window.google);
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly&loading=async&callback=${cbName}`;
    s.async = true;
    s.onerror = () => reject(new Error("Google Maps failed to load"));
    document.head.appendChild(s);
  });
  return googleLoader;
}

function GoogleRegionMap({ markers, center, zoom, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<google.maps.Map | null>(null);
  const circles = useRef<google.maps.Circle[]>([]);
  const [ready, setReady] = useState(false);
  const cb = useLatest(onSelect);

  useEffect(() => {
    loadGoogleMaps(MAPS_KEY).then((g) => {
      if (!el.current || map.current) return;
      map.current = new g.maps.Map(el.current, { center: { lat: center[0], lng: center[1] }, zoom });
      setReady(true);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!ready) return;
    map.current?.setCenter({ lat: center[0], lng: center[1] });
    map.current?.setZoom(zoom);
  }, [ready, center, zoom]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    circles.current.forEach((c) => c.setMap(null));
    circles.current = markers.map((mk) => {
      const c = new google.maps.Circle({
        center: { lat: mk.lat, lng: mk.lon },
        radius: mk.radius * (zoom <= 5 ? 9000 : 1800),
        strokeColor: mk.color,
        fillColor: mk.color,
        fillOpacity: 0.5,
        map: m,
      });
      c.addListener("click", () => cb.current(mk.id));
      return c;
    });
  }, [ready, markers, zoom, cb]);

  return <div ref={el} className="h-96 w-full overflow-hidden rounded-lg border" />;
}

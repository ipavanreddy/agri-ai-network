"use client";

import dynamic from "next/dynamic";

// Client-only: Leaflet / Google Maps need the browser.
const OfficerApp = dynamic(() => import("@/components/officer-app"), {
  ssr: false,
  loading: () => <p className="p-6 text-muted-foreground">Loading officer dashboard...</p>,
});

export function OfficerAppLoader() {
  return <OfficerApp />;
}

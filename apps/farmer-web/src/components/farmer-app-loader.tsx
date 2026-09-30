"use client";

import dynamic from "next/dynamic";

// Client-only: the app reads localStorage (language) and uses browser-only map/speech APIs.
const FarmerApp = dynamic(() => import("@/components/farmer-app"), {
  ssr: false,
  loading: () => <p className="p-6 text-muted-foreground">Loading Agri AI Network...</p>,
});

export function FarmerAppLoader() {
  return <FarmerApp />;
}

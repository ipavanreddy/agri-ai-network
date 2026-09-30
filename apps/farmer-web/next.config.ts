import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloud Run: self-contained server (apps/<app>/Dockerfile copies .next/standalone + static assets).
  output: "standalone",
  // pnpm workspace: trace dependencies from the repo root.
  outputFileTracingRoot: path.join(__dirname, "../.."),
};

export default nextConfig;

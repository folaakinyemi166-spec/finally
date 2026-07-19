import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: FastAPI serves this build output as static files from a
  // single origin in production (see planning/PLAN.md §11). No server-side
  // Next.js features (API routes, ISR, image optimization server) are used.
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The production Docker image runs the traced Next.js server. Static export
  // output is incompatible with that image because it does not create
  // `.next/standalone/server.js`.
  output: "standalone",
  images: {
    unoptimized: true,
  },
  // We need to disable trailing slashes and handle other settings if needed for Tauri
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  }
};

export default nextConfig;

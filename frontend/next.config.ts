import type { NextConfig } from "next";

const isExport = process.env.NEXT_EXPORT === 'true' || process.env.TAURI_BUILD === '1';

const nextConfig: NextConfig = {
  // Use static export for Tauri client bundling; use standalone server for Docker
  output: isExport ? "export" : "standalone",
  images: {
    unoptimized: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  ...(!isExport
    ? {
        async rewrites() {
          const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
          return [
            {
              source: '/api/:path*',
              destination: `${backendUrl}/api/:path*`,
            },
          ];
        },
      }
    : {}),
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The production Docker image runs the traced Next.js server. Static export
  // output is incompatible with that image because it does not create
  // `.next/standalone/server.js`.
  output: "standalone",
  images: {
    unoptimized: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

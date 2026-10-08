import type { NextConfig } from "next";

const API = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/actions.json", destination: `${API}/actions.json` },
      { source: "/actions/:path*", destination: `${API}/actions/:path*` },
    ];
  },
};

export default nextConfig;

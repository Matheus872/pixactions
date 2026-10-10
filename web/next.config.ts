import type { NextConfig } from "next";

const API = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // WSL de 4 GB: um worker e despejo agressivo de memória mantêm o build abaixo do limite.
  experimental: { cpus: 1, turbopackMemoryEviction: "full" },
  // Tailwind v4 is compiled by Turbopack through this loader (Next 16 template).
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [
      { source: "/actions.json", destination: `${API}/actions.json` },
      { source: "/actions/:path*", destination: `${API}/actions/:path*` },
    ];
  },
};

export default nextConfig;

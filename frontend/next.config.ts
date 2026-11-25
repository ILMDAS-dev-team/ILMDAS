import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Required by docker/frontend/Dockerfile standalone runner.
  output: "standalone",
  async redirects() {
    // /login is the single sign-in route; keep old /sign-in links working.
    // Query strings such as ?next= are carried over.
    return [{ source: "/sign-in", destination: "/login", permanent: false }]
  },
}

export default nextConfig

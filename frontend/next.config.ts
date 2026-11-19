import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Required by docker/frontend/Dockerfile standalone runner.
  output: "standalone",
}

export default nextConfig

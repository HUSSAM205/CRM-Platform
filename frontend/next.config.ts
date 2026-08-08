import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal, self-contained build output for the production Docker image (see
  // frontend/Dockerfile) - copies only the files actually needed to run `next start`.
  output: "standalone",
};

export default nextConfig;

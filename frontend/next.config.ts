import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal, self-contained build output for the production Docker image (see
  // frontend/Dockerfile) - copies only the files actually needed to run `next start`.
  // Only enabled for Docker builds: Vercel's own build/routing layer doesn't understand
  // standalone output and serves 404s for every route if this is set unconditionally.
  ...(process.env.DOCKER_BUILD === "true" ? { output: "standalone" as const } : {}),
};

export default nextConfig;

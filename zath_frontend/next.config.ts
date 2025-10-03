import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Enable Docker support
  output: "standalone",
  // Allow external images if needed
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

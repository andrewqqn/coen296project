import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Only use 'export' for production builds
  ...(process.env.NODE_ENV === 'production' && { output: 'export' }),
  images: {
    unoptimized: true,
  },
  // Disable strict mode to prevent double-rendering in dev
  reactStrictMode: false,
};

export default nextConfig;

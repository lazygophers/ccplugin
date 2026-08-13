import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  // Turbopack 禁止 distDir 跳出 projectPath; build 后 serve.py 把 .dist 移到 ../dist
  distDir: '.dist',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

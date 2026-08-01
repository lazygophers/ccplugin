import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: 'dist',
  // SPA: 所有路由都走前端, 不走服务端路由
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

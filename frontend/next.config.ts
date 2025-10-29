import type { NextConfig } from "next";

// Get backend URL from environment variable
// For Docker: use NEXT_PUBLIC_API_URL if set, otherwise try backend service name
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 
  (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000');

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Catch-all: proxy all /api/* requests to backend
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`
      }
    ];
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || BACKEND_URL
  }
};

export default nextConfig;

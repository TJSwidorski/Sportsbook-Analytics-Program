import type { NextConfig } from 'next'

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:5000'

const nextConfig: NextConfig = {
  // Allow long-running backtests proxied through /api/* without an idle timeout
  // ECONNRESET. Default Node proxy idle timeout is too aggressive for 30s+ runs.
  experimental: {
    proxyTimeout: 600_000,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/api/:path*`,
      },
    ]
  },
}

export default nextConfig

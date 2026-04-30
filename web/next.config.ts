import type { NextConfig } from 'next'

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
        destination: 'http://localhost:5000/api/:path*',
      },
    ]
  },
}

export default nextConfig

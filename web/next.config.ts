import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',   // static HTML/JS/CSS — no server needed, perfect for Cloudflare Pages
}

export default nextConfig

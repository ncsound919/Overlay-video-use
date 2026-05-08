/** @type {import('next').NextConfig} */
const API_PORT = process.env.API_PORT || "8002"
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `http://localhost:${API_PORT}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig

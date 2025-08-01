/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/auth/:path*',
        destination: 'http://127.0.0.1:8000/api/auth/:path*',
      },
      {
        source: '/api/extract/:path*',
        destination: 'http://127.0.0.1:8000/api/extract/:path*',
      },
      {
        source: '/api/ingest/:path*',
        destination: 'http://127.0.0.1:8000/api/ingest/:path*',
      },
      {
        source: '/api/search/:path*',
        destination: 'http://127.0.0.1:8000/api/search/:path*',
      },
      {
        source: '/api/summarize/:path*',
        destination: 'http://127.0.0.1:8000/api/summarize/:path*',
      },

    ]
  },
}

module.exports = nextConfig
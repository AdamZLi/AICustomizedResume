/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/keywords_text',
        destination: 'http://localhost:8000/keywords_text',
      },
    ]
  },
}

module.exports = nextConfig

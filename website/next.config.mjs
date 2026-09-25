/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_ASTRAOS_DASHBOARD_URL: 'https://astra-os-mu.vercel.app/',
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [{ source: '/runtime', destination: 'https://astra-os-mu.vercel.app/', permanent: false }]
  },
}

export default nextConfig

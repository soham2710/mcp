/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Environment variables
  env: {
    FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
  
  // Rewrites for API proxy (optional - for production)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.FASTAPI_URL || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
  
  // Image domains (if you plan to use Next.js Image component)
  images: {
    domains: ['localhost'],
  },
  
  // Webpack configuration for better performance
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Optimize bundle size
    if (!dev && !isServer) {
      config.optimization.splitChunks.cacheGroups = {
        ...config.optimization.splitChunks.cacheGroups,
        commons: {
          name: 'commons',
          chunks: 'all',
          minChunks: 2,
        },
      }
    }
    
    return config
  },
  
  // Experimental features
  experimental: {
    // Enable if you want to use the new app directory features
    appDir: true,
  },
  
  // TypeScript configuration
  typescript: {
    // Dangerously allow production builds to successfully complete even if your project has TypeScript errors
    ignoreBuildErrors: false,
  },
  
  // ESLint configuration  
  eslint: {
    // Warning: This allows production builds to successfully complete even if your project has ESLint errors
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig
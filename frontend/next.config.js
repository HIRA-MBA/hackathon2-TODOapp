/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better debugging
  reactStrictMode: true,
  // Enable standalone output for Docker deployment
  output: 'standalone',
};

module.exports = nextConfig;

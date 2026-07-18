/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://api-woad-ten-44.vercel.app/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;

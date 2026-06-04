/** @type {import('next').NextConfig} */
// INTERNAL_API_URL is read at server start (runtime) — distinct from the
// NEXT_PUBLIC_* family, which Next.js inlines at build time. Use this for the
// rewrite destination so changing it in compose doesn't require a rebuild.
const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.INTERNAL_API_URL || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Routes from the old Vite app, so bookmarks and shared links keep working.
  async redirects() {
    return [
      { source: "/analysis", destination: "/contracts", permanent: true },
      { source: "/analysis/:id", destination: "/contracts/:id", permanent: true },
      { source: "/obligations/:id", destination: "/obligations", permanent: true },
    ];
  },
};

export default nextConfig;
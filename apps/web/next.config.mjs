import { assertDeployable } from "./security-policy.mjs";

assertDeployable(); // fail loudly: no mock data / dev token in a production build

// The Content-Security-Policy (nonce-based) is set per request in middleware.ts.
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "Referrer-Policy", value: "no-referrer" },
      { key: "X-Content-Type-Options", value: "nosniff" },
    ] }];
  },
};
export default nextConfig;

// Shared by next.config.mjs (build-time guard), middleware.ts (per-request CSP) and tests.
// Plain ESM so Node can load it without a TS step.

const SAFE_DEPLOY_ENVS = ["dev", "local", "test"];

/**
 * Refuse to build/serve a production bundle that would ship mock data or a dev token.
 * `next build` always runs with NODE_ENV=production, so an explicit APP_ENV in {dev, local, test}
 * is required to opt in to a mock/dev-token build (e.g. for demos or CI); anything else fails.
 */
export function assertDeployable(env = process.env) {
  if (env.NODE_ENV !== "production") return;
  const appEnv = String(env.APP_ENV || "").trim().toLowerCase();
  if (SAFE_DEPLOY_ENVS.includes(appEnv)) return;
  const bad = [];
  if (env.NEXT_PUBLIC_API_MOCK === "1") bad.push("NEXT_PUBLIC_API_MOCK=1");
  if (env.NEXT_PUBLIC_DEV_TOKEN) bad.push("NEXT_PUBLIC_DEV_TOKEN");
  if (bad.length) {
    throw new Error(
      `Refusing to build/serve a production bundle with ${bad.join(" and ")}. ` +
        `Unset them, or set APP_ENV=dev|local|test for a non-production build.`,
    );
  }
}

/** Origin of the configured API (the only connect-src besides 'self'). */
export function apiOrigin(env = process.env) {
  const raw = env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return new URL(raw).origin;
}

/** Nonce-based CSP. Production has no unsafe-inline/unsafe-eval in script-src; dev relaxes eval for React refresh. */
export function buildCsp(nonce, env = process.env) {
  const dev = env.NODE_ENV !== "production";
  const script = ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'"];
  if (dev) script.push("'unsafe-eval'");
  const connect = ["'self'", apiOrigin(env)];
  if (dev) connect.push("ws://localhost:*");
  return [
    "default-src 'self'",
    `script-src ${script.join(" ")}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    `connect-src ${connect.join(" ")}`,
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "object-src 'none'",
  ].join("; ");
}

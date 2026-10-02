import { NextResponse, type NextRequest } from "next/server";
import { assertDeployable, buildCsp } from "./security-policy.mjs";

// Per-request nonce CSP. Next reads the nonce from the request CSP header and applies it to its scripts.
export function middleware(req: NextRequest) {
  assertDeployable(); // refuse to serve a production bundle with mock/dev-token settings
  const nonce = btoa(crypto.randomUUID());
  const csp = buildCsp(nonce);
  const headers = new Headers(req.headers);
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", csp);
  const res = NextResponse.next({ request: { headers } });
  res.headers.set("Content-Security-Policy", csp);
  return res;
}

export const config = {
  matcher: [{ source: "/((?!_next/static|_next/image|favicon.ico).*)", missing: [{ type: "header", key: "next-router-prefetch" }] }],
};

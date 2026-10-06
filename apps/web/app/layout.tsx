import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";
import { AppShell } from "@/components/shell";
import { SessionProvider } from "@/components/session";
import { ToastProvider } from "@/components/toast";

export const metadata: Metadata = { title: "Buy-side RFQ", description: "Get comparable quotes from your own suppliers; you approve every send" };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  await headers(); // opt into dynamic rendering so Next applies the per-request CSP nonce to its scripts
  return (
    <html lang="en-GB">
      <body>
        <SessionProvider><ToastProvider><AppShell>{children}</AppShell></ToastProvider></SessionProvider>
      </body>
    </html>
  );
}

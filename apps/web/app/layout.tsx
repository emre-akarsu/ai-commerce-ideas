import type { Metadata } from "next";
import Link from "next/link";
import { headers } from "next/headers";
import "./globals.css";
import { MockBanner } from "@/components/ui/ui";

export const metadata: Metadata = { title: "Parts purchasing", description: "Identify and source maintenance parts" };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  await headers(); // opt into dynamic rendering so Next applies the per-request CSP nonce to its scripts
  return (
    <html lang="en">
      <body>
        <MockBanner />
        <header className="border-b bg-white">
          <nav aria-label="Main" className="mx-auto flex max-w-4xl gap-4 px-4 py-3 text-base font-medium">
            <Link href="/requests">Requests</Link>
            <Link href="/vendors">Vendors</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-4xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}

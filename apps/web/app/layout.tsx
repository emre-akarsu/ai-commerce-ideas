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
      <body className="flex min-h-screen flex-col">
        <MockBanner />
        <header className="border-b bg-white">
          <nav aria-label="Main" className="mx-auto flex max-w-7xl gap-6 px-4 py-3 text-base font-medium">
            <Link href="/" className="hover:text-blue-700">Inbox</Link>
            <Link href="/requests" className="hover:text-blue-700">Requests</Link>
            <Link href="/vendors" className="hover:text-blue-700">Suppliers</Link>
            <Link href="/setup" className="hover:text-blue-700">Setup</Link>
            <Link href="/audit" className="hover:text-blue-700">Audit</Link>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">{children}</main>
      </body>
    </html>
  );
}

import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app"),
  title: "Daam Kemon — Grocery price intelligence for Bangladesh",
  description:
    "Compare grocery and daily essential prices across Chaldal, Shwapno, Othoba and Unimart.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="bg-brand text-white">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
            <Link href="/" className="font-bold text-lg tracking-tight">
              Daam Kemon
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/" className="hover:underline">
                Search
              </Link>
              <Link href="/categories" className="hover:underline">
                Categories
              </Link>
              <Link href="/basket" className="hover:underline">
                Basket
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 py-8 text-xs text-gray-500">
          Daam Kemon is independent and not affiliated with the listed stores.
        </footer>
      </body>
    </html>
  );
}

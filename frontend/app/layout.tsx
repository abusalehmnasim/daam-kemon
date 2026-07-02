import "./globals.css";
import type { Metadata } from "next";
import { Inter, Noto_Sans_Bengali } from "next/font/google";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const bengali = Noto_Sans_Bengali({
  subsets: ["bengali"],
  weight: ["400", "500", "600"],
  variable: "--font-bengali",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app"),
  title: "Daam Kemon — Grocery price intelligence for Bangladesh",
  description:
    "Compare grocery and daily essential prices across Chaldal, Shwapno, Othoba and Unimart.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${bengali.variable}`}>
      <body>
        <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-[15px] font-semibold tracking-tight text-ink"
            >
              <span className="h-2 w-2 rounded-full bg-brand" aria-hidden="true" />
              Daam Kemon
            </Link>
            <SiteNav />
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 pb-10 pt-6 text-xs text-muted">
          Daam Kemon is independent and not affiliated with the listed stores.
        </footer>
      </body>
    </html>
  );
}

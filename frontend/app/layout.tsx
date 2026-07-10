import "./globals.css";
import type { Metadata } from "next";
import { Hind_Siliguri, Anek_Bangla } from "next/font/google";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

// One bilingual UI/body family — renders Bengali + Latin from a single file.
const sans = Hind_Siliguri({
  subsets: ["bengali", "latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});
// Warm, brand-forward display type — wordmark only.
const display = Anek_Bangla({
  subsets: ["bengali", "latin"],
  variable: "--font-display",
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
    <html lang="en" className={`${sans.variable} ${display.variable}`}>
      <body>
        <header className="sticky top-0 z-20 border-b border-line bg-paper/85 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <Link
              href="/"
              className="flex items-center gap-2 font-display text-[17px] font-bold tracking-tight text-ink"
            >
              <span className="h-2 w-2 rounded-full bg-brand-bright" aria-hidden="true" />
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

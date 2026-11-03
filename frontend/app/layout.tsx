import "./globals.css";
import type { Metadata } from "next";
import { Hind_Siliguri, Anek_Bangla } from "next/font/google";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { FloatingBasketPill } from "@/components/FloatingBasketPill";
import { MobileBottomNav } from "@/components/MobileBottomNav";

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
  weight: ["700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app"),
  title: "Daam Kemon — Grocery Price Intelligence for Bangladesh",
  description:
    "Compare grocery prices across Chaldal, Shwapno, Unimart, Agora, Daraz and Othoba — live daily price comparison.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn" className={`${sans.variable} ${display.variable}`}>
      <body className="min-h-screen bg-paper font-sans text-ink antialiased">
        <header className="sticky top-0 z-20 border-b border-line bg-paper/90 backdrop-blur-md">
          <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
            <Link href="/" className="group flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-bright text-white shadow-sm transition-transform group-hover:scale-105">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
                  <path d="M3 6h18" />
                  <path d="M16 10a4 4 0 0 1-8 0" />
                </svg>
              </span>
              <div>
                <div className="flex items-center gap-1.5 leading-none">
                  <span className="font-display text-lg font-bold tracking-tight text-ink">
                    Daam Kemon
                  </span>
                  <span className="rounded bg-brand/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand">
                    দাম কেমন
                  </span>
                </div>
                <div className="mt-0.5 hidden items-center gap-1.5 text-[11px] text-muted sm:flex">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-save animate-pulse" />
                  <span>৬টি স্টোরের লাইভ বাজার দর</span>
                </div>
              </div>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-1 rounded-full border border-line bg-card px-2.5 py-1 text-xs text-muted md:flex">
                <span className="h-2 w-2 rounded-full bg-save" />
                <span className="font-medium text-ink">
                  Chaldal · Shwapno · Unimart · Agora · Daraz · Othoba
                </span>
              </div>
              <SiteNav />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-4 pb-28 pt-6 sm:pb-16 sm:pt-8">{children}</main>

        <FloatingBasketPill />
        <MobileBottomNav />

        <footer className="border-t border-line bg-card/60 pb-20 pt-8 sm:pb-8">
          <div className="mx-auto max-w-5xl px-4">
            <div className="flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
              <div>
                <p className="font-display text-base font-bold text-ink">Daam Kemon · দাম কেমন</p>
                <p className="mt-1 text-xs text-muted">
                  Grocery price intelligence engine for Bangladesh. Scraped and verified daily.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-muted">
                <span className="rounded bg-line/50 px-2 py-0.5">Chaldal</span>
                <span className="rounded bg-line/50 px-2 py-0.5">Shwapno</span>
                <span className="rounded bg-line/50 px-2 py-0.5">Unimart</span>
                <span className="rounded bg-line/50 px-2 py-0.5">Agora</span>
                <span className="rounded bg-line/50 px-2 py-0.5">Daraz</span>
                <span className="rounded bg-line/50 px-2 py-0.5">Othoba</span>
              </div>
            </div>
            <div className="mt-6 border-t border-line/60 pt-4 text-center text-[11px] text-faint">
              Daam Kemon is an independent price comparison service and is not affiliated with the
              listed supermarkets.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

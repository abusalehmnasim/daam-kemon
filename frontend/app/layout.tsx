import "./globals.css";
import type { Metadata } from "next";
import { Hind_Siliguri, Anek_Bangla } from "next/font/google";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { FloatingBasketPill } from "@/components/FloatingBasketPill";
import { MobileBottomNav } from "@/components/MobileBottomNav";

const sans = Hind_Siliguri({
  subsets: ["bengali", "latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const display = Anek_Bangla({
  subsets: ["bengali", "latin"],
  weight: ["700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://daam-kemon.vercel.app"),
  title: "Daam Kemon — Grocery Price Intelligence for Bangladesh",
  description:
    "Compare grocery prices across Chaldal, Shwapno, Unimart, Agora, Daraz and Othoba — live daily price comparison.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn" className={`${sans.variable} ${display.variable}`}>
      <body className="min-h-screen bg-[#0D0A08] font-sans text-white antialiased selection:bg-orange-600">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0D0A08]/80 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Link href="/" className="group flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-display text-sm font-black text-black shadow-lg transition-transform group-hover:scale-105">
                DK
              </span>
              <div>
                <div className="flex items-center gap-2 leading-none">
                  <span className="font-display text-lg font-black tracking-tight text-white">
                    Daam Kemon
                  </span>
                  <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold text-orange-300">
                    দাম কেমন
                  </span>
                </div>
                <div className="mt-1 hidden items-center gap-1.5 text-[11px] text-white/50 sm:flex">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-save animate-pulse" />
                  <span>৬টি স্টোরের লাইভ বাজার দর</span>
                </div>
              </div>
            </Link>

            <div className="flex items-center gap-4">
              <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60 md:flex">
                <span className="h-2 w-2 rounded-full bg-save" />
                <span className="font-semibold text-white/80">
                  Chaldal · Shwapno · Unimart · Agora · Daraz · Othoba
                </span>
              </div>
              <SiteNav />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 pb-28 pt-6 sm:px-6 sm:pb-20 sm:pt-10">
          {children}
        </main>

        <FloatingBasketPill />
        <MobileBottomNav />

        <footer className="border-t border-white/10 bg-[#0A0705] pb-24 pt-10 sm:pb-10">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="flex flex-col items-center justify-between gap-6 text-center sm:flex-row sm:text-left">
              <div>
                <div className="flex items-center justify-center gap-2 sm:justify-start">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white font-display text-xs font-black text-black">
                    DK
                  </span>
                  <p className="font-display text-lg font-black text-white">
                    Daam Kemon · দাম কেমন
                  </p>
                </div>
                <p className="mt-1.5 text-xs text-white/50">
                  Grocery price intelligence engine for Bangladesh. Scraped and verified daily.
                </p>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-white/60">
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Chaldal
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Shwapno
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Unimart
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Agora
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Daraz
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Othoba
                </span>
              </div>
            </div>

            <div className="mt-8 border-t border-white/10 pt-6 text-center text-[11px] text-white/40">
              Daam Kemon is an independent price comparison service and is not affiliated with the
              listed supermarkets.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Hind Siliguri renders Bengali conjuncts + Latin from one family.
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        // Anek Bangla — warm, brand-forward display type for the wordmark only.
        display: ["var(--font-display)", "var(--font-sans)", "sans-serif"],
      },
      colors: {
        paper: "#F5F4F0", // warm near-white page background
        card: "#FFFFFF",
        ink: "#1A1B1D", // primary text — high contrast
        muted: "#565961", // secondary text — readable, not dim
        faint: "#8B8E94", // hints / tertiary
        line: "#E6E4DD", // hairline borders
        "line-strong": "#D4D2CA", // hover borders
        // BRAND — warm "guava" coral. Logo, CTAs, focus, brand accents ONLY.
        // Never used for error states (red convention) or for savings (that's green).
        brand: {
          DEFAULT: "#CF4E2B", // AA-safe: ~4.7:1 on paper, ~4.8:1 white-on-it
          bright: "#E8623D", // livelier accent / focus glow (decorative)
          dark: "#A63C20", // hover / pressed
          weak: "#FEF3EE", // tint background
        },
        // SAVINGS — emerald green. The ONE cheapest/you-save signal, nothing else.
        // Emerald (not flag-green) so it reads as functional money-green.
        save: {
          DEFAULT: "#0E7C59", // AA-safe text + badge background with white
          bright: "#12936A",
          dark: "#0A5E44",
          weak: "#E7F5EE",
        },
        // ERROR — desaturated crimson, kept distinct from coral. Errors only.
        error: {
          DEFAULT: "#C0362C",
          weak: "#FDECEA",
        },
        // WARNING — amber, for stale-price / "updated N days ago".
        warn: {
          DEFAULT: "#B77410",
          weak: "#FBF1DF",
        },
      },
      borderRadius: {
        card: "12px",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(26,27,29,.06), 0 2px 8px rgba(26,27,29,.05)",
      },
    },
  },
  plugins: [],
};

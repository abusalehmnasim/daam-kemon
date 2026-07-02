/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "var(--font-bengali)", "system-ui", "sans-serif"],
      },
      colors: {
        paper: "#F5F4F0", // warm near-white page background
        card: "#FFFFFF",
        ink: "#1A1B1D", // primary text — high contrast
        muted: "#565961", // secondary text — readable, not dim
        faint: "#8B8E94", // hints / tertiary
        line: "#E6E4DD", // hairline borders
        "line-strong": "#D4D2CA", // hover borders
        // Green is reserved for the "cheapest / best" signal, used sparingly.
        brand: {
          DEFAULT: "#0E7A46",
          dark: "#0A5230",
          weak: "#EAF3EC",
        },
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};

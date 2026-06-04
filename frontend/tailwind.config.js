/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0f7a3e",
          dark: "#0a5c2e",
          light: "#36a866",
        },
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#05070d",
          900: "#0a0e1a",
          800: "#0f1424",
          700: "#171d31",
          600: "#222a44",
          500: "#2f3a5c",
        },
        accent: {
          400: "#7dd3fc",
          500: "#38bdf8",
          600: "#0284c7",
        },
        aqi: {
          good: "#22c55e",
          satisfactory: "#84cc16",
          moderate: "#eab308",
          poor: "#f97316",
          verypoor: "#ef4444",
          severe: "#a21caf",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

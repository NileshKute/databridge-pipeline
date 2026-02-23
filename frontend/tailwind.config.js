/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Backgrounds (dark to light)
        surface: {
          950: "#0a0a0a",
          900: "#121212",
          850: "#1a1a1a",
          800: "#222222",
          700: "#2d2d2d",
          600: "#3d3d3d",
        },
        // Primary — Redchillies Red
        primary: {
          DEFAULT: "#DC2626",
          50: "#FEF2F2",
          100: "#FEE2E2",
          200: "#FECACA",
          300: "#FCA5A5",
          400: "#F87171",
          500: "#EF4444",
          600: "#DC2626",
          700: "#B91C1C",
          800: "#991B1B",
          900: "#7F1D1D",
        },
        // Accent colors for status indicators
        accent: {
          red: "#DC2626",
          crimson: "#BE123C",
          amber: "#F59E0B",
          emerald: "#10B981",
          blue: "#3B82F6",
          violet: "#8B5CF6",
          orange: "#F97316",
          rose: "#FB7185",
        },
        // Text
        text: {
          primary: "#F5F5F5",
          secondary: "#A3A3A3",
          muted: "#737373",
          inverse: "#0a0a0a",
        },
        // Legacy aliases for gradual migration
        "bg-primary": "#0a0a0a",
        "bg-secondary": "#121212",
        "bg-card": "#121212",
        "bg-card-hover": "#1a1a1a",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};

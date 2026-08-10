import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        success: { DEFAULT: "#16a34a", bg: "#dcfce7" },
        warning: { DEFAULT: "#d97706", bg: "#fef3c7" },
        danger: { DEFAULT: "#dc2626", bg: "#fee2e2" },
        info: { DEFAULT: "#2563eb", bg: "#dbeafe" },
        neutral: { DEFAULT: "#6b7280", bg: "#f3f4f6" },
      },
    },
  },
  plugins: [],
} satisfies Config;

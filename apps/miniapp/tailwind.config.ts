import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#0F4CFF",
        success: "#10B981",
        pending: "#F59E0B",
        danger: "#EF4444",
      },
    },
  },
  plugins: [],
} satisfies Config;
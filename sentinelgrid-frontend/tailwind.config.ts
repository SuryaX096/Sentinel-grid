import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0B0F14",       // page background — near-black slate, not pure black
        surface: "#131A22",    // card/panel background
        raised: "#1A222C",     // hover/raised surface
        border: "#212C38",
        muted: "#7C8A99",
        foreground: "#E6EDF3",
        signal: {
          critical: "#FF6B4A", // active threat / high risk
          warning: "#F0B429",  // medium risk / pending
          safe: "#3DDC97",     // resolved / low risk
          intel: "#5B8DEF",    // MITRE attribution / info
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;

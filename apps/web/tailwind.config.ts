import type { Config } from "tailwindcss";
const v = (n: string) => `var(--${n})`;
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"), surface: v("surface"), sunken: v("sunken"), line: v("line"), strong: v("strong"),
        ink: v("ink"), mute: v("mute"), accent: v("accent"), "accent-ink": v("accent-ink"), "accent-soft": v("accent-soft"),
        ok: v("ok"), "ok-soft": v("ok-soft"), warn: v("warn"), "warn-soft": v("warn-soft"), bad: v("bad"), "bad-soft": v("bad-soft"),
      },
      fontFamily: { sans: ["var(--font-sans)"], mono: ["var(--font-mono)"] },
      minHeight: { target: "2.5rem" },
    },
  },
  plugins: [],
};
export default config;

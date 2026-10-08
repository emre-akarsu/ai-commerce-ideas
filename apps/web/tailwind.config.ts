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
        serious: v("serious"), "serious-soft": v("serious-soft"),
        // chart marks (never used for text)
        "series-1": v("series-1"), "series-2": v("series-2"), "series-3": v("series-3"), "series-4": v("series-4"),
        "series-5": v("series-5"), "series-6": v("series-6"), "series-other": v("series-other"),
        "seq-100": v("seq-100"), "seq-200": v("seq-200"), "seq-300": v("seq-300"), "seq-400": v("seq-400"),
        "seq-500": v("seq-500"), "seq-600": v("seq-600"), "seq-700": v("seq-700"),
        grid: v("grid"), axis: v("axis"),
      },
      fontFamily: { sans: ["var(--font-sans)"], mono: ["var(--font-mono)"] },
      // 44 px targets; 48 px for the main action of a screen
      minHeight: { target: "2.75rem", "target-lg": "3rem" },
      minWidth: { target: "2.75rem" },
      boxShadow: { card: "var(--shadow-card)" },
      borderRadius: { xl: "0.75rem" },
    },
  },
  plugins: [],
};
export default config;

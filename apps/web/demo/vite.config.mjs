import { defineConfig } from "vite";
import path from "node:path";
const root = path.resolve(import.meta.dirname, "..");
export default defineConfig({
  root: import.meta.dirname,
  base: "./",
  esbuild: { jsx: "automatic" },
  oxc: { jsx: { runtime: "automatic" } },
  resolve: { alias: [
    { find: "next/link", replacement: path.join(import.meta.dirname, "next-link.tsx") },
    { find: "next/navigation", replacement: path.join(import.meta.dirname, "next-navigation.ts") },
    { find: /^@\//, replacement: root + "/" },
  ] },
  define: {
    "process.env.NEXT_PUBLIC_API_MOCK": JSON.stringify("1"),
    "process.env.NEXT_PUBLIC_DEV_TOKEN": "undefined",
    "process.env.NEXT_PUBLIC_API_URL": "undefined",
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: { outDir: path.join(root, "demo-dist"), emptyOutDir: true, cssMinify: true, rollupOptions: { output: { entryFileNames: "app.js", assetFileNames: "app[extname]" } } },
  css: { postcss: root },
});

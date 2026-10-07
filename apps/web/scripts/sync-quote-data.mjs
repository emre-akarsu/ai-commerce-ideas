#!/usr/bin/env node
// Copies the generated quote data (lib/quote-data/index.json and <tenant>/<scope>.json, each
// { meta, price_book, quote_first, quote_after_review, reviewer_decisions[] }) into the bundle by writing lib/quote/generated.ts,
// which imports every file statically so `next build` and the single-file demo both include it.
// lib/quote-data/ is written by the Python side; this script only reads it.
// Usage: npm run sync-quote-data            (validate and write lib/quote/generated.ts)
//        npm run sync-quote-data -- --check (exit 1 when generated.ts is stale or a file is malformed)
// Checks are shallow on purpose (JSON parses, formats start with price-books-ui/ and quote-draft-ui/); the app's tolerant readers
// do the real reading and show a clear error for anything they cannot read.
import fs from "node:fs";
import path from "node:path";

const web = path.resolve(import.meta.dirname, "..");
const src = path.join(web, "lib/quote-data");
const target = path.join(web, "lib/quote/generated.ts");
const check = process.argv.includes("--check");

const problems = [];
const files = [];
if (fs.existsSync(src)) {
  const index = path.join(src, "index.json");
  if (fs.existsSync(index)) { try { JSON.parse(fs.readFileSync(index, "utf8")); } catch (e) { problems.push(`index.json: not valid JSON (${e.message})`); } }
  for (const tenant of fs.readdirSync(src).sort()) {
    const dir = path.join(src, tenant);
    if (!fs.statSync(dir).isDirectory()) continue;
    for (const f of fs.readdirSync(dir).filter((n) => n.endsWith(".json")).sort()) {
      const rel = `${tenant}/${f}`;
      let doc;
      try { doc = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")); } catch (e) { problems.push(`${rel}: not valid JSON (${e.message})`); continue; }
      const fmt = (o) => (o && typeof o === "object" ? String(o.format ?? "") : "");
      if (!fmt(doc.price_book).startsWith("price-books-ui/")) problems.push(`${rel}: price_book.format is "${fmt(doc.price_book)}", expected price-books-ui/<n>`);
      if (!fmt(doc.quote_first).startsWith("quote-draft-ui/")) problems.push(`${rel}: quote_first.format is "${fmt(doc.quote_first)}", expected quote-draft-ui/<n>`);
      if (!fmt(doc.quote_after_review).startsWith("quote-draft-ui/")) problems.push(`${rel}: quote_after_review.format is "${fmt(doc.quote_after_review)}", expected quote-draft-ui/<n>`);
      files.push({ key: `${tenant}/${path.basename(f, ".json")}`, rel });
    }
  }
}

const lines = [
  "// Written by scripts/sync-quote-data.mjs from lib/quote-data/<tenant>/<scope>.json. Do not edit.",
  files.length ? `// ${files.length} generated file(s) bundled.` : "// No generated data has been synced yet.",
  ...files.map((f, i) => `import d${i} from "../quote-data/${f.rel}";`),
  "export const GENERATED: Record<string, unknown> = {",
  ...files.map((f, i) => `  ${JSON.stringify(f.key)}: d${i},`),
  "};",
  "",
];
const next = lines.join("\n");
const cur = fs.existsSync(target) ? fs.readFileSync(target, "utf8") : "";
for (const p of problems) console.error(`problem: ${p}`);
if (check) {
  if (cur !== next) { console.error("lib/quote/generated.ts is stale: run `npm run sync-quote-data`."); process.exit(1); }
  if (problems.length) process.exit(1);
  console.log(`lib/quote/generated.ts is current (${files.length} file(s)).`);
} else {
  fs.writeFileSync(target, next);
  console.log(`wrote lib/quote/generated.ts (${files.length} file(s))${problems.length ? `, ${problems.length} problem(s)` : ""}`);
  if (files.length === 0) console.log("lib/quote-data/ has no generated files yet; the screens say there is no data yet.");
}

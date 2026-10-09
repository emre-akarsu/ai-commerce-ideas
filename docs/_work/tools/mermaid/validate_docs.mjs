import puppeteer from "puppeteer-core";
import fs from "node:fs";
const blocks = JSON.parse(fs.readFileSync("/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/val/blocks.json", "utf8"));
const b = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args: ["--no-sandbox", "--allow-file-access-from-files"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900 });
await p.goto("file:///tmp/claude-0/mm/page.html");
await p.evaluate(() => mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "strict", flowchart: { htmlLabels: false, useMaxWidth: false } }));
let bad = 0;
for (const d of blocks) {
  const r = await p.evaluate(async (d) => {
    try { await mermaid.parse(d.body); const { svg } = await mermaid.render("v_" + Math.random().toString(36).slice(2), d.body); return { ok: true, n: svg.length, err: /Syntax error in text/.test(svg) }; }
    catch (e) { return { ok: false, err: String(e.message || e).slice(0, 400) }; }
  }, d);
  if (!r.ok || r.err) { bad++; console.log("FAIL", d.id, r.err); }
}
console.log("checked", blocks.length, "failed", bad);
await b.close();

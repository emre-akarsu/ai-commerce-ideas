import puppeteer from "puppeteer-core";
import fs from "node:fs";
const want = process.argv.slice(2);
const blocks = JSON.parse(fs.readFileSync("/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/val/blocks.json", "utf8")).filter((b) => want.includes(b.id));
const b = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args: ["--no-sandbox", "--allow-file-access-from-files"] });
const p = await b.newPage();
await p.setViewport({ width: 1600, height: 1000 });
await p.goto("file:///tmp/claude-0/mm/page.html");
await p.evaluate(() => mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose", flowchart: { htmlLabels: true, useMaxWidth: false } }));
fs.mkdirSync("/tmp/claude-0/mm/png", { recursive: true });
for (const d of blocks) {
  await p.evaluate(async (d) => { const { svg } = await mermaid.render("s_" + Math.random().toString(36).slice(2), d.body); document.getElementById("out").innerHTML = svg; }, d);
  const el = await p.$("#out svg");
  const name = d.id.replace(/[^a-z0-9]/gi, "_");
  await el.screenshot({ path: `/tmp/claude-0/mm/png/val_${name}.png` });
  const box = await el.boundingBox();
  console.log(d.id, Math.round(box.width) + "x" + Math.round(box.height), `/tmp/claude-0/mm/png/val_${name}.png`);
}
await b.close();

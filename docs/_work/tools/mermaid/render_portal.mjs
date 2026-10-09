import puppeteer from "puppeteer-core";
import fs from "node:fs";
const base = "/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/portal";
const blocks = JSON.parse(fs.readFileSync(base + "/blocks.json", "utf8"));
const b = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args: ["--no-sandbox", "--allow-file-access-from-files"] });
const p = await b.newPage();
await p.setViewport({ width: 1400, height: 900 });
await p.goto("file:///tmp/claude-0/mm/page.html");
await p.evaluate(() => mermaid.initialize({
  startOnLoad: false, theme: "base", securityLevel: "strict", fontFamily: "\"Source Sans 3\", system-ui, sans-serif",
  themeVariables: {
    fontFamily: "Source Sans 3, system-ui, sans-serif", fontSize: "15px",
    background: "#ffffff",
    primaryColor: "#e6edf7", primaryTextColor: "#10203a", primaryBorderColor: "#5b7ba6",
    secondaryColor: "#f3e6c4", secondaryTextColor: "#10203a", secondaryBorderColor: "#a9822d",
    tertiaryColor: "#f4f6f9", tertiaryTextColor: "#10203a", tertiaryBorderColor: "#b7c0cc",
    lineColor: "#44546a", textColor: "#10203a",
    noteBkgColor: "#f3e6c4", noteTextColor: "#10203a", noteBorderColor: "#a9822d",
    edgeLabelBackground: "#ffffff", clusterBkg: "#f4f6f9", clusterBorder: "#b7c0cc",
    actorBkg: "#e6edf7", actorBorder: "#5b7ba6", actorTextColor: "#10203a", actorLineColor: "#7d8ba0",
    signalColor: "#44546a", signalTextColor: "#10203a", labelBoxBkgColor: "#f3e6c4", labelBoxBorderColor: "#a9822d", labelTextColor: "#10203a",
    loopTextColor: "#10203a", activationBkgColor: "#d6e0f0", activationBorderColor: "#5b7ba6", sequenceNumberColor: "#ffffff",
    attributeBackgroundColorOdd: "#f4f6f9", attributeBackgroundColorEven: "#e6edf7",
    transitionColor: "#44546a", stateBkg: "#e6edf7", stateLabelColor: "#10203a", compositeBackground: "#f4f6f9", compositeBorder: "#b7c0cc", compositeTitleBackground: "#e6edf7",
    altBackground: "#f4f6f9", specialStateColor: "#44546a", innerEndBackground: "#44546a", errorBkgColor: "#fde3e1", errorTextColor: "#3a0d0d"
  },
  flowchart: { htmlLabels: false, useMaxWidth: false, curve: "basis", nodeSpacing: 40, rankSpacing: 48, padding: 16 },
  sequence: { useMaxWidth: false, wrap: true }, er: { useMaxWidth: false }, state: { useMaxWidth: false },
}));
let ok = 0, bad = 0;
for (const d of blocks) {
  const r = await p.evaluate(async (d) => {
    try { await mermaid.parse(d.body); const { svg } = await mermaid.render("g_" + d.key, d.body); return { ok: true, svg }; }
    catch (e) { return { ok: false, err: String(e.message || e).slice(0, 300) }; }
  }, d);
  if (r.ok) { fs.writeFileSync(base + "/svg/" + d.key + ".svg", r.svg); ok++; } else { bad++; console.log("FAIL", d.id, r.err); }
}
console.log("rendered", ok, "failed", bad);
await b.close();

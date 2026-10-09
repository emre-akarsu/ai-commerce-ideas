import puppeteer from "puppeteer-core";
import fs from "node:fs";
const base = "/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/portal/out";
const b = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args: ["--no-sandbox", "--allow-file-access-from-files"] });
const errors = [];
async function open(w, h, scheme, hash) {
  const p = await b.newPage();
  await p.setViewport({ width: w, height: h });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
  p.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 200)); });
  p.on("pageerror", (e) => errors.push("pageerror " + String(e).slice(0, 200)));
  await p.goto("file://" + base + "/test.html" + (hash || ""), { waitUntil: "load" });
  await new Promise((r) => setTimeout(r, 400));
  return p;
}
const shots = [
  [1440, 900, "light", "", "hub-light"],
  [1440, 1000, "light", "#tg-02", "tg02-light"],
  [1440, 1000, "dark", "#ar-activity", "activity-dark"],
  [390, 844, "light", "#ug-03", "ug03-phone"],
];
for (const [w, h, scheme, hash, name] of shots) {
  const p = await open(w, h, scheme, hash);
  const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, title: document.querySelector("#ui-doc h1")?.textContent, figs: document.querySelectorAll("#ui-doc figure.diagram").length, imgs: document.querySelectorAll("#ui-doc img").length }));
  console.log(name, JSON.stringify(info));
  await p.screenshot({ path: `${base}/shot-${name}.png` });
  await p.close();
}
console.log("errors:", errors.length, errors.slice(0, 5));
await b.close();

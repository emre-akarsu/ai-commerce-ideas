import puppeteer from "puppeteer-core";
const base = "/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/portal/out";
const b = await puppeteer.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args: ["--no-sandbox", "--allow-file-access-from-files"] });
const p = await b.newPage();
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));
await p.setViewport({ width: 1440, height: 900 });
await p.goto("file://" + base + "/test.html#tg-06~where-a-model-can-be-used", { waitUntil: "load" });
await new Promise((r) => setTimeout(r, 500));
const a = await p.evaluate(() => ({ h1: document.querySelector("#ui-doc h1").textContent, y: Math.round(window.scrollY), target: document.querySelector('#ui-doc [id="where-a-model-can-be-used"]')?.getBoundingClientRect().top }));
console.log("deep link:", JSON.stringify(a));
// click a nav link
await p.click('#ui-side a[data-doc="ug-03"]');
await new Promise((r) => setTimeout(r, 200));
console.log("after nav click:", await p.evaluate(() => [document.querySelector("#ui-doc h1").textContent, location.hash]));
// in-doc cross link: first link inside the doc that goes to another doc
const cross = await p.evaluate(() => { const a = document.querySelector('#ui-doc a[data-doc]:not(.permalink)'); return a ? [a.textContent, a.getAttribute("href")] : null; });
console.log("first cross link:", JSON.stringify(cross));
// search
await p.type("#ui-q", "preferred");
await new Promise((r) => setTimeout(r, 400));
const res = await p.evaluate(() => ({ n: document.querySelectorAll("#ui-results li").length, first: document.querySelector("#ui-results li a")?.textContent.slice(0, 120) }));
console.log("search:", JSON.stringify(res));
await p.click("#ui-results li a");
await new Promise((r) => setTimeout(r, 300));
console.log("after result click:", await p.evaluate(() => [document.querySelector("#ui-doc h1").textContent, location.hash, document.getElementById("ui-results").hidden]));
// diagram toggle
await p.goto("file://" + base + "/test.html#tg-02", { waitUntil: "load" });
await new Promise((r) => setTimeout(r, 300));
await p.click(".dfull");
console.log("full:", await p.evaluate(() => [document.querySelector(".diagram").className, getComputedStyle(document.querySelector(".diagram-scroll svg")).width]));
await p.click(".dfit");
console.log("fit:", await p.evaluate(() => [document.querySelector(".diagram").className, getComputedStyle(document.querySelector(".diagram-scroll svg")).width]));
// phone menu
await p.setViewport({ width: 390, height: 844 });
await p.goto("file://" + base + "/test.html#hub", { waitUntil: "load" });
await new Promise((r) => setTimeout(r, 300));
await p.click("#ui-menu");
console.log("menu open:", await p.evaluate(() => [document.body.className, getComputedStyle(document.getElementById("ui-side")).visibility]));
await p.click('#ui-side a[data-doc="tg-04"]');
await new Promise((r) => setTimeout(r, 300));
console.log("after phone nav:", await p.evaluate(() => [document.querySelector("#ui-doc h1").textContent, document.body.className, document.documentElement.scrollWidth]));
console.log("errors:", errs);
await b.close();

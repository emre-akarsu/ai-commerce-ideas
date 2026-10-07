// Drives Quote and Price books in a running mock-mode app (default http://localhost:3100) at 1280 px and 390 px (plus 360 px
// overflow), light and dark. Checks the synthetic banner, the not-a-quote note, page-level overflow, 40 px targets, focus,
// the stage toggle, "Why this price", demo-only choose buttons, the request/upload/RFQ previews and console errors.
// Saves docs/mvp/screenshots/quote-*.png and price-books-*.png.
// Usage: node e2e/quote.mjs   (WEB_URL, OUT_DIR override; QUOTE_PATH=/page.html#/quote PB_PATH=/page.html#/price-books for the demo; SHOTS=0 skips screenshots)
import { launch } from "./cdp.mjs";

const base = process.env.WEB_URL || "http://localhost:3100";
const quotePath = process.env.QUOTE_PATH || "/quote";
const pbPath = process.env.PB_PATH || "/price-books";
const out = process.env.OUT_DIR || new URL("../../../docs/mvp/screenshots/", import.meta.url).pathname;
const shots = process.env.SHOTS !== "0";
const b = await launch(9366);
const res = []; const ok = (name, cond, extra = "") => res.push([cond ? "PASS" : "FAIL", name, extra]);
const log = [];
const has = async (s) => (await b.text()).includes(s);
const sel = (s) => b.ev(`!!document.querySelector(${JSON.stringify(s)})`);
const clickSel = async (s, i = 0) => { const r = await b.ev(`(()=>{const e=document.querySelectorAll(${JSON.stringify(s)})[${i}];if(!e)return false;e.click();return true})()`); await b.sleep(350); return r; };
const setSelect = async (s, v) => { await b.ev(`(()=>{const e=document.querySelector(${JSON.stringify(s)});const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(e,${JSON.stringify(v)});e.dispatchEvent(new Event('change',{bubbles:true}))})()`); await b.sleep(400); };
async function overflow(label) { const o = await b.overflow(); log.push(`${label.padEnd(46)} scrollW ${o.scrollW} of ${o.w}${o.bad.length ? " " + JSON.stringify(o.bad) : ""}`); return o.scrollW <= o.w; }
async function smallTargets() { // visible interactive controls under 40 px high (inline text links inside prose are excluded)
  return b.ev(`[...document.querySelectorAll('main button, main select, main summary, main a[class*="min-h-target"], main input')].filter(e=>e.offsetParent!==null).filter(e=>e.getBoundingClientRect().height<39.5).map(e=>e.tagName+':'+(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,30)+' h='+Math.round(e.getBoundingClientRect().height)).slice(0,8)`);
}
async function open(path) { await b.go(base + path); await b.sleep(900); if (path.includes("#")) { await b.ev("location.reload()"); await b.sleep(1300); } }
const top = () => b.ev("window.scrollTo(0,0)");
const scrollTo = (s) => b.ev(`document.querySelector(${JSON.stringify(s)})?.scrollIntoView({block:'start'})`);

const modes = [["desktop", 1280, 900, false, false], ["desktop-dark", 1280, 900, false, true], ["mobile", 390, 844, true, false], ["mobile-dark", 390, 844, true, true]];
for (const [mode, w, h, mobile, dark] of modes) {
  await b.dark(dark); await b.size(w, h, mobile);
  // ---------------- Price books
  await open(pbPath);
  ok(`${mode} price books: synthetic banner`, await has("Synthetic demo data: fictional merchants and prices"));
  ok(`${mode} price books: merchant cards`, (await b.ev("document.querySelectorAll('[data-merchant]').length")) === 5);
  ok(`${mode} price books: status reason shown`, (await b.ev("[...document.querySelectorAll('[data-status-reason]')].every(e=>e.innerText.trim().length>5)")));
  ok(`${mode} price books: ladder pill, coverage bar, visibility, VAT`, await b.ev(`(()=>{const t=document.querySelector('[data-merchant]').innerText;return t.includes('Level')&&t.includes('lines priced')&&t.includes('Private to you')&&t.includes('VAT basis')&&t.includes('Next refresh due')})()`));
  ok(`${mode} price books: summary counts`, await has("5 merchants: 2 current, 1 stale, 1 missing"));
  ok(`${mode} price books: overflow`, await overflow(`${mode} price-books`));
  const small = await smallTargets(); ok(`${mode} price books: targets >= 40 px`, small.length === 0, small.join(" | "));
  if (shots) { await top(); await b.shot(`${out}/price-books-${mode}.png`); }
  if (mode === "desktop" || mode === "mobile") {
    ok(`${mode} price books: filter stale`, (await clickSel('[data-filter="stale"]')) && (await b.ev("document.querySelectorAll('[data-merchant]').length")) === 1);
    await clickSel('[data-filter="stale"]'); // toggle back
    ok(`${mode} price books: filter cleared`, (await b.ev("document.querySelectorAll('[data-merchant]').length")) === 5);
    await clickSel('[data-act="request"]');
    ok(`${mode} price books: request preview shows draft exactly`, (await sel('[data-dialog="request"]')) && (await b.ev(`document.querySelector('[data-draft-subject]').innerText.length>0 && document.querySelector('[data-draft-body]').innerText.includes('Hello')`)) && await has("Nothing is sent"));
    ok(`${mode} price books: dialog focus inside`, await b.ev(`document.querySelector('[role=dialog]').contains(document.activeElement)`));
    if (shots) await b.shot(`${out}/price-books-${mode}-request.png`);
    await clickSel("[data-demo-button]");
    ok(`${mode} price books: demo button sends nothing`, await has("Demo only: nothing was sent and nothing was approved."));
    ok(`${mode} price books: dialog overflow`, await overflow(`${mode} request dialog`));
    await b.key("Escape"); ok(`${mode} price books: Escape closes`, !(await sel("[role=dialog]")));
    await b.click("Upload price file");
    ok(`${mode} price books: upload shows static example`, (await sel('[data-dialog="upload"]')) && (await has("Static example only")) && (await has("quarantined")));
    if (shots) await b.shot(`${out}/price-books-${mode}-upload.png`);
    await b.key("Escape");
    await b.click("Send RFQ for these gaps");
    ok(`${mode} price books: RFQ lists gaps per merchant`, (await b.ev("document.querySelectorAll('[data-rfq-merchant]').length")) >= 2);
    if (shots) await b.shot(`${out}/price-books-${mode}-rfq.png`);
    ok(`${mode} price books: RFQ dialog overflow`, await overflow(`${mode} rfq dialog`));
    await b.key("Escape");
    ok(`${mode} price books: customer B has no data in the fixture state (clear message)`, await (async () => { await setSelect("[data-tenant]", "demo-tenant-b"); const t = await has("No price book for this customer"); await setSelect("[data-tenant]", "demo-tenant-a"); return t; })());
  }
  // ---------------- Quote
  await open(quotePath);
  ok(`${mode} quote: synthetic banner`, await has("Synthetic demo data: fictional merchants and prices"));
  ok(`${mode} quote: not a supplier quote note`, await sel("[data-notice]") && await has("This is not a supplier quote."));
  ok(`${mode} quote: totals card`, await b.ev(`(()=>{const t=document.querySelector('[data-totals]').innerText;return t.includes('Goods')&&t.includes('Delivery')&&t.includes('Subtotal')&&t.includes('VAT at 20%')&&t.includes('Total ex VAT')&&t.includes('Total inc VAT')&&t.includes('Basket')})()`));
  ok(`${mode} quote: partition adds up`, await b.ev(`(()=>{const n=[...document.querySelectorAll('[data-count] .num')].map(e=>Number(e.innerText));const t=document.querySelector('[data-partition-total]').innerText;return n.reduce((a,c)=>a+c,0)===12&&t.endsWith('= 12 lines')})()`));
  ok(`${mode} quote: all sections`, await b.ev(`['firm','review','indicative','unmatched','no-offer'].every(s=>document.querySelector('[data-section="'+s+'"]'))`));
  ok(`${mode} quote: indicative labelled and not in totals`, await b.ev(`(()=>{const e=document.querySelector('[data-section="indicative"]');return e.innerText.includes('indicative, not a quote')&&e.innerText.includes('never in totals')&&!document.querySelector('[data-totals]').innerText.includes('7.40')})()`));
  ok(`${mode} quote: arithmetic checks agree`, await b.ev(`document.querySelector('[data-checks] summary').innerText.includes('checked')`));
  ok(`${mode} quote: overflow`, await overflow(`${mode} quote first`));
  const small2 = await smallTargets(); ok(`${mode} quote: targets >= 40 px`, small2.length === 0, small2.join(" | "));
  if (shots) { await top(); await b.shot(`${out}/quote-${mode}-1-top.png`); }
  if (shots) { await scrollTo('[data-section="firm"]'); await b.shot(`${out}/quote-${mode}-2-firm.png`); }
  await clickSel("[data-why] summary");
  ok(`${mode} quote: why this price opens with reason codes and provenance`, await b.ev(`(()=>{const d=document.querySelector('[data-why]');return d.open&&d.innerText.includes('selected_lowest_landed_cost')&&d.innerText.includes('Provenance')&&d.innerText.includes('Synthetic')})()`));
  if (shots) { await b.ev(`document.querySelector('[data-why]').scrollIntoView({block:'center'})`); await b.shot(`${out}/quote-${mode}-3-why.png`); }
  ok(`${mode} quote: why overflow`, await overflow(`${mode} quote why open`));
  if (shots) { await scrollTo('[data-section="review"]'); await b.shot(`${out}/quote-${mode}-4-review.png`); }
  if (shots) { await scrollTo('[data-section="indicative"]'); await b.shot(`${out}/quote-${mode}-5-indicative.png`); }
  if (mode === "desktop" || mode === "mobile") {
    const before = await b.ev(`document.querySelector('[data-total="inc"]').innerText`);
    ok(`${mode} quote: review shows 3 candidates max with choose`, (await b.ev(`[...document.querySelectorAll('[data-review-line]')].every(l=>l.querySelectorAll('[data-candidate]').length<=3)`)) && (await b.ev("document.querySelectorAll('[data-candidate] button').length")) >= 3);
    await clickSel("[data-candidate] button");
    ok(`${mode} quote: choose is demo-only and does not move totals`, (await has("Chosen in this demo only")) && (await b.ev(`document.querySelector('[data-total="inc"]').innerText`)) === before);
    await clickSel('[data-stage="after"]');
    ok(`${mode} quote: stage toggle -> after review`, (await b.ev(`document.querySelector('[data-stage="after"]').getAttribute('aria-pressed')`)) === "true" && (await sel("[data-decisions]")) && await has("invented"));
    ok(`${mode} quote: after review has one more firm line and a different total`, (await b.ev("document.querySelectorAll('[data-firm-line]').length")) === 4 && (await b.ev(`document.querySelector('[data-total="inc"]').innerText`)) !== before);
    ok(`${mode} quote: after partition adds up`, await b.ev(`(()=>{const n=[...document.querySelectorAll('[data-count] .num')].map(e=>Number(e.innerText));return n.reduce((a,c)=>a+c,0)===12})()`));
    ok(`${mode} quote: after overflow`, await overflow(`${mode} quote after review`));
    if (shots) { await top(); await scrollTo("[data-decisions]"); await b.shot(`${out}/quote-${mode}-6-after-review.png`); }
    await clickSel('[data-stage="first"]');
    ok(`${mode} quote: toggle back`, (await b.ev("document.querySelectorAll('[data-firm-line]').length")) === 3);
    await setSelect("[data-tenant]", "demo-tenant-b");
    ok(`${mode} quote: customer without data says so`, await has("No quote for this customer and job scope yet"));
    await setSelect("[data-tenant]", "demo-tenant-a");
    // keyboard: the stage buttons are focusable and Enter/Space toggles
    await b.ev(`document.querySelector('[data-stage="after"]').focus()`); await b.key("Enter", { code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
    ok(`${mode} quote: keyboard toggles stage`, (await b.ev(`document.querySelector('[data-stage="after"]').getAttribute('aria-pressed')`)) === "true");
    ok(`${mode} quote: focus ring visible`, await b.ev(`(()=>{const e=document.activeElement;const s=getComputedStyle(e);return s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>=2})()`));
    await clickSel('[data-stage="first"]');
  }
}
// 360 px overflow on both screens, with every expander open
await b.dark(false); await b.size(360, 740, true);
await open(pbPath); ok("360 price books: overflow", await overflow("360 price-books"));
await open(quotePath);
await b.ev(`document.querySelectorAll('details').forEach(d=>d.open=true)`); await b.sleep(300);
ok("360 quote: overflow with all details open", await overflow("360 quote all open"));
await clickSel('[data-stage="after"]'); ok("360 quote after: overflow", await overflow("360 quote after"));
// Reduced motion: no animations declared on these screens
await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
ok("reduced motion: nothing on the page animates", await b.ev(`[...document.querySelectorAll('main *')].every(e=>{const s=getComputedStyle(e);return s.animationName==='none'||parseFloat(s.animationDuration)===0})`));
// Navigation entries exist
await b.size(1280, 900, false); await open(quotePath);
ok("nav has Price books and Quote", await b.ev(`(()=>{const t=[...document.querySelectorAll('nav[aria-label=Main] a')].map(a=>a.innerText.trim());return t.includes('Price books')&&t.includes('Quote')})()`));

ok("no console errors or warnings", b.logs.length === 0, b.logs.slice(0, 5).join(" | "));
for (const r of res) console.log(r.join("  "));
console.log("\noverflow (page scrollWidth vs viewport):\n" + log.join("\n"));
console.log("\nconsole:", b.logs.length ? b.logs.slice(0, 10) : "none");
console.log(res.filter((r) => r[0] === "FAIL").length, "failures of", res.length);
b.close();

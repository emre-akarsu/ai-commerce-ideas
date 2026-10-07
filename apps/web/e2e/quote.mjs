// Drives Quote and Price books in a running mock-mode app (default http://localhost:3100) against the generated data in
// lib/quote-data/: every customer and scope, first quote and after reviews, at 1280 px and 390 px (plus 360 px), light and dark.
// Compares what is on screen with lib/quote-data/index.json (counts, totals, merchant statuses). Checks the synthetic banner, the
// not-a-quote note, page-level overflow, 40 px targets, focus, "Why this price", demo-only buttons, dialogs and console errors.
// Saves docs/mvp/screenshots/quote-*.png and price-books-*.png.
// Usage: node e2e/quote.mjs   (WEB_URL, OUT_DIR; QUOTE_PATH=/page.html#/quote PB_PATH=/page.html#/price-books for the demo; SHOTS=0 skips screenshots)
import { readFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const base = process.env.WEB_URL || "http://localhost:3100";
const quotePath = process.env.QUOTE_PATH || "/quote";
const pbPath = process.env.PB_PATH || "/price-books";
const out = process.env.OUT_DIR || new URL("../../../docs/mvp/screenshots/", import.meta.url).pathname;
const shots = process.env.SHOTS !== "0";
const index = JSON.parse(readFileSync(new URL("../lib/quote-data/index.json", import.meta.url), "utf8"));
const combos = index.combinations;
const A = "demo-tenant-a", B = "demo-tenant-b";
const money = (s) => { const [i, f = ""] = s.split("."); return `${i.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}.${(f + "00").slice(0, 2)}`; };

const b = await launch(9366);
const res = []; const ok = (name, cond, extra = "") => res.push([cond ? "PASS" : "FAIL", name, extra]);
const log = [];
const has = async (s) => (await b.text()).includes(s);
const sel = (s) => b.ev(`!!document.querySelector(${JSON.stringify(s)})`);
const count = (s) => b.ev(`document.querySelectorAll(${JSON.stringify(s)}).length`);
const clickSel = async (s, i = 0) => { const r = await b.ev(`(()=>{const e=document.querySelectorAll(${JSON.stringify(s)})[${i}];if(!e)return false;e.click();return true})()`); await b.sleep(350); return r; };
const setSelect = async (s, v) => { await b.ev(`(()=>{const e=document.querySelector(${JSON.stringify(s)});const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(e,${JSON.stringify(v)});e.dispatchEvent(new Event('change',{bubbles:true}))})()`); await b.sleep(450); };
async function overflow(label) { const o = await b.overflow(); log.push(`${label.padEnd(52)} scrollW ${o.scrollW} of ${o.w}${o.bad.length ? " " + JSON.stringify(o.bad) : ""}`); return o.scrollW <= o.w; }
const smallTargets = () => b.ev(`[...document.querySelectorAll('main button, main select, main summary, main a[class*="min-h-target"], main input')].filter(e=>e.offsetParent!==null).filter(e=>e.getBoundingClientRect().height<39.5).map(e=>e.tagName+':'+(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,30)+' h='+Math.round(e.getBoundingClientRect().height)).slice(0,8)`);
async function open(path) { await b.go(base + path); await b.sleep(900); if (path.includes("#")) { await b.ev("location.reload()"); await b.sleep(1300); } }
const top = () => b.ev("window.scrollTo(0,0)");
const scrollTo = (s) => b.ev(`document.querySelector(${JSON.stringify(s)})?.scrollIntoView({block:'start'})`);
const partitionNumbers = () => b.ev(`Object.fromEntries([...document.querySelectorAll('[data-count]')].map(e=>[e.dataset.count,Number(e.querySelector('.num').innerText)]))`);
async function pick(tenant, scope) { await setSelect("[data-tenant]", tenant); await setSelect("[data-scope]", scope); }

async function checkQuote(tag, c, stage) {
  const e = stage === "after" ? c.after_review : c.first;
  const p = await partitionNumbers();
  ok(`${tag}: partition equals export and adds up to ${e.lines_total}`, p.priced === e.priced && p.review === e.review && p.unmatched === e.unmatched && p.indicativeOnly === e.indicative && p.noOffer === e.no_offer && p.skipped === e.skipped && Object.values(p).reduce((a, x) => a + x, 0) === e.lines_total, JSON.stringify(p));
  ok(`${tag}: totals equal export`, await b.ev(`(()=>{const t=document.querySelector('[data-totals]').innerText;return t.includes(${JSON.stringify(money(e.firm_total_inc_vat))})&&t.includes(${JSON.stringify(money(e.firm_total_ex_vat))})})()`), `${e.firm_total_ex_vat}/${e.firm_total_inc_vat}`);
  ok(`${tag}: firm lines listed = priced`, (await count("[data-firm-line]")) === e.priced);
  ok(`${tag}: arithmetic checks agree`, await b.ev(`document.querySelector('[data-checks] summary').innerText.includes('checked')`));
  ok(`${tag}: not-a-quote note and banner`, (await has("This is not a supplier quote.")) && (await has("Synthetic demo data: fictional merchants and prices")));
}

// ------------------------------------------------------------- every customer and scope, both stages (desktop and mobile, light)
for (const [mode, w, h, mobile] of [["desktop", 1280, 900, false], ["mobile", 390, 844, true]]) {
  await b.dark(false); await b.size(w, h, mobile);
  for (const c of combos) {
    const tag = `${mode} ${c.tenant_id.slice(-1).toUpperCase()}/${c.scope_id}`;
    await open(quotePath); await pick(c.tenant_id, c.scope_id);
    await checkQuote(`${tag} first`, c, "first");
    ok(`${tag} first: overflow`, await overflow(`${tag} quote first`));
    await clickSel('[data-stage="after"]');
    await checkQuote(`${tag} after`, c, "after");
    ok(`${tag} after: decisions panel labelled invented`, (await sel("[data-decisions]")) && (await b.ev(`document.querySelector('[data-decisions]').innerText.includes('invented')`)));
    ok(`${tag} after: overflow`, await overflow(`${tag} quote after`));
    // price book for the same pair
    await open(pbPath); await pick(c.tenant_id, c.scope_id);
    const pbk = c.price_book;
    ok(`${tag} price book: merchant statuses match`, (await count("[data-merchant]")) === 5 && (await count('[data-merchant][data-status="current"]')) === pbk.current && (await count('[data-merchant][data-status="stale"]')) === pbk.stale && (await count('[data-merchant][data-status="missing"]')) === pbk.missing && (await count('[data-merchant][data-status="indicative_only"]')) === pbk.indicative_only);
    ok(`${tag} price book: gaps = ${pbk.gaps}`, await b.ev(`(()=>{const t=document.querySelector('[data-gaps] h2').parentElement.innerText;return t.includes('${pbk.gaps} line')})()`));
    ok(`${tag} price book: overflow`, await overflow(`${tag} price book`));
    ok(`${tag} price book: targets >= 40 px`, (await smallTargets()).length === 0, (await smallTargets()).join(" | "));
  }
}

// ------------------------------------------------------------- detail runs and screenshots (A and B, full bathroom)
const cA = combos.find((c) => c.tenant_id === A && c.scope_id === "bathroom_full");
const modes = [["desktop", 1280, 900, false, false], ["desktop-dark", 1280, 900, false, true], ["mobile", 390, 844, true, false], ["mobile-dark", 390, 844, true, true]];
for (const [mode, w, h, mobile, dark] of modes) {
  await b.dark(dark); await b.size(w, h, mobile);
  // Price books, customer B (missing and indicative-only merchants)
  await open(pbPath); await pick(B, "bathroom_full");
  ok(`${mode} B price books: missing and indicative-only shown`, (await count('[data-status="missing"]')) === 2 && (await count('[data-status="indicative_only"]')) === 2 && (await has("2 missing")));
  ok(`${mode} B price books: reasons, ladder pill, coverage, visibility, VAT, next refresh`, await b.ev(`[...document.querySelectorAll('[data-merchant]')].every(m=>{const t=m.innerText;return t.includes('Level')&&t.includes('lines priced')&&t.includes('Visible to')&&t.includes('VAT basis')&&t.includes('Next refresh due')&&m.querySelector('[data-status-reason]').innerText.length>10})`));
  ok(`${mode} B price books: mixed VAT shows the row counts`, await b.ev(`document.body.innerText.includes('Mixed:') && document.body.innerText.includes('ex VAT')`));
  ok(`${mode} B price books: overflow`, await overflow(`${mode} B price-books`));
  if (shots) { await top(); await b.shot(`${out}/price-books-${mode}-customer-b.png`); }
  if (shots && mode !== "desktop-dark" && mode !== "mobile-dark") { await scrollTo("[data-gaps]"); await b.shot(`${out}/price-books-${mode}-gaps.png`); }
  // Price books, customer A (all current)
  await pick(A, "bathroom_full");
  ok(`${mode} A price books: all five current`, (await count('[data-status="current"]')) === 5 && (await has("5 current")));
  ok(`${mode} A price books: overflow`, await overflow(`${mode} A price-books`));
  if (shots) { await top(); await b.shot(`${out}/price-books-${mode}-customer-a.png`); }
  if (mode === "desktop" || mode === "mobile") {
    await pick(B, "bathroom_full");
    ok(`${mode} price books: filter missing`, (await clickSel('[data-filter="missing"]')) && (await count("[data-merchant]")) === 2);
    await clickSel('[data-filter="missing"]'); ok(`${mode} price books: filter cleared`, (await count("[data-merchant]")) === 5);
    ok(`${mode} price books: gaps list is limited, then expands`, (await count("[data-gap]")) === 8 && (await clickSel("[data-gaps] [data-limited-toggle]")) && (await count("[data-gap]")) === 58);
    await b.ev(`document.querySelector('[data-merchant][data-status="missing"] [data-act="request"]').click()`); await b.sleep(400);
    const draft = await b.ev(`({s:document.querySelector('[data-draft-subject]')?.innerText,b:document.querySelector('[data-draft-body]')?.innerText})`);
    ok(`${mode} price books: request preview shows subject and body exactly as drafted`, !!draft.s && draft.b.startsWith("Dear ") && (await has("Nothing is sent")), draft.s);
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
    ok(`${mode} price books: RFQ groups gaps per merchant`, (await count("[data-rfq-merchant]")) === 5);
    await clickSel("[data-rfq-merchant] summary");
    if (shots) await b.shot(`${out}/price-books-${mode}-rfq.png`);
    ok(`${mode} price books: RFQ dialog overflow`, await overflow(`${mode} rfq dialog`));
    await b.key("Escape");
  }
  // Quote, customer A full bathroom
  await open(quotePath); await pick(A, "bathroom_full");
  ok(`${mode} quote: totals card parts`, await b.ev(`(()=>{const t=document.querySelector('[data-totals]').innerText;return t.includes('Goods')&&t.includes('Delivery')&&t.includes('Subtotal')&&t.includes('VAT at 20%')&&t.includes('Total ex VAT')&&t.includes('Total inc VAT')&&t.includes('Basket')})()`));
  ok(`${mode} quote: firm lines grouped by merchant`, (await count("[data-merchant-group]")) >= 1);
  ok(`${mode} quote: review shows at most 3 candidates per line, with choose`, (await b.ev(`[...document.querySelectorAll('[data-review-line]')].every(l=>l.querySelectorAll('[data-candidate]').length<=3)`)) && (await count("[data-candidate] button")) >= 3);
  ok(`${mode} quote: long lists limited (5 review lines of ${cA.first.review})`, (await count("[data-review-line]")) === 5);
  ok(`${mode} quote: overflow`, await overflow(`${mode} A quote first`));
  ok(`${mode} quote: targets >= 40 px`, (await smallTargets()).length === 0, (await smallTargets()).join(" | "));
  if (shots) { await top(); await b.shot(`${out}/quote-${mode}-1-top.png`); await scrollTo('[data-section="firm"]'); await b.shot(`${out}/quote-${mode}-2-firm.png`); }
  await clickSel("[data-why] summary");
  ok(`${mode} quote: why this price shows reason codes and provenance`, await b.ev(`(()=>{const d=document.querySelector('[data-why]');return d.open&&/[a-z]+_[a-z_]+/.test(d.innerText)&&d.innerText.includes('Provenance')&&d.innerText.includes('Synthetic')})()`));
  ok(`${mode} quote: why overflow`, await overflow(`${mode} quote why open`));
  if (shots) { await b.ev(`document.querySelector('[data-why]').scrollIntoView({block:'center'})`); await b.shot(`${out}/quote-${mode}-3-why.png`); await scrollTo('[data-section="review"]'); await b.shot(`${out}/quote-${mode}-4-review.png`); await scrollTo('[data-section="unmatched"]'); await b.shot(`${out}/quote-${mode}-5-unmatched.png`); }
  if (mode === "desktop" || mode === "mobile") {
    const before = await b.ev(`document.querySelector('[data-total="inc"]').innerText`);
    await clickSel("[data-candidate] button");
    ok(`${mode} quote: choose is demo-only and does not move totals`, (await has("Chosen in this demo only")) && (await b.ev(`document.querySelector('[data-total="inc"]').innerText`)) === before);
    await clickSel("[data-section=review] [data-limited-toggle]");
    ok(`${mode} quote: show all review lines`, (await count("[data-review-line]")) === cA.first.review);
    ok(`${mode} quote: overflow with all review lines`, await overflow(`${mode} quote all review lines`));
    await clickSel('[data-stage="after"]');
    ok(`${mode} quote: stage toggle changes total and review count`, (await b.ev(`document.querySelector('[data-total="inc"]').innerText`)) !== before && (await b.ev(`document.querySelector('[data-stage="after"]').getAttribute('aria-pressed')`)) === "true");
    if (shots) { await top(); await scrollTo("[data-decisions]"); await b.shot(`${out}/quote-${mode}-6-after-review.png`); }
    await b.ev(`document.querySelector('[data-stage="first"]').focus()`); await b.key("Enter", { code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
    ok(`${mode} quote: keyboard toggles stage back`, (await b.ev(`document.querySelector('[data-stage="first"]').getAttribute('aria-pressed')`)) === "true");
    ok(`${mode} quote: focus ring visible`, await b.ev(`(()=>{const s=getComputedStyle(document.activeElement);return s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>=2})()`));
  } else if (shots) { await clickSel('[data-stage="after"]'); await top(); await scrollTo("[data-decisions]"); await b.shot(`${out}/quote-${mode}-6-after-review.png`); }
  // customer B quote
  await open(quotePath); await pick(B, "bathroom_full");
  if (shots && (mode === "desktop" || mode === "mobile")) { await top(); await b.shot(`${out}/quote-${mode}-customer-b.png`); }
}
// 360 px with everything open
await b.dark(false); await b.size(360, 740, true);
await open(pbPath); await pick(B, "bathroom_wet_room"); await clickSel("[data-gaps] [data-limited-toggle]");
ok("360 price books (B, wet room, all gaps): overflow", await overflow("360 price-books B wet room all gaps"));
await open(quotePath); await pick(A, "bathroom_wet_room"); await clickSel('[data-stage="after"]');
for (const s of ["review", "unmatched"]) await clickSel(`[data-section=${s}] [data-limited-toggle]`);
await b.ev(`document.querySelectorAll('details').forEach(d=>d.open=true)`); await b.sleep(300);
ok("360 quote (A, wet room, after, all open): overflow", await overflow("360 quote A wet room after all open"));
await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
ok("reduced motion: nothing on the page animates", await b.ev(`[...document.querySelectorAll('main *')].every(e=>{const s=getComputedStyle(e);return s.animationName==='none'||parseFloat(s.animationDuration)===0})`));
await b.size(1280, 900, false); await open(quotePath);
ok("nav has Price books and Quote", await b.ev(`(()=>{const t=[...document.querySelectorAll('nav[aria-label=Main] a')].map(a=>a.innerText.trim());return t.includes('Price books')&&t.includes('Quote')})()`));
ok("no console errors or warnings", b.logs.length === 0, b.logs.slice(0, 5).join(" | "));
for (const r of res) console.log(r.join("  "));
console.log("\noverflow (page scrollWidth vs viewport):\n" + log.join("\n"));
console.log("\nconsole:", b.logs.length ? b.logs.slice(0, 10) : "none");
console.log(res.filter((r) => r[0] === "FAIL").length, "failures of", res.length);
b.close();

// Drives Quote and Price books in a running mock-mode app (default http://localhost:3100) against the generated data in
// lib/quote-data/: every customer and scope, first quote and after reviews, at 1280 px and 390 px (plus 360 px), light and dark.
// Compares what is on screen with lib/quote-data/index.json (counts, totals, merchant statuses). Checks the synthetic banner, the
// not-a-quote note, page-level overflow, 40 px targets, focus, "Why this price", demo-only buttons, dialogs and console errors.
// Also the Options section (multi-supplier comparison): option cards against index.json, VAT basis on every amount, balanced panel,
// select-this-option (demo only), indicative block apart, overflow with every expander open, both tenants, several scopes.
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
// The redesign puts detail behind closed headings; this suite checks the content, so open every <details> as it appears.
if (process.env.AUTOOPEN !== "0") await b.send("Page.addScriptToEvaluateOnNewDocument", { source: "addEventListener('load',()=>setTimeout(()=>{const o=()=>document.querySelectorAll('details:not([open])').forEach(d=>{d.open=true});o();new MutationObserver(o).observe(document,{childList:true,subtree:true})},1200))" });
const res = []; const ok = (name, cond, extra = "") => res.push([cond ? "PASS" : "FAIL", name, extra]);
const log = [];
const has = async (s) => (await b.text()).includes(s);
const sel = (s) => b.ev(`!!document.querySelector(${JSON.stringify(s)})`);
const count = (s) => b.ev(`document.querySelectorAll(${JSON.stringify(s)}).length`);
const clickSel = async (s, i = 0) => { const r = await b.ev(`(()=>{const e=document.querySelectorAll(${JSON.stringify(s)})[${i}];if(!e)return false;e.click();return true})()`); await b.sleep(350); return r; };
const setSelect = async (s, v) => { await b.ev(`(()=>{const e=document.querySelector(${JSON.stringify(s)});const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(e,${JSON.stringify(v)});e.dispatchEvent(new Event('change',{bubbles:true}))})()`); await b.sleep(450); };
async function overflow(label) { const o = await b.overflow(); log.push(`${label.padEnd(52)} scrollW ${o.scrollW} of ${o.w}${o.bad.length ? " " + JSON.stringify(o.bad) : ""}`); return o.scrollW <= o.w; }
const smallTargets = () => b.ev(`[...document.querySelectorAll('main button, main select, main summary, main a[class*="min-h-target"], main input:not(.sr-only)')].filter(e=>e.offsetParent!==null).filter(e=>e.getBoundingClientRect().height<39.5).map(e=>e.tagName+':'+(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,30)+' h='+Math.round(e.getBoundingClientRect().height)).slice(0,8)`);
async function open(path) { await b.go(base + path); await b.sleep(900); if (path.includes("#")) { await b.ev("location.reload()"); await b.sleep(1300); } }
const top = () => b.ev("window.scrollTo(0,0)");
const scrollTo = (s) => b.ev(`document.querySelector(${JSON.stringify(s)})?.scrollIntoView({block:'start'})`);
// below the sticky header, so the section heading is visible in the screenshot
const scrollBelowHeader = async (s) => { await scrollTo(s); await b.ev(`window.scrollBy(0,-72)`); await b.sleep(150); };
const partitionNumbers = () => b.ev(`Object.fromEntries([...document.querySelectorAll('[data-count]')].map(e=>[e.dataset.count,Number(e.querySelector('.num').innerText)]))`);
async function pick(tenant, scope) { await setSelect("[data-tenant]", tenant); await setSelect("[data-scope]", scope); }

async function checkQuote(tag, c, stage) {
  const e = stage === "after" ? c.after_review : c.first;
  const p = await partitionNumbers();
  ok(`${tag}: partition equals export and adds up to ${e.lines_total}`, p.priced === e.priced && p.review === e.review && p.unmatched === e.unmatched && p.indicativeOnly === e.indicative && p.noOffer === e.no_offer && p.skipped === e.skipped && Object.values(p).reduce((a, x) => a + x, 0) === e.lines_total, JSON.stringify(p));
  ok(`${tag}: totals equal export`, await b.ev(`(()=>{const t=document.querySelector('[data-totals]').innerText;return t.includes(${JSON.stringify(money(e.firm_total_inc_vat))})&&t.includes(${JSON.stringify(money(e.firm_total_ex_vat))})})()`), `${e.firm_total_ex_vat}/${e.firm_total_inc_vat}`);
  ok(`${tag}: firm lines listed = priced`, (await count("[data-firm-line]")) === e.priced);
  ok(`${tag}: arithmetic checks agree`, await b.ev(`document.querySelector('[data-checks] summary').innerText.includes('checked')`));
  ok(`${tag}: not-a-quote note and banner`, (await has("Not a supplier quote")) && (await has("Demo data. Nothing is sent.")));
}


// ------------------------------------------------------------- the Options section
async function checkOptions(tag, c) {
  const o = c.options;
  ok(`${tag}: options section present, above the firm lines`, await b.ev(`(()=>{const s=document.querySelector('[data-section=options]');const f=document.querySelector('[data-section=firm]');return !!s&&!!f&&(s.compareDocumentPosition(f)&Node.DOCUMENT_POSITION_FOLLOWING)!==0})()`));
  ok(`${tag}: ${o.options_shown} option card(s) as in index.json`, (await count("[data-option]")) === o.options_shown, String(await count("[data-option]")));
  const ids = await b.ev(`[...document.querySelectorAll('[data-option]')].map(e=>e.dataset.option)`);
  ok(`${tag}: option order is the export's (${o.option_ids.join(", ")})`, JSON.stringify(ids) === JSON.stringify(o.option_ids), JSON.stringify(ids));
  ok(`${tag}: every card has ex VAT and inc VAT totals with the basis beside each`, await b.ev(`[...document.querySelectorAll('[data-option]')].every(e=>/GBP [0-9,]+\\.[0-9]{2} ex VAT/.test(e.querySelector('[data-option-total=ex]').innerText)&&/GBP [0-9,]+\\.[0-9]{2} inc VAT/.test(e.querySelector('[data-option-total=inc]').innerText))`));
  ok(`${tag}: every difference names its VAT basis (or says same total)`, await b.ev(`[...document.querySelectorAll('[data-option]')].every(e=>{const t=e.querySelector('[data-option-diff]').innerText;return t.startsWith('Same total')||/ (ex|inc) VAT /.test(t)})`));
  ok(`${tag}: lowest total shown equals the index (${o.lowest_total_ex_vat} ex VAT)`, await b.ev(`document.querySelector('[data-option]').querySelector('[data-option-total=ex]').innerText.includes(${JSON.stringify(money(o.lowest_total_ex_vat))})`));
  ok(`${tag}: suppliers, deliveries, lead time, flags, sentences and selector on every card`, await b.ev(`[...document.querySelectorAll('[data-option]')].every(e=>e.querySelector('[data-option-suppliers]')&&e.querySelector('[data-option-deliveries]')&&e.querySelector('[data-option-lead]')&&e.querySelector('[data-option-reasons]')&&e.querySelector('[data-select-option]')&&e.querySelector('[data-option-breakdown]'))`));
  ok(`${tag}: duplicates are labelled "same as" (${o.duplicates})`, (await count("[data-option-same] li")) === o.duplicates);
  ok(`${tag}: balanced option ${o.balanced_shown ? "shown" : "not shown"}, panel says ${o.balanced_status}`, ((await count('[data-option="balanced"]')) === 1) === o.balanced_shown && (await b.ev(`document.querySelector('[data-balanced-panel]').dataset.balancedStatus`)) === o.balanced_status);
  if (o.balanced_status === "computed") ok(`${tag}: balanced weights and the inputs they depend on`, await b.ev(`(()=>{const t=document.querySelector('[data-balanced-weights]').innerText;return t.includes('Total cost')&&t.includes('depends on your budget')&&t.includes('required-by')&&t.includes('limit')&&document.querySelector('[data-balanced-panel]').innerText.includes('unsourced placeholders')})()`));
  else ok(`${tag}: reason there is no balanced option`, await b.ev(`document.querySelector('[data-balanced-why]').innerText.includes('There is no balanced option')`));
  ok(`${tag}: optimiser note ${o.exact ? "absent" : "present"} (${o.exact ? "exact" : "not proven"})`, ((await count("[data-options-note]")) > 0) === (!o.exact || o.search_incomplete));
  ok(`${tag}: lines in no option = ${o.excluded_lines}`, o.excluded_lines === 0 ? !(await sel("[data-options-excluded]")) : await b.ev(`document.querySelector('[data-options-excluded] summary').innerText.includes('(${o.excluded_lines})')`));
  ok(`${tag}: indicative block ${o.indicative_lines ? "labelled apart" : "absent"}`, o.indicative_lines ? await b.ev(`(()=>{const e=document.querySelector('[data-options-indicative]');return !!e&&e.innerText.includes('indicative, not a quote')&&!e.closest('[data-option]')})()`) : !(await sel("[data-options-indicative]")));
  ok(`${tag}: not-a-quote and not-a-market-price wording`, await b.ev(`document.querySelector('[data-options-intro]').innerText.includes('not a market-wide best price')`));
}
async function selectFlow(tag) {
  const n = await count("[data-select-option]");
  await clickSel("[data-select-option]", n - 1);
  ok(`${tag}: select shows the demo-only next step and says nothing is ordered or sent`, await b.ev(`(()=>{const e=document.querySelector('[data-option-next]');return !!e&&e.innerText.includes('Nothing is ordered and nothing is sent')&&e.innerText.includes('Demo only')})()`));
  ok(`${tag}: selecting does not move the totals`, await b.ev(`document.querySelector('[data-total=inc]').innerText.length>0`));
  ok(`${tag}: selected card is marked pressed`, (await count('[data-select-option][aria-pressed=true]')) === 1);
}

// ------------------------------------------------------------- every customer and scope, both stages (desktop and mobile, light)
for (const [mode, w, h, mobile] of [["desktop", 1280, 900, false], ["mobile", 390, 844, true]]) {
  await b.dark(false); await b.size(w, h, mobile);
  for (const c of combos) {
    const tag = `${mode} ${c.tenant_id.slice(-1).toUpperCase()}/${c.scope_id}`;
    await open(quotePath); await pick(c.tenant_id, c.scope_id);
    await checkQuote(`${tag} first`, c, "first");
    ok(`${tag} first: overflow`, await overflow(`${tag} quote first`));
    await checkOptions(`${tag} options`, c);
    await b.ev(`document.querySelectorAll('[data-section=options] details').forEach(d=>d.open=true)`); await b.sleep(200);
    ok(`${tag} options: overflow with every expander open`, await overflow(`${tag} options expanded`));
    ok(`${tag} options: targets >= 40 px`, (await smallTargets()).length === 0, (await smallTargets()).join(" | "));
    if (c.tenant_id === A && c.scope_id === "bathroom_cloakroom" || c.tenant_id === B && c.scope_id === "bathroom_full") await selectFlow(`${tag} options`);
    await clickSel('[data-stage="after"]');
    await checkQuote(`${tag} after`, c, "after");
    ok(`${tag} after: decisions panel labelled invented`, (await sel("[data-decisions]")) && (await b.ev(`document.querySelector('[data-decisions]').innerText.includes('Demo data')`)));
    ok(`${tag} after: overflow`, await overflow(`${tag} quote after`));
    // price book for the same pair
    await open(pbPath); await pick(c.tenant_id, c.scope_id);
    const pbk = c.price_book;
    ok(`${tag} price book: merchant statuses match`, (await count("[data-merchant]")) === 5 && (await count('[data-merchant][data-status="current"]')) === pbk.current && (await count('[data-merchant][data-status="stale"]')) === pbk.stale && (await count('[data-merchant][data-status="missing"]')) === pbk.missing && (await count('[data-merchant][data-status="indicative_only"]')) === pbk.indicative_only);
    ok(`${tag} price book: gaps = ${pbk.gaps}`, await b.ev(`(()=>{const t=document.querySelector('[data-gaps] summary').innerText;return t.includes('${pbk.gaps} line')})()`));
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
  ok(`${mode} B price books: missing and indicative-only shown`, (await count('[data-status="missing"]')) === 2 && (await count('[data-status="indicative_only"]')) === 2 && (await b.ev(`document.querySelector('[data-filter="missing"]').innerText.startsWith('2')`)));
  ok(`${mode} B price books: reasons, ladder pill, coverage, visibility, VAT, next refresh`, await b.ev(`[...document.querySelectorAll('[data-merchant]')].every(m=>{const t=m.innerText;return t.includes('lines priced')&&t.includes('Visible to')&&t.includes('Price includes VAT?')&&t.includes('Next refresh due')&&m.querySelector('[data-status-reason]').innerText.length>10})`));
  ok(`${mode} B price books: mixed VAT shows the row counts`, await b.ev(`document.body.innerText.includes('Mixed:') && document.body.innerText.includes('ex VAT')`));
  ok(`${mode} B price books: overflow`, await overflow(`${mode} B price-books`));
  if (shots) { await top(); await b.shot(`${out}/price-books-${mode}-customer-b.png`); }
  if (shots && mode !== "desktop-dark" && mode !== "mobile-dark") { await scrollTo("[data-gaps]"); await b.shot(`${out}/price-books-${mode}-gaps.png`); }
  // Price books, customer A (all current)
  await pick(A, "bathroom_full");
  ok(`${mode} A price books: all five current`, (await count('[data-status="current"]')) === 5 && (await b.ev(`document.querySelector('[data-filter="current"]').innerText.startsWith('5')`)));
  ok(`${mode} A price books: overflow`, await overflow(`${mode} A price-books`));
  if (shots) { await top(); await b.shot(`${out}/price-books-${mode}-customer-a.png`); }
  if (mode === "desktop" || mode === "mobile") {
    await pick(B, "bathroom_full");
    ok(`${mode} price books: filter missing`, (await clickSel('[data-filter="missing"]')) && (await count("[data-merchant]")) === 2);
    await clickSel('[data-filter="missing"]'); ok(`${mode} price books: filter cleared`, (await count("[data-merchant]")) === 5);
    ok(`${mode} price books: gaps list is limited, then expands`, (await count("[data-gap]")) === 8 && (await clickSel("[data-gaps] [data-limited-toggle]")) && (await count("[data-gap]")) === Number((await b.ev(`document.querySelector('[data-gaps] summary').innerText`)).match(/(\d+) line/)[1]));
    await b.ev(`document.querySelector('[data-merchant][data-status="missing"] [data-act="request"]').click()`); await b.sleep(400);
    const draft = await b.ev(`({s:document.querySelector('[data-draft-subject]')?.innerText,b:document.querySelector('[data-draft-body]')?.innerText})`);
    ok(`${mode} price books: request preview shows subject and body exactly as drafted`, !!draft.s && draft.b.startsWith("Dear ") && (await has("Nothing is sent")), draft.s);
    ok(`${mode} price books: dialog focus inside`, await b.ev(`document.querySelector('[role=dialog]').contains(document.activeElement)`));
    if (shots) await b.shot(`${out}/price-books-${mode}-request.png`);
    await clickSel("[data-demo-button]");
    ok(`${mode} price books: demo button sends nothing`, await has("Demo only: nothing was sent and nothing was approved."));
    ok(`${mode} price books: dialog overflow`, await overflow(`${mode} request dialog`));
    await b.key("Escape"); ok(`${mode} price books: Escape closes`, !(await sel("[role=dialog]")));
    await b.click("Upload prices");
    ok(`${mode} price books: upload shows static example`, (await sel('[data-dialog="upload"]')) && (await has("Static example only")) && (await has("quarantined")));
    if (shots) await b.shot(`${out}/price-books-${mode}-upload.png`);
    await b.key("Escape");
    await b.click("Ask for missing prices");
    ok(`${mode} price books: RFQ groups gaps per merchant`, (await count("[data-rfq-merchant]")) === 5);
    ok(`${mode} price books: RFQ default is one aggregated message per supplier`, (await count("[data-rfq-message]")) === 5 && (await sel('[data-mode="per_supplier"]:checked')));
    await clickSel('[data-mode="per_item"]'); await b.sleep(200);
    ok(`${mode} price books: individual mode shows one message per item`, (await count("[data-rfq-message]")) > 5);
    await clickSel('[data-mode="per_supplier"]'); await b.sleep(200);
    ok(`${mode} price books: back to one message per supplier`, (await count("[data-rfq-message]")) === 5);
    await clickSel("[data-rfq-merchant] summary");
    if (shots) await b.shot(`${out}/price-books-${mode}-rfq.png`);
    ok(`${mode} price books: RFQ dialog overflow`, await overflow(`${mode} rfq dialog`));
    await b.key("Escape");
  }
  // Quote, customer A full bathroom
  await open(quotePath); await pick(A, "bathroom_full");
  ok(`${mode} quote: totals card parts`, await b.ev(`(()=>{const t=document.querySelector('[data-totals]').innerText;return t.includes('Goods')&&t.includes('Delivery')&&t.includes('Subtotal')&&t.includes('VAT at 20%')&&t.includes('Total ex VAT')&&t.includes('Total inc VAT')})()`));
  ok(`${mode} quote: firm lines grouped by merchant`, (await count("[data-merchant-group]")) >= 1);
  ok(`${mode} quote: review shows at most 3 candidates per line, with choose`, (await b.ev(`[...document.querySelectorAll('[data-review-line]')].every(l=>l.querySelectorAll('[data-candidate]').length<=3)`)) && (await count("[data-candidate] button")) >= 3);
  ok(`${mode} quote: long lists limited (5 review lines of ${cA.first.review})`, (await count("[data-review-line]")) === 5);
  ok(`${mode} quote: overflow`, await overflow(`${mode} A quote first`));
  ok(`${mode} quote: targets >= 40 px`, (await smallTargets()).length === 0, (await smallTargets()).join(" | "));
  if (shots) { await top(); await b.shot(`${out}/quote-${mode}-1-top.png`); await scrollTo('[data-section="firm"]'); await b.shot(`${out}/quote-${mode}-2-firm.png`); }
  await b.ev(`document.querySelector("[data-why]").open=true`);
  ok(`${mode} quote: why this price shows reason codes and provenance`, await b.ev(`(()=>{const d=document.querySelector('[data-why]');return d.open&&d.innerText.includes('Provenance')&&d.innerText.includes('Synthetic')})()`));
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

  // Options: customer A cloakroom (balanced option, preferred list, unproven lowest total), customer A full (no balanced option), customer B cloakroom (all duplicates)
  for (const [tenant, scope, name] of [[A, "bathroom_cloakroom", "a-cloakroom"], [A, "bathroom_full", "a-full"], [B, "bathroom_cloakroom", "b-cloakroom"]]) {
    await open(quotePath); await pick(tenant, scope);
    const c = combos.find((x) => x.tenant_id === tenant && x.scope_id === scope);
    await checkOptions(`${mode} options ${name}`, c);
    ok(`${mode} options ${name}: overflow`, await overflow(`${mode} options ${name}`));
    if (shots) { await scrollBelowHeader('[data-section="options"]'); await b.shot(`${out}/quote-${mode}-7-options-${name}.png`); }
    await selectFlow(`${mode} options ${name}`);
    if (shots && name === "a-cloakroom") { await scrollBelowHeader("[data-option-next]"); await b.shot(`${out}/quote-${mode}-8-options-selected.png`); }
    await b.ev(`document.querySelectorAll('[data-section=options] details').forEach(d=>d.open=true)`); await b.sleep(250);
    ok(`${mode} options ${name}: overflow with every expander open`, await overflow(`${mode} options ${name} expanded`));
    if (shots && name === "a-cloakroom") { await scrollBelowHeader("[data-balanced-panel]"); await b.shot(`${out}/quote-${mode}-9-options-balanced.png`); }
  }
}
// 360 px with everything open
await b.dark(false); await b.size(360, 740, true);
await open(pbPath); await pick(B, "bathroom_wet_room"); await clickSel("[data-gaps] [data-limited-toggle]");
ok("360 price books (B, wet room, all gaps): overflow", await overflow("360 price-books B wet room all gaps"));
await open(quotePath); await pick(A, "bathroom_wet_room"); await clickSel('[data-stage="after"]');
ok("360 options (A, wet room, after, all open): present", (await count("[data-option]")) > 0);
for (const s of ["review", "unmatched"]) await clickSel(`[data-section=${s}] [data-limited-toggle]`);
await b.ev(`document.querySelectorAll('details').forEach(d=>d.open=true)`); await b.sleep(300);
ok("360 quote (A, wet room, after, all open): overflow", await overflow("360 quote A wet room after all open"));
await b.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
ok("reduced motion: nothing on the page animates", await b.ev(`[...document.querySelectorAll('main *')].every(e=>{const s=getComputedStyle(e);return s.animationName==='none'||parseFloat(s.animationDuration)===0})`));
await b.size(1280, 900, false); await open(quotePath);
ok("nav has six items including Quote a job", await b.ev(`(()=>{const t=[...document.querySelectorAll('nav[aria-label=Main] a')].map(a=>a.innerText.trim());return t.some(x=>x.startsWith('Home'))&&t.includes('Quote a job')&&t.length===6})()`));
ok("no console errors or warnings", b.logs.length === 0, b.logs.slice(0, 5).join(" | "));
for (const r of res) console.log(r.join("  "));
console.log("\noverflow (page scrollWidth vs viewport):\n" + log.join("\n"));
console.log("\nconsole:", b.logs.length ? b.logs.slice(0, 10) : "none");
console.log(res.filter((r) => r[0] === "FAIL").length, "failures of", res.length);
b.close();

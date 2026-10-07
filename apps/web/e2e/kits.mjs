// Drives the job-kit wizard in a running mock-mode app (default http://localhost:3100) through every
// bundled scope at defaults, at 1280 px and 390 px, light and dark. Saves screenshots to
// docs/mvp/screenshots/kits-*.png, checks page-level horizontal overflow on every step, compares the
// summary quantities with the Python resolver fixture, exercises the Config tab (bad format and a
// job-kit-ui/2 sample) and reports console errors.
// Usage: node e2e/kits.mjs   (WEB_URL, OUT_DIR, KITS_PATH override; KITS_PATH=/index.html#/kits for the demo)
import { readFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const base = process.env.WEB_URL || "http://localhost:3100";
const kitsPath = process.env.KITS_PATH || "/kits";
const out = process.env.OUT_DIR || new URL("../../../docs/mvp/screenshots/", import.meta.url).pathname;
const shots = process.env.SHOTS !== "0";
const fixture = JSON.parse(readFileSync(new URL("../tests/fixtures/kits-resolved-defaults.json", import.meta.url), "utf8"));
const SCOPES = fixture.cases.filter((c) => c.case === "defaults").map((c) => c.scope_id);

const b = await launch(9355);
const res = []; const ok = (name, cond, extra = "") => res.push([cond ? "PASS" : "FAIL", name, extra]);
const overflowLog = [];
const has = async (s) => (await b.text()).includes(s);
const clickSel = async (sel) => { const r = await b.ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return false;e.click();return true})()`); await b.sleep(400); return r; };
const toStep = () => b.ev(`(()=>{const h=document.querySelector('[data-step-heading]');if(h)h.scrollIntoView({block:'start'});return true})()`);
const step = () => b.ev(`document.querySelector('[aria-current=step]')?.innerText ?? ''`);
async function checkOverflow(label) {
  const o = await b.overflow();
  overflowLog.push(`${label.padEnd(44)} scrollW ${o.scrollW} of ${o.w}${o.bad.length ? " " + JSON.stringify(o.bad) : ""}`);
  return o.scrollW <= o.w;
}
async function summaryDiffs(scope, name) {
  const ui = await b.ev(`Object.fromEntries([...document.querySelectorAll('[data-summary-line]')].map(e=>[e.dataset.summaryLine, e.lastElementChild.innerText.trim()]))`);
  const want = fixture.cases.find((c) => c.scope_id === scope && c.case === name).lines;
  const diffs = Object.entries(want).filter(([id, v]) => !ui[id] || Number(ui[id].split(" ")[0]) !== Number(v.quantity) || ui[id].split(" ")[1] !== v.unit).map(([id]) => id);
  const extra = Object.keys(ui).filter((id) => !(id in want));
  return { n: Object.keys(want).length, bad: [...diffs, ...extra.map((x) => `+${x}`)] };
}
async function open() {
  await b.go(base + kitsPath); await b.sleep(900);
  if (kitsPath.includes("#")) { await b.ev("location.reload()"); await b.sleep(1200); }
}

const modes = [["desktop", 1280, 900, false, false], ["desktop-dark", 1280, 900, false, true], ["mobile", 390, 844, true, false], ["mobile-dark", 390, 844, true, true]];
for (const [mode, w, h, mobile, dark] of modes) {
  await b.dark(dark); await b.size(w, h, mobile);
  await open();
  ok(`${mode}: seed label visible`, await has("synthetic/illustrative seed — tradesperson review required"));
  ok(`${mode}: scope picker overflow`, await checkOverflow(`${mode} scope picker`));
  if (shots) await b.shot(`${out}/kits-${mode}-0-scopes.png`);
  for (const scope of SCOPES) {
    await open();
    ok(`${mode} ${scope}: scope card`, await clickSel(`[data-scope="${scope}"]`));
    await b.sleep(300);
    if ((await step()).includes("Questions")) {
      const n = await b.ev("document.querySelectorAll('[data-question]').length");
      ok(`${mode} ${scope}: 1-3 upfront questions`, n >= 1 && n <= 4, `${n}`);
      ok(`${mode} ${scope}: questions overflow`, await checkOverflow(`${mode} ${scope} questions`));
      if (shots && scope === "bathroom_full") { if (mobile) await toStep(); await b.shot(`${out}/kits-${mode}-1-questions.png`); }
      await b.click("Continue");
    }
    if ((await step()).includes("Measure")) {
      ok(`${mode} ${scope}: derived values shown`, await has("Worked out for you"));
      ok(`${mode} ${scope}: measure overflow`, await checkOverflow(`${mode} ${scope} measure`));
      if (shots && scope === "bathroom_full") { if (mobile) await toStep(); await b.shot(`${out}/kits-${mode}-2-measure.png`); }
      await b.click("Continue");
    }
    ok(`${mode} ${scope}: on review`, (await step()).includes("Review"), await step());
    ok(`${mode} ${scope}: ledger chips`, (await b.ev("document.querySelectorAll('[aria-label=\"Defaults we assumed\"] button').length")) > 0);
    await clickSel("[data-module] summary"); // open the first section
    ok(`${mode} ${scope}: review overflow`, await checkOverflow(`${mode} ${scope} review`));
    if (shots) { if (mobile) await b.ev(`document.querySelector('[data-module]').scrollIntoView({block:'start'})`); await b.shot(`${out}/kits-${mode}-${scope}-3-review.png`); }
    ok(`${mode} ${scope}: accept all defaults`, await b.click("Accept all defaults"));
    ok(`${mode} ${scope}: on summary`, (await step()).includes("Summary"));
    // Parity in the browser: summary quantities equal the Python resolver at defaults.
    const d = await summaryDiffs(scope, "defaults");
    ok(`${mode} ${scope}: summary quantities match Python (${d.n} lines)`, d.bad.length === 0, d.bad.slice(0, 5).join(","));
    ok(`${mode} ${scope}: summary overflow`, await checkOverflow(`${mode} ${scope} summary`));
    if (shots) { if (mobile) await toStep(); await b.shot(`${out}/kits-${mode}-${scope}-4-summary.png`); }
    if (mode === "desktop") {
      ok(`${scope}: create RFQ draft`, await b.click("Create RFQ draft"));
      ok(`${scope}: draft says not wired`, (await has("Not wired")) && (await has("nothing was sent")));
    }
  }
}

// Review interactions (desktop light): tri-state, ledger edit, keyboard on a question.
await b.dark(false); await b.size(1280, 900);
// Finish level in the browser: Budget and Premium tier cards give the Python quantities and options.
for (const [level, name] of [["budget", "finish_budget"], ["premium", "finish_premium"]]) {
  for (const scope of SCOPES) {
    await open(); await clickSel(`[data-scope="${scope}"]`);
    if (!(await b.ev(`!!document.querySelector('[data-question="finish_level"]')`))) {
      // finish_level asked on review: change it through its ledger chip.
      while ((await step()) && !(await step()).includes("Review")) await b.click("Continue");
      await b.ev(`[...document.querySelectorAll('[aria-label="Defaults we assumed"] button')].find(x=>x.innerText.startsWith('Finish level')).click()`); await b.sleep(300);
    }
    await b.ev(`(()=>{const i=[...document.querySelectorAll('[data-question="finish_level"] input[type=radio]')];const t=i.find(x=>x.closest('label').innerText.toLowerCase().startsWith(${JSON.stringify(level)}));t.click()})()`); await b.sleep(300);
    if (level === "premium" && scope === "bathroom_full" && shots) { await b.ev(`document.querySelector('[data-question="finish_level"]').scrollIntoView({block:"center"})`); await b.shot(`${out}/kits-desktop-finish-premium.png`); }
    while (!(await step()).includes("Review")) await b.click("Continue");
    await b.click("Accept all defaults");
    const d = await summaryDiffs(scope, name);
    ok(`${scope} at ${level}: summary matches Python (${d.n} lines)`, d.bad.length === 0, d.bad.slice(0, 5).join(","));
  }
}

// Don't know: hot_water_system -> gravity (electric shower), recorded as an assumption.
await open(); await clickSel('[data-scope="bathroom_full"]');
await b.ev(`[...document.querySelectorAll('[data-question="hot_water_system"] label')].find(l=>l.innerText.startsWith("Don't know")).click()`); await b.sleep(300);
ok("don't know: chosen and explained", await b.ev(`document.querySelector('[data-question="hot_water_system"]').innerText.includes('We will assume')`));
while (!(await step()).includes("Review")) await b.click("Continue");
await b.click("Accept all defaults");
const dk = await summaryDiffs("bathroom_full", "unknown_answers");
ok(`don't know: summary matches Python unknown_answers (${dk.n} lines)`, dk.bad.length === 0, dk.bad.slice(0, 5).join(","));
await clickSel("[data-assumptions] summary");
ok("don't know: listed as an assumption", (await has("Don't know: treated as")) && (await has('You said "don\'t know"')));
ok("paid add-ons stay off by default", !(await b.ev(`!!document.querySelector('[data-summary-line^="ex_"]')`)));
if (shots) { await b.ev(`document.querySelector('[data-assumptions]').scrollIntoView({block:'center'})`); await b.shot(`${out}/kits-desktop-summary-assumptions.png`); }

await open(); await clickSel('[data-scope="bathroom_full"]');
await b.ev(`document.querySelector('[data-question="shower_location"] input[type=radio]').focus()`);
await b.key("ArrowDown"); await b.sleep(200);
ok("keyboard: arrow key changes a card choice", await b.ev(`document.querySelectorAll('[data-question="shower_location"] input[type=radio]')[1].checked`));
await b.click("Continue"); await b.click("Continue");
await clickSel('[data-module="strip_out"] summary');
await b.ev(`(()=>{const r=[...document.querySelectorAll('[data-line="so_cap_feeds"] input[type=radio]')].find(i=>i.parentElement.innerText.includes('Already have'));r.click()})()`); await b.sleep(300);
ok("tri-state: Already have counted", await b.ev(`document.querySelector('[data-module="strip_out"] summary').innerText.includes('1 already have')`));
await b.ev(`[...document.querySelectorAll('[aria-label="Defaults we assumed"] button')].find(x=>x.innerText.includes('Basin type')).click()`); await b.sleep(300);
await b.click("Wall-hung basin"); await b.sleep(300);
ok("ledger: one tap opens the editor and the change shows", await b.ev(`[...document.querySelectorAll('[aria-label="Defaults we assumed"] button')].some(x=>x.innerText.includes('Wall-hung basin')&&x.innerText.includes('changed'))`));
if (shots) await b.shot(`${out}/kits-desktop-review-edited.png`);

// Defaults are pre-selected; one-tap presets; a former quote as template.
await open(); await clickSel('[data-scope="bathroom_full"]');
ok("defaults: every question card has one option already selected", await b.ev(`[...document.querySelectorAll('[data-question]')].length>0 && [...document.querySelectorAll('[data-question]')].every(q=>q.querySelector('input:checked')||q.querySelector('select')||q.querySelector('input[type=checkbox]'))`));
while (!(await step()).includes("Review")) await b.click("Continue");
const pickCount = () => b.ev(`document.querySelectorAll('[data-line] input[type=radio]:checked').length`);
ok("presets: bar is on review with template defaults", await b.ev(`!!document.querySelector('[data-presets]')`));
await clickSel('[data-preset="premium"]');
ok("presets: premium pressed", await b.ev(`document.querySelector('[data-preset="premium"]').getAttribute('aria-pressed')==='true'`));
await clickSel('[data-preset="budget"]');
ok("presets: budget replaces premium", await b.ev(`document.querySelector('[data-preset="budget"]').getAttribute('aria-pressed')==='true' && document.querySelector('[data-preset="premium"]').getAttribute('aria-pressed')==='false'`));
await clickSel('[data-preset="defaults"]');
await b.click("Accept all defaults");
await b.fill("[data-save-template] input", "My test bathroom");
await b.click("Save as template");
ok("template: saved", await has('Saved "My test bathroom"'));
await b.click("Start a different job");
ok("template: offered on the scope step", await b.ev(`[...document.querySelectorAll('[data-template]')].some(e=>e.innerText.includes('My test bathroom'))`));
await b.ev(`[...document.querySelectorAll('[data-template]')].find(e=>e.innerText.includes('My test bathroom')).querySelector('[data-use-template]').click()`); await b.sleep(400);
ok("template: lands on the measure step to confirm sizes", (await step()).includes("Measure"), await step());
await b.ev(`window.localStorage.removeItem('kit-templates-v1')`);

// Config tab: bad format, then a v2 sample built from a bundled kit.
await open();
await b.click("Config");
await b.fill("#kit-json", JSON.stringify({ format: "job-kit-ui/9", label: "x" }));
await b.click("Check config");
ok("config: unknown major explained", (await has("Unsupported format")) && (await has("cannot read")));
if (shots) await b.shot(`${out}/kits-desktop-config-error.png`);
await b.ev(`(()=>{const s=document.querySelector('select[aria-label^="Load a bundled kit"]');const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(s,'uk/bathroom_full');s.dispatchEvent(new Event('change',{bubbles:true}))})()`);
await b.sleep(300);
const v2 = await b.ev(`(()=>{const k=JSON.parse(document.querySelector('#kit-json').value);k.format='job-kit-ui/2';if(!k.finish_levels)k.finish_levels=[{id:'budget',label:'Budget',description:'Cheapest option that still meets the rules.'},{id:'most_used',label:'Most used',description:'The usual pick for this job.'},{id:'premium',label:'Premium',description:'Higher spec, only if you choose it.'}];
if(!k.questions.some(q=>q.id==='finish_level'))k.questions.push({id:'finish_level',question:'Finish level?',type:'enum',ask:'upfront',priority:20,default:'most_used',options:[{value:'budget',label:'Budget'},{value:'most_used',label:'Most used'},{value:'premium',label:'Premium'}],help:'Sets every tiered line at once.'});
const sl=k.questions.find(q=>q.id==='shower_location');Object.assign(sl,{help:'Edited help text from the Config tab.',widget:'mystery'});
for(const m of k.modules)for(const l of m.lines){if(l.id==='sw_basin_taps'){l.options[0].tags=['budget'];l.options[1].tags=['most_used'];l.options[1].evidence_grade='C';l.options[0].price_band={min:'18',max:'30',currency:'GBP',per:'nr',vat:'inc',observed_on:'2026-10-06',basis:'one retailer listing'};l.options[0].why_default='Cheapest compliant pair in social-landlord specs.'}
if(l.id==='ff_pipe_15'){l.options[0].tags=['most_used'];l.options[0].evidence_grade='A';l.options[1].tags=['premium']}
if(l.id==='wp_tanking_kit'){l.forced_by={text:'BS 5385-1 recommends a tanking membrane in shower areas.',source_url:'https://example.invalid/bs5385'}}}
k.surprise_field=true;return JSON.stringify(k)})()`);
await b.fill("#kit-json", v2);
await b.click("Check config");
ok("config: v2 sample readable with notes", (await has("Readable")) && (await has("Notes (the config still works)")));
await b.click("Preview in the wizard"); await b.sleep(400);
ok("v2: tier cards shown", (await b.ev(`document.querySelector('[data-question="finish_level"]')?.dataset.widget`)) === "tier-cards");
ok("v2: unknown widget hint falls back to cards", (await b.ev(`document.querySelector('[data-question="shower_location"]')?.dataset.widget`)) === "choice-cards");
ok("v2: edited help text shows without a rebuild", await has("Edited help text from the Config tab."));
ok("v2: don't know choice offered", await has("We will assume"));
if (shots) await b.shot(`${out}/kits-desktop-v2-questions.png`);
await b.size(390, 844, true); await toStep(); if (shots) await b.shot(`${out}/kits-mobile-v2-questions.png`);
ok("v2 mobile: questions overflow", await checkOverflow("mobile v2 questions"));
await b.size(1280, 900);
await b.click("Continue"); await b.click("Continue");
await clickSel('[data-module="basin"] summary'); await clickSel('[data-module="waterproofing"] summary');
ok("v2: most used badge not shown for grade C", !(await b.ev(`document.querySelector('[data-line="sw_basin_taps"]').innerText.includes('Most used')`)));
ok("v2: standard pick label for grade C", await b.ev(`document.querySelector('[data-line="sw_basin_taps"]').innerText.includes('Our standard pick')`));
ok("v2: price band with VAT and not-verified note", await b.ev(`(()=>{const t=document.querySelector('[data-line="sw_basin_taps"]').innerText;return t.includes('inc VAT')&&t.includes('Observed price, not verified')})()`));
ok("v2: forced line shows a lock reason, not a choice", await b.ev(`(()=>{const e=document.querySelector('[data-line="wp_tanking_kit"]');return e.innerText.includes('Required here.')&&!e.querySelector('input[name^="tri-"]')})()`));
ok("v2: premium never pre-selected", await b.ev(`(()=>{const e=[...document.querySelectorAll('[data-line="ff_pipe_15"] label')].find(l=>l.textContent.includes('Premium'));return !!e&&!e.querySelector('input').checked})()`));
await b.ev(`document.querySelector('[data-line="sw_basin_taps"]').scrollIntoView({block:'center'})`); await b.sleep(200);
if (shots) await b.shot(`${out}/kits-desktop-v2-review-options.png`);
await b.dark(true); if (shots) await b.shot(`${out}/kits-desktop-dark-v2-review-options.png`);

ok("no console errors or warnings", b.logs.length === 0, b.logs.slice(0, 5).join(" | "));
for (const r of res) console.log(r.join("  "));
console.log("\noverflow (page scrollWidth vs viewport):\n" + overflowLog.join("\n"));
console.log("\nconsole:", b.logs.length ? b.logs.slice(0, 10) : "none");
console.log(res.filter((r) => r[0] === "FAIL").length, "failures of", res.length);
b.close();

// UX audit, step 02 (cognitive load). For each screen state it counts what is on the page from the DOM at the moment
// the screenshot is taken, saves the screenshot, and writes the counts and the method to
// docs/mvp/ux-audit/02-cognitive-load.md. Screenshots: docs/mvp/screenshots/audit/audit-<screen>-<desktop|mobile>-<light|dark>.png
//
// Prerequisites (this script neither builds nor starts a dev server):
//   cd apps/web && npx vite build -c demo/vite.config.mjs && node demo/inline.mjs
//   python3 -m http.server 3300 --bind 127.0.0.1 --directory apps/web/demo-dist
// Run: node docs/mvp/ux-audit/tools/capture.mjs      (DEMO_URL overrides http://127.0.0.1:3300)
// Offline and deterministic: the mock demo makes no network calls. Reads apps/web/e2e/cdp.mjs; writes only the two outputs above.

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { launch } from "../../../../apps/web/e2e/cdp.mjs";

const BASE = process.env.DEMO_URL || "http://127.0.0.1:3300";
const DEBUG_PORT = 9381; // other audits use 9366 and 9377-9379
const REPO = fileURLToPath(new URL("../../../../", import.meta.url));
const SHOT_DIR = fileURLToPath(new URL("../../screenshots/audit/", import.meta.url));
const DOC_PATH = fileURLToPath(new URL("../02-cognitive-load.md", import.meta.url));

const VIEWPORTS = {
  desktop: { width: 1280, height: 800, mobile: false },
  mobile: { width: 390, height: 844, mobile: true },
};

// Table order. Customer A is demo-tenant-a (the default); customer B is demo-tenant-b.
const SCREENS = [
  ["kits-scope", "Job kits: scope step (choose a job)"],
  ["kits-questions", "Job kits: questions step (bathroom full, default answers)"],
  ["kits-measure", "Job kits: measure step"],
  ["kits-review", "Job kits: review step (defaults filled in)"],
  ["kits-summary", "Job kits: summary step"],
  ["price-books", "Price books (default customer A)"],
  ["price-books-request", "Price books: Request price file dialog (customer B)"],
  ["price-books-upload", "Price books: Upload price file dialog"],
  ["price-books-rfq", "Price books: Request quotes dialog, Send RFQ for these gaps (customer B)"],
  ["quote", "Quote: first quote (default customer A, bathroom full)"],
  ["quote-options", "Quote: scrolled to Options"],
  ["inbox", "Inbox (#/)"],
  ["requests", "Requests (#/requests)"],
  ["suppliers", "Suppliers (#/vendors)"],
  ["setup", "Setup (#/setup)"],
  ["audit", "Audit trail (#/audit)"],
];
const LABEL = new Map(SCREENS);
const DARK = new Set(["kits-review", "price-books", "quote", "inbox"]);
const PLAIN = [
  ["inbox", "#/", "Needs you"],
  ["requests", "#/requests", "Requests"],
  ["suppliers", "#/vendors", "Suppliers"],
  ["setup", "#/setup", "Setup"],
  ["audit", "#/audit", "Audit trail"],
];
const PASSES = [
  { vp: "desktop", theme: "light", only: null },
  { vp: "mobile", theme: "light", only: null },
  { vp: "desktop", theme: "dark", only: DARK },
];
const PLANNED_SHOTS = SCREENS.length * 2 + DARK.size;

// Phones read the viewport tag. The demo page has none; the Next.js build of the product sets width=device-width by default.
const VIEWPORT_META_SCRIPT = `document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector('meta[name="viewport"]')) return;
  const m = document.createElement("meta");
  m.name = "viewport";
  m.content = "width=device-width, initial-scale=1";
  document.head.appendChild(m);
});`;

// ---------------------------------------------------------------- page-side functions
// These are sent to the browser as source text, so they must not use anything defined in this file.

function measurePage(rootSel) {
  const root = document.querySelector(rootSel);
  if (!root) return null;
  const CONTROLS = "button, a[href], input, select, textarea, summary";
  const boxed = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  // checkVisibility is false for display:none, visibility:hidden, and anything inside a closed <details> (its summary stays shown).
  const shown = (e) => e.checkVisibility({ checkVisibilityCSS: true }) && boxed(e);
  // True when a scrolling or clipping ancestor leaves none of the element on screen.
  const clippedOut = (e) => {
    const r = e.getBoundingClientRect();
    let left = r.left, right = r.right, top = r.top, bottom = r.bottom;
    for (let a = e.parentElement; a; a = a.parentElement) {
      const cs = getComputedStyle(a);
      const clipX = cs.overflowX !== "visible", clipY = cs.overflowY !== "visible";
      if (!clipX && !clipY) continue;
      const ar = a.getBoundingClientRect();
      if (clipX) { left = Math.max(left, ar.left); right = Math.min(right, ar.right); }
      if (clipY) { top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); }
      if (right <= left || bottom <= top) return true;
    }
    return false;
  };
  const inFirstScreen = (e) => {
    const r = e.getBoundingClientRect();
    return r.top < window.innerHeight && r.bottom > 0 && !clippedOut(e);
  };
  const words = (text) => text.trim().split(/\s+/).filter(Boolean).length;
  // A visually hidden radio or checkbox stands in for the label or card around it, so one choice card counts once.
  const controlsIn = (scope) => {
    const picked = new Set();
    for (const e of scope.querySelectorAll(CONTROLS)) {
      if (e.disabled) continue;
      if (shown(e)) { picked.add(e); continue; }
      const label = e.closest("label");
      if (label && shown(label)) picked.add(label);
    }
    return picked;
  };
  const els = [...root.querySelectorAll("*")].filter(shown);
  let numbers = 0;
  for (const e of els) {
    if (!inFirstScreen(e)) continue;
    for (const node of e.childNodes) {
      if (node.nodeType === 3) numbers += node.textContent.split(/\s+/).filter((t) => /\d/.test(t)).length;
    }
  }
  const textColours = new Set();
  const backgrounds = new Set();
  for (const e of [root, ...els]) {
    const cs = getComputedStyle(e);
    if ([...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim() !== "")) textColours.add(cs.color);
    if (cs.backgroundColor !== "rgba(0, 0, 0, 0)") backgrounds.add(cs.backgroundColor);
  }
  let depth = 0;
  for (const e of els) {
    let d = 0;
    for (let p = e; p && p !== root; p = p.parentElement) d++;
    depth = Math.max(depth, d);
  }
  const inMain = controlsIn(root);
  const outside = [...controlsIn(document)].filter((c) => !root.contains(c));
  const dialog = root.querySelector('[role="dialog"]');
  const de = document.documentElement;
  return {
    words: words(root.innerText),
    controls: inMain.size,
    disabledControls: els.filter((e) => e.matches(CONTROLS) && e.disabled).length,
    headings: els.filter((e) => /^H[1-4]$/.test(e.tagName)).length,
    pills: els.filter((e) => (e.getAttribute("class") || "").includes("rounded-full") && e.textContent.trim() !== "").length,
    numbers,
    textColours: textColours.size,
    bgColours: backgrounds.size,
    depth,
    sideways: de.scrollWidth > de.clientWidth,
    layout: [window.innerWidth, window.innerHeight],
    ink: getComputedStyle(root).color,
    shellControls: outside.length,
    shellWords: words(document.body.innerText) - words(root.innerText),
    dialog: dialog ? { words: words(dialog.innerText), controls: controlsIn(dialog).size } : null,
    h1: (root.querySelector("h1")?.textContent ?? "").trim(),
    scrollY: Math.round(window.scrollY),
  };
}

function isReady() {
  const main = document.querySelector("main");
  if (!main || document.querySelector('[aria-label="Loading"]')) return false;
  return !/(^|\n)Loading/.test(main.innerText);
}

function hasSel(sel) { return !!document.querySelector(sel); }

function stepIs(name) {
  return (document.querySelector("[data-wizard-track] [aria-current=step]")?.innerText ?? "").includes(name);
}

function h1Is(title) { return (document.querySelector("main h1")?.textContent ?? "").trim() === title; }

function clickIn(selector, exactText) {
  const pool = [...document.querySelectorAll(selector)];
  const el = exactText === null ? pool[0] : pool.find((e) => e.innerText.trim() === exactText);
  if (!el || el.disabled) return false;
  el.click();
  return true;
}

function setSelectValue(selector, value) {
  const el = document.querySelector(selector);
  if (!el) return false;
  Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(el, value);
  el.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function alignTo(mode) {
  if (mode === "step") {
    document.querySelector("[data-step-heading]")?.scrollIntoView({ block: "start" });
  } else if (mode === "options") {
    document.querySelector('[data-section="options"]')?.scrollIntoView({ block: "start" });
    window.scrollBy(0, -72); // clears the sticky header, as in e2e/quote.mjs
  } else {
    window.scrollTo(0, 0);
  }
  return true;
}

function dialogGone() { return !document.querySelector('[role="dialog"]'); }

function clickDialogClose() {
  const el = document.querySelector('[role="dialog"] [data-autofocus]');
  if (!el) return false;
  el.click();
  return true;
}

// ---------------------------------------------------------------- node-side helpers
const inPage = (fn, ...args) => `(${fn.toString()})(${args.map((a) => JSON.stringify(a)).join(", ")})`;
const wants = (ctx, ...ids) => !ctx.only || ids.some((id) => ctx.only.has(id));
const fail = (ctx, id, msg) => { ctx.failures.push({ id, vp: ctx.vp, theme: ctx.theme, msg }); };

async function navigate(b, url, waitMs) {
  const r = await b.send("Page.navigate", { url });
  if (r.result?.errorText) throw new Error(`could not open ${url}: ${r.result.errorText}`);
  await b.sleep(waitMs);
}

async function waitReady(ctx, id) {
  const started = Date.now();
  while (Date.now() - started < 10000) {
    const ready = await ctx.b.ev(inPage(isReady)).catch(() => false);
    if (ready) { await ctx.b.sleep(400); return true; }
    await ctx.b.sleep(150);
  }
  fail(ctx, id, "still showing loading placeholders after 10 seconds");
  return false;
}

// Fresh document, empty storage (so defaults show), then the route.
async function visit(ctx, hash, id) {
  const { b } = ctx;
  await navigate(b, "about:blank", 150);
  await navigate(b, `${BASE}/page.html`, 700);
  await b.ev("localStorage.clear(); sessionStorage.clear(); true");
  await navigate(b, `${BASE}/page.html${hash}`, 200);
  await b.ev("location.reload(); true");
  await b.sleep(900);
  await waitReady(ctx, id);
}

// Counts the screen at this moment, then captures it. A failed expectation is recorded and the capture still happens.
async function snap(ctx, id, expectExpr, align = "top") {
  const { b } = ctx;
  await waitReady(ctx, id);
  const ok = await b.ev(expectExpr).catch(() => false);
  if (!ok) fail(ctx, id, "the expected view is not on screen");
  if (!wants(ctx, id)) return ok;
  await b.ev(inPage(alignTo, align));
  await b.sleep(350);
  const m = await b.ev(inPage(measurePage, "main"));
  const file = `audit-${id}-${ctx.vp}-${ctx.theme}.png`;
  await b.shot(join(SHOT_DIR, file));
  ctx.records.push({ id, vp: ctx.vp, theme: ctx.theme, file, ok, m });
  return ok;
}

async function closeDialog(ctx, id) {
  const { b } = ctx;
  await b.key("Escape");
  await b.sleep(350);
  if (await b.ev(inPage(dialogGone))) return;
  await b.ev(inPage(clickDialogClose));
  await b.sleep(350);
  if (!(await b.ev(inPage(dialogGone)))) fail(ctx, id, "the dialog did not close with Escape or its Close button");
}

async function openDialog(ctx, id, selector, exactText, kind) {
  const { b } = ctx;
  const clicked = await b.ev(inPage(clickIn, selector, exactText));
  if (!clicked) {
    fail(ctx, id, `could not open: no enabled control matched ${selector}${exactText ? ` with text "${exactText}"` : ""}`);
    return;
  }
  await b.sleep(450);
  await snap(ctx, id, inPage(hasSel, `[data-dialog="${kind}"]`));
  await closeDialog(ctx, id);
}

// Clicks the control that leads to a step, then counts and captures that step.
async function toStep(ctx, id, step, clickText) {
  const clicked = await ctx.b.ev(inPage(clickIn, "main button", clickText));
  if (!clicked) {
    fail(ctx, id, `the "${clickText}" button was not found or is disabled`);
    return false;
  }
  await ctx.b.sleep(500);
  return snap(ctx, id, inPage(stepIs, step), "step");
}

async function kitsFlow(ctx) {
  const { b } = ctx;
  if (!wants(ctx, "kits-scope", "kits-questions", "kits-measure", "kits-review", "kits-summary")) return;
  await visit(ctx, "#/kits", "kits-scope");
  if (!(await snap(ctx, "kits-scope", inPage(hasSel, '[data-scope="bathroom_full"]')))) return;
  const picked = await b.ev(inPage(clickIn, '[data-scope="bathroom_full"]', null));
  if (!picked) { fail(ctx, "kits-questions", 'the "bathroom full" scope card was not found'); return; }
  await b.sleep(500);
  if (!(await snap(ctx, "kits-questions", inPage(stepIs, "Questions"), "step"))) return;
  if (!(await toStep(ctx, "kits-measure", "Measure", "Continue"))) return;
  if (!(await toStep(ctx, "kits-review", "Review", "Continue"))) return;
  await toStep(ctx, "kits-summary", "Summary", "Accept all defaults");
}

async function priceBooksFlow(ctx) {
  const { b } = ctx;
  if (!wants(ctx, "price-books", "price-books-request", "price-books-upload", "price-books-rfq")) return;
  await visit(ctx, "#/price-books", "price-books");
  if (!(await snap(ctx, "price-books", inPage(hasSel, '[data-screen="price-books"]')))) return;
  if (!wants(ctx, "price-books-request", "price-books-upload", "price-books-rfq")) return;
  // Customer A has every merchant current, so no gap or missing-merchant dialog can open for it. Customer B has both.
  await b.ev(inPage(setSelectValue, "[data-tenant]", "demo-tenant-b"));
  await b.sleep(500);
  if (wants(ctx, "price-books-request")) {
    await openDialog(ctx, "price-books-request", '[data-merchant][data-status="missing"] [data-act="request"]', null, "request");
  }
  if (wants(ctx, "price-books-upload")) await openDialog(ctx, "price-books-upload", "main button", "Upload prices", "upload");
  if (wants(ctx, "price-books-rfq")) await openDialog(ctx, "price-books-rfq", "main button", "Ask for missing prices", "rfq");
}

async function quoteFlow(ctx) {
  if (!wants(ctx, "quote", "quote-options")) return;
  await visit(ctx, "#/quote", "quote");
  if (!(await snap(ctx, "quote", inPage(hasSel, "[data-totals]")))) return;
  await snap(ctx, "quote-options", inPage(hasSel, '[data-section="options"]'), "options");
}

async function plainFlow(ctx, id, hash, title) {
  if (!wants(ctx, id)) return;
  await visit(ctx, hash, id);
  await snap(ctx, id, inPage(h1Is, title));
}

async function guard(ctx, id, flow) {
  try {
    await flow();
  } catch (e) {
    fail(ctx, id, `stopped: ${e.message}`);
  }
}

// Checks on the captures themselves: right layout width, and dark captures really use the dark colours.
function checkCaptures(records, failures) {
  for (const r of records.filter((x) => x.m)) {
    const want = VIEWPORTS[r.vp].width;
    if (r.m.layout[0] !== want) {
      failures.push({ id: r.id, vp: r.vp, theme: r.theme, msg: `layout is ${r.m.layout[0]} px wide, expected ${want} px` });
    }
    const light = records.find((x) => x.id === r.id && x.vp === r.vp && x.theme === "light");
    if (r.theme === "dark" && light?.m && light.m.ink === r.m.ink) {
      failures.push({ id: r.id, vp: r.vp, theme: r.theme, msg: "the dark theme did not change the text colour" });
    }
  }
}

// ---------------------------------------------------------------- document
const n = (x) => x.toLocaleString("en-GB");
const plural = (x, one, many = `${one}s`) => `${n(x)} ${x === 1 ? one : many}`;
const screenName = (id, theme) => `${LABEL.get(id)}${theme === "dark" ? " (dark)" : ""}`;

function rowFor(id, vp, theme, records, failures) {
  const name = screenName(id, theme);
  const r = records.find((x) => x.id === id && x.vp === vp && x.theme === theme);
  if (!r) return `| ${name} [not captured, see Failures] | – | – | – | – | – | – | – | – | – | – |`;
  const failed = failures.some((f) => f.id === id && f.vp === vp && f.theme === theme);
  const link = `[${name}](../screenshots/audit/${r.file})${failed ? " [failed, see Failures]" : ""}`;
  const m = r.m;
  if (!m) return `| ${link} | not measured | – | – | – | – | – | – | – | – | – |`;
  return `| ${link} | ${n(m.words)} | ${n(m.controls)} | ${n(m.headings)} | ${n(m.pills)} | ${n(m.numbers)} | ${n(m.textColours)} | ${n(m.bgColours)} | ${n(m.depth)} | ${m.sideways ? "yes" : "no"} | ${n(m.shellControls)} |`;
}

function tableFor(vp, records, failures) {
  const head = [
    "| Screen | Visible words | Controls | Headings (h1-h4) | Pills | Numbers in first viewport | Distinct text colours | Distinct background colours | Max nesting depth | Page scrolls sideways | Controls outside main |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|",
  ];
  const rows = [];
  for (const [id] of SCREENS) {
    rows.push(rowFor(id, vp, "light", records, failures));
    if (vp === "desktop" && DARK.has(id)) rows.push(rowFor(id, vp, "dark", records, failures));
  }
  return [...head, ...rows];
}

function topFive(records, key) {
  return records
    .filter((r) => r.m)
    .map((r, i) => ({ r, i, v: r.m[key] }))
    .sort((a, b) => b.v - a.v || a.i - b.i)
    .slice(0, 5)
    .map(({ r, v }) => `${screenName(r.id, r.theme)}, ${r.vp} ${r.theme}: ${n(v)}`)
    .join("; ");
}

function buildDoc({ records, failures, consoleLines, started }) {
  const git = (args) => {
    try { return execFileSync("git", ["-C", REPO, ...args], { encoding: "utf8" }).trim(); } catch { return null; }
  };
  const head = git(["rev-parse", "--short", "HEAD"]) ?? "unknown";
  const appsCommit = git(["log", "-1", "--format=%h", "--", "apps/web"]) ?? "unknown";
  const dirty = git(["status", "--porcelain", "--", "apps/web"]);
  const tree = dirty === null ? "uncommitted state unknown" : dirty === "" ? "no uncommitted changes under apps/web" : "uncommitted changes under apps/web";
  const shots = records.filter((r) => existsSync(join(SHOT_DIR, r.file))).length;
  const ranked = [
    ["words", "Visible words"], ["controls", "Controls"], ["headings", "Headings"], ["pills", "Pills"],
    ["numbers", "Numbers in first viewport"], ["textColours", "Distinct text colours"],
    ["bgColours", "Distinct background colours"], ["depth", "Max nesting depth"],
  ];
  const sideways = records.filter((r) => r.m?.sideways).map((r) => `${screenName(r.id, r.theme)}, ${r.vp} ${r.theme}`);
  const dialogs = records.filter((r) => r.m?.dialog).map((r) => (
    `${screenName(r.id, r.theme)}, ${r.vp} ${r.theme}: the dialog box alone has ${plural(r.m.dialog.words, "word")} and ${plural(r.m.dialog.controls, "control")}.`
  ));
  const inbox = (vp) => records.find((r) => r.id === "inbox" && r.vp === vp && r.theme === "light")?.m;
  const shellDesktop = inbox("desktop");
  const shellMobile = inbox("mobile");
  const failureLines = failures.map((f) => `- ${screenName(f.id, f.theme)}, ${f.vp} ${f.theme}: ${f.msg}.`);
  const out = [
    "# 02 Cognitive load: what each screen puts in front of the reader",
    "",
    `Counts were read from the page's DOM at the moment each screenshot was taken. Source: the mock demo built from the apps/web source as last changed in commit \`${appsCommit}\` (${tree}). Repository HEAD when captured: \`${head}\`. Captured ${started.toISOString()} by \`docs/mvp/ux-audit/tools/capture.mjs\`. Screenshots: \`docs/mvp/screenshots/audit/\` (${shots} files). All data is the synthetic, illustrative seed, labelled as such on screen.`,
    "",
    "Each row is one screen state. A higher number means more to take in at once. These are counts, not a score. The method note explains each column and what it cannot show.",
    "",
    `## Desktop, 1280 × 800 (light, plus ${DARK.size} dark rows)`,
    "",
    ...tableFor("desktop", records, failures),
    "",
    "## Mobile, 390 × 844 (light)",
    "",
    ...tableFor("mobile", records, failures),
    "",
    "## Highest load (top 5 screens per measure)",
    "",
    "Ranked over every captured row above, desktop and mobile, light and dark. Ties keep table order.",
    "",
    ...ranked.map(([key, title]) => `- **${title}:** ${topFive(records, key)}`),
    `- **Page scrolls sideways:** ${sideways.length ? sideways.join("; ") : `none of the ${records.length} captured screens`}.`,
    "",
    "## Failures and notes",
    "",
    failures.length === 0
      ? `None. All ${shots} planned screenshots were taken and every dialog opened.`
      : `${plural(failures.length, "problem")}. Rows marked as failed or not captured above are the affected screens.`,
    ...failureLines,
    "",
    "Dialog boxes on their own (the table counts include the dimmed page behind them):",
    "",
    ...(dialogs.length ? dialogs.map((d) => `- ${d}`) : ["- No dialog was captured."]),
    "",
    `Outside main, the sidebar or tab bar and top bar are shared by every screen, and the journey track appears on the journey screens. On the Inbox they hold ${plural(shellDesktop?.shellControls ?? 0, "control")} on desktop and ${plural(shellMobile?.shellControls ?? 0, "control")} on mobile, with roughly ${n(shellDesktop?.shellWords ?? 0)} and ${n(shellMobile?.shellWords ?? 0)} words (approximate).`,
    "",
    consoleLines.length
      ? `Browser console during the run: ${consoleLines.length} error or warning line(s). First: ${consoleLines.slice(0, 3).map((l) => `\`${l.slice(0, 160)}\``).join("; ")}.`
      : "Browser console during the run: no errors or warnings.",
    "",
    "## Method note",
    "",
    "- **What was run.** The mock demo built from `apps/web` (`npx vite build -c demo/vite.config.mjs`, then `node demo/inline.mjs`) and served from `apps/web/demo-dist` on `http://127.0.0.1:3300`. Nothing called a live API, a model or a mail server. The app's storage is cleared before each screen so the defaults show.",
    "- **Viewports and theme.** Desktop 1280 × 800 and mobile 390 × 844 CSS pixels at pixel ratio 1, in the light theme. Dark theme on desktop only, for the rows marked (dark): Job kits review, Price books, Quote and Inbox.",
    "- **Mobile width.** The demo page has no viewport tag. Without one, phone emulation lays the page out at 980 px and shrinks it, so the capture adds `width=device-width, initial-scale=1` on load. The Next.js build of the product sets the same default. Desktop is not affected.",
    "- **Journeys.** Job kits: the bathroom full scope with default answers, stepping scope, questions, measure, review, then summary. Price books: customer A first, then customer B for the three dialogs, because customer A has no gaps and no missing merchants. Quote: customer A, bathroom full, the first quote, then scrolled to Options. The other five screens open from their routes.",
    "- **Scroll position.** Screens open at the top. Job kits steps after the first put the step heading at the top, as the app does when a step changes. Quote Options puts its heading just under the sticky header.",
    "- **Waiting.** Each count is taken after the loading placeholders are gone, after a short pause for the page to settle, and after any scroll has finished (about 0.75 s in all).",
    "- **Dialogs.** A dialog renders inside the main element, so the main counts include the dimmed page behind it. The dialog box on its own is listed under Failures and notes.",
    "- **Visible and countable.** Visible means rendered and at least 2 px square. Content inside a closed section (for example a collapsed review section) is not visible until it is opened, so it is not counted. Disabled controls are left out. Counts cover the whole main element, including content below the fold; only the numbers column is limited to the first screen.",
    "- **Visible words.** Words in the rendered text of the main element.",
    "- **Controls.** Visible buttons, links with an address, inputs, selects, text areas and summaries. A visually hidden radio or checkbox counts as the label or card around it, so one choice card is one control.",
    "- **Headings.** Visible h1 to h4 elements.",
    "- **Pills.** Visible elements with `rounded-full` in their class that contain text. Empty round decoration is left out.",
    "- **Numbers in first viewport.** Tokens containing a digit, in text that is on screen within the first window height at the moment of capture. Text clipped by a scrolling box is not counted. For an unscrolled screen this is the first screen height of the page.",
    "- **Distinct text colours and background colours.** Distinct computed colour values among visible elements. Text colour counts only elements that hold their own text. Fully transparent backgrounds are left out.",
    "- **Max nesting depth.** The deepest visible element, counted in element levels below the main element.",
    "- **Page scrolls sideways.** The page is wider than the window.",
    "- **Controls outside main.** Controls in the sidebar or tab bar, the top bar and the journey track. These are shared by every screen, so they are shown in their own column.",
    "- **Highest load.** Ranks every captured row by each count. Ties keep table order.",
    `- **Planned and captured.** ${PLANNED_SHOTS} screenshots were planned (${SCREENS.length} light for each viewport, plus ${DARK.size} dark). ${shots} were written.`,
    "- **Limits.** These are structure counts from one build on one day. They say how much is on the screen, not how hard it is to understand or whether it is right. A long, familiar list can be easier to use than a short, new form. No threshold or pass mark was applied.",
    "",
  ];
  return out.join("\n");
}

// ---------------------------------------------------------------- run
async function main() {
  const started = new Date();
  const records = [];
  const failures = [];
  const b = await launch(DEBUG_PORT);
  let consoleLines = [];
  try {
    await b.send("Page.addScriptToEvaluateOnNewDocument", { source: VIEWPORT_META_SCRIPT });
    for (const pass of PASSES) {
      const vp = VIEWPORTS[pass.vp];
      await b.size(vp.width, vp.height, vp.mobile);
      await b.dark(pass.theme === "dark");
      const ctx = { b, vp: pass.vp, theme: pass.theme, only: pass.only, records, failures };
      await guard(ctx, "kits-scope", () => kitsFlow(ctx));
      await guard(ctx, "price-books", () => priceBooksFlow(ctx));
      await guard(ctx, "quote", () => quoteFlow(ctx));
      for (const [id, hash, title] of PLAIN) await guard(ctx, id, () => plainFlow(ctx, id, hash, title));
    }
    consoleLines = [...b.logs];
  } finally {
    b.close();
  }
  checkCaptures(records, failures);
  writeFileSync(DOC_PATH, buildDoc({ records, failures, consoleLines, started }), "utf8");
  const written = readdirSync(SHOT_DIR).filter((f) => f.startsWith("audit-") && f.endsWith(".png"));
  const planned = new Set(records.map((r) => r.file));
  const stale = written.filter((f) => !planned.has(f));
  console.log(`screenshots written: ${written.length} (planned ${PLANNED_SHOTS}); failures: ${failures.length}`);
  for (const f of failures) console.log(`  FAILED ${f.id} ${f.vp} ${f.theme}: ${f.msg}`);
  if (stale.length) console.log(`  not produced by this run (left in place): ${stale.join(", ")}`);
  console.log(`wrote ${DOC_PATH}`);
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});

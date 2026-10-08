#!/usr/bin/env node
/*
 * WCAG 2.2 contrast audit for the web app colour tokens.
 *
 * Reads the --token values from apps/web/app/globals.css. Light comes from
 * :root. Dark comes from :root[data-theme="dark"], which must equal the
 * @media (prefers-color-scheme: dark) block. For each pair in PAIRS it computes
 * the WCAG contrast ratio, prints a table per mode, and for each failing pair
 * prints the smallest single-token change that passes it.
 *
 * The suggested fix changes only OKLab lightness of one token: its hue and
 * chroma stay the same. The search takes the smallest lightness step, up or
 * down, at which every pair that uses the token passes. The new colour is
 * rounded to 8-bit sRGB and the ratio is checked on that rounded value. This
 * is a per-token search, not a global optimum over all colours.
 *
 * The CSS is read only and never written. No dependencies, no network.
 *
 *   node docs/mvp/ux-audit/tools/contrast.mjs              report (default)
 *   node docs/mvp/ux-audit/tools/contrast.mjs --self-test  formula checks only
 *   node docs/mvp/ux-audit/tools/contrast.mjs --css FILE   read another stylesheet
 *
 * Exit codes: 0 all required pairs pass; 1 a pair fails or the two dark
 * definitions differ; 2 usage, parse or self-test error.
 *
 * Not checked: disabled controls (opacity 50, exempt under WCAG), hover-only
 * backgrounds, and anything drawn over images. Only the pairs in PAIRS are checked.
 */

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CSS = resolve(HERE, '../../../../apps/web/app/globals.css');

// WCAG 1.4.3 normal text. Large text needs only 3:1, so 4.5:1 is applied to every text pair.
const TEXT_MIN = 4.5;
// WCAG 1.4.11 non-text contrast: UI component boundaries and focus indicators.
const UI_MIN = 3;

// [id, foreground token, background token, minimum ratio, where the UI uses it]
// Token names match the CSS custom properties without the leading "--".
const PAIRS = [
  ['T01', 'ink', 'bg', TEXT_MIN, 'body text on page'],
  ['T02', 'ink', 'surface', TEXT_MIN, 'card and field text'],
  ['T03', 'ink', 'sunken', TEXT_MIN, 'kbd, grey badge, hover rows'],
  ['T04', 'ink', 'accent-soft', TEXT_MIN, 'text on accent-soft'],
  ['T05', 'mute', 'bg', TEXT_MIN, 'hints and secondary text on page'],
  ['T06', 'mute', 'surface', TEXT_MIN, 'input placeholder, hints in cards'],
  ['T07', 'mute', 'sunken', TEXT_MIN, 'secondary text on sunken'],
  ['T08', 'mute', 'accent-soft', TEXT_MIN, 'secondary text on accent-soft'],
  ['T09', 'mute', 'warn-soft', TEXT_MIN, 'secondary text on warn-soft'],
  ['T10', 'mute', 'bad-soft', TEXT_MIN, 'ErrorNote help text'],
  ['T11', 'accent-ink', 'accent', TEXT_MIN, 'primary button label'],
  ['T12', 'accent', 'surface', TEXT_MIN, 'links and active nav on cards'],
  ['T13', 'accent', 'bg', TEXT_MIN, 'links on page'],
  ['T14', 'accent', 'accent-soft', TEXT_MIN, 'blue badge'],
  ['T15', 'accent', 'sunken', TEXT_MIN, 'text button on hover'],
  ['T16', 'ok', 'ok-soft', TEXT_MIN, 'green badge'],
  ['T17', 'ok', 'surface', TEXT_MIN, 'ok text on surface'],
  ['T18', 'warn', 'warn-soft', TEXT_MIN, 'amber badge, demo banner'],
  ['T19', 'bad', 'bad-soft', TEXT_MIN, 'red badge, alerts'],
  ['T20', 'surface', 'bad', TEXT_MIN, 'danger button label'],
  ['T21', 'ink', 'bad-soft', TEXT_MIN, 'alert message text'],
  ['N01', 'line', 'surface', UI_MIN, 'card border on card'],
  ['N02', 'line', 'bg', UI_MIN, 'card border on page'],
  ['N03', 'strong', 'surface', UI_MIN, 'input and secondary button border'],
  ['N04', 'strong', 'bg', UI_MIN, 'empty-state border on page'],
  ['F01', 'accent', 'surface', UI_MIN, 'focus outline on card'],
  ['F02', 'accent', 'bg', UI_MIN, 'focus outline on page'],
];

const LIGHTNESS_STEP = 0.0005; // OKLab L step for the fix search (L runs 0 to 1)
const EPS = 1e-9; // guards floating-point error at exactly 4.5:1 or 3:1
const BLACK = [0, 0, 0];
const WHITE = [255, 255, 255];
const USAGE = 'usage: node docs/mvp/ux-audit/tools/contrast.mjs [--css FILE] [--self-test]';

class InputError extends Error {}

// ---------- colour maths ----------

/** WCAG 2.x relative-luminance channel for one 8-bit value. The 0.03928 break point is the WCAG 2.x text. */
function wcagLinear(v8) {
  const c = v8 / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** L = 0.2126 R + 0.7152 G + 0.0722 B on linearised channels (WCAG 2.2 uses the WCAG 2.x definition). */
function relativeLuminance([r, g, b]) {
  return 0.2126 * wcagLinear(r) + 0.7152 * wcagLinear(g) + 0.0722 * wcagLinear(b);
}

/** (L1 + 0.05) / (L2 + 0.05) with L1 the lighter colour. Range 1 to 21. */
function contrastRatio(a, b) {
  const la = relativeLuminance(a);
  const lb = relativeLuminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

/** Two-decimal ratio, truncated so the printed value never overstates the result. */
function fmtRatio(ratio) {
  return (Math.floor(ratio * 100 + EPS) / 100).toFixed(2);
}

/** Standard sRGB transfer function (used only for OKLab conversions). */
function srgbToLinear(c) {
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function linearToSrgb(c) {
  return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055;
}

/** OKLab (Ottosson, 2020): L is perceptual lightness; a and b carry hue and chroma. */
function rgbToOklab(rgb) {
  const [r, g, b] = rgb.map((v) => srgbToLinear(v / 255));
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

/** OKLab back to 8-bit sRGB. Returns null when the colour is outside the sRGB gamut. */
function oklabToRgb8([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const linear = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
  if (linear.some((v) => v < -1e-6 || v > 1 + 1e-6)) return null;
  return linear.map((v) => Math.round(255 * linearToSrgb(Math.min(1, Math.max(0, v)))));
}

function parseHex(text) {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(text.trim());
  if (!m) throw new InputError(`not a #rgb or #rrggbb colour: "${text}"`);
  const digits = m[1].length === 3 ? [...m[1]].map((c) => c + c).join('') : m[1];
  return [0, 2, 4].map((i) => parseInt(digits.slice(i, i + 2), 16));
}

function toHex(rgb) {
  return `#${rgb.map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

// ---------- CSS reading: only the custom-property blocks are needed ----------

function stripComments(css) {
  return css.replace(/\/\*[\s\S]*?\*\//g, '');
}

function normalise(text) {
  return text.replace(/\s+/g, ' ').trim();
}

/**
 * Returns every block in the stylesheet with its selector, its enclosing
 * at-rules (ancestors), its opening index, and its "--name: value" declarations.
 */
function readBlocks(css) {
  const done = [];
  const open = [];
  let pending = '';
  let counter = 0;
  const addDecl = (block, text) => {
    const t = normalise(text);
    if (block && t.startsWith('--') && t.includes(':')) {
      const i = t.indexOf(':');
      block.decls.push([t.slice(0, i).trim(), t.slice(i + 1).trim()]);
    }
  };
  for (const ch of stripComments(css)) {
    if (ch === '{') {
      open.push({
        selector: normalise(pending),
        ancestors: open.map((b) => b.selector),
        index: counter,
        decls: [],
      });
      counter += 1;
      pending = '';
    } else if (ch === '}') {
      const top = open.pop();
      if (!top) throw new InputError('unbalanced "}" in the stylesheet');
      addDecl(top, pending);
      pending = '';
      done.push(top);
    } else if (ch === ';') {
      addDecl(open[open.length - 1], pending);
      pending = '';
    } else {
      pending += ch;
    }
  }
  if (open.length) throw new InputError('unclosed "{" in the stylesheet');
  return done;
}

function tokensWhere(blocks, test) {
  const tokens = new Map();
  const matching = blocks.filter(test).sort((a, b) => a.index - b.index);
  for (const block of matching) {
    for (const [name, value] of block.decls) tokens.set(name, value);
  }
  return tokens;
}

function isDarkMedia(atRule) {
  return atRule.replace(/\s+/g, '') === '@media(prefers-color-scheme:dark)';
}

/** Light, dark (data-theme block) and dark (prefers-color-scheme block) token maps. */
function loadTokenSets(css) {
  const blocks = readBlocks(css);
  const light = tokensWhere(blocks, (b) => b.selector === ':root' && b.ancestors.length === 0);
  const dark = tokensWhere(blocks, (b) => b.selector === ':root[data-theme="dark"]' && b.ancestors.length === 0);
  const darkOs = tokensWhere(
    blocks,
    (b) => b.selector === ':root:not([data-theme="light"])' && b.ancestors.some(isDarkMedia),
  );
  if (light.size === 0) throw new InputError('no :root token block found');
  if (dark.size === 0) throw new InputError('no :root[data-theme="dark"] token block found');
  if (darkOs.size === 0) throw new InputError('no prefers-color-scheme: dark token block found');
  return { light, dark, darkOs };
}

function differingTokens(a, b) {
  const names = new Set([...a.keys(), ...b.keys()]);
  return [...names].filter((n) => a.get(n) !== b.get(n)).sort();
}

function colourOf(tokens, name) {
  const raw = tokens.get(`--${name}`);
  if (raw === undefined) throw new InputError(`token --${name} is not defined`);
  return parseHex(raw);
}

// ---------- evaluation and smallest-fix search ----------

function evaluate(tokens) {
  return PAIRS.map(([id, fg, bg, need, use]) => {
    const fgRgb = colourOf(tokens, fg);
    const bgRgb = colourOf(tokens, bg);
    const ratio = contrastRatio(fgRgb, bgRgb);
    return {
      id, fg, bg, need, use, ratio,
      pass: ratio >= need - EPS,
      fgRgb, bgRgb, fgHex: toHex(fgRgb), bgHex: toHex(bgRgb),
    };
  });
}

/** Ratio of one pair if token `name` were replaced by `candidate` (8-bit sRGB). */
function ratioWithCandidate(pair, name, candidate, tokens) {
  const fg = pair.fg === name ? candidate : colourOf(tokens, pair.fg);
  const bg = pair.bg === name ? candidate : colourOf(tokens, pair.bg);
  return contrastRatio(fg, bg);
}

/**
 * Smallest OKLab lightness change to token `name` (hue and chroma kept) that
 * makes every pair using it pass. Returns null if no lightness works in gamut.
 */
function smallestLightnessMove(name, tokens, results) {
  const original = colourOf(tokens, name);
  const [L0, a, b] = rgbToOklab(original);
  const using = results.filter((r) => r.fg === name || r.bg === name);
  const passes = (rgb) => using.every((r) => ratioWithCandidate(r, name, rgb, tokens) >= r.need - EPS);
  let best = null;
  for (const dir of [-1, 1]) {
    for (let k = 1; ; k += 1) {
      const L = L0 + dir * k * LIGHTNESS_STEP;
      if (L < 0 || L > 1) break;
      const rgb = oklabToRgb8([L, a, b]);
      if (rgb === null) break;
      if (passes(rgb)) {
        const dL = Math.abs(L - L0);
        if (best === null || dL < best.dL) {
          best = { token: name, from: toHex(original), to: toHex(rgb), L0, L1: L, dL, rgb, using: using.length };
        }
        break;
      }
    }
  }
  return best;
}

// ---------- output ----------

function printMode(title, results) {
  console.log(`\n${title}`);
  console.log(
    `${'ID'.padEnd(4)} ${'Use'.padEnd(36)} ${'Foreground'.padEnd(22)} ${'Background'.padEnd(22)} ${'Ratio'.padStart(6)}  ${'Rule'.padEnd(13)} Result`,
  );
  for (const r of results) {
    const rule = r.need === TEXT_MIN ? 'text 4.5:1' : 'non-text 3:1';
    const fgCell = `--${r.fg} ${r.fgHex}`;
    const bgCell = `--${r.bg} ${r.bgHex}`;
    console.log(
      `${r.id.padEnd(4)} ${r.use.padEnd(36)} ${fgCell.padEnd(22)} ${bgCell.padEnd(22)} ${fmtRatio(r.ratio).padStart(6)}:1  ${rule.padEnd(13)} ${r.pass ? 'PASS' : 'FAIL'}`,
    );
  }
  const failing = results.filter((r) => !r.pass).length;
  console.log(`${title.split(' ')[0].toLowerCase()}: ${results.length} pairs checked, ${failing} failing.`);
}

function describeMove(move) {
  return `set --${move.token} ${move.from} -> ${move.to} (OKLab lightness ${move.L0.toFixed(3)} -> ${move.L1.toFixed(3)})`;
}

function printFixes(tokens, results) {
  const failing = results.filter((r) => !r.pass);
  if (failing.length === 0) {
    console.log('No failing pairs, so no fixes are needed.');
    return;
  }
  console.log('Smallest single-token fix for each failing pair (lightness only, hue and chroma kept):');
  for (const r of failing) {
    const moves = [r.fg, r.bg]
      .map((t) => smallestLightnessMove(t, tokens, results))
      .filter((m) => m !== null)
      .sort((x, y) => x.dL - y.dL);
    if (moves.length === 0) {
      console.log(`  ${r.id}: no lightness change of either token passes it in gamut.`);
      continue;
    }
    const [best, alt] = moves;
    const after = ratioWithCandidate(r, best.token, best.rgb, tokens);
    const usingBest = results.filter((x) => x.fg === best.token || x.bg === best.token);
    const allPass = usingBest.every((x) => ratioWithCandidate(x, best.token, best.rgb, tokens) >= x.need - EPS);
    console.log(
      `  ${r.id} (${r.fg} on ${r.bg}, ${fmtRatio(r.ratio)}:1, needs ${r.need}): ${describeMove(best)}.` +
        ` ${r.id} becomes ${fmtRatio(after)}:1. All ${usingBest.length} pairs using --${best.token} ${allPass ? 'pass' : 'DO NOT ALL PASS'}.`,
    );
    if (alt) console.log(`      alternative: ${describeMove(alt)}.`);
  }
}

// ---------- self-test: WCAG reference values and OKLab conversions ----------

function selfTest() {
  const ratioChecks = [
    ['white on black', contrastRatio([255, 255, 255], BLACK), 21],
    ['#767676 on white', contrastRatio([0x76, 0x76, 0x76], WHITE), 4.54],
    ['#777777 on white', contrastRatio([0x77, 0x77, 0x77], WHITE), 4.48],
    ['#808080 on white', contrastRatio([0x80, 0x80, 0x80], WHITE), 3.95],
  ];
  for (const [name, got, want] of ratioChecks) {
    if (Math.abs(got - want) > 0.005) {
      throw new Error(`self-test failed: ${name} gave ${got.toFixed(4)}, expected ${want}`);
    }
  }
  const weights = [
    [[255, 0, 0], 0.2126],
    [[0, 255, 0], 0.7152],
    [[0, 0, 255], 0.0722],
  ];
  for (const [rgb, want] of weights) {
    if (Math.abs(relativeLuminance(rgb) - want) > 1e-4) {
      throw new Error(`self-test failed: luminance of ${toHex(rgb)} is not ${want}`);
    }
  }
  const [redL, redA, redB] = rgbToOklab([255, 0, 0]);
  const known = [Math.abs(redL - 0.62796), Math.abs(redA - 0.22486), Math.abs(redB - 0.12585)];
  if (known.some((d) => d > 5e-4)) throw new Error('self-test failed: OKLab of #ff0000 is off');
  for (const rgb of [[0, 0, 0], [255, 255, 255], [11, 95, 103], [92, 196, 204], [170, 182, 185], [15, 21, 22]]) {
    const back = oklabToRgb8(rgbToOklab(rgb));
    if (back === null || back.some((v, i) => v !== rgb[i])) {
      throw new Error(`self-test failed: OKLab round trip changed ${toHex(rgb)}`);
    }
  }
}

function parseArgs(argv) {
  const opts = { css: DEFAULT_CSS, selfTest: false, help: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--css') {
      if (!argv[i + 1]) throw new InputError('--css needs a file path');
      opts.css = resolve(argv[i + 1]);
      i += 1;
    } else if (arg === '--self-test') {
      opts.selfTest = true;
    } else if (arg === '--help' || arg === '-h') {
      opts.help = true;
    } else {
      throw new InputError(`unknown argument "${arg}". ${USAGE}`);
    }
  }
  return opts;
}

function main(argv) {
  const opts = parseArgs(argv);
  if (opts.help) {
    console.log(USAGE);
    return 0;
  }
  selfTest();
  if (opts.selfTest) {
    console.log('self-test passed: WCAG reference ratios, luminance weights, OKLab known values and round trip.');
    return 0;
  }
  const sets = loadTokenSets(readFileSync(opts.css, 'utf8'));
  const mismatched = differingTokens(sets.darkOs, sets.dark);

  console.log(`Source: ${opts.css}`);
  console.log(`Formula: WCAG 2.x relative luminance, ratio = (L1 + 0.05) / (L2 + 0.05). Text ${TEXT_MIN}:1, non-text ${UI_MIN}:1.`);
  console.log(
    mismatched.length === 0
      ? 'Dark definitions: the data-theme block and the prefers-color-scheme block are identical.'
      : `Dark definitions DISAGREE on: ${mismatched.map((n) => `--${n}`).join(', ')}`,
  );

  let failures = mismatched.length > 0 ? 1 : 0;
  for (const [title, tokens] of [
    ['LIGHT (:root)', sets.light],
    ['DARK (:root[data-theme="dark"])', sets.dark],
  ]) {
    const results = evaluate(tokens);
    failures += results.filter((r) => !r.pass).length;
    printMode(title, results);
    printFixes(tokens, results);
  }

  console.log(failures === 0 ? '\nRESULT: all required pairs pass.' : `\nRESULT: FAIL (${failures} problem(s)).`);
  return failures === 0 ? 0 : 1;
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (err) {
  console.error(`contrast.mjs: ${err.message}`);
  process.exitCode = 2;
}

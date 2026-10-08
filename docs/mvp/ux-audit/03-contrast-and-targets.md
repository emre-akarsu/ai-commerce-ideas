# 03 Contrast, target sizes and other accessibility facts (2026-10-07)

Inputs for the UX/UI redesign. This is an audit of what `apps/web` does today, not a design. Nothing under `apps/web` was changed.

## Method and limits

- **Contrast** comes from `docs/mvp/ux-audit/tools/contrast.mjs` (no dependencies; run `node docs/mvp/ux-audit/tools/contrast.mjs`). It reads the colour tokens in `apps/web/app/globals.css` and computes the WCAG 2.x ratio, (L1 + 0.05) / (L2 + 0.05), for the foreground and background pairs the app uses. Text needs 4.5:1; non-text parts of the interface need 3:1. The tool lists 27 pairs per mode (21 text, 4 border, 2 focus ring). The lead re-ran it and the figures below match.
- **Target sizes** come from a static scan of the JSX and Tailwind classes in `apps/web` (a subagent's script, not committed; its per-element output has 164 lines). Heights are estimated from classes (`min-h-target` is 2.5rem, 40 px), not measured in a browser. The lead has not re-run the scan. Treat the counts as a map of where to look, and measure the rendered page (bounding boxes) in the redesign's end-to-end checks.
- **Not checked:** disabled and hover states, text over images, and any state that needs data the mock demo does not show. The generated `demo-dist/app.js` is not counted.
- Colour contrast is one part of accessibility. This audit says nothing about screen-reader behaviour, keyboard order or zoom; the redesign adds an automated axe pass for those.

## Text contrast: passes in both modes

All 21 text pairs pass in light and in dark. The lowest ratios are 5.5:1 (green badge on its soft background, light) and 5.7:1 (secondary text on the accent-soft background, dark). Focus rings pass: the accent colour is 7.37:1 on a card and 6.74:1 on the page in light, 8.08:1 and 8.97:1 in dark.

## Non-text contrast: borders fail in both modes

| Token | Used for | Light on surface / page | Dark on surface / page |
|---|---|---|---|
| `--line` | Card and panel edges | 1.38:1 / 1.26:1 | 1.36:1 / 1.51:1 |
| `--strong` | Input borders, secondary-button borders, empty-state edges | 2.07:1 / 1.90:1 | 2.38:1 / 2.65:1 |

WCAG asks for 3:1 where the border is what tells a person that a control exists (input fields, secondary buttons). A decorative card edge is a judgement call, because the card also differs from the page by fill and by its text. The tool applies 3:1 to all four pairs, so all four are listed as failing.

The smallest single-token fixes the tool found keep hue and chroma and change OKLab lightness only:

| Mode | Token | Now | Fix | Result |
|---|---|---|---|---|
| Light | `--strong` | `#aab6b9` | `#849093` | 3.28:1 on surface, 3.00:1 on page |
| Light | `--line` | `#d5dcde` | `#888f91` | 3.28:1 on surface, 3.00:1 on page |
| Dark | `--strong` | `#4a5d5f` | `#596c6f` | 3.00:1 on surface, 3.33:1 on page |
| Dark | `--line` | `#2b3839` | `#5d6c6d` | 3.02:1 on surface, 3.36:1 on page |

Each fix was checked against every pair that uses that token. A card edge at 3:1 is a heavy line; the redesign may instead separate cards by fill and spacing and keep a 3:1 border only on controls.

## Target size

WCAG 2.2 level AA asks for at least 24 × 24 CSS px per target (with exceptions for inline links, native controls and targets with enough spacing). Level AAA asks for 44 × 44. The app's own token is 40 px. Mobile approval is a stated requirement (spec section 7: approval in three taps or fewer on a phone).

Static scan of 162 visible interactive tags (6 more are screen-reader-only):

| Size | Count | Notes |
|---|---:|---|
| 44 px or taller | 7 | |
| 24 to 43 px | 138 | 135 are the 40 px token; `requests/page.tsx:28` is 36 px; `toast.tsx:27` is 24 px; one textarea is sized by rows |
| Under 24 px | 12 | See below |
| Inline text links | 5 | Exempt at AA |

The 12 under 24 px, all inside labels at least 40 px tall (the label is the click target):

- Declared: radios at `h-4` (16 px) in `components/kits/widgets.tsx:34,57` and `components/kits/lines.tsx:55`; checkboxes at `h-5` (20 px) in `app/page.tsx:62,63` and `components/workspace/step-suppliers.tsx:56,73`.
- Unstyled native radios and checkboxes (about 13 px) in `components/quote/price-books-app.tsx:268,271` and `components/quote/price-file-upload.tsx:88,91,113`.

## Other facts

- **Reduced motion is honoured:** `globals.css:35` sets `animation: none` and `transition: none` under `prefers-reduced-motion: reduce`.
- **Page language is set:** `app/layout.tsx:13` has `<html lang="en-GB">`.
- **Focus is visible:** a global `:focus-visible` outline in the accent colour (`globals.css:33`), plus ring styles on custom controls. Radios hide their own ring and rely on the label's ring.
- **Small text:** four uses under 12 px: `text-[10px]` at `components/kits/lines.tsx:183` and `components/shell.tsx:126`; `text-[11px]` at `components/kits/kits-app.tsx:143` and `components/journey.tsx:59`.

## What this means for the redesign

1. Every text pair in the new palette must pass 4.5:1 and every control boundary and focus ring 3:1, in light and in dark, checked with `contrast.mjs` (extended with the new tokens) and, for chart colours, `validate_palette.js` from the dataviz skill. Do not ship a token pair that the tool fails.
2. Set the target token to 44 px for anything a person taps on a phone, and 48 px for the primary action of a screen. Give radios and checkboxes a visible control of at least 24 px inside a 44 px row.
3. Remove text below 12 px. Where a 10 or 11 px label exists, the label is probably carrying detail that belongs behind a disclosure.
4. Keep the reduced-motion rule, the language attribute and the global focus outline.
5. Replace the static scan with a rendered check in the end-to-end suite (bounding boxes of interactive elements) so target size cannot regress silently.

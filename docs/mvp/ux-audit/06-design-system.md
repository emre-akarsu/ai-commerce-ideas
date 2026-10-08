# 06 Design system (2026-10-08)

Implements `04-redesign-brief.md` sections 5 and 6. Tokens live in `apps/web/app/globals.css`, names in `apps/web/lib/labels.ts`, primitives in `apps/web/components/ui/`, charts in `apps/web/components/charts/`, chart logic in `apps/web/lib/quote/viz.ts`.

## Validation results (run, not estimated)

- `node docs/mvp/ux-audit/tools/contrast.mjs`: 36 pairs in light and 36 in dark, 0 failing. Text 4.5:1; control edges, marks and focus rings 3:1.
- `validate_palette.js` (dataviz skill), categorical slots 1 to 6, light, surface `#fcfcfb`: lightness band, chroma floor, adjacent-pair CVD separation (worst ΔE 9.1, protan) and the normal-vision floor (worst 19.6) pass. **Contrast against the surface is a WARN** for slots 3, 4 and 5 (2.74, 2.11, 2.62 against the 3:1 target). The skill makes that a duty to give relief: every chart here has a visible legend with the name, amount and share beside each swatch, and a Table view with the same numbers, and no text sits on a series colour.
- The sequential ramp (`--seq-100` to `--seq-700`) is one blue hue, light to dark in light mode and reversed in dark mode.

## Rules the components follow

- One status language: Confirmed price, Rough price, Needs your choice, No price yet, Skipped, each with icon, colour and word (`StateChip`).
- Supplier colour is the supplier's slot (sorted position, 1 to 6, then grey "Other suppliers"), the same on every screen and unaffected by spend (`supplierSlots`).
- Every chart is inside `ChartFrame`: a Chart / Table switch, the same numbers in both.
- Money stays a decimal string; only bar lengths use floats.
- Targets are 44 px (`min-h-target`), 48 px for the main action; no text under 12 px.
- Names come from `labels.ts`; a hard term gets a one-sentence tip behind an info button (`Term`, `InfoTip`).

## Not yet checked

Rendered target sizes at 390 px, axe on the redesigned screens, and screenshot review are done in work package R9.

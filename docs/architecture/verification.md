# Verification layer

Spec: `docs/product/04-product-spec.md` v0.3 DRAFT, F28 and section 8 item 9. Triage: `docs/product/12-next-version-improvement-triage.md`, item 9.

The verification layer looks at a quote after it has been read and normalised, and adds **findings**. A finding can raise a flag or send the quote to a person. It cannot approve a quote, choose between two readings, fill a blank, or change an amount, recipient or rule (R1, R3, R6, R9). Passing every check does not approve anything.

## What runs

For each vendor reply, `PurchasingService._build_quote` does, in order:

1. The extractor reads the text (the model when one is configured, the deterministic regex reader otherwise).
2. The **grounding check** blanks any value that does not appear verbatim in the text and flags it (`ungrounded:<field>`, R6).
3. **Normalisation** turns the raw strings into money with a currency, a unit and a VAT basis, and adds its own flags (for example `tax_basis_unknown`, `validity_expired`, `currency_ambiguous`).
4. **Verification** (`components/rfq/quotes/verify_quote.py`) runs three kinds of check and returns findings:
   - **Second reading** (`components/verify/shadow.py`). When a model is the primary reader, the deterministic reader reads the same text. For each of the twelve extracted fields where both readings have a value and they differ, or only one has a value, it adds `readings_disagree` or `reading_missing`. Values are compared by meaning: amounts as numbers, "£" and "GBP" as the same currency, lead times and validity as days, units by their divisor. It never picks a reading.
   - **Number checks** (`components/verify/checks.py`): negative or absurd values on the unit price today. Line total against quantity times price, pack size times packs, VAT arithmetic, and currency or unit consistency across lines are written and tested, but the quote extraction schema has no line total or pack count to feed them, so they wait for price-file rows and multi-line quotes.
   - **Plausibility against the customer's own history** (`components/verify/plausibility.py`): `price_jump_vs_last_paid`, `unit_basis_shift` (a price near 10, 12, 100 or 1000 times the usual) and `quantity_unusual`. Needs at least `min_history_points` earlier prices of the same part in the same currency.
5. The findings become quote flags: `verification_review` for a finding of severity review (it forces an approval by a person other than the requester, like the other forcing flags) and `verification_flag` for one that asks for a look (shown on the approval page). A `quote.verified` event records the finding codes with their templated text. Findings carry plain values only; anything that is not plain text is replaced by "[not shown]".

Thresholds come from the resolved deployment profile (`verification:` block, `VerificationPolicy` in `aiplat/profile.py`): `arith_abs_tolerance`, `arith_rel_tolerance`, `vat_rel_tolerance`, `price_jump_ratio`, `unit_basis_tolerance`, `quantity_ratio`, `min_history_points`. The component's own defaults exist only so it can be tested alone.

## Price history

Plausibility reads the tenant's price history through `PriceHistory` (`components/verify/history.py`). The service takes a function from tenant id to a history bound to that tenant, so one tenant's prices are never read for another (hard rule 7).

- **Write.** When a quote becomes a PO draft (`create_po_draft`), its price is stored as one point (`source = accepted_quote`, unit "each", ex VAT, filed under the normalised part number). It is best effort: a failure is a `price_history.record_failed` audit event, never a failed draft.
- **Store.** In memory in dev; in Postgres the table `price_observations` (migration 0007) under row level security. The app role can read and insert only, so a later price-file load cannot erase an earlier point (F28 clause 5).
- **Not written yet.** The PO history CSV import (F11) validates rows and counts them; it does not store prices. Price-file loads do not write history either. Backfill from files is F33.

## Seeded-error evaluation

`python -m evals.verification.run` (and `make eval`, with `--check`) runs a generated set through the real service: 210 vendor replies with one injected error each (decimal slips, wrong pack, ex or inc VAT swaps, unit swaps, wrong currency, transposed quantities, expired validity; 30 each, 3 to 4 mechanisms per type) and 300 clean replies, over 30 vendors under the UK profile. The set is deterministic and frozen: `baseline.json` holds its SHA-256 and a test fails if the generator changes it without the baseline being rewritten on purpose.

An error is **flagged** when the quote carries an alarm (a flag that forces a second person, refuses the quote, marks a value as not found in the text, or comes from this layer), **neutralised** when there is no flag but the final quote still holds the right values (grounding dropped the bad value and the right one remained), and an **escape** when there is no flag and a value is wrong. A blank value is not a wrong value. The model is a stand-in: each case says what the second reader returned.

Result on the first run (2026-10-08, synthetic):

| | |
|---|---|
| Injected errors | 210; 15 escaped (decimal slips 10, wrong pack 5) |
| Escapes if this layer did not exist | 70, so the layer removed 55 |
| Clean replies flagged | 0 of 300 (Wilson 95% interval 0 to 1.3%) |
| Spec gate (zero escapes in at least 189, false-alarm ceiling 10%, proposed) | **FAIL** on this set |

All 15 escapes are the same mechanism: the **vendor's own typo, with no history to compare with** (a price ten times too high, or a per-100 price where a per-piece price was meant). Every error that came from a misreading was caught or neutralised. This says what the current checks do, not how real vendors write: the set is generated text, the base quotes are synthetic, and a gate on real quotes needs design-partner data (spec F28 clause 6).

`--check` fails only if something gets worse (more escapes in a type, more clean replies flagged, or a changed set), so the gap stays visible without blocking the build. `--list-escapes` prints the escaped case ids.

## Known gaps

- A vendor's own typo escapes when the customer has no history for the part. History comes from accepted quotes only so far; PO import and file backfill would add points (F33).
- The number checks that need a line total, pack count or several lines have no input from quote extraction yet.
- The second reading runs only when a model is the primary reader. With the regex reader alone, grounding, normalisation and plausibility still run.
- The set is synthetic. The release gate in spec section 8 needs real quotes: at least 300 from at least 30 vendors, at least 189 held-out injected errors, scored on a sealed set.
- A disagreement carries the primary reading, flagged, rather than leaving the field unresolved (open decision O16 in the spec).

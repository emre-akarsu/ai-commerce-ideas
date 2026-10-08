# Offer and best-price engine (stage 2)

As of 2026-10-07. Status: built as a generic core with offline adapters; **no real provider adapter, no persistence, no API wiring**. All fixture data is synthetic/illustrative. Product-market fit is unproven; nothing here is a market claim. Code: `packages/components/pricing/`; tests: `tests/pricing/`; fixtures: `profiles/data/pricing/fixtures/`. Position in the pipeline: `docs/product/07-product-matching-engine-spec-v2.md` maps order lines to approved SKUs (stage 1, where pricing was a non-goal); this component prices them.

Numbering. Rules are cited as in CLAUDE.md (rules 1-7), with the spec §4 number in brackets where they differ (CLAUDE.md compresses R1-R12; MASTER §8.3 C1).

## 1. What it does

Given resolved lines (an approved match group of SKUs, a quantity and a unit) and the offers a tenant may see, it computes for each line the whole packs needed, goods, delivery and landed cost, picks the best offer with a reason trail, optimises the basket across merchants with delivery thresholds, and assembles a `QuoteDraft`. Nothing is sent or ordered (rule 1 [R1]); a draft is data for a person.

```
ResolvedLine ──► price_line ──► PricedLine ──┐
 (SKU group,       (assess every offer,       ├─► optimise_basket ─► BasketResult ─► QuoteDraft
  qty, unit)        gates, rank)             ─┘   (exact DP / fallback)
OfferRepository (tenant-bound) ─► offers          unmatched / ambiguous lines listed apart
```

## 2. Model (`models.py`, `units.py`, `lines.py`)

- `Price(amount, currency, per, uom, vat_basis, vat_rate)`: money for 1/100/1000 (`UoM`, reused from `core.domain`) of a pack or of one piece/m2/m/kg/litre. `vat_rate` is only what the source claims (untrusted).
- `PackSize(quantity, unit | None)`: what one purchasable pack holds: sale units of the catalogue SKU ("pack of 10") or measured content the merchant stated ("1.44 m2").
- `UnitBasis`: supplied by the caller from catalogue attributes: content of ONE sale unit per measured unit (sheet area from dimensions, kg per bag, m per coil, litres per tub, count per box); `each` is 1 unless the catalogue says otherwise. A combination it cannot convert is `unit_not_convertible`, never a guess.
- `DeliveryTerms`: flat fee, optional "free strictly over" threshold, or spend tiers (inclusive from their minimum), on a stated VAT basis (default: the offer's).
- `Offer`: ids, `source_kind` (`trade_feed | merchant_api | affiliate_feed | search_snapshot | manual_quote`, equal to `aiplat.profile.MATCHING_SOURCE_KINDS`; it describes the data, not a connection), `price`, `pack`, `min_order_qty` and `order_multiple` (in packs), `stock_status`, `lead_time_days`, `delivery`, `observed_at`, `valid_until`, `visibility` + `tenant_id`, `provenance`, `licence` tag, `confidence` (Decimal 0..1), `flags`, `price_type` (`retail | trade_list | account_specific | quoted`), `account_specific`, `tenant_attested`, `availability` (optional tuple of `Tranche(packs, in_days)`, strictly increasing days, at most 10: how many packs the supplier says it can supply within that many days, added up; an empty tuple means unknown) and `source_ref` (inert display text).
- Strict validation (`OfferValidationError`): Decimal only (floats, ints for money, NaN, infinities, negatives and zero prices rejected; at most 6 places), ids are validated tokens and never repaired, free text has control/bidi/zero-width characters removed and every link replaced by `[link removed]`, datetimes are timezone-aware (UTC), enums must be real members, flags are sorted unique tokens. The deployment-dependent check (currency in the accepted set) is `PricingConfig.check_offer`, called by repositories and the parser.

## 3. Which offers may feed a quote line (`eligibility.py`)

Follows ADR-013 (draft) and the legal notes' risk ranking (research_notes legal_and_terms.md §7). One pure function, `quote_line_eligible(kind, price_type, account_specific, has_validity, tenant_attested)`, table-tested in `tests/pricing/test_eligibility.py`:

| Source | May feed a quote line when |
|---|---|
| manual quote, trade-account feed/EDI, user-supplied price file (`trade_feed`) | validity (`valid_until`) present, tenant attested, and not a retail list price |
| official merchant API/feed | only if it returns account-specific prices with validity and attestation (then it is a trade-account feed in practice) |
| affiliate feed, search snapshot | never |

Everything else is `Offer.is_indicative`: shown as a range with its observation time, never selected, never in a firm total, labelled "indicative, not a quote". Attested and account-specific offers must be tenant-private (model rule), so shared data is always indicative.

## 4. Algorithms

### 4.1 One line (`assess.py`, `best_price.py`)

Per offer of an SKU in the approved group (others are never looked at): gates, then exact arithmetic, then rank.

1. Gates, each a reason code: `substitution_not_approved` (a non-Tier-A SKU needs a recorded approval id; rule 2 [R2]), `currency_not_comparable` (no FX is applied), `vat_basis_unknown` / `vat_rate_mismatch`, `unit_not_convertible`, `expired` (`valid_until` passed; always excludes), `observed_in_future`, `stale` (per source kind, config), `out_of_stock`, `availability_insufficient` and `availability_too_late` (a line may carry `need_by_days`; `feasibility.assess_feasibility` checks the packs that would actually be bought, after the minimum order and multiple, against the offer's tranches: too few packs in total excludes whatever the day, enough packs only after the day excludes when a day was given), relative sanity (4.2). An offer with no tranches is never excluded for availability and is flagged `availability_unknown` only when a day was given. Surplus packs are not a reason to exclude: landed cost ranks, not price per piece (a pack offer with the lower price per piece can still cost more in total). `stale_offers: flag_only` keeps stale offers selectable but flagged; expired never is. Search snapshots are dropped before anything else unless `allow_search_snapshot_sources`.
2. Arithmetic, all `Fraction` until one rounding: pack content in the line unit; `packs = ceil(required / content)` (exact), raised to `min_order_qty`, then up to a multiple of `order_multiple`; pack price converted to the comparison basis; goods = packs x pack price; delivery = the offer's terms at this line's goods alone; landed = goods + delivery (unknown terms count as nothing and flag `delivery_unknown`).
3. Rank key: comparison cost (landed, or goods if `include_delivery_in_comparison` is false), shorter lead time (unknown last), higher confidence, more recent observation, offer id. If winner and runner-up tie on cost the first differing key is reported (`tie_break`). The result is a pure function of the offer set (order-independent, tested).
4. Output `PricedLine`: `status` (priced, indicative_only, no_eligible_offer, no_offers), `best`, all `ranked`, `runner_ups`, `excluded` (with codes and reasons), `indicative` range, flags, templated reasons. Complexity O(n log n) in offers per line.

Rounding (documented once, `decimals.py`): money is rounded once, half-up, to `minor_unit_places` (default 2); displayed unit prices to 4 places; pack content and surplus to 6; totals come from exact values, not from the rounded display figures. `landed_unit_cost = landed / required quantity` has the meaning of `rfq.comparison.landed_unit_cost` (tested against it).

VAT: conversion uses the configured rate and basis only (`vat.py`, exact, never a hard-coded 20%). With rate 0 there is no VAT handling (as in `rfq.quotes.normalise`). Unknown basis is flagged and excluded (UK profile: unknown goes to a human) unless the profile says `assume_default_flag`.

### 4.2 Sanity (`sanity.py`): relative only

- Outliers: unit prices on the comparison basis against the median of comparable offers (same line, base currency, VAT known, convertible, not indicative, not stale/expired): above `median x ratio` or below `median / ratio` (strict, exact; `pricing.price_outlier_ratio`, needs `outlier_min_peers` offers). Default policy excludes the offer for a person (`engine.outlier_offers`); `flag_only` keeps it, flagged.
- Optional `IndexBand`: a reference unit price seen earlier (for example the tenant's last paid price) moved by a published index ratio, with a tolerance factor. The index is used only to say how prices MOVED, never as a price level: the DBT construction-material indices are factory-gate indices that exclude merchant discounts, and the MHCLG dataset named in the matching spec was last updated in 2017. A month-on-month change cap per offer needs price history, which is not stored (open question 5).

### 4.3 Basket (`basket.py`)

Model: each priced line is bought from one merchant at that merchant's cheapest eligible offer (cost c_ij); a merchant order costs spend + a delivery step function of that spend. The problem is NP-hard (NP-complete even with two shops).

- Independent groups: lines sharing no merchant are separate sub-problems (union-find), solved separately. Exact.
- Exact DP per group: lines with a single possible merchant are forced and become that merchant's base spend; the rest ("free" lines) are solved by a DP over subsets of lines, merchant by merchant, O(m x 3^n), pruned by a bound from the heuristic incumbent (strict, so equal-cost solutions survive; exact). Used when the group has at most `engine.basket_exact_max_lines` (default 12) free lines and the work estimate fits `engine.basket_work_budget`. Measured here (pure Python, synthetic): 12 lines x 6 merchants 0.15-0.45 s, 12 x 8 0.6 s. Ties prefer fewer merchants, then a fixed order, so results do not depend on input order.
- Fallback above that: deterministic greedy start (line-by-line cheapest, each single merchant that covers the group) plus local search (move one line, merge one merchant into another) until no strict improvement. The result says `exact=False`, `method="heuristic"`, `optimality_gap` (objective minus the sum of per-line minima: the true optimum is at most that much lower) and a templated note.
- Baselines (reported, never beaten by the result, property-tested): line-by-line cheapest with honest consolidation (lines landing at one merchant share one delivery charge) and the best single merchant covering every line. Savings versus each are exact Decimals.
- Production path: a MILP with assignment binaries x_ij, merchant-used y_j, threshold-met z_j, minimising sum c_ij x_ij + sum f_j (y_j - z_j) (flat fee with a free-over threshold; tiers need one binary per tier), solved by HiGHS, with this DP as the test oracle. No solver dependency is added here.
- Modelling assumption: a merchant's cheapest offer per line is used; the engine never buys a dearer pack to cross a delivery threshold. Merchant terms are the larger fee at every spend over that merchant's offers (tenant-private terms preferred over shared), so delivery is never understated. Unknown terms count nothing and set `delivery_incomplete`.

### 4.4 QuoteDraft (`quote.py`)

Priced lines (SKU, offer, merchant, quantity, packs, unit price, line total on the comparison basis, assumptions, provenance with match tier/basis, licence, observed/valid times, inert `source_ref`), delivery per merchant, totals with VAT shown once on the total (net + VAT = gross by construction), separate lists for unmatched, ambiguous, indicative-only and no-offer lines (excluded from every firm total), a freshness summary and the note "not a supplier quote, not a reservation, nothing sent or ordered" (`notice_code` lets a UI localise).

## 5. Configuration (`config.py`)

`PricingConfig.from_mapping(resolved.profile.model_dump())` (python or json dump). Components never import `aiplat`; defaults mirror the profile's and `tests/pricing/test_config.py` fails if they drift (it also builds a config from every real profile).

| Key | Source | Default |
|---|---|---|
| `base_currency`, `accepted_currencies`, `symbol_map` | `money.*` | none (required), base only |
| `vat_rate`, `unknown_basis`, `quote_basis_default` | `tax.standard_rate/unknown_basis/quote_basis_default` | 0, flag_require_approval, unknown |
| `max_offer_age_hours` (per source kind), `stale_offers`, `compare_basis`, `include_delivery_in_comparison`, `price_outlier_ratio`, `allow_search_snapshot_sources` | `pricing.*` | 168/24/48/24/720 h, exclude_from_best, ex_tax, true, 3, false |
| `outlier_offers`, `outlier_min_peers`, `runner_up_count`, `minor_unit_places`, `basket_exact_max_lines`, `basket_work_budget`, `future_skew_minutes` | `engine.*` (not profile keys; proposals) | exclude_from_best, 3, 3, 2, 12, 6,000,000, 5 |

A source kind missing from a profile's age map falls back to its default, so none is ever unlimited. The default ages are the profile's v1 placeholders: no quantitative UK staleness model exists, so they are configuration to tune, not evidence. `pricing.*` is not tenant-overridable.

## 6. Hard-rule mapping

| Rule | How |
|---|---|
| 1 [R1] nothing sent/ordered | No transport, no order path; `QuoteDraft` is data; a static test bans network, file and process imports |
| 2 [R2] no silent substitution | Only SKUs of the approved match group are priced; non-Tier-A members need a recorded substitution approval id, else `substitution_not_approved`; the chosen SKU and tier are on every line |
| 3 [R3] provenance | Every offer carries provenance, licence tag, confidence, observation/validity times; explanations are fixed templates over ids and typed values (`reasons.py`), parameters cannot carry free text |
| 4 [R6, R7] untrusted vendor content | Strict parser, quarantine with reason codes only, titles and URLs never read, links never stored or followed, text made inert, no network code |
| 5 [R9] money | Decimal only, explicit currency/UoM/basis, exact rationals, one documented rounding; no floats (static scan) |
| 6 events | Not applicable yet: nothing here changes request state; recording a draft as an event belongs to the caller (open question 4) |
| 7 [R10] tenancy | Repositories are tenant-bound capabilities that cannot reach other tenants' data in memory; shared writer is separate with no read methods; shared data is structured list data only (no vendor quotes, no free text, no account-specific or attested offers, licence must be on the shareable list) |

## 7. Hard rule R7 and network price sources

Spec R7: "No fetching or scraping of third-party links or sites; no link-fetch capability exists; attachments parsed in a no-network sandbox". This component obeys it literally:

- Adapters work on data handed to them: `CsvPriceFileSource.parse(text_or_bytes, mapping)` (also `parse_rows` for a table, for example an Excel sheet already parsed by `components.doc_parse`) and `JsonShoppingResultsSource.parse(payload)`. The package performs no file, network or clock access.
- `HttpClient` is a documented, unwired seam: a Protocol with no implementation anywhere in the package and no source accepts one. A test scans the package for imports of `urllib`, `http`, `requests`, `httpx`, sockets and process/file modules, and for any class implementing the seam.
- URLs found in offer data are never stored or followed; `source_ref` is inert text such as `prices.csv#row=3`, and any link in text is replaced by `[link removed]`. Product URL and title columns cannot even be mapped.
- Real provider APIs (merchant APIs, affiliate feeds, search/shopping APIs) would need an explicit, recorded amendment of R7 (a proposed ADR such as ADR-013, a user decision, legal review) before any HTTP client is wired. Until then data enters only as tenant-supplied files or emailed attachments, loaded tenant-private by default. The `source_kind` values are kept as they are: they describe what produced a file (an affiliate feed downloaded and uploaded by a person is `affiliate_feed`), not a live connection.

## 8. Not built

Real provider adapters (blocked by R7 as above); persistence (Postgres repository with RLS; the in-memory store is the reference); API/worker wiring and events; FX conversion (other currencies are excluded, not converted); month-on-month price-change checks (no history); consent recording when promoting data to a shared dataset; the MILP solver path; Excel/PDF parsing (use `doc_parse`); UI and localisation of reason codes; per-unit conversion beyond the five units; price breaks; reading availability from price files (the model and the checks exist, no source fills them yet); a line supplied from several offers (a partial quantity from one supplier and the rest from another) or in several deliveries.

## 9. Open questions

1. Unknown delivery terms count as zero and are flagged (the rfq comparison ranks unknown freight last). Which policy do buyers want? A profile key could choose.
2. Should a low outlier be held back by default (current) or only flagged? Needs real order lines to tune; the ratio 3 and 3 peers are placeholders.
3. Strictly-over free-delivery thresholds are conservative; merchants who say "£50 or more" are entered as tiers. Confirm how real terms read.
4. Who records a `QuoteDraft` as hash-chained events, and when does a draft expire?
5. Where does price history live (needed for month-on-month caps), and for how long (licence cache limits)?
6. Which licence tags may be stored in the shared dataset (currently only `synthetic-illustrative`), and what consent record backs a promotion from private to shared (solicitor items in ADR-013)?
7. The engine's private-over-shared delivery-terms rule and "cheapest offer per merchant" assumption: acceptable for the first pilot?

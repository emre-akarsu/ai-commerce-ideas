# Intent-driven quoting: advised spec (proposal v0.1)

Status: **proposal for review**, not an amendment to `04-product-spec.md` (v0.2). Product-market fit is unproven; this document contains no market claims. Evidence: `research/intent/01-market.md`, `02-academic.md`, `03-domain-uk-bathroom.md` (tags `[opened]`, `[snippet]`, `[memory]` as in those files). Not building-control, legal, structural or asbestos advice. Seed and price data stay synthetic.

## 1. The change

Today the refurb pack takes a materials list or RFQ line items. The proposal adds an upstream stage that takes an **intent**, for example "Victorian terrace, mid-size full bathroom refurb, on a budget", and produces a reviewed scope, bill of materials, labour packages and RFQ packets. Everything downstream (mandate, `check_send`, quarantine parser, comparison, audit chain, human approval) is unchanged.

What the research says about the space:

- UK marketplaces turn intent into a lead and leave scoping and pricing to the trade [opened, 01-market §2]. BOM-from-description exists for contractors only (Home Depot Material List Builder, Houzz AI, Clear Estimates) [opened/snippet, §5]. Supplier-RFQ automation starts from takeoffs or requisitions, not homeowner intent [opened, §7]. Consumer agent checkout buys single SKUs [opened, §8].
- No product page found shows an assumption ledger, budget-ceiling optimisation, property-age risk loading or regulated-scope gating (01-market §11). This is absence in a limited sample, medium strength. Published accuracy figures are all vendor claims.
- LLMs alone plan poorly under constraints (TravelPlanner 0.6% for GPT-4, NATURAL PLAN below 5% at 10 cities) and under-clarify (CLAMBER) [opened, 02-academic]. The supported pattern is an LLM that proposes and deterministic critics that check (LLM-Modulo, a position paper), with arithmetic in code and question choice by expected information gain.

## 2. Non-goals

No ordering or payment (v1 ends at approved RFQ sends and quote comparison). No auto-selection of tradespeople. No claim that an estimate is accurate. No scraping of registers, retailers or marketplaces. No acceptance of any regulated work as "priced" while its gate is open.

## 3. Pipeline

| Stage | Deterministic | Model (quarantined, typed output) | Human |
|---|---|---|---|
| 1 Intent intake | `IntentBrief` slot schema; mandatory-slot gate; budget ceiling as Decimal with currency | Extract slots from free text and photos; draft questions | Answers, or picks "assume typical" per slot |
| 2 Question policy | Ask only when a slot's cost impact or gate exposure exceeds a profile threshold; cap questions per round; batch them | Rank candidate questions (expected-information-gain style) | n/a |
| 3 Assumption ledger | Append-only rows via the workflow module; dependency recompute when a row changes | Propose assumptions with a confidence label | Confirms every row that touches a gate or exceeds a cost-impact threshold |
| 4 Scope of work | Fixed work-package template (WP0 to WP12, `03-domain §1`); completeness and ordering critics; unresolved decision variables listed | Draft scope text and per-package contents | Reviews and signs the scope |
| 5 BOM and quantities | Quantity functions in code (areas, wastage, UoM, pack sizes) using Decimal | Dimension extraction from text or photo; map to catalogue items | Confirms dimensions and named products |
| 6 Tiers within budget | Choose the spec tier per package so the sum fits the ceiling (MILP or CP solver, OptiMUS-style formulation reviewed by a person); contingency is a ledger line | Explain the choice in templated text | Approves tier and contingency |
| 7 Ranges | Rule-based ranges from user-entered or quote-derived data; conformal/CQR ranges only after enough quote history exists | none | Sets contingency policy |
| 8 Gates | Fail closed (section 6) | none | Clears with a document or named professional's reply |
| 9 RFQ packets | Split into merchant materials RFQs, labour RFQs per trade and named provisional sums; build packets; mandate and `check_send`; send-service | Cover text over approved IDs only | Approves every send |
| 10 Compare | Existing `compare()` plus scope coverage; no ranking across quotes with different regulated-item coverage ("scope gap" row instead) | Parse replies (quarantined, grounding check) | Awards |

## 4. New types (inside `employees/refurb`; frozen `core` contracts untouched)

`IntentBrief`, `Slot`, `Assumption`, `WorkPackage`, `Gate`, `ProvisionalSum`, `Tier`, `BomLine`, `RfqPacket`. Extend `Quote` with `exclusions`, `provisional_items`, `deposit_stages`, `cert_included`, `trade_registration_id` and `scope_coverage`. If any change needs `core/domain.py` or `ports.py`, write it to `docs/architecture/CONTRACT_CHANGES.md` and stop.

**Assumption row** (immutable, written as an `Event`): id, scope id, work package, statement, source (`user_said` | `photo_or_survey` | `default_template` | `model_inference` | `public_source:<url>`), confidence, status (open, confirmed_by_user, confirmed_by_trade, invalidated), cost impact if false (a money range entered by a human or a provisional-sum trigger, never invented), owner, gate link, expiry, evidence. A `model_inference` row can never close a critical gate (rule 3). Seed list for the example intent: `03-domain §6.1`.

## 5. Budget handling ("on a budget")

"On a budget" is an input, not an adjective: the agent asks for a ceiling or a tier and records which. Tiers are our own named definitions, because public sources define them inconsistently (`03-domain §3`). Public bathroom cost ranges come from marketplace and retailer blogs that disagree and ignore Victorian hazards; they may be shown only as dated, sourced context and must not feed a price claim. Victorian hazards (joists, soil stack, lead, ceiling, asbestos) belong in provisional sums and contingency, which are ledger items.

## 6. Gates (fail closed, modelled on `policy.check_send`)

| Gate | Trigger | Needed before a "firm" price is shown |
|---|---|---|
| G1 Building Regs / competent person | New circuit, plumbing or drainage change, structural change, unvented cylinder, extract fan | Named installer scheme or Building Control route; certificate line in scope |
| G2 Asbestos | Pre-2000 build or works with textured coatings, vinyl tiles, insulating board, or unknown | Survey result, or "assumed present" with a conditional provisional sum |
| G3 Party wall / structural | Chimney breast, wall cut, new opening, joist alteration beyond limits | Engineer note and notice status, else provisional sum |
| G4 Gas / hot water | Boiler, flue, gas pipe, cylinder | Gas Safe (and cylinder competent person) line item |
| G5 Heritage | Listed, conservation area, Article 4 | User confirms status; consent stated as outside the quote |
| G6 Lead / water | Lead pipe seen or suspected | Replacement scope and water-company notification noted |

Hard blocks: gas work without a Gas Safe line; electrical work in bathroom zones without a registered-installer line; suspected asbestos with no survey or recorded assumption; party-wall or structural change without engineer or notice status; internal alteration of a listed building with no consent statement. Warnings: missing Part F fan spec, bath over 230 L, tier against budget mismatch, missing VAT basis, deposit above the mandate threshold. The gate rules cite sources that are partly unverified (`03-domain §7`); a domain reviewer must confirm each before any customer sees them.

## 7. Hard-rule mapping

| Rule | How this design keeps it |
|---|---|
| R1 send only with a valid Approval | RFQ packets go through the existing mandate, `check_send` and send-service; planner has no transport |
| R2 no cross-tier substitution | Named products in the BOM; a swap is a new line needing approval |
| R3 provenance | Every BOM and ledger value carries a source; `model_inference` never satisfies a critical attribute or gate |
| R4 untrusted vendor content | Replies and merchant text go through the quarantined parser and grounding check; no link fetching |
| R5 Decimal money | Budget, quantities, tiers and contingency are Decimal with currency, UoM and VAT basis |
| R6 hash-chained events | Ledger rows, gate clearances and scope signatures are events through the workflow module |
| R7 tenant isolation | Tenant-scoped repositories for all new types |
| Config | `VAT_RATE = Decimal("0.20")` in `employees/refurb/model.py` violates "never hard-code tax"; move to the deployment profile with a rate per line (20% default; 5% and 0% cases per GOV.UK `[opened]`). Currency, deposit thresholds, question caps and contingency bounds also come from the profile |

## 8. Evaluation (offline, deterministic, no real LLM)

- Synthetic homeowner simulator with scripted ground-truth slots: slots recovered, questions asked, unnecessary questions.
- Hard-constraint pass rate: budget cap, UoM, completeness, gate coverage (the TravelPlanner style of metric).
- Line-item coverage and quantity accuracy against a hand-built expert takeoff of the synthetic house.
- Hostile fixtures in replies (injection, bank-detail change) reusing the existing quarantine suite.
- Promotion gate for any rule set or model: zero hard-gate violations on the frozen set, plus the existing Wilson upper-bound convention for error rates. No accuracy number is claimed until independent data exists; no academic or independent benchmark for domestic refurb costing against real invoices was found.

## 9. Minimum viable build (about three increments)

1. `IntentBrief`, slot schema, ledger and question policy over one canonical scope (full bathroom), with a synthetic Victorian-terrace house. No prices.
2. Work packages, quantity functions and BOM with synthetic catalogue rows, tier solver against a ceiling, gates G1 to G6 with fail-closed tests.
3. RFQ packets (materials, labour, provisional sums) through the existing send gate; `Quote` extensions; scope-coverage comparison; refreshed demo.

Out of v1: photo or floor-plan takeoff, conformal ranges (need quote history), merchant APIs (terms not read), other room types, multi-jurisdiction rules beyond England and Wales.

## 10. Owner decisions (answered) and what they imply

| # | Decision | Answer | Consequence for the design |
|---|---|---|---|
| 1 | Who is the user | Generic across the three ideas | The principal is a generic "buyer": a household, a contractor, a plant or a company. Persona-specific wording, gates and mandate limits come from the deployment profile. No consumer-only features in the core |
| 2 | Where price comes from | Use everything available in the UK market | See section 12. Only sources whose terms allow it; terms for several are still unread |
| 3 | "Mid-size" | London averages as an illustrative example | Size stays a square-metre input. London figures are labelled example data, sourced and dated, never hard-coded and never presented as a price |
| 4 | Regulated-work stance | Gates block and warn only | Confirmed. The product never advises on compliance |
| 5 | RFQ targets | All: merchants and tradespeople | Needs the counterparty-reach rules in section 13 before any trade send |

## 12. Price sourcing strategy (from `research/intent/04-uk-price-sources.md`)

| Layer | Source | Use |
|---|---|---|
| Escalation and regional adjustment | ONS price indices, DBT materials price indices (monthly), ASHE Table 15 regional pay; all OGL v3 `[opened]` | Adjust a quote-derived or customer-supplied base. They contain no bathroom unit prices, so they cannot be the base |
| Base prices (v1) | Customer-supplied price lists, quotes received through the product, merchant trade accounts and RFQs | The only lawful base found without a licence |
| Licensed unit rates (later) | BCIS (terms and price not found), Spon's 2026 (about GBP 185 as a book, snippet) | Needs a licence covering storage and AI use; ask the publisher before building on it |
| Affiliate and product feeds | Awin feeds are open to any publisher; storage and AI terms unconfirmed | Candidate for product attributes and indicative retail prices after the terms are read |
| Do not use | Scraping any merchant or marketplace. Every merchant robots.txt read disallows search, basket and checkout; Screwfix and NBS terms ban crawling and text mining | Hard no |

No merchant API or punchout documentation was found, so merchant quotes arrive by email RFQ or a customer's own trade account. Marketplace cost guides (MyJobQuote, Book a Builder and similar) are marketing-grade and may be shown only as dated context.

## 13. London worked example and counterparty reach (from `research/intent/05-london-example-and-reach.md`)

- **Illustrative only.** The demo shows a London Victorian-terrace bathroom with third-party guide ranges beside the sourced uplift, each labelled "illustrative example, dated". Five sources give five London uplift ranges (10-20%, 12-18%, 20-30%, 20-40%, 25-40%); the demo shows them side by side and does not average them. Plumber day rates range from 180 to 480 across sources, and one source gave two different electrician ranges two weeks apart. Size figures run from 3-4 m2 to 5-6 m2, so the slot is "floor m2 plus wall m2", asked of the user.
- **VAT.** 20% standard; 5% and 0% cases per GOV.UK `[opened]`; the domestic reverse charge does not apply to private homeowners (GOV.UK technical guide) `[opened]`; CIS for householders is memory only.
- **Emailing tradespeople.** Sole traders and ordinary partnerships are individual subscribers under PECR; companies are corporate subscribers (ICO) `[opened]`. No page read says whether a one-to-one RFQ email is "marketing". **Blocker for trade sends:** counsel must confirm before the first send to a sole trader; until then the product refuses sends to unverified individual subscribers and uses opt-in or inbound contact for them. Registers and directories (Checkatrade, MyBuilder, TfL, Gas Safe, NAPIT) were blocked, so the product does not harvest contacts from them; contacts come from the buyer.
- **Not found:** London sub-regional costs, tile and trade lead times, any merchant confirming emailed RFQs, a labourer rate. ASHE London trade figures sit in a zip file that was not read. Congestion Charge and ULEZ amounts are snippet-only.

## 11. Known weak evidence

Part F 15 l/s and the 230 L Water Regulations threshold are from snippets; Part P scope and Welsh equivalents were not read; the HSE domestic asbestos page returned 404; Historic England and Gas Safe pages were blocked; party wall notice periods are from memory; the 40/30/30 deposit split is one vendor's suggestion; competitor and checkout claims rest on blocked or single-source pages (`01-market §13`); several paper venues are from memory (`02-academic §9`).

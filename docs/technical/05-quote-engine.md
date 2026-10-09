# The quote engine

The quote engine turns a job template and the supplier price files into a priced materials list, ways to buy it, a map of who has prices, and unsent messages asking for the prices that are missing. It is a set of pure, offline components wired together by one service, `apps/api/quote_service.py` (`QuoteService`), behind the `/v1/kits`, `/v1/quotes`, `/v1/price-books`, `/v1/kit-templates` and `/v1/price-files` routes.

It is separate from the request-to-order flow: nothing here uses the request state machine. The one bridge is the unsent text messages, which become requests that go through the normal approval and send path.

Everything in the demo is **synthetic**: fictional merchants, invented prices and a job-kit library that no tradesperson has reviewed. The shipped data exists only for the `uk` profile, and the API starts only with that profile (see Configuration).

## Data flow

```mermaid
flowchart TB
  subgraph web["Web: Job, Prices, Quote, Compare, Ask suppliers"]
    wz["Job wizard"]
    qv["Quote and Ways to buy"]
    pb["Supplier prices"]
  end
  subgraph api["API routes (quote_routes.py and friends)"]
    r1["POST /v1/kits/resolve"]
    r2["POST /v1/quotes<br/>GET /v1/quotes/id<br/>GET /v1/quotes/id/options"]
    r3["GET /v1/price-books<br/>POST /v1/price-files"]
    r4["POST /v1/quotes/id/decisions<br/>/v1/kit-templates"]
    r5["POST /v1/quotes/id/rfq-drafts"]
  end
  qs["QuoteService"]
  subgraph comps["Components (pure, offline)"]
    jk["job_kits<br/>resolve a kit"]
    ql["quoting.kit_lines<br/>order lines"]
    mt["matching<br/>parse, retrieve, check, gate"]
    pr["pricing<br/>offers, freshness, VAT, units, packs, delivery"]
    bk["pricing.basket<br/>best price, basket optimiser"]
    qb["quoting.pipeline<br/>build_quote"]
    qo["quoting.options_engine<br/>ways to buy"]
    pbk["pricebook<br/>status, coverage, gaps, drafts"]
  end
  subgraph stores["Stores (memory, or Postgres under RLS)"]
    of[("offers, shared_offers")]
    am[("approved_matches")]
    qsn[("quote_snapshots")]
    kt[("kit_templates")]
    pi[("price_imports")]
  end
  pur["PurchasingService<br/>prepare_text_rfq"]
  wz --> r1
  wz --> r2
  qv --> r2
  pb --> r3
  qv --> r4
  pb --> r5
  r1 --> qs
  r2 --> qs
  r3 --> qs
  r4 --> qs
  r5 --> pur
  qs --> jk --> ql --> mt --> pr --> bk --> qb --> qo
  qs --> pbk
  mt <--> am
  pr <--> of
  qs <--> qsn
  qs <--> kt
  pbk <--> pi
  pur -->|"unsent messages, approved one by one"| req["Request flow: approve and send"]
```

## The stages

| Stage | Module | What it does | Key rules |
|---|---|---|---|
| 1. Resolve the kit | `components/job_kits` | Reads a template (modules, lines, questions, rules) and resolves it with the person's answers, measurements and choices into a materials list. | A few upfront questions at most (`max_upfront_questions`, three in the shipped data). Every default and every "don't know" mapping is logged as an assumption with source `default_template`. About a third of the lines are forced by a stated rule (`forced_by`). Formulas are parsed with `ast` against a whitelist and never reach `eval`. Quantities are `Decimal` with an explicit unit, and count units must be whole. |
| 2. Make order lines | `components/quoting/kit_lines.py` | Turns each kept line into an `OrderLine`, passing the spec text on word for word. | Lines are generic specs, never part numbers (R2). |
| 3. Match | `components/matching` | Parses the line, retrieves candidates from the catalogue index, runs the attribute checks, and lets the decision gate **accept**, send to **review**, or **reject** it. | A line that names an MPN or GTIN and finds a SKU is decided by the identifier branch first. The attribute checks have no off switch. Defaults from the profile: auto-accept at a score of 0.75 with a lead of 0.05, reject below 0.35, retrieve 50, show 3 in review. A person's approval of one product is stored per customer (`approved_matches`, keyed by a signature) and there is no "none" choice. |
| 4. Price | `components/pricing` | Prices every eligible offer for each matched line: freshness, VAT basis, unit conversion, whole packs, delivery fees and thresholds. | Only a merchant-confirmed quote, a trade-account feed or an attested, dated customer file may feed a firm line. Stale offers are excluded from the best price. An outlier (about three times the median) is held. A price with no stated VAT basis is not compared. |
| 5. Best price and basket | `components/pricing` | Picks one offer per line, then the cheapest complete basket across suppliers with their delivery thresholds. | The basket search is **exact** while a connected group has at most 12 lines with a real choice. Beyond that it is a heuristic, and the result says so (`not_proven_optimal`). |
| 6. Build the quote | `components/quoting/pipeline.py` | Sorts every line into **firm** (priced, in the total), **review** (waiting for a person's choice), **unmatched**, **indicative only** (rough, never in a total), **no offer** or **skipped**, and totals the firm lines. | The totals use `split_total`: net plus VAT equals gross by construction, shown on one stated basis. |
| 7. Ways to buy | `components/quoting/options_engine.py` | Searches for up to five complete alternative baskets: lowest total, fewest deliveries, fastest, preferred suppliers, one supplier, and a balanced option. | It chooses nothing for the buyer. Tolerance, search caps (`max_solver_calls` 64, `max_search_merchants` 8) and weights are `OptionsConfig` defaults, all unsourced placeholders. The balanced option exists only when the buyer supplies a budget, a required-by date or a delivery limit. |
| 8. Price book | `components/pricebook` | Works out who has prices (status ladder from *On request* to *Contract feed*), coverage per supplier, and the gap list. Drafts the text of a request for a missing price. | Computed on each call from the offer store. Nothing is stored. |
| 9. Ask suppliers | `employees/purchasing/rfq_from_quote.py` and `PurchasingService.prepare_text_rfq` | Turns the gap messages into unsent RFQs, one container request per message. | R1: a person approves each exact message in the ordinary flow. Only *preferred*, verified, unsuppressed suppliers can be asked. No link or markup is allowed in the text. |

Judgement calls are deterministic code. The only model step in the engine is the **match judge**, which can re-order candidates that already passed every check. It is off in the shipped API, and the engine is built without a model. Without one, a marginal accept goes to review.

## What the documents look like

`POST /v1/quotes` stores a snapshot (`quote_snapshots`, one row per version) and answers a `quote-draft-ui/1` document. The page reads partitions (`priced`, `review`, `unmatched`, `indicativeOnly`, `noOffer`, `skipped`), the totals, deliveries per supplier, checks, and a `notice` that says it is not a supplier quote. `GET .../options` re-runs the quote for the saved kit, searches the ways to buy with the query parameters, and answers `quote-options-ui/1`. `GET /v1/price-books` answers `price-books-ui/1`. The schemas are in `profiles/data/{quoting,pricebook,job_kits}/*.schema.json`, and the web app validates each document on read.

## Persistence

| Store | In memory | PostgreSQL |
|---|---|---|
| Offers (per tenant) | `InMemoryOfferStore` | `PgOfferStore` (`offers`) |
| Shared platform prices | seeded in memory in the demo | `PgSharedOfferWriter` (`shared_offers`, written by the owner role only) |
| Approved matches | `InMemoryApprovedMatchStore` | `PgApprovedMatchStore` (`approved_matches`) |
| Imports | `InMemoryImportStore` | `PgImportStore` (`price_imports`) |
| Templates | `InMemoryTemplateStore` | `PgTemplateStore` (`kit_templates`, at most 30 per tenant) |
| Quote snapshots | `InMemoryQuoteSnapshotStore` | `PgQuoteSnapshotStore` (`quote_snapshots`) |

With `DATABASE_URL` set, `apps/api/quote_pg.py` builds the Postgres stores, and the quote service records `quote_created`, `match_approved` and kit-template events in the same hash-chained log as the rest of the system. The synthetic demo prices are loaded by `scripts/provision_demo_tenant.py` (owner role), or into memory when `QUOTE_DEMO_DATA=1` and there is no database.

## Price files

`POST /v1/price-files` (buyer) accepts a `.csv` or `.xlsx`. `apps/api/price_file_service.py` parses it in the API process, with no network, row by row:

- A row is **quarantined**, never guessed, when it has no VAT basis, when the price is an outlier, when the unit cannot be converted, or when the row says it expired.
- A file only becomes **firm** when the uploader attests that they may use it and gives a valid-until date. Otherwise its offers load as indicative and never reach a total.
- The date check and the replacement of the supplier's earlier offers run only if the file yields at least one offer. A file whose rows are all quarantined is summarised and logged, and replaces nothing.
- The report (`price_imports`) says how many rows were read, accepted and quarantined, and why.

Price files enter only as files a person uploads (R7: nothing is fetched). Invoice and statement ingestion, a forwarded-to-alias path, and a separate sandboxed parser service are described in the design documents but **not built**.

## Configuration

`QuoteService` reads the resolved deployment profile (`PricingConfig.from_mapping` and `GatePolicy.from_mapping`), so currency, VAT basis, delivery policy, offer ages and the matching gate come from `profiles/<id>.yaml`, never from constants. It selects data by the profile id:

- matching data from `profiles/data/matching/<id>/` (classification, ontology, catalogue seed),
- the kit library from `profiles/data/job_kits/<id>/`,
- the message templates from `profiles/data/pricebook/`.

Only `uk` has matching and kit data. **With any other profile, the API entrypoint does not start.** `build_quote_service` raises `QuoteUnavailableError` only when the data directory is missing as a `FileNotFoundError`, but `load_classification` wraps that in a `ClassificationError`, so the process stops at start-up with `ClassificationError: cannot read profiles/data/matching/<id>/classification.yaml`. That covers `us` (the default when `DEPLOYMENT_PROFILE` is unset), `uk-scotland` and `uk-ni`. The `503` that the quote routes are meant to answer for a profile without data is therefore never reached. Run the API with `DEPLOYMENT_PROFILE=uk`. `QUOTE_CATALOGUE_FILE` points the service at a real catalogue file (validated strictly) and wins over the demo seed.

## Known gaps

- `QuoteService.price_books` does not catch `RequestTemplateError`. The buyer name in the drafts is the token's `sub` (and the company is the tenant id) for any tenant that is not a demo one, so a `sub` that looks like an email address or holds markup fails the template's plain-text rule (`buyer_name: links, markup or addresses are not allowed`), and `GET /v1/price-books` answers a generic `500`.
- The web's *After my reviews* view shows the same quote as *First quote* when the app is connected to the API, because no reviewer decisions are replayed into it.
- The *Best overall* option cannot be reached from the web app when it is connected to the API: the page sends no budget, date or delivery limit.
- The kit library and its option tags are an unreviewed synthetic seed (`needs_tradesperson_review`). Option compatibility is not rule-checked, and regulated-work gates are only proposed.
- There is no intent step ("quote me a bathroom"), no RFQ packets and no catalogue management screen.

Design detail for each stage: [`job-kits.md`](../architecture/job-kits.md), [`matching-engine.md`](../architecture/matching-engine.md), [`pricing-engine.md`](../architecture/pricing-engine.md), [`quoting.md`](../architecture/quoting.md), [`quote-options.md`](../architecture/quote-options.md), [`pricebook.md`](../architecture/pricebook.md). Activity diagrams for each: [`activity-diagrams.md`](../architecture/activity-diagrams.md) section 4 and 6. Note that parts of those design documents still describe the engine as library-only, and are being corrected.

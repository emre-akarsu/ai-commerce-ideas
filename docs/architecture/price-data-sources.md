# Price data sources: final list and activity diagram per method

Status as of 2026-10-07. Research, not legal advice. Hard rule R7 (spec section 4): no fetching or scraping of third-party links or sites. ADR-013 (proposed, not accepted) describes the only amendment that would allow contracted sources. All merchants and prices in demo data are synthetic. Evidence: `reports/UK product sourcing and price data.md` and the seven notes in `research_notes/UK product sourcing and price data/`.

**As built (2026-10-09), added to this 2026-10-07 research note:** only two of the sources below are in the code. A **manual quote** goes through the existing request flow. A person's **price file** is uploaded in the app (`POST /v1/price-files`: `.csv` or `.xlsx`, up to 900,000 bytes, attested by the uploader) and parsed in the API process with no network access; a separate sandboxed parser (stack-map item S4) is not built, and forwarding a file to the alias address is not built. **Invoice and statement ingestion is not built**: nothing in the code parses invoices, and the price book reports that level as not produced. Every source marked as needing the R7 amendment is not built. See [`docs/technical/05-quote-engine.md`](../technical/05-quote-engine.md).

Diagram key: teal = a person must act; amber dashed = step needs the R7 amendment and is not built; green = quote line or reference data; amber solid = indicative only; red = refused.

## Final list

| Method | What it gives | Who supplies it | How it enters | Becomes | Status |
| --- | --- | --- | --- | --- | --- |
| [Manual quote](#manual) | A price a merchant has confirmed for this job, with VAT basis and validity | The merchant, by email reply or a logged phone call | Existing RFQ flow: you approve the exact message; the reply is quarantined and extracted | Quote line | Use now (inside R7) |
| [Merchant price file](#pricefile) | Your negotiated trade prices for many products at once | Your merchant's account manager, as CSV or Excel by email | You upload it in the app; parsed in the API process, no network (forwarding to the alias address and a separate sandbox are not built) | Quote line (if attested) | Built (upload); inside R7 |
| [Your invoices and statements](#invoices) | What you last paid, by product and merchant | You, forwarding supplier invoices or statements | Planned: per-merchant alias email, parsed in a sandbox (not built) | Indicative only | Not built (would be inside R7) |
| [Merchant trade-account integration](#tradeacct) | Your live account prices through the merchant's own channel | The merchant, after a written agreement: EDI, punch-out (cXML, OCI) or an account API | Allowlisted gateway with fixed endpoints; no URL input | Quote line (account-specific, with validity) | After R7 amendment (ADR-013, not decided) |
| [Retail feed: affiliate network or merchant feed](#retailfeed) | Public retail prices, usually VAT-inclusive, with barcodes and stock | Awin (Wickes, Travis Perkins, Homebase, Plumbworld), Impact (B&Q), Kelkoo; Screwfix says its programme is closed | Allowlisted gateway, only with written advertiser permission | Indicative only | After R7 amendment (ADR-013, not decided) |
| [Search or shopping API](#searchapi) | Google Shopping style prices across merchants, via a scraping vendor | SerpApi, Serper, DataForSEO and similar; Google's own APIs cannot read other sellers' prices | Allowlisted gateway, only after gate S and the owner switching it on | Indicative only, off by default | After R7 amendment (ADR-013, not decided) |
| [Scraping merchant websites](#scrape) | Nothing we may keep: it is out of scope under R7 | Nobody; no capability exists | Not possible | Never | Never (R7 and site terms) |
| [Reference data: structure, not prices](#reference) | Product types, attribute templates (size, grade, pack), synonyms and codes | Uniclass 2015 (CC BY-ND), ETIM via bSDD (ODC-By), manufacturer spec sheets, Data Yard (to approach) | A person imports it at build time; nothing is fetched while the product runs | Not prices | Use now (build time, not prices) |

## Activity diagram for each method

<a id="manual"></a>
### Manual quote

**Status:** Use now (inside R7). **Becomes:** Quote line.

Any merchant, any product. Slowest, lowest risk, and the only route that needs no new capability.

```mermaid
flowchart LR
  subgraph L0["Buyer"]
    direction LR
    manual_a["Prepare RFQ to chosen merchants"]
    manual_b["Approve the exact message"]
    manual_f["Confirm the quote"]
  end
  subgraph L1["Platform"]
    direction LR
    manual_c["Send-service checks approval, then sends"]
    manual_e["Quarantine, extract, check values in text"]
    manual_g(["Stored private to you; quote line if valid"])
  end
  subgraph L2["Merchant"]
    direction LR
    manual_d["Replies with price, VAT basis, validity"]
  end
  manual_a --> manual_b
  manual_b --> manual_c
  manual_c --> manual_d
  manual_d --> manual_e
  manual_e --> manual_f
  manual_f --> manual_g
  class manual_b gate
  class manual_f gate
  class manual_g ok
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Counts as a quote line only if the merchant states validity in writing
- A reply with no VAT basis is flagged and goes to a person
- Stays private to your account

<a id="pricefile"></a>
### Merchant price file

**Status:** Built for upload (inside R7); forwarding to an alias address is not built. **Becomes:** Quote line (if attested).

You hold a trade account. The fastest real source: City Plumbing already emails price lists to Tradify customers.

```mermaid
flowchart LR
  subgraph L0["Buyer"]
    direction LR
    pricefile_a["Ask your account manager for the file"]
    pricefile_c["Upload it in the app (forwarding to an alias address is not built)"]
    pricefile_f["Attest validity and VAT basis"]
  end
  subgraph L1["Platform"]
    direction LR
    pricefile_d["Parse in the API process, no network, by row (separate sandbox not built)"]
    pricefile_e["Quarantine bad rows, strip links, strict types"]
    pricefile_g(["Stored private to you; quote line if attested"])
  end
  subgraph L2["Merchant"]
    direction LR
    pricefile_b["Emails the customer price list (CSV, Excel)"]
  end
  pricefile_a --> pricefile_b
  pricefile_b --> pricefile_c
  pricefile_c --> pricefile_d
  pricefile_d --> pricefile_e
  pricefile_e --> pricefile_f
  pricefile_f --> pricefile_g
  class pricefile_f gate
  class pricefile_g ok
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Each row is validated strictly; bad rows are quarantined with a reason
- You attest the validity period and VAT basis before prices can feed a quote line
- Never pooled with other customers; ask a solicitor about merchant confidentiality terms

<a id="invoices"></a>
### Your invoices and statements

**Status:** Not built (it would be inside R7). **Becomes:** Indicative only.

No price file yet. Gives a realistic reference price and shows which products you buy most.

```mermaid
flowchart LR
  subgraph L0["Buyer"]
    direction LR
    invoices_a["Forward invoice or statement PDF"]
    invoices_d["Confirm the matches"]
  end
  subgraph L1["Platform"]
    direction LR
    invoices_b["Sandbox parse: lines and prices paid"]
    invoices_c["Match lines to SKUs (matching engine)"]
    invoices_e["Last-paid price kept, private to you"]
    invoices_f(["Indicative only: not a quote line"])
  end
  invoices_a --> invoices_b
  invoices_b --> invoices_c
  invoices_c --> invoices_d
  invoices_d --> invoices_e
  invoices_e --> invoices_f
  class invoices_d gate
  class invoices_f ind
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Prices are history, not an offer: Travis Perkins' terms set the price at the delivery date
- Always indicative, never a quote line
- Matches to SKUs need your confirmation

<a id="tradeacct"></a>
### Merchant trade-account integration

**Status:** After R7 amendment (ADR-013, not decided). **Becomes:** Quote line (account-specific, with validity).

After the merchant signs. No UK merchant publishes a partner programme, so expect months. If the merchant just emails a file, use the price-file method instead.

```mermaid
flowchart LR
  subgraph L0["Buyer"]
    direction LR
    tradeacct_a["Ask the merchant for a written agreement"]
    tradeacct_c["Admin consents and connects the account"]
  end
  subgraph L1["Platform"]
    direction LR
    tradeacct_d["Gateway calls a fixed allowlisted endpoint"]
    tradeacct_e["Strict parse; account prices with validity"]
    tradeacct_f["Stored private to you; refreshed within age"]
    tradeacct_g(["Quote line if validity present"])
  end
  subgraph L2["Merchant"]
    direction LR
    tradeacct_b["Signs licence: storage, refresh, scope"]
  end
  tradeacct_a --> tradeacct_b
  tradeacct_b --> tradeacct_c
  tradeacct_c --> tradeacct_d
  tradeacct_d --> tradeacct_e
  tradeacct_e --> tradeacct_f
  tradeacct_f --> tradeacct_g
  class tradeacct_c gate
  class tradeacct_d amend
  class tradeacct_e amend
  class tradeacct_g ok
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Needs the R7 amendment and a signed licence first (ADR-013, gate 2)
- The gateway never holds order-capable credentials
- Refresh only within the licence's stated age; per-source kill switch

<a id="retailfeed"></a>
### Retail feed: affiliate network or merchant feed

**Status:** After R7 amendment (ADR-013, not decided). **Becomes:** Indicative only.

Product discovery and sense-checks. These are consumer prices, not your trade prices.

```mermaid
flowchart LR
  subgraph L0["Owner"]
    direction LR
    retailfeed_a["Written permission for link-less internal use"]
  end
  subgraph L1["Platform"]
    direction LR
    retailfeed_c["Gateway fetches the feed (allowlisted)"]
    retailfeed_d["Strict parse; licence and age recorded"]
    retailfeed_e["Offer flagged indicative"]
    retailfeed_f(["Price range shown; never a quote line"])
  end
  subgraph L2["Source"]
    direction LR
    retailfeed_b["Publishes product feed (retail, VAT-inclusive)"]
  end
  retailfeed_a --> retailfeed_b
  retailfeed_b --> retailfeed_c
  retailfeed_c --> retailfeed_d
  retailfeed_d --> retailfeed_e
  retailfeed_e --> retailfeed_f
  class retailfeed_a gate
  class retailfeed_c amend
  class retailfeed_d amend
  class retailfeed_f ind
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Awin cl. 10.7 limits data to the purpose of the agreement; a link-less internal price needs the advertiser's written permission
- Needs the R7 amendment
- Always indicative: never feeds a quote line

<a id="searchapi"></a>
### Search or shopping API

**Status:** After R7 amendment (ADR-013, not decided). **Becomes:** Indicative only, off by default.

Finding which merchants stock a product. Never a price someone could rely on.

```mermaid
flowchart LR
  subgraph L0["Owner"]
    direction LR
    searchapi_a["Gate S: licence, legal review, owner switch-on"]
  end
  subgraph L1["Platform"]
    direction LR
    searchapi_b["Query built from the matched product group"]
    searchapi_c["Gateway calls the vendor API"]
    searchapi_e["Snapshot stored, short life, indicative"]
    searchapi_f(["Merchant discovery or price range only"])
  end
  subgraph L2["Vendor"]
    direction LR
    searchapi_d["Returns title, price, merchant (scraped)"]
  end
  searchapi_a --> searchapi_b
  searchapi_b --> searchapi_c
  searchapi_c --> searchapi_d
  searchapi_d --> searchapi_e
  searchapi_e --> searchapi_f
  class searchapi_a gate
  class searchapi_c amend
  class searchapi_f ind
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Vendors scrape Google contrary to its terms; Google v SerpApi is unresolved
- Snapshots live briefly and are marked indicative
- Gemini, Bing and Brave terms bar caching their results

<a id="scrape"></a>
### Scraping merchant websites

**Status:** Never (R7 and site terms). **Becomes:** Never.

Not an option, even for 'just a price check'.

```mermaid
flowchart LR
  subgraph L0["Platform"]
    direction LR
    scrape_a["A price is wanted"]
    scrape_b["Fetch the merchant page"]
    scrape_d(["Refused: no fetch capability exists"])
  end
  subgraph L1["Site"]
    direction LR
    scrape_c["Terms bar crawling and commercial reuse"]
  end
  scrape_a --> scrape_b
  scrape_b --> scrape_c
  scrape_c --> scrape_d
  class scrape_b blocked
  class scrape_d stopn
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- R7: no fetching or scraping of third-party sites; no link-fetch capability exists
- Screwfix cl. 4.2 bars crawling and commercial use; other merchants bar commercial reuse
- Database right, contract and Computer Misuse Act risk; allowed only with a merchant's written permission, which then makes it a feed

<a id="reference"></a>
### Reference data: structure, not prices

**Status:** Use now (build time, not prices). **Becomes:** Not prices.

Always. It is the skeleton the matching engine checks against. Icecat is not usable here (its licence bars AI use).

```mermaid
flowchart LR
  subgraph L0["Owner"]
    direction LR
    reference_a["Download Uniclass, ETIM, spec sheets"]
    reference_d["Approve the first few per product family"]
  end
  subgraph L1["Platform"]
    direction LR
    reference_b["Import codes verbatim, attribution kept"]
    reference_c["Ontology builder drafts types, attributes"]
    reference_e(["Versioned data files, change log kept"])
  end
  reference_a --> reference_b
  reference_b --> reference_c
  reference_c --> reference_d
  reference_d --> reference_e
  class reference_d gate
  class reference_e ok
  classDef gate fill:#dcefef,stroke:#0b5f67,stroke-width:2px,color:#14201f
  classDef amend fill:#fbecd2,stroke:#8a4b00,stroke-dasharray:5 3,color:#14201f
  classDef ok fill:#dff1e5,stroke:#1b6b3a,color:#14201f
  classDef ind fill:#fbecd2,stroke:#8a4b00,color:#14201f
  classDef blocked fill:#f8e1e1,stroke:#a12626,stroke-dasharray:5 3,color:#14201f
  classDef stopn fill:#f8e1e1,stroke:#a12626,stroke-width:2px,color:#14201f
```

- Codes stored verbatim with attribution; our own types in a separate namespace
- People approve the first few entries per product family
- DBT price indices may sanity-check relative changes, never absolute prices

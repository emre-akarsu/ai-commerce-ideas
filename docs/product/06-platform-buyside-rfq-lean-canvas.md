# Lean canvas: buy-side RFQ on the platform (v0.1)

As of 2026-10-06. **A hypothesis to test; no customer has been interviewed.** Product-market fit is unproven. This canvas covers the first use case on the platform: buy-side RFQ, where a buyer asks suppliers for quotes, compares them and awards, with a person approving every send. It extends the industrial canvases in `docs/product/01-pmf-lean-canvas.md` (US) and `docs/uk/01-uk-pmf-lean-canvas.md` (UK; its sourced figures and Phase 0 tests T1 to T7 are reused, not repeated), and adds a second industry (refurbishment) from `docs/product/05-intent-driven-quotes-proposal.md`. "Medium confidence" findings come from `research/intent/01-market.md` and are absence of evidence in a limited sample.

## PMF hypothesis

Small and mid-size buyers who get prices by email and phone from several suppliers will let an agent turn a need, either a part or an outcome such as "Victorian terrace, mid-size full bathroom refurb, on a budget", into comparable quotes from their own suppliers, if it saves them time and prevents wrong-item, wrong-basis and missed-scope errors, and if they approve each send. First industries: industrial maintenance parts (UK first) and refurbishment (London as the worked example).

## Canvas

| Box | Content |
|---|---|
| **1 Problem** | 1) Getting comparable quotes means phone and email chasing across suppliers (frequency unmeasured; the UK evidence for the pain is stronger than for its frequency). 2) Quotes are not comparable: VAT basis, units, scope exclusions, provisional sums, delivery and credit terms. 3) The wrong item or a missed regulated step (part equivalence; for older houses, asbestos, soil stack, electrical zones). *Existing alternatives:* account rep, trade counter and phone, distributor portals and punch-out, marketplace lead sites, contractor estimating software, spreadsheets. No product was found that sends supplier RFQs from one stated intent (medium confidence). |
| **2 Customer segments** | A) Maintenance and purchasing staff at UK manufacturers with 50 to 249 staff (UK canvas beachhead). B) Building-services and facilities contractors buying for jobs. C) To test: small refurbishment contractors and property managers in London buying materials and trades. Size of C is not sourced. *Early adopters:* people who already juggle several supplier accounts in email and spreadsheets. Public-sector buyers are out of scope. |
| **3 Unique value proposition** | "Say what you need, a part or an outcome, and get comparable quotes from your own suppliers on a stated basis. You approve before anything is sent." High-level concept: an assistant buyer that drafts, and you approve. |
| **4 Solution** | 1) Intake from a request or an intent, with only the questions that change price, and an assumption ledger you confirm. 2) RFQ packets sent only after approval, replies read and compared like for like, scope gaps shown instead of ranked. 3) Hard gates and an audit trail: nothing sent without an Approval; regulated work blocks a firm price until cleared. |
| **5 Channels** | Founder-led outreach; trade shows and body newsletters named in the UK canvas; field-service software partners. For refurbishment no channel has been evidenced: to discover. |
| **6 Revenue streams** | Per completed request or a flat monthly tier (UK canvas assumes GBP 12 to 20 per request; stated willingness to pay in UK surveys was far lower than the model implies, so price is untested). Module or pack add-ons: untested. |
| **7 Cost structure** | Model inference; email infrastructure; exception handling by operators; reference-data licences (BCIS, Spon's and similar are licensed); technology errors-and-omissions insurance with affirmative AI wording; counsel; building and maintaining packs and the platform. |
| **8 Key metrics** | Requests resolved within two questions; supplier reply rate within one working day; quote-to-approval time; approver minutes per decision; wrong-basis quote count (target zero); requests per account per week; cost per request; share of ledger assumptions the user confirms; unsafe quotes stopped by a gate; new lines of Python per industry pack (platform metric). |
| **9 Unfair advantage** | None on day one. Candidates to test: a pack-based platform where a new industry is mostly data (effort unmeasured), a hard-gated safety record, an audit trail, and consented supplier-response and equivalence data (licensing is the blocker). |

## Riskiest assumptions, in order

| # | Assumption | How to test | What would change the plan |
|---|---|---|---|
| 1 | Enough RFQ events per account per month to pay for the product (UK canvas: unmeasured; per-request pricing needs far more volume than the US plan assumed) | UK canvas test T1: log real requests for a sample of accounts | Low volume: flat tier or a different segment |
| 2 | Suppliers answer an AI-assisted, emailed RFQ from an alias domain within one working day, and trade sends are lawful | T2, plus counsel on direct-marketing rules for sole traders | Low reply rate or an adverse legal view: restrict to companies and buyer-supplied contacts |
| 3 | Buyers trust drafts enough to approve quickly | Approver minutes and edit rate in the dry run | High edit rate: more questions or a narrower scope |
| 4 | Willingness to pay covers cost | T5 | Price below cost per request: change the model or the price unit |
| 5 | Refurbishment shares enough of the platform to be a data-only pack | Build `bathroom-refurb` and count new Python lines | Many lines: the contracts are wrong, revise before a third pack |
| 6 | Price and equivalence data can be sourced lawfully | Licence requests to BCIS, merchants and manufacturers | No licence: customer-supplied prices only, Tier B unavailable |
| 7 | Insurance with affirmative AI wording is available at a workable cost | Broker quote | None offered: limit liability scope or delay paid pilots |

## Next steps

Run the UK Phase 0 tests T1 to T7 (thresholds are assumptions set in `docs/uk/01-uk-pmf-lean-canvas.md`), interview refurbishment buyers before any pack work is sold, and settle the open decisions in `docs/architecture/platform-services-and-buyside-rfq.md` section 8.

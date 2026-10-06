# Idea 5 deep dive: Modules 4, 5, 6 (identity, signed approval/evidence, fraud/injection)

As of 2026-10-06. Tags: **[opened]** = page fetched and read this session (URL inline); **[snippet]** = search-result text only; **[memory]** = training memory, unverified. "Not found" = searched or opened, not stated. "Blocked" = fetch failed. Some "opened" pages were thin (noted). Product-market fit is unproven; nothing here is a market claim. Vendor claims are vendor claims.

Pages opened this session (distinct, ~41): Companies House auth, HMRC VAT v2, OpenCorporates pricing, GLEIF API page, OFAC SLS, EU sanctions dataset (thin), UK sanctions single-list page, OpenSanctions (thin), RFC 3161, RFC 9162, Rekor v2 blog, Tessera repo, UK SI 2016/696 (thin), Stripe Identity, Safe Browsing limits, VirusTotal limits, Gmail push, UK CoP (Pay.UK), NCSC phishing, FBI IC3 PSA190910, NIST AI RMF, OWASP LLM Top 10, OWASP Agentic page (thin), Zip, Didero, Fairmarkit, Paystand (nothing relevant), Ramp bill-pay fraud, Tipalti compliance, ITPro Basware/Trustpair, and arXiv/USENIX pages for Greshake, CaMeL, spotlighting, StruQ, SecAlign, Instruction Hierarchy, Geifman, CAPE BEC, BEC 2511.20944, Crosby-Wallach, CONIKS.

Blocked or empty: api.gleif.org/docs (Postman redirect, content empty), VIES technical page (empty), eur-lex eIDAS text (empty), EPC Verification of Payee (403), DocuSign pricing (404), Yousign pricing (redirected to an unrelated domain, not followed), Creditsafe developer site (DNS fail), opentimestamps.org (DNS fail), Brex agents page (404), Basware fraud page (404), Tipalti fraud page (404), IC3 2024 PDF (image-only, no text), gov.uk OFSI consolidated page (404).

---

## Module 4. Counterparty identity and verification

### A. Reference data and standards

| Source | Verified facts | Tag / URL |
|---|---|---|
| Companies House API | HTTP Basic auth, API key as username, blank password; OAuth 2.0 only for filing/end-user actions. Docs do not state price or detailed terms. | [opened] https://developer-specs.company-information.service.gov.uk/guides/authorisation |
| Companies House rate limit | 600 requests per application per 5-minute window; 429 on excess. | [opened, previous pass] https://developer-specs.company-information.service.gov.uk/guides/rateLimiting |
| Companies House licence | Register data is supplied under statutory approvals and "Acceptable use" terms, not clearly OGL; API free, bulk monthly snapshot free (older forum/news text). Current licence text not opened. | [snippet] https://forum.companieshouse.gov.uk/t/what-licence-applies-to-the-beta-service/912 |
| GLEIF LEI API | Full LEI search, filters, full-text, fuzzy matching, ownership (relationship) data from the Golden Copy; production since fall 2020. Page states no licence, rate limit or cost. Docs live at api.gleif.org/docs (Postman, blocked). | [opened] https://www.gleif.org/en/lei-data/gleif-lei-look-up-api |
| GLEIF data licence (CC0), no auth | Believed CC0 and free, no key. Licence page returned 404. | [memory] unverified |
| EU VIES | REST endpoint `https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number`, Swagger at ec.europa.eu/assets/taxud/vow-information/swagger_publicVAT.yaml; rate limits undisclosed, flood-blocking, `MS_MAX_CONCURRENT_REQ` and `MS_UNAVAILABLE` errors exist. Official page fetch empty. | [snippet, third-party libs] https://ec.europa.eu/taxation_customs/vies/#/technical-information |
| HMRC Check a UK VAT Number v2 | Behind authentication (v1 discontinued 2025-02-17); v2 is beta; returns registered flag, name, address; "verified check" mode returns a reference number as proof; registration via Software Developer Hub takes about 2 weeks; sandbox first, then Terms of Use 2.0 for production. | [opened] https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/vat-registered-companies-api/2.0 |
| HMRC rate limit | 3 requests/second/application (from previous pass). Not on this page. | [snippet] https://www.tax.service.gov.uk/api-documentation/docs/reference-guide |
| UK sanctions | OFSI Consolidated List closed 2026-01-28; the UK Sanctions List is the sole source; 7 static-URL formats (ODT, ODS, XML, HTML, TXT, CSV, PDF); migrate from OFSI Group ID to Unique ID; search tool with fuzzy logic. | [opened] https://www.gov.uk/guidance/moving-to-a-single-list-for-uk-sanctions-designations-28-january-2026 |
| OFAC | Sanctions List Service: free download and search, SDN and Non-SDN lists, advanced and legacy formats, fuzzy search tool. | [opened] https://ofac.treasury.gov/sanctions-list-service |
| EU financial sanctions | Consolidated list exists on data.europa.eu with formats/licence/token notes; page content too thin to state terms. EU FSF token requirement: not confirmed. | [opened, thin] https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions |
| OpenSanctions | Aggregator with API, bulk and self-host; page notes a commercial-licence requirement for data use. Price: not found. | [opened] https://www.opensanctions.org/faq/37/terms |
| UK Confirmation of Payee | Name-check service, launched 2020; 300+ organisations, 2M+ daily checks; personal/business indicator; participants must be FCA/NCA-regulated payment service providers; indirect access through aggregators (Banfico, ClearBank, iPiD, Lloyds Bank, OB Connect, SurePay, Technoxander, Tell Money, XBP Europe). Pricing: not found. | [opened] https://www.wearepay.uk/what-we-do/overlay-services/confirmation-of-payee/ |
| EU Verification of Payee | Mandatory under Instant Payments Regulation from 2025-10-09; results MATCH / CLOSE MATCH / NO MATCH / NOT POSSIBLE. EPC page blocked. | [snippet] (previous pass) https://www.europeanpaymentscouncil.eu/what-we-do/verification-payee |
| Orbis | Moody's/BvD; 625M+ entities, 170+ sources, ~1.9B ownership links (third-party text); "platform-and-bulk, enterprise-only pricing, restrictive licensing". API price/limits not found. | [snippet] https://zephira.ai/top-kyb-apis-for-fintechs-in-2025-compare-the-best-tools-for-instant-business-verification/ |

### B. APIs (name, auth, quota, price, ToS)

| API | Auth | Quota | Price | ToS note | Tag |
|---|---|---|---|---|---|
| Companies House Public Data API | API key (Basic) | 600/5 min | Not stated; believed free | Acceptable-use terms; read before reselling | [opened] auth page above |
| GLEIF API | none stated | not stated | not stated (believed free) | licence not verified | [opened, thin] |
| VIES REST | none | undisclosed, flood-blocked | free | availability varies by member state | [snippet] |
| HMRC Check VAT v2 | OAuth app via Developer Hub | 3 req/s | free (not stated) | Terms of Use 2.0, approval about 2 weeks | [opened] / [snippet] |
| OpenCorporates | API key | Essentials 500/mo and 200/day GBP 2,250/yr; Starter 2,500/mo and 500/day GBP 6,600/yr; Basic 5,000/mo and 1,000/day GBP 12,000/yr; Enterprise custom bulk | as listed | internal and external use permitted; free for journalists, NGOs, academics | [opened] https://opencorporates.com/pricing/ |
| Creditsafe API | not found (site blocked) | not found | not found | not found | blocked |
| Moody's Orbis | not found | not found | enterprise | restrictive | [snippet] |
| D&B Direct+ | OAuth 2.0 (previous pass) | not found | quote | not found | [snippet] |
| Stripe Identity | Stripe account | not stated | pay-as-you-go/custom, figure not on page | verifies government ID documents (120+ countries), selfie match, SSN; supported in listed countries incl. GB, many EU, US, CA, AU, JP; this is individual identity, not company KYB | [opened] https://docs.stripe.com/identity |
| Open Banking account verification providers | not researched in depth | | | PSP-gated access (CoP above) | not found |

### C. Competitor methods (own pages)

| Vendor | What their page says | Tag |
|---|---|---|
| Tipalti | Validates contact, payment and tax data against "27,000+ global rules"; TIN matching; screens payees against OFAC, Anti-Terror, Anti-Narcotics and "Do Not Pay" lists at onboarding and before each payment; "Tipalti Detect" network fraud module. | [opened] https://tipalti.com/en-uk/accounts-payable-software/financial-compliance/ |
| Basware | Acquiring Trustpair (binding agreement, close expected later in 2026): validates account ownership at onboarding, on change, and before payment; claims 2.5B invoices, 20M suppliers of intelligence. | [opened] https://www.itpro.com/business/acquisition/basware-to-acquire-trustpair-to-strengthen-payment-fraud-prevention |
| Ramp | Bill-pay risk alerts for new or changed bank details, unusual amounts, vendors unverified across its network; yellow/red severity; dismissals audit-logged; says to confirm changes via a verified phone number. | [opened] https://support.ramp.com/bill-pay-fraud |
| Coupa | Third-party Trustpair connector validates active company status and bank ownership; this is the partner's claim, Coupa's own method not found. | [snippet] https://trustpair.com/connect/coupa/ |
| Zip | Page covers permissions and audit; no supplier verification stated. | [opened] https://www.zip.com/ai |
| Didero, Fairmarkit, Paystand | No supplier verification or KYB stated on pages opened. Didero lists SOC 2 Type II and ISO 27001. | [opened] https://www.didero.ai/ |
| Brex, Aron | Not found (Brex page 404; Aron search returned no own-page claim). | blocked / not found |

### D. Integrations and verdict

| Integration | Verdict |
|---|---|
| Companies House + HMRC/VIES + GLEIF | Adopt as free evidence snapshots. They prove a legal entity and VAT number exist; they do not prove the emailer belongs to it or owns the bank account. |
| UK Sanctions List, OFAC SLS, EU list | Adopt by downloading lists and screening names locally (static URLs, free). Fuzzy match is a human-review trigger, never an auto-clear. |
| OpenSanctions | Optional; commercial licence applies. |
| OpenCorporates | Only when multi-jurisdiction demand exists (GBP 2,250/yr minimum). |
| CoP/VoP | Strongest bank-detail check; requires an FCA/regulated or aggregator route. v1: instruct the human payer to run the bank's own check, record result. |
| Stripe Identity | Not needed for company KYB; possible for a named human approver. Low priority. |
| Orbis, D&B, Creditsafe | Later, enterprise only. |

### E. Academic

LLM-based KYB entity resolution: not found in searches; no paper opened. Use deterministic identifiers (registry number, VAT, LEI) and classical name matching [memory].

### Recommended hybrid build (module 4)
- Deterministic: supplier state machine `unverified -> evidence_collected -> human_verified`; only `human_verified` may receive a send. Evidence = registry status, VAT validity, LEI if present, sanctions screening with list version/date, domain/email-sender binding, bank detail hash; each stored with timestamp and raw response hash.
- Deterministic: bank details can change only via human-approved process with callback to a number from the verified record; recent change = payment hold.
- Model: fuzzy name matching and plain-language summary only; never the verdict.
- Human: approves first send to a new supplier and any sanctions near-match.

### Min viable version (module 4)
Supplier record with `verified_at`, evidence refs, list-version stamp and bank-detail hash; Companies House and HMRC/VIES lookups behind recorded fixtures; local sanctions screening against downloaded UK/OFAC/EU lists; manual attestation for all else; CoP/VoP delegated to the human payer.

---

## Module 5. Signed approval, audit log and evidence

### A. Reference data and standards

| Standard | Verified facts | Tag / URL |
|---|---|---|
| RFC 3161 (TSP) | TimeStampToken = CMS signed data wrapping TSTInfo (hash, time, serial, TSA policy); request has hash, optional nonce; proves a datum existed before a time. | [opened] https://www.rfc-editor.org/rfc/rfc3161 |
| RFC 9162 (CT 2.0) | Append-only Merkle logs; inclusion and consistency proofs (consistency proof at most ceil(log2 n)+1 nodes); domain-separated leaf/node hashes; changes vs RFC 6962: algorithm agility, CMS precertificates, OID log IDs. | [opened] https://www.rfc-editor.org/rfc/rfc9162 |
| RFC 6962 | Original CT. | [memory] |
| eIDAS (EU 910/2014) | Levels SES/AdES/QES and qualified time-stamp presumption: text fetch empty. | blocked https://eur-lex.europa.eu/eli/reg/2014/910/oj/eng; previous pass [snippet] |
| UK eIDAS | The Electronic Identification and Trust Services for Electronic Transactions Regulations 2016 (SI 2016/696) exist; page opened is structural (supervisory body ICO, penalties); signature legal effect text not read. | [opened, thin] https://www.legislation.gov.uk/uksi/2016/696/contents |
| C2PA | Not researched. | not found |
| NIST AI RMF | AI RMF 1.0 released 2023-01-26 (Govern, Map, Measure, Manage); Generative AI Profile NIST-AI-600-1 2024-07-26; framework under revision per page. | [opened] https://www.nist.gov/itl/ai-risk-management-framework |

### B. APIs

| Item | Facts | Tag |
|---|---|---|
| Sigstore Rekor v2 | Tile-backed on Tessera (not Trillian); yearly shard URLs like `log2025-1.rekor.sigstore.dev` distributed via TUF, do not hardcode; only `hashedrekord` and `dsse` entry types; Cosign 2.6.0+. The public log is public: never submit customer data. | [opened] https://blog.sigstore.dev/rekor-v2-ga/ |
| Tessera | Go library for tile-based logs; GCP, AWS, POSIX drivers; Apache 2.0; Beta v0.2.0; witnessing support. Self-host option for a private tenant log. | [opened] https://github.com/transparency-dev/tessera |
| Trillian | Superseded by Tessera per above. | [opened] same |
| OpenTimestamps | Site unreachable (DNS). Bitcoin-anchored, free: previous pass. | blocked; [snippet] |
| DocuSign eSignature API | Pricing page 404. Third-party figures from previous pass conflict. | blocked; unverified |
| Adobe Sign | Not found. | not found |
| Yousign | Pricing URL redirected to a different domain; not followed. | blocked |
| Qualified TSA prices | Not found. | not found |
| Gmail `users.watch` | Renew at least every 7 days; max 1 notification/second per watched user, excess dropped; payload only email address and `historyId`, then `history.list` to fetch changes. | [opened] https://developers.google.com/workspace/gmail/api/guides/push |

### C. Competitors

| Vendor | Audit/approval claim | Tag |
|---|---|---|
| Zip | "rich audit trail with reasoning and a record of approvals"; human-in-the-loop approvals configurable; same roles as users. | [opened] https://www.zip.com/ai |
| Ramp | Alert dismissals audit-logged; agent writes in Audit Log (previous pass). | [opened] bill-pay page; [snippet] |
| Tipalti | "audit trails, reporting, and document storage"; 20+ role permissions for segregation of duties. | [opened] https://tipalti.com/en-uk/accounts-payable-software/financial-compliance/ |
| All above | Hash-chained, signed or externally anchored logs: not stated by any page opened. | not found |

### D. Integrations and verdict
- Own per-tenant hash chain (already in repo): keep. Add checkpoint signing and daily head-hash anchoring.
- RFC 3161 TSA: adopt only if a customer needs legal weight; provider price not found. OpenTimestamps: free, no legal presumption claimed; site unverified this pass.
- Rekor v2 public instance: head hashes only, optional. Tessera POSIX/cloud log: only if auditors need third-party witnessing; extra operational burden.
- DocuSign/Yousign/Adobe: only if a buyer demands qualified signature on a PO. Default is an in-app Ed25519 signature over the canonical content hash.
- Gmail: store raw RFC 822 message and headers as evidence; watch renewal job needed.

### E. Academic

| Paper | Authors, year, venue | Method | Adaptation | Tag / link |
|---|---|---|---|---|
| Efficient Data Structures for Tamper-Evident Logging | Scott A. Crosby, Dan S. Wallach; 2009; USENIX Security 18th (pp. 317-334 per search) | Merkle-tree history with logarithmic membership and consistency proofs against an untrusted logger | Tenant log gives auditors proofs; publish checkpoints | [opened, no abstract on page] https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident |
| CONIKS: Bringing Key Transparency to End Users | Melara, Blankstein, Bonneau, Felten, Freedman; 2015; USENIX Security 24th (pp. 383-398) | Auditable key directory; users monitor own bindings (<20 kB/day), non-equivocation audit | Approver public-key directory with signed epochs | [opened] https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/melara |
| Certificate transparency design | RFC 9162 above (IETF, 2021) [year memory] | Merkle logs plus proofs | Same primitives for approval log | [opened] |

### Recommended hybrid build (module 5)
- Deterministic: canonical JSON (JCS, [memory]) -> SHA-256 -> Approval = Ed25519 signature over {document hash, mandate hash, approver, expiry}; send-service verifies and refuses mismatch.
- Deterministic: per-tenant append-only chain with prev-hash; Merkle checkpoint daily; anchor via RFC 3161 and/or OpenTimestamps; offline verifier script.
- Model: none in the trust path; summaries are templated from fields.
- Human: approver uses a separate credential (passkey); requester differs from approver above a threshold.

### Min viable version (module 5)
Ed25519 approval + chain + daily checkpoint with one external anchor (RFC 3161 if a TSA is available, else OpenTimestamps), export bundle (events, raw emails, proofs) verified by one offline script. No e-signature vendor.

---

## Module 6. Fraud, injection and anomaly defence

### A. Reference data and standards

| Source | Verified facts | Tag / URL |
|---|---|---|
| OWASP Top 10 for LLM Apps 2025 | LLM01 Prompt Injection, 02 Sensitive Information Disclosure, 03 Supply Chain, 04 Data and Model Poisoning, 05 Improper Output Handling, 06 Excessive Agency, 07 System Prompt Leakage, 08 Vector and Embedding Weaknesses, 09 Misinformation, 10 Unbounded Consumption. | [opened] https://genai.owasp.org/llm-top-10/ |
| OWASP Top 10 for Agentic Applications 2026 | Released 2025-12-09, peer-reviewed; item list is in a download, not on the page. | [opened, thin] https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |
| NCSC phishing guidance | Four layers: block before delivery (DMARC, SPF, DKIM, filtering), support reporting, limit impact (MFA, patching, least privilege), respond fast; training alone insufficient. | [opened] https://www.ncsc.gov.uk/guidance/phishing |
| FBI IC3 BEC PSA (2019) | Verify account-change requests via secondary channel; check sender domain, misspelled link domains; keep patches. | [opened] https://www.ic3.gov/PSA/2019/PSA190910 |
| FBI IC3 2024 report | BEC totals: PDF is image-only, not read. A search summary quoted ">$2.9 billion" [snippet, unverified]. | blocked; https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf |
| NIST AI RMF / 600-1 | see module 5. | [opened] |
| EchoLeak CVE | Not verified. | not found |

### B. APIs

| API | Facts | Tag |
|---|---|---|
| Gmail API | Headers readable incl. `Authentication-Results` [memory]; push via `users.watch` per module 5. | [opened] push; [memory] headers |
| Google Safe Browsing | Non-commercial use only; commercial use must use Web Risk; free; warnings must be qualified ("suspected", "possible") with attribution "Advisory provided by Google". | [opened] https://developers.google.com/safe-browsing/v4/usage-limits |
| Google Web Risk | Lookup API `uris.search` free up to 100,000 calls/month then $0.50 per 1,000 up to 10M; Update API `threatLists.computeDiff` free; `hashes.search` confirm $50 per 1,000. Pricing page fetch gave no content; figures from search. | [snippet] https://cloud.google.com/web-risk/pricing |
| VirusTotal | Public API 4 requests/min, 500/day, not for commercial products or services; premium has no such caps and an SLA. A commercial product must use premium (price not found). Note rule 4: never fetch vendor links; hash-lookups of attachments only. | [opened] https://docs.virustotal.com/reference/public-vs-premium-api |
| Third-party BEC API | None verified. | not found |
| Model Armor / Cloud DLP | Not verified. | not found |

### C. Competitors

| Vendor | Method stated | Tag |
|---|---|---|
| Ramp | AI risk scoring on "dozens of risk factors": changed bank details, unusual amount, unverified vendor; human must verify; confirm via known phone. | [opened] https://support.ramp.com/bill-pay-fraud |
| Tipalti | Tipalti Detect pattern network, blocks repeated account creation, screening before each payment. | [opened] |
| Basware/Trustpair | Bank-account ownership validation at change and before payment; duplicate/overpayment detection historically. | [opened] ITPro URL above |
| Coupa | via Trustpair connector. | [snippet] |
| Zip, Didero, Fairmarkit, Paystand | No injection or fraud defence stated on pages opened. Paystand page has nothing relevant. | [opened] |
| Aron, Brex | Not found / blocked. | |
| Prompt-injection defence of any competitor | Not found. | |

### D. Integrations and verdict
- Header authentication (SPF/DKIM/DMARC result), Reply-To mismatch, display-name vs domain, lookalike distance to known supplier domains: self-built; adopt as risk features, never as proof (NCSC says layers).
- Web Risk: acceptable for domain reputation if no link is fetched (rule 4); free tier 100k calls/month [snippet]. Safe Browsing and VirusTotal public are barred for commercial use [opened].
- CoP/VoP via bank partner: best defence against fake bank details.
- Model-based BEC classifier: second opinion only; can escalate but not clear.

### E. Academic methods (all opened unless stated)

| Paper | Authors, year, venue | Method | Adaptation |
|---|---|---|---|
| Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection | Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz; 2023; arXiv cs.CR | Shows instructions hidden in retrieved data hijack LLM apps (Bing Chat etc.) | Treat every supplier email/PDF as an attack vector; build hostile-email corpus. https://arxiv.org/abs/2302.12173 |
| Defeating Prompt Injections by Design (CaMeL) | Debenedetti, Shumailov, Fan, Hayes, Carlini et al.; 2025; arXiv cs.CR | Separates control and data flow from the trusted query; capabilities; 77% of AgentDojo tasks with provable security vs 84% undefended | Planner sees only trusted request; vendor text is tainted data. https://arxiv.org/abs/2503.18813 |
| Defending Against Indirect Prompt Injection Attacks With Spotlighting | Hines, Lopez, Hall, Zarfati, Zunger, Kiciman; 2024; arXiv | Transforms (delimiting, datamarking, encoding) untrusted input to signal provenance; ASR from over 50% to under 2% on GPT models | Datamark vendor text in extractor prompt; defence in depth only. https://arxiv.org/abs/2403.14720 |
| StruQ: Defending Against Prompt Injection with Structured Queries | Chen, Piet, Sitawarin, Wagner; USENIX Security 2025 | Secure front-end separates prompt and data; model fine-tuned to ignore instructions in data | Needs open-weights fine-tune; not v1. https://arxiv.org/abs/2402.06363 |
| SecAlign | Chen, Zharmagambetov, Mahloujifar, Chaudhuri, Wagner, Guo; ACM CCS 2025 | Preference optimisation on injected vs clean outputs; injection success under 10% | Same: future option. https://arxiv.org/abs/2410.05451 |
| The Instruction Hierarchy | Wallace, Xiao, Leike, Weng, Heidecke, Beutel; 2024; arXiv | Trains model to prioritise system over user over third-party instructions | Provider-side property; do not rely on it for gates. https://arxiv.org/abs/2404.13208 |
| A Modular and Adaptive System for Business Email Compromise Detection (CAPE) | Brabec, Šrajer, Starosta, Sixta, Dupont, Lenoch, Menšík, Becker, Boros, Pop, Novák; 2023; arXiv | Ensemble of independent models across text, images, metadata, communication context; Bayesian adaptation; in production 2+ years | Feature list for header/context checks. https://arxiv.org/abs/2308.10776 |
| Semantic Superiority vs. Forensic Efficiency (BEC) | Adjei, Ayivor; 2025 (rev. 2026-04); arXiv | DistilBERT vs CatBoost psycholinguistic features on 7,990 emails, adversarial examples synthetic | Weak evidence (synthetic data); cheap CatBoost-style features only as a scorer. https://arxiv.org/abs/2511.20944 |
| Selective Classification for Deep Neural Networks | Geifman, El-Yaniv; 2017; arXiv (NIPS 2017 per [memory]) | Abstain below a confidence threshold to guarantee a chosen risk | Extractor abstains to human when below calibrated threshold. https://arxiv.org/abs/1705.08500 |
| InjecAgent, AgentDojo, Beurer-Kellner patterns, Progent, AgentHarm | previous pass [opened] | benchmarks and patterns | see 05-mandate-rfq-layer.md |

Invoice/payment anomaly detection papers: not found as arXiv/venue pages (search returned vendor blogs only). A vendor-blog snippet mentions Isolation Forest, LODA and OCSVM ensembles [snippet, unnamed source]; use Isolation Forest-style price-band checks only after labelled data exists [memory].

### Recommended hybrid build (module 6)
- Deterministic: extractor output is schema-only; no link fetch; quote/PO tools cannot be invoked from vendor-derived text; hard holds on bank-detail change, new payee, sender-domain change, Reply-To mismatch, urgency plus changed amount, duplicate invoice number/hash, currency/UoM mismatch, price outside history band.
- Model: quarantined extractor with grounding check and spotlighting-style datamarking; separate risk scorer may only raise severity.
- Human: reviews flagged items; callback to number in the verified record for bank changes.
- Release gate: hostile-email regression suite, runs offline with a stubbed model.

### Min viable version (module 6)
Existing quarantine + bank-change rules; add SPF/DKIM/DMARC result features, lookalike-domain distance, duplicate and price-band rules, abstain-to-human threshold, and a 100+ case hostile suite (stubbed LLM). No external reputation API in v1.

---

## Key findings
1. Free official stack confirmed: Companies House (API key, 600/5 min), HMRC VAT v2 (OAuth, verified-check reference number, ~2-week approval), UK Sanctions List (single list since 2026-01-28), OFAC SLS free.
2. VIES limits are undisclosed; GLEIF terms not confirmed from its own pages.
3. CoP is PSP-gated; a non-bank needs an aggregator. Price not found.
4. Commercial-use traps: Safe Browsing (non-commercial) and VirusTotal public API (no commercial) are barred; Web Risk is the legal alternative.
5. Rekor v2 is public, so only head hashes may go there; Tessera is an Apache 2.0 self-host option.
6. No competitor page opened documents hash-bound approvals or injection defence.

## Unverified
eIDAS/UK signature legal effect; EU VoP rules; VIES rate numbers; GLEIF licence; DocuSign/Yousign/Adobe/Creditsafe/Orbis/D&B prices; OpenTimestamps this pass; Web Risk pricing page itself; FBI 2024 BEC totals; EU FSF token; OWASP agentic item list; C2PA; invoice-anomaly papers; Brex/Aron.

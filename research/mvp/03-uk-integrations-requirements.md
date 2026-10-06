# UK integrations and data connections for a buy-side RFQ agent MVP

Research date: 2026-10-06. Scope: email-first buy-side RFQ agent for UK (England) industrial parts buyers and refurbishment/trade buyers. Product-market fit is unproven; nothing here is a marketing claim, and no customer has been asked what they use. Where I say "buyers need X", the evidence is usually about the vendor's API, not about buyer demand, and I say so.

## 0. Method, tags and limits

- Tags: **[opened]** = page fetched this session (the fetch tool returns a model-written summary, not raw text, so exact legal wording needs human re-reading); **[snippet]** = seen only in a search-result summary (often vendor blogs, weaker); **[memory]** = my background knowledge, unverified today.
- About 45 URLs returned usable content; roughly 20 more returned 403/404/DNS errors or JavaScript shells that the fetch tool could not read. Failures are listed in section 10. I did not work around any block, scrape, or log in.
- Not found / blocked, up front: Xero Purchase Orders API field reference (page returned only its title); Xero certification requirements and developer-terms page (Not Authorized); Sage Accounting API reference (403); QuickBooks Online throttling, PurchaseOrder entity and developer terms (page truncated, unreadable); Fiix developer site (DNS failure) and FAQ (403); Limble and Joblogic API docs (not readable); Gas Safe terms (bot wall); TrustMark terms (404); Peppol.org pages (404); HMRC VAT-check API page (404 on the path tried); Twilio UK SMS pricing (404); NCSC passkey page (404).
- Repo rules that bound the recommendations: R1 (no send without an Approval; the planner holds no mail credentials), R3 (provenance), R4 (inbound content untrusted; no link fetching), R5 (Decimal money with UoM/currency), R7 (tenant isolation), and CLAUDE.md "no marketing claims". The stack map says OAuth tokens live in Vault, adds Nango "only past three OAuth providers", and already lists `email-alias` and `csv-import` as the pack's integrations (docs/architecture/ai-employees-stack-map.md [opened, local]).
- Context from the repo: the stack map's U11 says "CSV first; Nango when the third OAuth provider arrives", and S8 says the inbound email provider must be one with inbound parsing [opened, local]. The lean canvas lists "field-service software partners" as a channel and "email infrastructure" as a cost; it has no integration requirement evidence yet [opened, local].

## 1. Executive summary

1. **Day-one must-haves are small and mostly not OAuth integrations.** An inbound alias address (forward or CC the agent), an outbound sender behind the send-service, CSV/XLSX import of parts and supplier lists, and a PO export file (CSV plus PDF) that a buyer can load into their accounting system or send to a supplier. This matches the repo's current manifest (`email-alias, csv-import`).
2. **Do not start with Gmail/Microsoft mailbox OAuth.** Gmail read scopes are classed Restricted and trigger an annual third-party security assessment (CASA) [opened]. Microsoft Graph delegated mail scopes do not need admin consent per the permissions table, but app-only mail scopes do [opened], and tenants can disable user consent [opened]. Alias/forwarding avoids both and fits R1/R4.
3. **Accounting push is "should", not "must", and Xero is the first candidate** because the API is open to any developer, but it carries a certification and (from 2 March 2026) a tiered fee, and a ban on using API data to train or fine-tune AI models [opened]. The PO payload should be designed from day one so that a CSV export and a later Xero push use the same object.
4. **CMMS/FSM connectors are "later".** Several gate API access to higher paid plans (MaintainX Premium/Enterprise [snippet]; Limble Premium+/Enterprise [snippet]; UpKeep Enterprise [opened]; Fiix limits calls per user licence per day [snippet]). That is a blocker for small UK buyers and for a pilot.
5. **Peppol and cXML are "later" for a buy-side RFQ agent.** UK e-invoicing is about VAT invoices, not RFQs or POs; the mandate date and Peppol statement come mostly from vendor blogs, with the primary gov.uk consultation response saying 2029 and a roadmap at Budget 2026 [opened]. Peppol BIS Billing 3.0 covers invoices and credit notes, not orders [opened].
6. **Supplier data: Companies House (free key, 600 requests per 5 minutes [opened/snippet]) and HMRC VAT-number check are cheap "should" items** for vendor verification (an R12 adjacent control). Trade registers (Gas Safe, NICEIC, TrustMark) are link-out only; no data route found.
7. **WhatsApp: not in the MVP.** Opt-in rules, templates and 24-hour windows apply [opened], and Meta banned general-purpose AI chatbot distribution from January 2026 [snippet]; a buyer-to-supplier RFQ agent is not obviously covered either way. Evidence that UK trades buy by WhatsApp: not found.
8. **Identity:** Email magic link or password plus TOTP is enough to start; Microsoft and Google SSO is a "should" once a customer with a tenant asks; passkeys for approvers are a good fit for R11 and cheap (WebAuthn), recommended as "should".

## 2. Accounting and purchase orders

### 2.1 Findings by product

| Product | API route and auth | Rate limits | Approval / partner terms | AI and data-use terms | Price (public) | UK relevance |
|---|---|---|---|---|---|---|
| **Xero** | Accounting API; OAuth 2.0; Purchase Orders resource exists (page unreadable this session; resource list from [memory]) | Per tenant: 5 concurrent, 60/min, 5,000/day; 10,000/min per app across tenants; 429 with Retry-After; limits cannot be raised [opened: developer.xero.com/faq/limits] | App certification required for Core tier and above; Plus and above also need an initial and annual security assessment [opened: developer.xero.com/pricing]. Certification page itself: not found (Not Authorized). Uncertified apps capped at 25 connections [snippet: search summary of the same FAQ]; the current tier table instead lists 5 connections on the free Starter tier [opened], so the older 25 figure may be superseded. | New terms prohibit using API data to "train or fine tune any artificial intelligence models including machine learning tools, large language models or predictive analytics tools"; automated monitoring, audits twice a year, suspension on breach; 24-hour breach reporting to Xero [opened: developer.xero.com/xero-developer-platform-terms-conditions]. Live inference on a user's own data is described as allowed only by a third-party commentary [snippet]; treat as unconfirmed. | AUD, not GBP: Starter free (5 connections); Core 35/month (50 connections, 10 GB egress); Plus 245 (1,000, 50 GB); Advanced 1,445 (10,000, 250 GB); overage 2.40 AUD per GB; effective 2 March 2026 for existing developers [opened: developer.xero.com/pricing and /faq/pricing-and-policy-updates] | Xero is widely used by UK small businesses [memory]; no UK share figure found. Xero app store listing requires "Sign up with Xero" [opened]. |
| **Sage Business Cloud Accounting** | Sage Accounting API v3.1; OAuth 2.0 [memory]; purchase endpoints listed by a third-party guide include suppliers, purchase invoices and purchase credits; a `purchase_orders` endpoint is described only as an "illustrative pattern" and **not confirmed** [opened: cleverence.com guide, third party] | Third-party sources disagree: 1,296,000 requests per app per day and 150 concurrent [snippet], versus 60/min per application [snippet]. Official page: blocked (403). | Not found | Not found | Not found | UK is Sage's home market [memory]; a PO endpoint is unconfirmed, so bills/suppliers may be the only reliable object. |
| **Sage Intacct** | REST API recommended over legacy XML API; Purchasing module with "Purchasing Transactions" [opened: developer.intacct.com/api/] | Not found | Web services sender ID / partner requirements: not found on the page opened [memory says a sender ID is needed; unverified] | Not found | Not found | Mid-market/enterprise finance system; unlikely for the stated segments' day one. |
| **QuickBooks Online (UK)** | Intuit Developer; OAuth 2.0; PurchaseOrder entity [memory] | Throttle docs unreadable [not found]. Search summary: writes mostly unmetered "Core" calls, reads/queries/reports metered "CorePlus" [snippet] | Production review required; marketplace estimate 10 business days technical, up to 30 security, 5 marketing (estimates, not SLAs) [snippet] | Developer terms require NIST compliance and Responsible AI principles for AI/LLM use, user consent, and processor agreements before sending QBO data to a hosted LLM [snippet; primary page unreadable] | Builder tier free [snippet] | QuickBooks is sold in the UK [memory]; no UK share found. |
| **FreeAgent** | REST API, OAuth 2.0, JSON/XML; resources include bills, contacts, estimates, invoices, bank, VAT returns; **purchase orders not listed** [opened: dev.freeagent.com] | Not found | Apps registered via a developer dashboard; users approve through OAuth [opened]; any partner review: not found | See "API Terms" (not read) | Not found | UK-focused small-business accounting [memory]; MTD for Income Tax software [memory]. |

Interpretation: of the five, only Xero is confirmed to expose a PO resource (from memory, not re-verified) and have a public developer programme with published limits. FreeAgent has bills but no listed PO resource [opened]. **Recommendation: write POs to a neutral file first; add Xero as the first push connector; treat Sage/QuickBooks/FreeAgent as "bill/contact sync or CSV only" until their PO routes are verified.**

### 2.2 Making Tax Digital (MTD) relevance

- MTD for Income Tax Self Assessment starts 6 April 2026 for qualifying income over 50,000 GBP, 6 April 2027 over 30,000 GBP, and from 6 April 2028 over 20,000 GBP; users must keep digital records and use software that connects to HMRC [opened: gov.uk MTD ITSA page]. That is the reason small trade buyers (sole traders) are moving to bridging/cloud software such as Xero, FreeAgent or QuickBooks [memory for product names].
- MTD for VAT already applies to VAT-registered businesses [memory, not re-opened].
- Relevance to this product: an RFQ agent is **not** MTD software and should not record transactions. Its relevance is that the buyer's source of truth is a digital ledger; the agent's PO and quote data should be exportable in a way the buyer's accounting software can ingest. It should never claim to make a buyer MTD-compliant.

### 2.3 What a PO export must contain

No primary source gives a mandatory PO field list for UK buyers (a PO is not a regulated document in the way a VAT invoice is). The list below is a design proposal assembled from [memory] of Xero and typical ERP fields, plus the VAT invoice fields that the matching bill must eventually carry [opened: gov.uk Notice 700/63].

| Field | Why | Source/status |
|---|---|---|
| PO number (unique, sequential per buyer entity) | Matches bill to PO; the VAT invoice also needs a sequential unique number [opened] | Design + opened |
| Buyer legal entity name, registered address, VAT number | Needed for the supplier's VAT invoice [opened: invoice must show customer information] | Opened (invoice side) |
| Supplier name, Companies House number or VAT number where known, contact, delivery and remit-to details | Verification and R12 (remit-to changes need admin with callback) | Design |
| Issue date, required-by date, delivery address | Operational | Design |
| Per line: buyer part number, supplier part number, description, quantity, UoM, unit price (Decimal), currency, VAT rate or "VAT status unknown", line total | R5 (Decimal with UoM/currency); the invoice side needs unit price, quantity and VAT rate [opened] | Design + opened |
| Price basis: ex VAT / inc VAT, delivery and carriage terms, payment terms, quote reference and date, validity | The lean canvas names "VAT basis, units, scope exclusions, delivery and credit terms" as the quote comparability problems [opened, local] | Opened (local) |
| Provenance: Approval ID and hash, approver, approval time, source quote ID | R1, R3, R6 audit link | Repo rules |
| Tier A or SubstitutionApproval reference | R2 | Repo rules |
| Currency and totals: net, VAT, gross in GBP unless a profile says otherwise | Profile-driven; never hard-code | CLAUDE.md |

Formats: CSV (one header row, one row per line), PDF for suppliers, and a JSON object for later accounting push. VAT invoice guidance accepts XML-based standards and PDF [opened]. Retain records six years [opened: Notice 700/63 on invoice retention].

## 3. Email

### 3.1 Mailbox access (read/send on the buyer's own account)

| Option | Scope / permission | Verification and assessment | Limits | Data-use terms | UK data residency |
|---|---|---|---|---|---|
| **Gmail API** | `gmail.readonly`, `gmail.modify`, `gmail.metadata`, `gmail.compose`: Restricted; `gmail.send`: Sensitive [opened: developers.google.com/gmail/api/auth/scopes] | Restricted scopes need OAuth app verification and, for apps that store data on servers, an annual security assessment through CASA (AL1/AL2 by risk), producing a Letter of Validation; revalidated every year, level may rise [opened: support.google.com/cloud/answer/13465431]. Cost and calendar time: not found. | Not read | Limited Use: data limited to user-facing features prominent in the UI; revoke/suspend for non-compliance [opened: API Services User Data Policy]. Google does not name AI training in the page, but the Limited Use rule effectively bars it (the fetch tool's inference; re-read legal text). | Google Workspace data regions offer United States, European Union or No preference; **UK not listed** [opened: knowledge.workspace.google.com] |
| **Microsoft 365 / Graph** | Mail.Read, Mail.ReadWrite, Mail.Send: delegated do not require admin consent; application permissions (all mailboxes) do [opened: Graph permissions reference]. Mail.ReadBasic excludes bodies and attachments [opened]. | Multitenant apps: users or admins consent; tenant admins can disable user consent, in which case admin consent is always required [opened: Entra multitenant guide]. Publisher verification page: 404 (not found). Microsoft 365 App Compliance/annual assessment: **not found** (the task premise cannot be confirmed). | Global 130,000 requests per 10 seconds per app; Outlook per-mailbox limits not read [opened: throttling-limits; Outlook-specific figure is [memory]] | Microsoft Graph terms: not read | **UK is a Local Region Geography** for Advanced Data Residency, a paid add-on needing 100% seat coverage, with migration up to 12 months [opened: advanced-data-residency] |
| **Outlook add-in** | Office add-in with manifest, task pane or event activation; works in Outlook on web, Windows (new and classic), Mac, iOS, Android; acquired from Microsoft Marketplace or sideloaded by admin/user [opened: outlook-add-ins-overview] | Add-ins do not activate on IRM-protected/encrypted items on mobile, delivery reports, attached .eml, or in shared mailboxes and archive mailboxes unless later requirement sets (shared mailbox from 1.13) [opened]; not supported on Gmail accounts in Outlook [opened] | n/a | Marketplace requirements: not found | Runs on the add-in host's servers; same residency questions as the app |

Implication: reading a buyer's Gmail needs Restricted scopes and a yearly assessment. For an email-first MVP, ask the buyer to **forward or CC** to an alias, or send RFQs from the alias with the buyer in Reply-To and CC. This also keeps R1 (the planner holds no mail credentials) and R4 (untrusted inbound content) simple. A Gmail/Outlook "draft to my own drafts folder" mode, via `gmail.compose` or `Mail.ReadWrite`, is a later option and runs into the Restricted-scope assessment for Gmail.

### 3.2 Inbound alias and transactional providers

| Provider | Inbound route | Limits and price (public) | UK/EU data region | Notes |
|---|---|---|---|---|
| **Postmark** | Inbound server: send mail to a Postmark address or forward your domain; webhook JSON [opened: postmarkapp.com/developer/user-guide/inbound] | Inbound included on Pro and Platform plans only, not Free/Basic; USD 15 Basic, 16.50 Pro, 18 Platform for 10,000 emails/month; 45 to 365 day retention [opened: pricing] | Region selection **not found** on the pricing page | Webhook payload size, retry, spam handling: referenced but not read |
| **Amazon SES** | Receipt rules to S3, SNS, WorkMail, Lambda; spam/virus scanning; Spamhaus-based blocking [opened: docs.aws.amazon.com/ses] | Account sandbox defaults 200 emails per 24 hours and 1 per second, adjustable [opened: SES endpoints and quotas] | **Europe (London) eu-west-2 supports email receiving and SMTP** [opened: AWS General Reference SES endpoints] | Needs engineering (S3/SNS plumbing); strongest verified UK residency option among the four |
| **SendGrid (Twilio) Inbound Parse** | MX `mx.sendgrid.net` priority 10 on a dedicated subdomain; webhook; limit message plus attachments to 30 MB; raw MIME option; DKIM/SPF results in payload [opened] | Price: not found | EU region for Inbound Parse: **not found** | Spam score in payload helps R4 |
| **Mailgun** | Routes, forward and store; stored messages retrievable via API [opened, only the "viewing stored messages" page read] | Not found | Not found | Opened page covered storage retrieval only; routes docs not read |

The stack map already notes Resend is outbound-focused and inbound must be verified [opened, local]. Recommendation: SES London if UK residency for raw email matters to the first pilot; otherwise Postmark Pro for speed. Both need a decision after asking the first customers. Evidence that UK buyers require UK-resident email processing: **not found**. Note that Supabase region and the LLM provider region also matter and were out of scope here.

## 4. Maintenance, field-service and CMMS systems

Goal: read assets, parts, POs, suppliers. Most primary doc sites for these products are JavaScript pages the fetch tool could not read, so many rows rest on search snippets (often third-party API directories). Treat plan-gating claims as unverified until a vendor page is read.

| Product | API availability | Auth | Rate limits | Plan gate / approval | Objects for assets, parts, POs, suppliers | UK relevance |
|---|---|---|---|---|---|---|
| **Fiix** (Rockwell) | REST plus RPC | API access keys, OAuth2 [snippet] | 1,000 calls per day per user licence [snippet] | FAQ page blocked (403); developer site DNS failure | Assets, work orders, parts, purchase orders, users [snippet] | Used by manufacturers [memory]; UK share not found |
| **MaintainX** | REST API v1; Bearer token, multi-organisation, webhooks, polling guidance [opened: help.getmaintainx.com/build] | Bearer | Rate-limit guidance exists; numbers not read [opened] | "Premium and Enterprise only" [snippet, third party]; **unverified** | Purchase orders list/get, vendors, parts, assets [snippet] | UK customer base: not found |
| **Limble** | REST API V2; regional endpoints including Europe [snippet] | Basic auth [snippet] | Not found | Premium+ and Enterprise [snippet, third party] | Assets, parts, purchase orders, vendors, webhooks [snippet] | Not found |
| **UpKeep** | REST v2, session tokens from email/password via `POST /api/v2/auth/` [opened: developers.onupkeep.com] | Session token | 429 with message when exceeded; numbers not given [opened] | "The UpKeep API is enabled only for accounts on the Enterprise Plan" [opened] | Users, customers, vendors, assets, work orders, PM, parts, locations, meters, purchase orders, webhooks [opened] | Not found |
| **Joblogic** (UK FSM) | Marketed as "an API" plus a 70+ app marketplace; integrates with Xero, Sage, QuickBooks; stock control and purchase orders are core features [snippet]; official docs: not found/blocked | Not found | Not found | Not found | PO and stock features exist; API coverage of POs not found | UK-focused FSM [snippet] |
| **Simpro** | UK marketplace lists Screwfix, Toolstation, Travis Perkins, ADI and "Simplementary Procure" with catalogue and PO integration; live pricing and stock inside Simpro [snippet; marketplace page itself returned 403] | Not found | Not found | Marketplace partner terms: not found | Purchase orders can be created and sent online [snippet: Simpro help pages] | UK/Ireland marketplace [snippet] |
| **BigChange** (UK FSM) | REST API with OpenAPI spec (108 paths cited by a directory); OAuth; webhooks; developer portal; "generous free pricing tier" [opened: bigchange.com/extra/rest-api; snippet for spec details]; docs page: 403 | OAuth [snippet] | Not found | "Secure key management", Partner Network [opened] | Jobs, contacts, resources, vehicles, assets, invoices [snippet]; PO/supplier endpoints: not found. Xero contact sync allows supplier sync [snippet] | UK-focused [memory] |
| **ServiceTitan** | Developer portal covers tenant access, inventory purchase orders and vendors [snippet-level; fetch summary generic, treat as unverified] | OAuth client credentials [memory] | Not found | App approval needed [memory] | Purchase orders, vendors [unverified] | UK availability: the fetch summary said UK operations are supported; **not verified**; ServiceTitan's UK footprint is [memory] small |

Implications:
- Day one should read **none** of these live. Ask buyers to export an assets/parts CSV and a supplier list. That is what the repo already plans (`imports`, U11).
- If a first customer is on one of these, the likeliest working path is a one-way PO or quote push, not a read connection. Plan gating (Enterprise-only at UpKeep [opened]) will exclude small buyers.
- Simpro's marketplace shows UK merchants already syncing catalogues and POs into Simpro [snippet]; that is a possible partner channel, not a data licence (consistent with the existing price-sources note #37 [opened, local]).

## 5. Procurement formats

| Topic | Finding | Status |
|---|---|---|
| **UK e-invoicing mandate** | The gov.uk consultation response states UK mandatory e-invoicing for VAT invoices from 2029, B2B and B2G where VAT is due; roadmap to be published at Budget 2026; stakeholder design starts January 2026; the response "does not explicitly commit" to Peppol in the text read [opened: gov.uk consultation response]. The consultation was announced 13 February 2025 [opened: gov.uk news]. Vendor blogs claim April 2029 and that Peppol was confirmed as the core network (one gives 23 June 2026) and that a four-corner roadmap is due at the November 2026 Budget [snippet: truecommerce, storecove, vatcalc, spendesk]. | Primary says 2029 and a Budget 2026 roadmap; Peppol confirmation is **[snippet] only**, verify on gov.uk before relying on it |
| **Peppol** | Peppol BIS Billing 3.0 (release shown May 2026) covers invoices and credit notes in UBL, with EN16931 binding and code lists; it does not cover orders [opened: docs.peppol.eu/poacc/billing/3.0]. Peppol.org pages: 404 (not found). | Invoice-side; out of RFQ scope for MVP |
| **UBL Order / Peppol Order** | A separate Peppol specification exists [opened: the Billing page says order transactions are a separate BIS]; not read | Later |
| **cXML / punch-out** | cXML is a protocol for business documents between procurement apps, e-commerce hubs and suppliers; PunchOut and PurchaseOrderRequest are in the spec; version 1.2.071 shown, updated 14 August 2026; governance by SAP Ariba is not stated on the page (my inference) [opened: cxml.org] | Large-merchant punch-out docs for UK merchants: not found |
| **Open Banking** | Out of scope: it concerns payment initiation and account data, not RFQ or PO workflows [memory] | Out of scope |
| **VAT invoice content (the downstream document)** | Sequential number, tax point, supplier name/address/VAT number, customer information, description, unit price, quantity, VAT rate and amounts; XML or PDF accepted; retain six years [opened: gov.uk Notice 700/63] | Informs what the PO should carry for three-way match |

Conclusion: the agent is upstream of the invoice. Do not build Peppol access-point functionality in the MVP. Do make PO line data structured enough that an accounting package, or a later UBL generator, can use it. If a customer wants to receive supplier invoices over Peppol, that is the accounting software's job.

## 6. Identity and SSO

| Item | Finding | Status |
|---|---|---|
| **Microsoft Entra (multitenant sign-in)** | Multitenant registration uses the `/common` or `/organizations` endpoint; first sign-in triggers consent; admins can disable user consent, so admin consent may always be needed; admin consent with `prompt=consent` applies tenant-wide [opened: howto-convert-app-to-be-multi-tenant] | OAuth/OIDC route is standard; a "Sign in with Microsoft" button |
| **Google Workspace / Google sign-in** | Google Identity passkey guidance exists; Workspace data regions have no UK option [opened] | Sign-in itself is not the restricted piece; Gmail scopes are |
| **Passkeys** | Entra supports passkeys (FIDO2, WebAuthn); synced and device-bound; Entra says synced passkeys give "MFA simplicity at scale" and security keys are recommended for highly regulated or elevated-privilege users; if attestation is enforced only device-bound passkeys are allowed [opened: Entra passkeys page]. Google documents passkeys across Android, iOS, web, Chrome [opened: developers.google.com/identity/passkeys]. NCSC page: 404, not found. | Fits R11 (approver must authenticate in session; a link click alone is not enough) |
| **UK SME expectations** | Not found. I located no UK survey of SME SSO or MFA expectations. Anything stronger would be invention. | Not found |

Recommendation: email magic link plus passkey (WebAuthn) for approvers on day one; "Sign in with Microsoft/Google" as a convenience later. Do not request mail scopes at sign-in.

## 7. Supplier and company data

| Source | Access and auth | Limits | Terms and data use | Day-one use |
|---|---|---|---|---|
| **Companies House API** | Free; API key via "Your applications"; HTTP Basic with key as username; GET public data; OAuth 2.0 for functionality needing an end user [opened: developer-specs authorisation guide] | 600 requests per 5 minutes per key; response headers X-Ratelimit-*; small increases on request; may ban without notice apps that regularly exceed or bypass limits; designed for real-time retrieval, not bulk collection [snippet: developer guidelines via search; matches existing note #38] | Open-data licence terms: not read | Verify merchant or supplier legal entity, status, registered address. Store with source and as-of date (R3) |
| **HMRC Check a UK VAT number API** | Requires registering an app on the HMRC Developer Hub, subscribing and accepting terms (about two weeks reported) [snippet: third-party]; two modes, unverified and verified with a reference number [snippet] | Standard 3 requests per second per application; 429 `MESSAGE_THROTTLED_OUT`; rate limits "designed to encourage real-time interactions" [opened: HMRC reference guide] | HMRC terms of use: linked, not read | Verify supplier VAT registration; keep the verified reference as evidence |
| **Gas Safe Register** | Public check page with bot wall; no API found; terms page returned a bot-interruption page and could not be read (blocked) [opened] | n/a | Not found | Link out only; ask Gas Safe for a data agreement if gas-work suppliers matter |
| **NICEIC, TrustMark** | NICEIC: find-a-tradesperson with consumer terms (existing note #41, [opened, local]); TrustMark: terms URL 404 (not found); site describes itself as the Government Endorsed Quality Scheme [opened] | n/a | Not found | Link out only |
| **Google Business Profile APIs** | For merchants or representatives managing their own or client listings; requires a Google account, legitimate business reason, Cloud project and business website URL; "not available to all users"; approval process [opened]. Not a lookup of other businesses | n/a | Business Profile policies: not fully read | Not usable for supplier contact discovery |
| **Google Places API (New)** | Place IDs may be stored indefinitely; other responses may not be cached or stored beyond limited exceptions; attribution required; AI summaries need the disclosure text [opened: Places policies] | Not read | Pre-fetching/caching is prohibited | Possible for one-off lookup at the moment of use, not for building a supplier database. Terms need legal re-read |
| **Merchant trade accounts and ordering routes** | Existing price-source note: no UK merchant API found; Simpro's UK marketplace lists Screwfix, Toolstation, Travis Perkins, ADI [snippet; also existing note rows 17 to 21, [opened, local]]. No merchant punch-out docs found | n/a | Scraping barred (existing note) | Day one: the buyer supplies their own supplier list and emails (CSV). Merchant integrations later, via the buyer's trade account |

Also relevant to supplier outreach but not researched here: UK direct-marketing rules for sole traders (the lean canvas flags this as riskiest assumption 2 [opened, local]).

## 8. Messaging beyond email

| Item | Finding | Status |
|---|---|---|
| **WhatsApp Business Platform (Cloud API)** | OAuth tokens via Graph API; default 80 messages per second per number; pair rate limit of 1 message per 6 seconds to the same user; explicit opt-in needed before template messages; webhooks [opened: developers.facebook.com cloud-api overview]. Policy: business may contact a user only if they gave their number and opted in, with opt-out instructions; commerce sellers responsible for tax [opened: whatsappbusiness.com/policy]. | Opt-in: suppliers are third parties who have not opted in to an AI agent |
| **Pricing** | Per-message by category (marketing, utility, authentication, service); service messages free within 24-hour window; utility messages sent in response to users free; rates are market and currency specific; UK GBP rates not shown on the page read [opened: platform-pricing] | GBP rate: not found |
| **AI policy** | Search summaries: terms effective 15 January 2026 bar AI providers (named: OpenAI, Perplexity, Luzia, Poke) from using the Business Solution when the AI assistant is the primary function; customer-service bots for businesses (FAQs, bookings, order tracking) remain allowed [snippet: several news/blog sources]. The policy page opened did not state an AI provider rule [opened]. The Cloud API page mentions "Meta Business Agent for AI-powered autonomous conversations" [opened]. | Whether an RFQ agent messaging suppliers falls under either category: **not found**; ask Meta/BSP |
| **UK trades' use of WhatsApp for ordering** | Searches returned Travis Perkins and L.E.K. surveys on workload and sourcing, but no figure on WhatsApp ordering; a trade2base blog on WhatsApp Business for tradespeople exists [snippet]; Ofcom page: 403 | **Not found** |
| **SMS** | Twilio UK SMS pricing page: 404, not found. Down-now mode and SMS/phone scripts appear in the repo (U12) as later. Sender ID rules for UK: not found | Later |

Recommendation: no WhatsApp or SMS in the MVP. If pilots show suppliers answer by WhatsApp, log those replies manually (copy/forward into the alias) before building a channel.

## 9. The decision table

Legend: MVP = must (needed to run a pilot), should (add within the first 3 months if a customer asks), later. Evidence strength: strong = primary page opened and on point; medium = primary opened but partial, or primary plus snippet agreement; weak = snippet or memory only; none = not found. Buyer-demand evidence is **none** for every row: no customer has been interviewed; the strength rates the technical/terms facts only.

| # | Integration | Who needs it | MVP | Evidence strength | Blocker or open issue |
|---|---|---|---|---|---|
| 1 | Inbound alias address (forward/CC) | Both segments | **Must** | Medium (Postmark, SES, SendGrid docs opened; buyer behaviour not tested) | Provider choice; UK residency need unknown; Postmark inbound only on Pro+ |
| 2 | Outbound email via send-service from alias domain (SPF/DKIM/DMARC) | Both | **Must** | Medium | R1 design; deliverability; direct-marketing rules for sole traders |
| 3 | CSV/XLSX import: parts, assets, supplier list | Both | **Must** | Medium (repo plan; CMMS API plan gates support this) | Column mapping; buyers' data quality |
| 4 | PO export: CSV + PDF (+ JSON) | Both | **Must** | Medium (VAT invoice fields opened; PO fields are design) | No UK-mandated PO format; field list needs buyer review |
| 5 | Quote ingestion from PDF/Excel attachments | Both | **Must** | Weak for UK specifics (repo spec) | Parsing sandbox; not an integration but the data connection |
| 6 | Approver sign-in with email link + passkey | Both | **Must** (passkey optional at launch) | Medium (Entra/Google passkey docs) | R11 flow design |
| 7 | Companies House lookup | Both (supplier check) | **Should** | Strong (auth, limits) | Real-time use only; no bulk |
| 8 | HMRC VAT number check | Both | **Should** | Medium (limits opened; endpoint page 404; terms unread) | Developer Hub approval about two weeks [snippet] |
| 9 | Xero PO/bill push | Buyers on Xero | **Should** | Medium (limits, pricing, AI terms opened; PO schema unopened) | Certification and fees; AI-training ban; 5-connection Starter cap |
| 10 | Sign in with Microsoft / Google | Customers with tenants | **Should** | Medium | Admin consent where user consent disabled |
| 11 | Gmail/Outlook "save draft / read thread" mailbox mode | Buyers who live in their inbox | **Later** | Strong on the barrier (Restricted scopes, CASA annual) | Gmail annual assessment; Graph admin consent |
| 12 | Outlook add-in (forward to alias button) | Microsoft 365 buyers | **Later** | Medium (platform doc opened) | Marketplace listing; not Gmail |
| 13 | Sage, QuickBooks, FreeAgent push | Buyers on those | **Later** | Weak to medium (Sage PO endpoint unconfirmed; QBO/FreeAgent PO not confirmed) | Unverified PO endpoints; reviews |
| 14 | Sage Intacct | Larger buyers | **Later** | Weak | Segment mismatch |
| 15 | CMMS reads: MaintainX, Limble, UpKeep, Fiix | Industrial maintenance teams | **Later** | Weak (snippets; UpKeep Enterprise gate opened) | Plan gating; Nango at third OAuth provider |
| 16 | FSM: Joblogic, Simpro, BigChange, ServiceTitan UK | Contractors | **Later** | Weak | Docs unreadable; partner programmes unknown |
| 17 | Merchant catalogue/PO routes (via Simpro marketplace, trade accounts) | Contractors | **Later** | Weak | No public merchant API found |
| 18 | Peppol access point / UBL / cXML | Larger buyers; all after 2029 for invoices | **Later** | Medium for UK direction (gov.uk opened), weak for Peppol confirmation | Invoice-side only; roadmap at Budget 2026 |
| 19 | WhatsApp Business | Trades (assumed) | **Later** | Weak (policy summaries; usage evidence not found) | Opt-in; AI-provider clause ambiguity |
| 20 | SMS | Trades | **Later** | None | Pricing/sender rules not found |
| 21 | Gas Safe / NICEIC / TrustMark data | Regulated trades | **Later** (link-out now) | Weak | No data route found; terms unread |
| 22 | Google Business Profile / Places for contact discovery | Both | **Do not build** for storage | Medium (Places caching rules opened; Business Profile is own-listing only) | Terms bar caching |
| 23 | Open Banking | None | **Out of scope** | Memory | Not an RFQ concern |

## 10. Recommended MVP integration set

**Build:**
1. Inbound email alias with sender allow-list, DMARC/SPF capture, raw message to Storage, attachments to the quarantined parser. Pick SES London or Postmark Pro after asking the first pilot about residency.
2. Outbound send-service on the alias domain with Approval-bound sends only.
3. `imports`: CSV/XLSX for parts, assets and suppliers with a mapping step.
4. PO draft export: CSV and PDF; one internal JSON model with Decimal money, UoM and currency, ready for an accounting push.
5. Approver authentication with an email link plus a WebAuthn passkey.

**Add after the first paid pilot, only on request:** Companies House and HMRC VAT checks; Xero push (budget for certification and the Xero AI-training clause: never feed Xero data into model training, evals or embeddings); Microsoft/Google sign-in.

**Keep out until evidence arrives:** mailbox OAuth, CMMS/FSM connectors, Peppol, cXML, WhatsApp/SMS, trade-register automation, Google Business Profile.

**What would change this plan:** (a) several pilot buyers are on one CMMS or FSM tool with API access on their current plan, so build that single connector; (b) buyers refuse to forward email, so add a mailbox mode and budget for CASA; (c) suppliers answer by WhatsApp, so log manually first; (d) a UK merchant offers punch-out or EDI to a pilot buyer.

**Questions for the first five interviews** (T1-T7 in the UK canvas are the right vehicle): which accounting package; which CMMS or FSM tool and which plan; where RFQs live today (shared mailbox, personal inbox, WhatsApp); whether IT allows forwarding to an external alias; whether a UK-resident mail processor is required by contract.

## 11. Failed or unread pages (honesty list)

Not read or blocked: Xero PO, scopes, limits guide and certification pages; Intuit rate limits, PurchaseOrder, developer terms (truncated); Sage developer pages (403); Fiix developer and help (DNS, 403); Limble and ServiceTitan pages (generic echo, unusable); Joblogic integrations (404); BigChange documentation (403); Simpro marketplace Screwfix (403); HMRC VAT-number page (404) and developer hub terms of use (not opened); Companies House API docs index (404); gov.uk consultation landing page (404) and Peppol.org (404); Ofcom (403); Gas Safe terms (bot wall); TrustMark terms (404); Twilio SMS pricing (404); NCSC (404); Microsoft publisher verification (404); Mailgun routes docs (not read); Postmark data region (not found).

Items drawn from search-result summaries and therefore needing re-verification before use: Xero 25-connection uncertified cap; Sage rate limits; QBO review timelines and AI terms; Fiix call quota; MaintainX/Limble plan gating and prices; Joblogic/BigChange/Simpro integration claims; HMRC VAT-check two-week approval; UK e-invoicing Peppol confirmation date; WhatsApp 15 January 2026 AI-provider rule.

## 12. Sources

Xero: https://developer.xero.com/pricing · https://developer.xero.com/faq/pricing-and-policy-updates · https://developer.xero.com/xero-developer-platform-terms-conditions · https://developer.xero.com/faq/limits
FreeAgent: https://dev.freeagent.com/ · https://dev.freeagent.com/docs/quick_start
Sage: https://developer.intacct.com/api/ · https://www.cleverence.com/articles/sage-documentation/sage-accounting-api-purchase-transactions-3-1-7394 (third party)
Gmail: https://developers.google.com/gmail/api/auth/scopes · https://developers.google.com/terms/api-services-user-data-policy · https://support.google.com/cloud/answer/13465431 · https://knowledge.workspace.google.com/admin/compliance/choose-a-geographic-location-for-your-data
Microsoft: https://learn.microsoft.com/en-us/graph/permissions-reference · https://learn.microsoft.com/en-us/graph/throttling-limits · https://learn.microsoft.com/en-us/microsoft-365/enterprise/advanced-data-residency · https://learn.microsoft.com/en-us/office/dev/add-ins/outlook/outlook-add-ins-overview · https://learn.microsoft.com/en-us/entra/identity-platform/howto-convert-app-to-be-multi-tenant · https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2
Inbound email: https://postmarkapp.com/developer/user-guide/inbound · https://postmarkapp.com/pricing · https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html · https://docs.aws.amazon.com/general/latest/gr/ses.html · https://www.twilio.com/docs/sendgrid/for-developers/parsing-email/setting-up-the-inbound-parse-webhook · https://documentation.mailgun.com/docs/mailgun/user-manual/receive-forward-store/
CMMS/FSM: https://help.getmaintainx.com/build/build-with-maintainx · https://developers.onupkeep.com/ · https://www.bigchange.com/extra/rest-api (opened); Fiix, Limble, Joblogic, Simpro, BigChange spec details via search snippets only
UK gov: https://www.gov.uk/government/consultations/promoting-electronic-invoicing-across-uk-businesses-and-the-public-sector/outcome/promoting-electronic-invoicing-across-uk-businesses-and-the-public-sector-consultation-response · https://www.gov.uk/government/news/government-sets-out-plans-for-e-invoicing-overhaul-to-cut-paperwork · https://www.gov.uk/guidance/electronic-invoicing-notice-70063 · https://www.gov.uk/government/publications/extension-of-making-tax-digital-for-income-tax-self-assessment-to-sole-traders-and-landlords/making-tax-digital-for-income-tax-self-assessment-for-sole-traders-and-landlords · https://developer.service.hmrc.gov.uk/api-documentation/docs/reference-guide
Formats: https://docs.peppol.eu/poacc/billing/3.0/ · https://cxml.org/
Supplier data: https://developer-specs.company-information.service.gov.uk/guides/authorisation · https://developer.company-information.service.gov.uk/overview · https://developers.google.com/my-business/content/overview · https://developers.google.com/maps/documentation/places/web-service/policies
Messaging: https://whatsappbusiness.com/policy/ · https://whatsappbusiness.com/products/platform-pricing/ · https://developers.facebook.com/docs/whatsapp/cloud-api/overview
Identity: https://developers.google.com/identity/passkeys

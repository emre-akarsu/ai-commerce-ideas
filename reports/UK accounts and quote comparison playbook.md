# Open accounts through customers, not crawlers

**The product gets its accounts and its prices by asking for them, one customer and one merchant at a time, and the research found no shortcut that keeps hard rule R7 intact.** A contractor's own trade account is the only route that yields a firm, account-specific price: the contractor asks the account manager for a dated price file and written permission to load it, using the email script in section 4 (credit accounts open in days to a week; cash accounts open in minutes to two days). Affiliate accounts are cheap to open (Awin charges a refundable £5 and aims to review in 24 hours) but are a licence to promote, not to use data, so they can supply at best indicative retail prices and only after an R7 amendment and each advertiser's consent ([Awin](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee); [earlier sourcing report](UK%20product%20sourcing%20and%20price%20data.md)). Software and data partner programmes are channels and reference data, not price sources; the cheapest and best documented are the ServiceM8 add-on store and a free Xero Starter app ([ServiceM8](https://developer.servicem8.com/docs/addon-store-requirements); [Xero](https://developer.xero.com/pricing)). For requirement-to-SKU, the evidence supports guardrails over bigger models: an NBS-style equivalence contract per generic line, substitutes as a separate output that is always sent for approval, and taxonomy validation of every LLM output ([NBS](https://www.thenbs.com/knowledge/substitution-and-beyond); [Instacart](https://company.instacart.com/tech-innovation/building-the-intent-engine-how-instacart-is-revamping-query-understanding-with-llms)). For quote comparison, show up to five named options (lowest total, fewest deliveries, fastest, preferred suppliers, balanced), each with its extra cost against the lowest total, and score "balanced" against references fixed by the buyer's own inputs so adding an option cannot reorder the others. Every price source in the market is permissioned (supplier-pushed files, merchant-approved integrations, merchant partnerships), which is why this plan keeps customer-owned files first. This is research, not legal advice; product-market fit is unproven and all seed data in the product is synthetic.

**How to read this report.** Evidence labels follow the notes: **[V]** primary page read; **[V†]** primary page read through a summarising tool; **[V-vendor]** vendor's own marketing; **[U]** unverified (search snippet, secondary, unreadable page, or inference). The competitor note's labels map as VERIFIED = V and SEARCH-SNIPPET = U. Notes folder: [`../research_notes/UK sourcing accounts and quote comparison/`](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/). Where notes disagree, section 8 says which one this report follows.

| Your question | Section |
|---|---|
| Decisions and first actions | 1 |
| Per-merchant playbook | 2 |
| Affiliate and partner playbooks, ranking, 90 days | 3 |
| Price-file email script and checklist | 4 |
| Requirement to SKU, embedding path | 5 |
| Quote comparison | 6 |
| Competitors and entrant path | 7 |
| Conflicts between notes | 8 |
| R7 and ADR-013 | 9 |
| Gaps and solicitor questions | 10 |
| What changes in the matching plan and doc 08 | 11 |

## 1. Seven owner decisions and three actions for the first fortnight

The owner's 7 October decisions already fix the frame: stay inside R7 now, decide the amendment only at the first signed licence (ADR-013 Gate 2), keep negotiated prices private to each customer, and build the price book first ([decisions note](../docs/product/09-decisions-2026-10-07.md)). This research does not overturn any of that. It adds seven decisions that the account work forces.

| # | Decision | Recommendation | Why |
|---|---|---|---|
| 1 | Whose accounts supply prices? | The customer's accounts; the company holds its own accounts only for its own purchases and never logs in to read prices | No merchant page read describes a partner route for software firms; Key Accounts targets established buyers ([trade note §3](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/trade_accounts_howto.md)) |
| 2 | Who sends the price-file request? | The customer sends it, the platform drafts it, and the send-service sends it only after the customer approves the exact text (R1) | Merchants answer account holders; the request carries the customer's written permission |
| 3 | Apply to affiliate networks now or later? | Prepare the public site and application text in the first 60 days; submit after the solicitor answers the P1 items | Decision 09 #3 holds the public layer back; an application is cheap (£5 refundable) but a misdescribed one risks termination |
| 4 | Which partner programmes first? | ServiceM8 add-on, Xero Starter, Joblogic and Simpro conversations, in that order | Only ServiceM8 and Xero have a documented self-serve path ([partner note §6](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/partner_programmes_howto.md)) |
| 5 | Adopt the matching-engine additions? | Yes: the seven in section 5, starting with the substitute output class and taxonomy validation | They are guardrails; none touches a hard rule |
| 6 | Which options does the quote screen show, and what default weights? | Five named options; no composite score until pilot buyers set weights; the 50/25/15/10 starting weights are unsourced | No source gives validated weights ([quote note §6](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/quote_comparison_criteria.md)) |
| 7 | Fund the solicitor session? | Yes, on the questions in section 10, before any merchant clause is relied on | No merchant clause on third-party use of account prices was found in any page read |

**Three first actions.** First, recruit the three to five design-partner contractors from the strategy and have each approve a price-file request (section 4) to the merchant where they hold their largest account, starting with City Plumbing and Rexel because both publish a route. Second, book the solicitor session on the section 10 questions, the first two of which decide whether a customer may pass a merchant's negotiated price file to a software tool. Third, send one batch of written enquiries asking for terms (including whether AI use, caching and tenant-level reuse are allowed) to Joblogic, ETIM UK and Ireland and Data Yard, and register a ServiceM8 developer account and a Xero Starter app ([partner note §6](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/partner_programmes_howto.md)).

## 2. Merchants publish accounts, not APIs: the per-merchant playbook

Retail-style merchants have self-serve routes: cash accounts open near-instantly and credit accounts take days and need credit checks. Electrical wholesalers and Howdens use paper or depot-led applications, and a limited company under three years old should expect director personal guarantees at Yesss ([Yesss form](https://cdn.yesss.co.uk/downloads/Credit_Application_Form.pdf)). Only Rexel publishes an e-procurement route (EDI, punch-out, e-catalogue, webshop) ([Rexel UK](https://www.rexel.co.uk/uki/edi)). Cash accounts give list "trade" prices, not necessarily the negotiated discounts a credit account holder sees; Jewson ties "personalised prices" to credit [U] (trade note §1 inferences). The playbook is split in two tables for width; merchant names repeat.

### Table 2a: account to open, requirements, speed, what it unlocks

| Merchant | Account to open | Requirements and speed | Unlocks | Evidence |
|---|---|---|---|---|
| Screwfix | Credit account (online via credit site); Key Accounts later | Company number or owner details, address, bank details; credit check; "a few minutes" to apply; up to 60 days (paid by last day of following month), no annual fee ([Screwfix](https://www.screwfix.com/help/tradecreditaccounttermsandconditions)) | Credit, statements, itemised VAT invoices; Key Accounts adds purchasing controls; no price file or API mentioned ([Key Accounts](https://www.screwfix.com/landingpage/key-accounts)) | [V]; same account at 300+ TradePoint sites [U] |
| Toolstation | Trade Club credit, then Key Accounts | Key Accounts is for "large limited companies, PLCs, and organisations" ([Toolstation](https://www.toolstation.com/key-accounts)) | 5% off on account, account manager, quotations | [V] |
| Travis Perkins / TradePoint | Trade Cash (online) or Trade Credit | Cash "under 3 minutes"; credit: downloadable form to branch or New Accounts team, min. 30 days interest-free, credit check ([TP](https://www.travisperkins.co.uk/Credit-Account)) | Personal trade prices via app ([BMN](https://www.buildersmerchantsnews.co.uk/news/merchants/travis-perkins-launches-industry-app-customers-shop-manage-accounts)) | Account terms [U] (pages returned empty) |
| Jewson | Cash or credit | Cash: under 5 minutes, active in 2 days or less; credit: active in 5 days or less, up to 60 days, "sole traders to PLC's" ([Jewson](https://www.jewson.co.uk/expert-advice/self-build)) | Personalised prices, e-billing; link a branch account online by account number ([need-help](https://www.jewson.co.uk/need-help)) | Terms [U]; contacts [V] |
| Selco | Trade Card (cash) or Credit | Card "then and there"; credit limits from £1,500, up to 60 days, approval "about 5 - 7 days" ([Selco](https://selcobw.com/info/trade-accounts-explained)) | "Over 15,000 exclusive Trade Prices", statements | [V] |
| Wickes | TradePro membership (not credit) | Two forms of trade ID; UK-resident tradespeople ([Wickes](https://www.wickes.co.uk/tradepro/sign-up)) | Flat 10% (Installers 15%); no negotiated list to export | [V] |
| B&Q TradePoint | Membership, online or in store | Listed trades; tiers on the page may be historic ([B&Q](https://diy.com/corporate/tradepoint)) | Discount tiers; credit route unverified | [V]/[U] |
| Wolseley / Plumb Center | Trade account | Proof of trade, credit checks, tiers, portal (aggregator snippets only) | Tiered pricing, portal | [U] |
| City Plumbing | Cash or credit at /login | Credit up to 60 days, references at their discretion; invoices online after 3-5 working days ([FAQ](https://www.cityplumbing.co.uk/content/help-and-advice/faqs)) | Trade prices on registering; a price list issued to Tradify customers ([Tradify](https://help.tradifyhq.com/hc/en-us/articles/29891627370137-How-to-get-a-City-Plumbing-price-list-for-your-Tradify-account)) | [V] |
| Rexel UK | Trade account (documents not read) | Not read | EDI, punch-out, e-catalogue of "only your preferred products", webshop | Services [V]; opening gap |
| CEF | Trade account | Proof of trading (VAT), references | Listed in Fergus integrations ([Fergus](https://fergus.com/marketplace/cef/)) | [U] |
| Edmundson | Account application form | Form content not read | EELine catalogue | [V] page, content gap |
| Yesss | Credit application (paper or email) | Processed "usually within five working days"; under 3 years trading: personal guarantee from each director or 25%+ owner; no e-signatures ([Yesss](https://cdn.yesss.co.uk/downloads/Credit_Application_Form.pdf)) | Credit limit and account number | [V] |
| Howdens | Trade account | Trade ID, proof of address, trade status; "Apply now" online or at depot; up to 60 days on the page, 30 in a snippet ([Howdens](https://www.howdens.com/trade-customers/trade-account)) | "Confidential trade pricing"; trade terms cl. 10.2 bar disclosing pricing structure [V†] (earlier report) | [V]/[U] |
| Brewers | "Apply for an account" form | 10% off first order; credit 30 days unverified ([Brewers](https://www.brewers.co.uk/)) | Project Specification service | [V]/[U] |
| Topps Tiles | Trade app account | TradePay 30 days, Direct Debit ([Topps](https://www.toppstiles.co.uk/trade/trade-app)) | Contract sales support | [U] |
| Victorian Plumbing, Buildbase, TLC Direct | Trade accounts help exists (VP only) | Nothing readable | Unknown | [U]/gap |

### Table 2b: how to ask, affiliate route, contact

| Merchant | How to ask for a price file or integration | Affiliate route | Contact route |
|---|---|---|---|
| Screwfix | Account manager once on Key Accounts; website terms bar crawling and commercial use ([terms](https://www.screwfix.com/help/websitetermsandconditions)) | Closed to new applicants ([Screwfix](https://www.screwfix.com/jsp/help/affiliates.jsp)) | Key Accounts 01935 401444 or contact form |
| Toolstation | Account manager (Key Accounts) | Rakuten, reported [U] | key@toolstation.com |
| Travis Perkins | Account manager, then key accounts; sale terms silent on third-party price use | Awin merchant 16300, invites comparison publishers ([TP](https://www.travisperkins.co.uk/content/affiliate-programme)) | Branch or New Accounts team |
| Jewson | Account manager; ask whether personalised prices can be exported | Rakuten, reported [U] | 02476 608235; web form (two working days) |
| Selco | Branch or credit contact | None found | Online forms |
| Wickes | Nothing to request (flat discount); use invoices and RFQ | Awin merchant 1563 ([Awin](https://ui.awin.com/merchant-profile/1563)) | Sign-up page |
| B&Q TradePoint | RFQ or invoices | Impact ([Impact](https://help.impact.com/partner/what-would-you-like-to-learn-about/platform-features/marketing-content/product-marketplace-and-catalogs/download-product-catalogs-as-a-partner)) | In store or online |
| Wolseley / Plumb Center | Account manager; connectors to job software exist | None found | Not reachable (403/503) |
| City Plumbing | Ask for the same customer price list Tradify customers receive; script in section 4 | None found | Credit control ccadmin@cityplumbing.co.uk, 01788 211440 |
| Rexel UK | EDI form: "Start the conversation today"; ask for an e-catalogue for the customer | None found | 0330 0450 606 |
| CEF, Edmundson | Account manager | None found | Branch |
| Yesss | Account manager after the account opens | None found | tradecreditapplication@yesss.co.uk, 01924 227 948 |
| Howdens | Do not ask until the solicitor answers on cl. 10.2 | None found | Depot |
| Brewers | Account manager; Project Specification contacts | None found | 01323 576555 |
| Others | Case by case | Awin: Homebase, Plumbworld; Victorian Plumbing feed reported [U] | n/a |

**Rules that cut across every row.** No merchant page read says whether account prices may be given to or stored by a third-party tool; most credit T&Cs were unreadable, so written permission from the account manager is the safe route until a clause is read ([trade note §4](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/trade_accounts_howto.md)). A start-up can almost certainly open cash accounts at self-serve merchants, but doing so gives it no customer's prices (trade note §3 inference). Do not scrape with an account login: most terms bar automated access.

## 3. Affiliate and partner accounts promote, they do not license data

### Affiliate and publisher programmes

Every network is two-stage: network approval, then per-merchant approval, and feeds unlock only after the second ([affiliate note §1](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/affiliate_accounts_howto.md)). The data terms are the binding constraint: Awin confines feed data to "the purpose of this Agreement" (cl. 10.7), Impact licenses use "to promote Advertisers", Rakuten limits use to participating as a publisher, Webgains data is "only for fulfilling this agreement", and Tradedoubler grants no rights beyond links ([earlier sourcing report](UK%20product%20sourcing%20and%20price%20data.md); [Awin terms](https://www.awin.com/docs.awin.com/Legal/Publisher+Terms/2025/EN-%28UK%29_Awin-Ltd-Publisher-terms_August-2025.pdf); [Webgains](https://docs.webgains.io/EN_Webgains_General_Terms_and_Conditions_Publisher_2024_08.pdf)). Retail feeds carry VAT-inclusive prices, so they stay indicative at best.

| Network | Steps | Cost | Timeline | Data and other restrictions | Evidence |
|---|---|---|---|---|---|
| Awin | Form with URLs and a description of how promotions work; manual review; card deposit; activation email; apply to each advertiser | £5, refunded with first payout or on decline ([Awin](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee)) | Aims for 24 hours; a snippet says two working days | Cl. 10.7 purpose limit; advertisers may refuse or remove at any time; 20 API calls a minute ([FAQ](https://success.awin.com/articles/en_US/Knowledge/Product-Data-Feed-FAQ)) | [V] |
| impact.com | Account, mobile code, accept agreement, categorise business, add a verified property | No fee mentioned ([impact](https://help.impact.com/partner/what-would-you-like-to-learn-about/getting-started/sign-up-as-a-partner-on-impactcom.md)) | Not stated; ~3 business days in a secondary source | "Promote Advertisers" licence; B&Q route | [V]/[U] |
| Webgains | Apply, activation email, place a code comment on the site, sign T&Cs, data-protection and self-billing agreements, apply per advertiser ([Webgains](https://knowledgehub.webgains.com/home/getting-started-as-a-webgains-publisher)) | Not stated | Not stated | Data only for the agreement | [V] |
| Tradedoubler | Register, verify site, apply to programme | Not stated | 1-3 business days per stage [U] | Suspends after 3 months without traffic (earlier report) | [U] |
| Kelkoo | Publisher account; API token in Publisher Center ([docs](https://docs.kelkoogroup.com/for-publishers)) | Not stated | Not stated | Retail offers, unlikely to cover trade prices | services [V], token [U] |
| Rakuten, CJ | Network then advertiser; tax and bank details | Not stated | CJ network 1-7 days; Rakuten 2-4 weeks anecdotal | Rakuten limits to publisher participation | [U] |
| Skimlinks, Sovrn | Site review | Free | 2 business days [U] | Reportedly excludes downloadable software, extensions and apps; password-protected sites fail review | [U] |
| Amazon Associates | Conditional approval, then qualifying sales | Free | 3 sales in 180 days per a secondary source; the Creators API page says 10 qualifying sales in 30 days | No ML training; store most content 24 hours (earlier report) | [U]/[V] |

**What to write in the application.** Describe the real use plainly: a pre-launch UK B2B purchasing assistant for refurbishment contractors that compares prices across merchants and links to merchant pages through tracked links, with no traffic yet and no cashback ([affiliate note §7](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/affiliate_accounts_howto.md)). Do not claim an audience, reviews or editorial content that do not exist. Awin treats inaccurate information as a compliance issue. Comparison or shopping categories fit Awin and impact; a public site with real content is needed everywhere. Any monetised link needs a visible "Ad" label: the ASA says both advertiser and affiliate are responsible, and a bottom-of-page disclaimer is "unlikely to be sufficient" ([ASA](https://www.asa.org.uk/advice-online/affiliate-marketing.html)). Whether consumer-style disclosure rules reach a B2B-only audience was not read; ask the solicitor.

### Software, data and marketplace programmes

| Programme | Steps | Cost | Timeline | Data-use and other restrictions | Evidence |
|---|---|---|---|---|---|
| ServiceM8 add-on | Developer account, build to the checklist (OAuth 2.0, help docs, monitored support email, 3+ screenshots without real data, privacy policy stating what ServiceM8 data is stored and retained), submit ([ServiceM8](https://developer.servicem8.com/docs/addon-store-requirements)) | 90/10 revenue share in a snippet | None published | No payment processing; name cannot contain "ServiceM8" | checklist [V], share [U] |
| Xero | Starter app, later tiers | Free to 5 connections; A$35, A$245, A$1,445 a month ([Xero](https://developer.xero.com/pricing)) | Not published | New terms bar using API data "to train AI/ML models"; annual self-assessment over 1,000 connections ([security](https://developer.xero.com/partner/security-standard-for-xero-api-consumers)) | [V] |
| Joblogic | Email partners@joblogic.com; discovery meeting; test site ([Joblogic](https://www.joblogic.com/en-au/partners/)) | API Access "Available on Request" ([API](https://www.joblogic.com/marketplace/api-access)) | Not stated | Bronze/silver/gold by API customers | [V] |
| Simpro | Registered, Select, Premier tiers; "direct engagement" | Unknown | Unknown | Pages returned 403; 10% and 20% referral rates in a snippet | [U] |
| Fergus, Tradify, Powered Now, Commusoft, Buildxact | Bilateral; Fergus uses per-user tokens; Tradify has no developer portal; Commusoft partner API "coming soon" | Unknown | Unknown | Contact when a customer asks | [U]/[V] |
| Amazon Business API | Onboarding questionnaire (10-15 minutes), Amazon assigns roles, passport and proof of residence, Solution Provider Portal ([Amazon](https://docs.business.amazon.com/docs/onboarding-overview)) | No fee stated | 1-5 weeks [U] | Caching and AI terms not found | [V]/[U] |
| Data Yard (BMF/NMBS) | Ask for software-provider terms; ask whether tenant-merchant users can pull data under their own access | Shareholding undisclosed | Unknown | Suppliers control who can access; terms unpublished ([NMBS](https://www.nmbs.co.uk/building-materials-product-data-platform-marks-major-milestone/)) | [V] |
| ETIM UK and Ireland | Phone or email enquiry ([ETIM](https://www.etim-uk-and-ie.org)) | Unknown | Unknown | Fees and unlocks not published | [V] |
| GS1 UK | Membership only if the product must own GTINs | £50-£450 a year for small firms [U] | n/a | Verified by GS1 basic service 30 queries a day [U] | [U] |
| Peppol | Use a certified access point; do not become one | €1,050-€5,400 sign-up for own access point, [V] ([OpenPeppol](https://peppol.org/join/fees/)) | UK mandate April 2029 [U] | No urgency | [V]/[U] |

### Ranking and a 90-day sequence

By value over effort, from the partner note and adjusted for the owner's decisions: ServiceM8, Xero Starter, Simpro Registered, Joblogic, Amazon Business (only if a customer needs it), Data Yard and ETIM enquiries, then Sage and QuickBooks on demand, then the long tail and Peppol after first revenue. Affiliate networks rank Awin, impact, Webgains, Tradedoubler and Kelkoo, with Rakuten, CJ, Skimlinks, Sovrn and Amazon Associates deferred. The sequence below is a proposal, not a verified procedure; no application has been filed.

| Weeks | Action | R7 status |
|---|---|---|
| 1-2 | Design partners approve price-file requests (section 4) to their top merchants; email Joblogic, ETIM UK and Ireland and Data Yard asking for terms in writing; book solicitor | Inside (email, files) |
| 2-6 | Register ServiceM8 developer account and Xero Starter app; build the add-on against the checklist; publish a public site with product, methodology and disclosure pages | Inside (outbound to the customer's own software) |
| 4-8 | Price-file replies arrive: log each merchant's answer, validity and permission; request Simpro partner conversation; draft the affiliate application text | Inside |
| 8-12 | Submit ServiceM8 listing; submit Awin (and impact if wanted) after the P1 solicitor answers; send invoices-based requests for merchants that refused files | Affiliate use needs amendment and advertiser consent |
| After first revenue | Xero Core when over 5 tenants; Simpro Registered; Data Yard; Peppol through a provider | Per source |

## 4. The contractor's price-file request: script and checklist

Ask the account manager (else credit control or the branch manager) for a dated CSV or Excel customer price file, the VAT basis, and written permission to load it into the contractor's own purchasing software. Keep the request narrow and expect partial or delayed replies ([trade note §2](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/trade_accounts_howto.md)). Evidence that the ask works is thin: City Plumbing issues a customer price list to Tradify customers on request [V] and Rexel offers bespoke e-catalogues [V], but no public source gives response times, charges or refusal rates. Allow weeks, not days (inference).

**Checklist before sending.**
1. Gather the account number, trading name, branch and the named account manager.
2. Decide scope: the whole range, named brands or product groups, or the SKUs on the last 12 months of invoices.
3. Specify the format: one row per SKU with merchant SKU, manufacturer part number, description, unit of measure and pack size, net price, currency, price basis (list less discount, or net), discount percentage, valid-from and valid-to dates, VAT basis and any minimum order quantity.
4. State the use: loaded into the contractor's own purchasing software for its own staff, not shared with other customers or the software supplier's other users.
5. Ask for permission in writing; a reply by email is the record.
6. Offer a contact for the merchant's questions and to review confidentiality terms.
7. Diary follow-ups at 5 and 15 working days.

**Script (generic; fill the brackets; no personal data beyond business contact details).**

> Subject: Request for our account price file (CSV/Excel) and permission to load it
>
> Hello [name],
> We are [company], account number [number]. We are moving our purchasing to a software tool used only by our company. Could you please send us a customer price file in CSV or Excel for the products we buy from you (or [brands/categories], or all items on our account), with the columns: your SKU, manufacturer part number, description, unit of measure and pack size, our net price, valid-from and valid-to dates, and whether prices are shown ex-VAT or inc-VAT.
> We would also like your written confirmation that we may load these prices into our purchasing software for our own use, with access limited to our staff. If you have confidentiality terms for this, please send them and we will review them.
> If you do not provide price files, could you tell us whether you offer an e-catalogue, punch-out or EDI service, and who we should contact?
> Please let us know when prices are next reviewed and how often you can refresh the file.
> Thank you, [name, role, company, phone]

**What to expect.** The first answer is usually "log in to see prices" (Jewson, City Plumbing, Selco and Travis Perkins show account prices online); push for the file and say why. Outcomes range from an Excel or PDF export, to a partial file, a refusal citing confidentiality, a referral to head-office pricing, or a paid set-up service such as Rexel's e-catalogue. Prices can be project-specific, expire, or exclude rebates, so capture validity and VAT basis exactly. A file the customer attests to becomes a firm line only if it carries merchant, validity and VAT basis ([decisions note](../docs/product/09-decisions-2026-10-07.md)).

## 5. Requirement to SKU: guardrails beat bigger models

**What the evidence says.** UK trade software treats this as supplier-catalogue integration, not interpretation: the user picks the SKU, and Simpro merges catalogue items when part numbers match exactly ([Simpro marketplace](https://marketplace.simprogroup.com/apps/screwfix) [U]). The only vendor claiming automated requirement-to-SKU with reasoning is Buildxact's AI Estimator, which is marketing without accuracy figures ([Buildxact](https://www.buildxact.com/uk/?p=5836) [U]). So there is no proven trade design to borrow, and differentiation is real but unproven ([requirement note §1](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/requirement_to_sku_practice.md)). The best-documented production evidence is Instacart: plain LLM prompts produced synonym-only rewrites, and the fixes were per-type prompts, injecting top-converting brands and categories, embedding-similarity filtering and validating generated tags against the taxonomy; it reports rewrite coverage rising from 50% to over 95% at 90%+ precision, with offline caching for head queries and a fine-tuned 8B model for the tail (self-reported) ([Instacart](https://company.instacart.com/tech-innovation/building-the-intent-engine-how-instacart-is-revamping-query-understanding-with-llms)). Its LLM treats curly parsley as a substitute for flat parsley, precisely what must not be auto-applied in MRO. Zalando's 75% attribute-extraction accuracy is a warning that LLM-extracted attributes cannot satisfy a critical attribute ([ZenML](https://www.zenml.io/llmops-database/ai-assisted-product-attribute-extraction-for-e-commerce-content-creation)). On equivalence, NBS recommends a generic description, a named deemed-to-comply product, critical attributes with pass/fail points, and evidence from the contractor; it warns that "or equal" breeds disputes ([NBS](https://www.thenbs.com/knowledge/substitution-and-beyond); [Designing Buildings](https://www.designingbuildings.co.uk/wiki/Substitution_terminology_in_construction)). ESCI's Exact/Substitute/Complement/Irrelevant labels show that even human labellers disagree most on Substitute (about half of disagreements), and a BERT baseline reaches only 0.656 F1 on the four-class task ([ESCI](https://ar5iv.arxiv.org/html/2206.06588)).

### Recommended additions to the matching engine

The engine already has typed checks, a gate, an identifier-is-definitive rule, a generic-line match group and a tenant-scoped approval store ([matching-engine.md](../docs/architecture/matching-engine.md)). I read that document, not the code.

| # | Addition | Evidence | What it changes in the engine |
|---|---|---|---|
| 1 | Equivalence contract per generic line: generic description, critical attributes with pass/fail, named deemed-to-comply reference, evidence required for alternatives | NBS | Replaces the unreviewed required-attribute lists with an explicit, reviewable contract per line type |
| 2 | Substitute as a distinct output class, never auto-accepted, always routed to approval (R2) | ESCI; annotator disagreement | Adds an output label beside accept, review and reject |
| 3 | Validate every LLM-proposed attribute or category against the ontology and drop low-similarity outputs | Instacart | Applies to any LLM parse step and the ontology builder; the judge already discards unknown ids |
| 4 | Approval history as a retrieval prior only | Instacart grounding | The architecture shows `previously_approved` as a short-circuit; confirm it re-runs `check_candidate` and tier rules, or demote it to a prior |
| 5 | Cache LLM interpretation of repeated requirement strings; small tuned model for the tail | Instacart (self-reported) | The judge makes two calls per ambiguous line; key the cache on the normalised line signature plus catalogue version |
| 6 | Exact part-number merge across suppliers first | Simpro import behaviour | Closes the "no catalogue-ingestion normaliser" gap; solves identical SKUs, not equivalent ones |
| 7 | Evaluate on a labelled real set using ESCI/WANDS-style labels | ESCI, WANDS, Walmart preprint | Extends the 151-line synthetic gold set, which cannot certify below 0.5% (about 598 error-free auto-accepts needed) |

Avoid auto-applying LLM substitutes, "or approved equal" wording in outputs, vendor accuracy claims (Algolia, Bloomreach, Buildxact AI) as evidence, and treating LLM-extracted attributes as critical-attribute proof. Error classes (size, grade, pack, thickness, finish, fit) come from the spec, not from any sourced post-mortem.

### Embedding and search upgrade path, in three steps

Embeddings blur sizes, grades and codes: the Qdrant ESCI test found dense retrieval "blur exact matches", and the typed checks must stay the decider ([Qdrant](https://qdrant.tech/articles/sparse-embeddings-ecommerce-part-1/)). The embedder only needs to raise recall of synonyms and abbreviations such as "p/board". Cost is not a deciding factor: embedding 1M SKUs at 20 tokens each is about $0.40 on OpenAI's small model, $2.60 on the large one, $10 on Cohere Embed 5 [E] (note's arithmetic from [OpenAI](https://developers.openai.com/api/docs/pricing) and [Cohere](https://cohere.com/pricing) prices). Data terms and UK residency are.

| Step | What | Decision criterion | Licence and data-term traps |
|---|---|---|---|
| 1. Now (offline) | Keep `HashingEmbedder` in tests; add a second `Embedder` for eval runs only (bge-small-en-v1.5, MIT, 384 d, or multilingual-e5-small, MIT), pinned local path; add pure-Python BM25 for the lexical leg | Move on if gold-set recall@50 is below 0.98 or any wrong auto-accept occurs | jina-embeddings-v3 is CC-BY-NC by default ([HF](https://huggingface.co/api/models/jinaai/jina-embeddings-v3)); EmbeddingGemma needs a click-through licence ([HF](https://huggingface.co/google/embeddinggemma-300m)) |
| 2. Pilot | Postgres with pg_trgm and pgvector (HNSW per category partition, iterative scan), BM25 by extension or application side, RRF k=60 then a tuned convex weight, self-hosted embedder, optional reranker (bge-reranker-v2-m3, Apache-2.0) over the top 20-50 | Recall@50 not worse by more than 1 point, top-3 improves, zero new wrong auto-accepts | Render has no London region and no BM25 extension ([Render](https://render.com/docs/regions)); Supabase has London ([Supabase](https://supabase.com/docs/guides/platform/regions)); Gemini free tier content is used to improve products ([Gemini](https://ai.google.dev/gemini-api/docs/pricing)); Voyage training opt-out must be set ([Voyage FAQ](https://docs.voyageai.com/docs/faq)); OpenAI non-US residency needs approval ([OpenAI](https://developers.openai.com/api/docs/guides/your-data)) |
| 3. Scale (only on triggers) | Qdrant (Apache-2.0) or Typesense as a derived read-only index fed from Postgres; tenant filter enforced in code | About 1M vectors per tenant, filtered-ANN recall problems, typo-tolerant UI or sustained p95 breach | Typesense GPL-3.0 and ParadeDB AGPL-3.0 need legal review if bundled or networked ([Typesense](https://typesense.org/docs/29.0/api/vector-search.html)); Icecat licences void use inside generative AI frameworks (earlier report) |

Reranker or embedder scores stay advisory and never replace `check_candidate` or the gate. Do not compare models by leaderboard rank: MTEB itself concludes that no method dominates ([MTEB](https://arxiv.org/abs/2210.07316)), and no benchmark covers short UK trade titles. Evaluate with recall@1/3/10/50, hard-negative rank, wrong auto-accepts end to end, a size-and-grade sensitivity probe, and Wilson intervals, treating the synthetic set as a regression signal only ([embeddings note §4](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/embeddings_and_search_stack.md)).

## 6. Quote comparison: five named options scored against fixed references

**Criteria.** The only criteria sourced directly are those the Procurement Act 2023 guidance allows (price or cost, quality, life-cycle cost, wider benefits) and supplier-performance KPIs such as on-time-in-full ([gov.uk](https://www.gov.uk/government/publications/procurement-act-2023-guidance-documents-procure-phase/assessing-competitive-tenders-html)). The pricing engine already models landed cost, lead time, stock, MOQ and pack rounding, delivery fee and threshold, VAT basis, validity and substitution tier. Not modelled and unsourced: payment terms, returns, warranty, reliability history and sustainability; show them as "not known", never as zero, and keep them out of any score ([quote note §1](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/quote_comparison_criteria.md)). Normalisation follows bid levelling: unit and pack content, VAT basis, delivery included, validity and staleness, stock and lead time, plus explicit "assumptions differ" lines. Allow non-destructive annotations on an option, as Procore bid levelling does.

| Option | Definition | Show |
|---|---|---|
| Lowest total cost | Cheapest landed total including delivery, from firm offers | The baseline |
| Fewest deliveries | Best single merchant or fewest merchants covering every line | Extra cost against lowest total |
| Fastest | Earliest complete delivery; ties broken by cost | Days earlier and extra cost |
| Preferred suppliers | Cheapest among the tenant's list; only if a list exists | Extra cost |
| Balanced | Optional; shown only if it differs from the others | The weights and the scores |

Drop any duplicate and say so ("same as lowest total cost"). Indicative offers stay in a separate "indicative, not a quote" block, expired offers are excluded, and nothing is auto-selected for ordering. Each option must be best on a stated, different dimension: never include one to make another look better, because decoy-effect evidence is contested ([Huber, Payne and Puto](https://people.duke.edu/~jch8/bio/Papers/HuberPaynePutoJMR%202014.pdf)). Choice-overload evidence has a mean effect near zero across 50 experiments, so five options is judgement, not a proven number ([Scheibehenne et al.](https://ideas.repec.org/a/oup/jconrs/v37y2010i3p409-425.html)).

**Balanced scoring and rank reversal.** TOPSIS and AHP-style methods can change the order of existing alternatives when one is added or removed ([MPRA 59887](https://mpra.ub.uni-muenchen.de/59887); [Entropy 22(2):259](https://www.doi.org/10.3390/E22020259)). The note advises scoring against fixed references. My analysis goes one step further: a reference such as "the cheapest option" is itself derived from the option set, so adding a cheaper option rescales the cost score against the other criteria and can reorder the rest. The safe references come from the buyer's own inputs, not the displayed options: cost against a budget or last-paid total, lead time against the required-by date or absolute bands, deliveries against a stated cap. Where the buyer supplies none, show the named options without a composite score. The unsourced starting weights are total landed cost 50%, delivery date 25%, number of deliveries 15%, preferred-supplier match 10%; show them, let users change them, and tune with pilot buyers. They are a starting point, not evidence.

**Templated explanations and honesty rules.** Use text templated over typed values, with no free text: "£X more than the lowest total cost, with N fewer deliveries" and "arrives D days earlier for £Y more". Show the reason a default is highlighted ("lowest total including delivery"), not a bare "recommended". Adopt the CMA's online-choice-architecture warnings as a design standard even though they target consumers: explain ranking order, avoid drip pricing, no false scarcity ("5 left") unless from a firm stock figure, no countdowns, no sponsored ordering ([CMA paper](https://www.gov.uk/find-digital-market-research/online-choice-architecture-how-digital-design-can-harm-competition-and-consumers-2022-cma); [CMA blog](https://competitionandmarkets.blog.gov.uk/2022/04/07/online-choice-architecture-how-do-we-end-up-making-decisions-we-dont-want/)). For business audiences, the Business Protection from Misleading Marketing Regulations 2008 prohibit misleading advertising to traders, including as to price, and require comparative advertising to compare products meeting the same needs on "material, relevant, verifiable and representative features" ([reg 3](https://www.legislation.gov.uk/uksi/2008/1276/regulation/3); [reg 4](https://www.legislation.gov.uk/uksi/2008/1276/regulation/4)). The CAP Code applies to B2B marketing, and VAT-exclusive prices are allowed to audiences who can recover VAT with the VAT amount or rate stated prominently ([ASA](https://www.asa.org.uk/advice-online/misleading-advertising.html)). Whether reg 4 reaches a neutral tool comparing third-party quotes is unclear; the solicitor decides. For parts-only baskets the VAT domestic reverse charge normally does not apply, but a bundle with labour could be caught, so hand that case to a human ([HMRC](https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services)). Every price needs observation time and validity.

## 7. Competitors survive on permissioned data, and the entrant path starts with customer files

Proven models are all permissioned. Buildxact takes supplier-pushed price files by API, with "Managed" catalogues visible only to named builders, which confirms that trade pricing is account-specific ([Buildxact](https://developer.buildxact.com/suppliers-price-file)). Simpro sells merchant integrations (Screwfix, Toolstation, Travis Perkins, Selco, Yesss, Brewers) per supplier, with manual CSV or ZIP import for the rest ([competitors note §1](../research_notes/UK%20sourcing%20accounts%20and%20quote%20comparison/competitors_price_comparison.md)). BuyTrade launched free to users with City Plumbing, Wolseley and HRP Trade by partnership ([BMN](https://www.buildersmerchantsnews.co.uk/news/merchants/industry-multi-merchant-platform-launched)), and BuyMaterials routes RFQs to merchants who opt in ([BuyMaterials](https://www.buymaterials.com/trade)). "Scours the web" comparison sites such as BuildBuddy (£1m seed, June 2024), Go Banana and CompareTheBuild show no verified current traction ([Scottish Financial News](https://www.scottishfinancialnews.com/articles/buildbuddy-secures-ps1m-to-innovate-construction-material-procurement)). No UK trade-supplies scraping dispute was found, but the CJEU held in the Ryanair case that website terms can restrict use of an unprotected database, so terms breach is the realistic risk ([Pinsent Masons](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case)).

None of the products reviewed documents substitution tiers or pack-size normalisation, which is the gap this product targets; that is absence of evidence and does not prove demand. The main competitive risk is a job-software vendor adding comparison across its existing integrations: Simplementary already sells a "Procure" tool that compares suppliers inside Simpro (earlier report).

**Nexana.** The brief for this report states that Nexana's own website exists and describes supplier price sync for Simpro, BigChange and ServiceM8 without saying how prices are obtained. The competitors note found no relevant result at all. I did not re-check the site in this pass, so treat the brief's observation as unverified here. It matters for two reasons: it adds a fourth example, beside Simpro and Simplementary, of a vendor selling merchant price sync with undisclosed provenance, and strategy doc 08 already names "Nexana-style" vendors as a dependency risk.

**Realistic entrant path.** Merchants agree when the tool routes orders to them, respects account pricing, or lets them control what is shown; neutral public comparison offers them nothing (competitors note §3 inference). The path is: customer-owned price books first; RFQ fallback to merchants who opt in; partner feeds with one or two independents or a regional chain next; and piggybacking on existing trade-software integrations rather than negotiating national merchants first. Expect to pay or share revenue, since per-supplier add-ons show price access is monetised.

## 8. Eleven conflicts between notes, resolved

| # | Conflict | Resolution used here |
|---|---|---|
| 1 | Awin review time: 24 hours on the primary page versus "within two working days" in a snippet | Plan for two working days, treat 24 hours (weekdays only) as Awin's aim ([Awin](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee)) |
| 2 | Howdens credit: up to 60 days on the trade-account page versus 30 days in a snippet | The page wins; confirm at application ([Howdens](https://www.howdens.com/trade-customers/trade-account)) |
| 3 | Nexana: not found by the competitors note; the brief says its site exists | Treat as existing but unverified here; mechanism unknown; never a dependency |
| 4 | Simpro listing price: £15 a month per supplier (snippet) versus £17.50 for Screwfix (page read), bundles from £12.50 | The earlier report read the marketplace page: £17.50 for that listing; prices vary by listing, so quote a range and re-read each page ([Simpro](https://marketplace.simprogroup.com/apps/screwfix)) |
| 5 | Skimlinks excludes software tools (snippet) versus approval "at its entire discretion" (earlier report) | Unverified; moot because a password-protected tool fails site review anyway |
| 6 | Affiliate application framing: the affiliate note says "comparison/shopping" is honest; the earlier report advises against framing an application as a comparison portal | Describe the real use plainly and pick the closest honest category; claim no audience |
| 7 | Awin deposit: "possible small refundable deposit (amount unstated)" versus £5 refundable | £5 is verified on the Awin page; the affiliate note wins |
| 8 | Amazon Associates: three sales in 180 days (secondary) versus 10 qualifying sales in 30 days (Creators API page) | Different programmes and sources; defer either way |
| 9 | Xero uncertified-app cap of 25 connections (search summary) versus a security page that does not mention it | Confirm before relying on it |
| 10 | Fergus: "automatic supplier integrations" (vendor), invoicing only versus trade pricing flowing through (earlier report), personal-token API | Unresolved; ask Fergus how prices arrive |
| 11 | Rule numbering: spec R7 versus CLAUDE.md rule 4 | Cite the spec §4 numbering; fix at the ADR-013 decision |

## 9. What remains R7-bound, and what each route needs from ADR-013

R7 forbids fetching or scraping third-party links or sites ([spec §4](../docs/product/04-product-spec.md)), so every datum enters as a file the customer hands over, an email reply, or an invoice. Nothing in sections 2 and 4 needs the amendment. The amendment is needed only when the product itself makes a call to a merchant, network or marketplace. ADR-013 is proposed, not accepted; its Gate 2 requires a signed licence for the first source, the source's solicitor items answered in writing, the kill switch fixed (known gap H2), and a gateway in its own role with a network egress allowlist ([ADR-013](../docs/architecture/adr/013-contracted-price-source-ingestion-and-r7.md)).

| Route | R7 status | What it needs from ADR-013 | Quote-line eligible? |
|---|---|---|---|
| Customer price file by email or upload | Inside | Nothing; attestation of validity and VAT basis | Yes, if the six conditions hold |
| Invoice forwarding, RFQ replies | Inside | Nothing | Invoices indicative; written RFQ replies yes |
| Merchant-pushed scheduled email | Inside when emailed | Nothing | Yes within stated validity |
| Rexel EDI, punch-out, account API | Needs amendment | Gate 2: signed licence, gateway, kill switch | Yes, tenant-private |
| Awin, impact and other affiliate feeds | Needs amendment | Licence per source plus each advertiser's written consent for link-less internal use | No: indicative only |
| ServiceM8, Joblogic, Simpro outbound push | Outbound to the customer's own software | Likely none; confirm R7 wording | Not a price source |
| Xero, QuickBooks, Sage | Customer-authorised connection | Check R7 wording; no AI training on Xero data | Invoices, indicative |
| Amazon Business API | Needs amendment | Gate 2 plus terms not yet read | Indicative now |
| Data Yard, ETIM, bSDD | Build-time import, no runtime fetch | Licence terms in writing | Identity data only |
| Hosted embedding or LLM API | Not a third-party site fetch | Data-terms review; ADR-005 provider pinning | n/a |

The six-condition gate stays the test: a price is a quote line only if merchant-originated and addressed to this buyer, within validity, licensed for storage and display to this tenant, commercially complete (unit, currency, VAT, delivery, MOQ), grounded, and the approved match for the line ([ADR-013 §11](../docs/architecture/adr/013-contracted-price-source-ingestion-and-r7.md)).

## 10. Gaps and solicitor questions

**Gaps.** Not read: Travis Perkins, Wolseley, Plumb Center, CEF, Edmundson, Buildbase, Topps, Victorian Plumbing, TLC Direct and B&Q credit pages (blocked or empty), so their limits and documents are unverified. No merchant publishes a partner page for software firms. No public evidence of response times, charges or refusal rates for price-file requests. No source on payment terms, returns, warranty, split versus consolidated delivery risk, or default weights. Simpro application and API terms (403), ServiceM8 timeline and security review, Xero listing criteria, QuickBooks and Sage steps, Data Yard and ETIM fees, Amazon Business and eBay caching terms, and Titan embedding price and UK region are all missing. No benchmark covers embeddings on short UK trade titles, and the synthetic gold set cannot support any accuracy claim. The notes' coverage of Procore, STACK, Houzz Pro, Elastic and Vespa for matching was not reached.

**Questions for the solicitor** (research, not advice; the first two block any live source):
1. May a customer give a merchant's negotiated price file to a software tool, and what do merchant credit terms and confidentiality clauses (for example Howdens cl. 10.2) say about it?
2. Does storing those prices, and processing them through an LLM or vector store, need a licence from the merchant?
3. Is a written account-manager email enough permission, and what wording should it contain (store, display, process, no training)?
4. Does showing one tenant's data to others, or any pooling, raise confidentiality or competition issues?
5. Do BPRs reg 3 and 4, and the CAP Code, apply to a neutral comparison of third-party quotes to business buyers, and what wording is safe ("best price", "savings")?
6. Does affiliate disclosure ("Ad") apply to a B2B-only audience?
7. Liability for displayed prices, including "indicative" versus "quote" labelling, and the personal-data position of sole-trader details in files.
8. May Xero or Amazon Business data be sent to an LLM provider for inference?

## 11. What changes in the matching plan and in the data-sourcing strategy

The research confirms the strategy's core: prices are supplied, not found. It changes the following in `docs/product/08-data-sourcing-and-integration-strategy.md`.

| Where | Change |
|---|---|
| §2 step 1.4 (request email) | Use the section 4 script and checklist; the platform drafts, the customer approves, the send-service sends; log each reply, validity and permission |
| §2 step 1.1 and §5 merchant table | Add account type, speed and contact route from Table 2a/2b; start with City Plumbing and Rexel; ask Howdens nothing until the clause is reviewed; Wickes has no negotiated list, so use invoices |
| §3 step 2.5 (affiliate) | State costs and facts (Awin £5 refundable, 24 hours or two working days, per-advertiser approval, Screwfix closed); keep indicative-only; submit after the P1 solicitor answers; truthful application; "Ad" labels |
| §3 steps 2.6-2.8 | Reorder: ServiceM8 add-on and Xero Starter first (self-serve), Joblogic and Simpro second; Amazon Business only on customer demand |
| §3 step 2.2 (Data Yard) | First ask whether tenant-merchant users can pull data under their own authorised access, avoiding shareholding |
| §3 step 2.9 (quality) | Add the seven matching additions in section 5 and the embedding path; keep hard rules untouched |
| §6 integration map | Add Joblogic, ETIM UK and Ireland, GS1 UK (only if GTIN ownership is needed) and Peppol-through-a-provider rows |
| §7 risks | Name Nexana-style sync vendors with undisclosed provenance as a reason never to depend on them; add per-supplier fees as an expected cost |
| §9 decisions | Add the seven decisions in section 1 |

For the matching-engine plan, the changes are the equivalence contract, the substitute output class, taxonomy validation, approval history as a prior (check the short-circuit), caching, exact part-number merge at ingestion, and the three-step embedding path, each recorded in section 5. None edits `domain.py` or `ports.py`; if the new output class needs a contract field, write it to `docs/architecture/CONTRACT_CHANGES.md` and report.

## Conclusion

The research changes the framing from "which accounts do we need" to "whose accounts, and who may use what they yield". The product's own accounts are nearly worthless as a price source; a customer's credit account with a written permission email is worth more than any affiliate approval, and the affiliate approval is cheap precisely because it grants little. The one place where speed is within the company's control is the partner side, where ServiceM8 and Xero publish what to build, while the long-pole items (Data Yard terms, merchant licences, solicitor answers) are all requests that can be sent in the first fortnight.

Two findings are new rather than confirmatory. The "balanced" option can reorder other options even when scored against "the cheapest option", so references must come from the buyer's inputs or the score must be omitted. And the engine's approval short-circuit deserves a check against the research's "prior only" rule. The price-file response rate from real account managers remains the single most important unknown: nothing public measures it, and the design partners' first month will.

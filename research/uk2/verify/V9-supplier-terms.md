# V9 independent verification: UK supplier terms, trade accounts, quotes

Verifier: independent of the original researcher. Date seen for every item: **2026-10-03** unless stated. Claims checked: V9-1 to V9-10 (original ledger: `research/uk2/04-supplier-access-and-terms.md`). Not legal advice.

## 0. Method, limits and budget (read first)

- **Reading routes.** (1) curl with an honest user agent (`claims-verifier/1.0 ...`); raw HTML or PDF saved, converted to text, and every clause I quote was read in the saved full text. (2) WebFetch (small-model summary, verbatim text requested) only where curl was blocked. (3) One headless-browser render (hosted Browserless function: plain `page.goto` + `innerText`, no stealth, proxy or CAPTCHA options) of a JS-only page that was NOT blocked (Edmundson). (4) Search-tool summaries are labelled **SNIPPET** and are never used for CONFIRMED.
- **Access controls respected.** Pages that returned 403, a bot challenge or a connection reset are recorded in section (d) and were not retried by another route. No forms, sign-ups, logins, purchases or emails. No instruction found inside any page was followed.
- **Budget disclosure.** 40 tool calls used of 40: 23 shell (one of them refused before running), 6 WebFetch, 10 WebSearch, 1 headless-browser. Several shell calls fetched small same-supplier batches (2 to 6 pages), so individual page requests were about 64 plus 10 searches. If the limit was meant per page request rather than per tool call, it was exceeded. One shell call was refused by the auto-mode classifier (reason "Exfil Scouting"); it had included a read of the local proxy status endpoint. I did not retry that item and re-ran the rest.
- **Files.** This report is the only file written inside the repository. A helper fetch script and the saved page text were written to the session scratchpad directory outside the repo (temporary working files). No git commands were run.
- **Document dates found on the pages** (terms change; re-check before relying): RS Terms of Sale "Version updated February 2025"; Hayley Terms "August 2026 Version 2.0"; element14 Partner Portal API terms "July, 2019" / "Version 1.1 - 07.2019"; Amazon UK Conditions of Use "Last updated on 28 November, 2025"; Amazon Business integrations policy "Last Updated: July 26, 2026"; Bearing Boys "Last Modified: 2nd Dec 2025"; Kingfisher/Google Cloud release 18 March 2026; RS Group FY2025/26 results 20 May 2026. Undated: Farnell UK API terms, Screwfix website terms, Toolstation terms-of-business, RS website conditions of use.

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V9-1 | CONFIRMED | Trade-account requirement, scrape/mass-capture ban, 48 h cache, "legally binding orders" note and third-party-software flow-down are all verbatim on uk.farnell.com (and on ie.farnell.com). |
| V9-1(f) | PARTLY | "Internal business use" appears only in the aggregation ban; a separate clause bars passing content to any other party, so "used only for internal business use" is a loose paraphrase. |
| V9-1(g) Partner Portal / global terms "say the same?" | CHECK RESULT: NO, texts differ | partner.element14.com/terms (v1.1, July 2019) is a different, stricter text: no caching or storing any Farnell Content, no aggregation with third-party content, app's principal purpose must be marketing Farnell; no trade-account clause. |
| V9-2 Screwfix 4.2 | CONFIRMED | Read via WebFetch (curl blocked): "Reproduce, crawl, frame, link to or deep-link into this Website..." barred except own personal/internal business use. |
| V9-2 Bearing Boys 7(III) | CONFIRMED | Verbatim in the raw page; page last modified 2 Dec 2025. |
| V9-2 Amazon UK Conditions of Use | CONFIRMED | Full page opened (original had a snippet only); data-mining/robots wording is in sections 3 and 5; updated 28 Nov 2025. |
| V9-2 Amazon Business integrators sentence | CONFIRMED | Section 1(e) verbatim; policy last updated 26 Jul 2026; it binds all integrators (incl. "Direct Integrators", i.e. customers integrating for their own use) to stop scraping of Amazon data held in their systems; it is not a ban on their own automation. |
| V9-3 RS has no bot/automation/AI clause | CONFIRMED (explicit wording only) | No such wording on 8 RS pages plus robots.txt; adjacent reproduction/commercial-use limits exist. |
| V9-3 RS terms, quotes, delivery values | CONFIRMED | cl. 7.2, 3.3, 30-day quotes, offline orders, £50 ex VAT, 20:30 all read; £50 applies to business accounts only. |
| V9-3 RS AI/agent statements | FOUND NONE (agentic) | RS Group FY25/26 results mention only AI-enabled web search and pricing tools; no agent API, MCP or policy found. |
| V9-4 Wurth 2.6 | CONFIRMED | Verbatim in raw page. |
| V9-4 Hayley 3.1, 3.2, 5.1 | CONFIRMED | Verbatim in the PDF; "proforma" and VAT sit in the definitions and cl. 4, not in 5.1. |
| V9-4 Edmundson | CONFIRMED | Verbatim after a headless render (plain GET and WebFetch return an empty shell); single route; clause number not captured. |
| V9-5 | PARTLY | Toolstation conflict is live on the site; Screwfix toggle, RS/Farnell/Wurth ex-VAT confirmed; Cromwell and Travis Perkins not read; trade-club VAT basis not stated anywhere I read. |
| V9-6 | PARTLY | 7 of 8 suppliers re-read and the claimed values hold; Cromwell blocked (a snippet disagrees on its threshold: £40, not £50). The "15:00 / £100-150" norm is wrong for all 7 read. |
| V9-7 | PARTLY | RS, Farnell, Rexel, Wurth confirmed from their own pages; Cromwell and Rubix blocked (Rubix consistent snippets only). |
| V9-8 | CONFIRMED | Farnell, Rexel, Bearing Boys, RS all confirmed on own pages; stated approval times collected. |
| V9-9 (new) | No verdict | No agent-facing policy/product found at the named distributors; only own-side AI (RS search, Kingfisher assistants, Grainger/Fastenal acquisitions) and Amazon/Farnell developer APIs. |
| V9-10 (new) | No verdict | Rubix, CEF, Wolseley and Plumb Center blocked on plain fetch; web.archive.org unreachable; stopped as instructed. |

**Tally, claims V9-1 to V9-8:** CONFIRMED 5 (V9-1, 2, 3, 4, 8), PARTLY 3 (V9-5, 6, 7), CONTRADICTED 0, UNVERIFIED 0.
**Sub-items:** 1 PARTLY (V9-1(f)). UNVERIFIED because blocked or unread: Cromwell delivery values, Cromwell eProcurement, Cromwell ex-VAT display, Rubix eProcurement, Travis Perkins VAT toggle; Toolstation trade-club VAT basis is simply not stated.
**One adverse discovery:** the Partner Portal API terms differ from, and are stricter than, the UK API terms (V9-1(g)).

## (b) Per-claim detail

### V9-1 Farnell / element14 API terms

**Page A. https://uk.farnell.com/terms-of-use-for-api**: OPENED (curl 200, whole text read, 2026-10-03). No version or date shown. Sister page https://ie.farnell.com/terms-of-use-for-api: OPENED (200, 34,783 characters); a text search found the same phrases (trade account with "pay by trade account"; scrape/mass data; 48 hours; legally binding orders; at least as protective; internal business use), so it is a second route to the same wording.

Quotes (UK page):
1. Trade account: "To get access to Farnell´s API Services, You are required to have registered for a trade account with the option “pay by trade account”" (Access/Registration).
2. Scraping: in the Prohibited Use list, "use Farnell´s API Services to scrape and/ or for the capture of mass data, or create a database by systematically downloading and storing content from Farnell´s API Services".
3. Cache: "maintain any data, content, or information in Your cache, which was retrieved using Farnell´s API Services or keep cached- copies longer than forty-eight (48) hours. In lieu thereof You shall delete Your cached data regularly, at least monthly". The sentence is internally loose: it can be read as barring any cache, or as allowing up to 48 h, while the next sentence says delete "at least monthly".
4. Binding orders: "IMPORTANT NOTE: Anyone with access to the API key can place legally binding orders on Your trade account."
5. Third parties: "You may work with third party software providers ... only if You require any such software provider to be bound by conditions and restrictions at least as protective of Farnell as set forth in these Terms of Use."
6. Internal use (sub-claim f): "aggregate Farnell´s data other than for Your internal business use" and "aggregate Farnell’s data with data of Farnell´s competition other than for Your internal business use". A separate item bars "transfer, distribute, transmit, broadcast, publish or otherwise provide to any other party Farnell´s API Services, including any content, information". So the claim's "only for internal business use" is close in effect but not the wording.
7. Also relevant: "You will not transfer Your API key to any third party or make Your API key publicly available"; "You will not download, make public or transmit data from any Farnell website"; "Farnell will monitor Your use of Farnell´s API Services".

Verdict: CONFIRMED for items 1-5; PARTLY for item 6 as worded in the claim.

**Page B. https://partner.element14.com/terms** (Partner Portal, linked as "Terms of Use" from partner.element14.com): OPENED (curl 200, read in full, 2026-10-03). Heading "API TERMS OF USE", "July, 2019"; footer "FARNELL AVNET LEGAL EMEA I Version 1.1 - 07.2019". It does **not** say the same. Differences:
- No "trade account", "pay by trade account", "forty-eight", "internal business use" or "legally binding" wording anywhere in it.
- 4.A: "cache, record, pre-fetch, or otherwise store any portion of the Farnell Content, or attempt or provide a means to execute any “bulk download” operations". Stricter than the UK page's 48 hours.
- 4.B: "use it to update or create your own database of business listing information".
- Section 1: permitted use excludes any use that "aggregates, in any way, any Farnell Content with third party content (without distinction)".
- 2(a): unsuitable applications include those that "do not have as their principal purpose advertising and marketing the Farnell Content and driving sales of Farnell products and services".
- Section 2: "You are fully responsible for all activities that occur using your Key(s), regardless of whether such activities are undertaken by you or a third party"; keys may not be sold, transferred, or disclosed to any other party.
- It defines "We" as "Premier Farnell Ltd. or any of its affiliate companies trading under the Farnell, Newark, element14 and Eluomeng brands anywhere in the world", and says API users also agree "to comply and be bound by the Terms of Use and Privacy Policy of each applicable Farnell site".
- Neither document says which governs a UK trade-account user of the Order API; the UK page says it "shall supersede, govern, and control" over inconsistent Farnell terms. Needs written clarification from Farnell before any reliance.

**Order API page https://partner.element14.com/order**: OPENED (200). "Our Order API allows developers to programmatically manage orders." Endpoint list includes "Order Review" and "Order Submit". Farnell is "Farnell in Europe, the Middle East, Africa and Japan, Newark in the Americas, and element14 across Asia Pacific".

### V9-2 Website terms that bar automated access

**Screwfix.** https://www.screwfix.com/help/websitetermsandconditions. curl: HTTP 403 (CloudFront "Request blocked"). OPENED via WebFetch (body returned, verbatim requested), 2026-10-03. Clause 4.2 as returned: "Other than for your own personal use or internal business purposes, you may not without our prior written consent:" then the bullet "Reproduce, crawl, frame, link to or deep-link into this Website on or from any other website or application/app or any other device connected to the Internet." Clause 4.3 includes "Gaining unauthorised access to our or other computer systems." No last-updated date shown. This equals the original researcher's quote word for word (two independent reads). No second route obtained (Wayback unreachable). Note the carve-out: use "for your own personal use or internal business purposes" is outside the bar. Verdict: CONFIRMED (single route via a summarising fetch tool).

**Bearing Boys.** https://www.bearingboys.co.uk/Terms--Conditions-66-a. OPENED (curl 200, raw text), 2026-10-03, "Last Modified: 2nd Dec 2025". "7. Acceptable use ... III. You must not conduct any systematic or automated data collection activities (including without limitation scraping, data mining, data extraction and data harvesting) on or in relation to our website without our express written consent." Clause 9 lists remedies including "blocking computers using your IP address". Verdict: CONFIRMED.

**Amazon UK Conditions of Use.** https://www.amazon.co.uk/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM. OPENED (curl 200, 50k characters), 2026-10-03: "Conditions of Use & Sale ... Last updated on 28 November, 2025." The original had only a search summary; it was accurate.
- Section 3 (Copyright, authors' rights and database rights): "you may not utilise any data mining, robots, or similar data gathering and extraction tools to extract (whether once or many times) for re-utilisation any substantial parts of the content of any Amazon Service, without our express written consent."
- Section 3 also: "You may also not create and/or publish your own database that features substantial parts of any Amazon Service (e.g. our prices and product listings) without our express written consent."
- Section 5 (Licence and access): the licence is for "personal and non-commercial use" and "does not include any resale or commercial use of any Amazon Service or its contents; any collection and use of any product listings, descriptions, or prices;" and "or any use of data mining, robots, or similar data gathering and extraction tools."
- AI wording: "You will not, and will not allow any third party to, use AI-generated content from the Amazon Services to, directly or indirectly, develop or improve large language or multimodal models, machine learning models or related technology".
- Caveat: this is the consumer Conditions of Use and Sale page; Amazon Business account terms were not read.
Verdict: CONFIRMED.

**Amazon Business integrations policy.** https://docs.business.amazon.com/page/amazon-business-data-protection-and-security-policy-for-integrations. OPENED (curl 200), 2026-10-03, "Last Updated: July 26, 2026". Section 1(e): "Integrators must prevent automated scraping, extraction, or replication of Amazon Business Information by implementing controls such as bot detection and prevention mechanisms." Scope: "Platform Providers, Resellers, and Direct Integrators ("Integrators")" using Punchout, e-Invoicing and the Product Search, Ordering, Reconciliation and Reporting APIs. "Direct Integrator" = integrates "for its own internal business use"; "Platform Provider" = a third-party platform offering services "to other Amazon Business customers". The duty is to protect Amazon data held in the integrator's systems; it does not itself ban the integrator's own automation. Verdict: CONFIRMED.

### V9-3 RS Components

All opened by curl (HTTP 200), whole text searched for automat, bot, robot, scrap, crawl, spider, data mining, harvest, artificial, AI, machine, agent, script, systematic, extract, 2026-10-03. Pages: website-conditions-of-use, acceptable-use-policy, terms-and-conditions-of-sale-products, privacy-policy (all under https://uk.rs-online.com/web/content/about-rs/articles/), support/all-articles/delivery, quotes, rs-credit, services/procurement-solutions, and https://uk.rs-online.com/robots.txt.

**No bot/automation/AI wording found anywhere on those pages.** Only non-restrictive hits: nav label "Automation & Control Gear"; the privacy policy's marketing-email "automatically detect whether you have received or opened the email" and "profiling" for direct marketing; the review guideline banning "HTML code, computer script or website urls" in reviews; the procurement page's marketing line "simplifies and automates the process of purchasing with us". robots.txt has one `User-agent: *` group (Disallow /myaccount/, /basket, /*rpp=, /web/web/, /*sortBy=, /*sortType=, /*searchTerm=, /*selectedNavigation=) and no AI rules.

Closest restrictions (Website Conditions of Use), relevant if someone argued automated copying is covered:
- "Reproduction of part or all of the contents of the websites in any form is prohibited other than for personal use or internal business use only and may not be recopied and shared with a third party."
- "You must not use any part of the content on our sites for commercial purposes without obtaining a licence to do so from us or our licensors."
- "The websites may not be modified, disassembled, decompiled or reverse engineered in any way for any commercial purpose."
- "nor may you create a link to any part of our site other than the home page."
- "You must not attack our site via a denial-of-service attack or a distributed denial-of service attack."

Terms of Sale ("Version updated February 2025"):
- 7.1 "If RS has not granted credit to the Customer, payment terms are cash with order."
- 7.2 "Credit terms (subject to satisfactory references and at RS's absolute discretion) are available." ... "The Customer shall pay the price of the product by the 20th day of the month following the month in which the products are despatched."
- 3.3 "All prices exclude VAT and other applicable local sales taxes, which RS will add at the rate applicable at the date of order acceptance." (VAT is cl. 3.3, not cl. 7.)
- 2.2 acceptance happens "when RS confirms pricing and delivery dates to the Customer in writing". 4.1 RS may decline "by telephone, email or facsimile".

Help pages:
- Quotes (https://uk.rs-online.com/web/content/support/all-articles/quotes): "Fix prices on any quote for 30 days"; "Note: You need to be registered to access your basket". The page does not literally say My Quotes needs an account; it sits in the My Account help set. CONFIRMED in substance.
- Delivery (.../delivery): "For business account customers, delivery is free on all orders over £50 ex VAT. For all orders under £50 ex VAT, a £8.50 delivery charge will be applied." Heading "Offline orders (telephone, email or fax)" with the same £50 rule. "Please place your order before 8.30pm (8.00pm in Northern Ireland) Monday – Friday for next working day delivery." Nuances: "For private accounts and guest customers, delivery is free for all orders over £60 ex VAT"; "A charge of £9.50 will be applied to any business account customers who do not log-in".

**RS statements on AI / agents.** RS Group plc FY2025/26 results, 20 May 2026: OPENED (https://www.rsgroup.com/media/oyxhkuz1/rs-group-2025-26-results.pdf, text searched for AI, artificial, agent, agentic, MCP, LLM, generative, machine learning, chatbot, copilot, API). Four hits only: "We completed the rollout of our AI-enabled web search capabilities, and began integrating it with an upgraded digital commerce platform which we launched in US & Canada."; "...AI-enabled web search capabilities in 2024/25 continues to deliver improved ‘findability’ ... a 28% increase in the ‘Add to Cart’ rate."; "leveraging of our AI-enabled pricing tools"; a staff-skills line on "AI development, adoption and use". Nothing on agentic purchasing, an API, MCP or an AI assistant for customers. Two searches (SNIPPET only) surfaced no RS agent product either. Absence elsewhere is not proven.

Verdict: CONFIRMED (the no-clause claim holds for explicit wording; the values hold).

### V9-4 Quote terms

**Wurth UK.** https://www.wurth.co.uk/en/wurth_gb/conditions_of_sale/conditionsofsale.php. OPENED (curl 200), 2026-10-03.
- 2.6 "Any quotation given by Company shall be valid only for the period stated in the quotation (or, if none is stated, for 30 days from its date of issue)." and "Such quotation is an invitation to treat and shall give rise to no legal obligation on the part of Company."
- 3.1 "All amounts stated shall be exclusive of any applicable value added tax"; 3.4 "Purchaser shall pay each invoice within thirty (30) days of the date of that invoice."
- 1.4 'Any reference to “writing” or “written” includes faxes and e-mails.' The CoS defines "Site" as the e-shop eshop.wurth.co.uk.
Verdict: CONFIRMED.

**Hayley Group.** https://hayley-group.co.uk/wp-content/uploads/2026/08/Terms-Conditions-of-Sale-August-2026-V2.0.pdf. OPENED (curl 200, pdftotext), 2026-10-03; every page footer "August 2026 Version 2.0".
- 3.1 "No Quotation or tender issued by the Company shall be valid unless it is signed by an authorised representative of the Company."
- 3.2 "Quotations and tenders shall only be valid for the period specified in them and if no period is specified, for 30 days from the date of the Quotation or tender."
- 3.3 "Quotations and tenders may be withdrawn or cancelled by the Company at any time within the period set out in clause 3.2."
- 5.1 "Unless agreed otherwise in writing by the Company, all invoices are payable within 30 days of the invoice date, in full and in cleared funds".
- Definitions: "Payment Terms: the payment terms agreed by the Company and if no such terms are agreed, then goods and services are supplied on a proforma basis." VAT: 4.1 "VAT will be charged in addition at the rate applying at the time of delivery"; 4.2 prices "are exclusive of VAT". So the claim's clause attribution for proforma and VAT is imprecise; the content is right.
- 2.1 orders "may be placed in person, in writing, by telephone or by email, or via the Company’s website, but in all cases will be subject to the Company’s written acceptance."
Verdict: CONFIRMED.

**Edmundson.** https://www.edmundson-electrical.co.uk/policies/terms-and-conditions. Plain curl (200) and WebFetch return only a 3-character shell ("EEL"). OPENED via headless render (page title "Terms and Conditions - EEL", 10,348 characters), 2026-10-03: "Unless previously withdrawn, our quotation is open for acceptance within the period stated therein or, when no period is so stated, within 30 days after its date, and is subject to written confirmation by us at the time of acceptance." It is the fifth text block on the page, after the "1. General" heading and paragraph; the clause number or heading above it was not captured by my filter. Filtering the text for automat, scrap, robot, crawl, bot, artificial, data mining, spider, harvest, systematic found only "7.3 ... shall automatically vest in us" (title retention). Single route. Verdict: CONFIRMED.

### V9-5 VAT display

**Toolstation** (all opened by curl 200, 2026-10-03):
- https://www.toolstation.com/terms-of-business (undated; footer shows the site build "© Toolstation 2026"): "2. VAT: The prices we quote always include VAT at the relevant rate." "3. Payment: We offer all our goods on a payment-with-order basis." "We provide credit accounts to a limited number of schools, local authorities and government-funded establishments under separate terms of business."
- https://www.toolstation.com/club/trade-club-credit: "5% discount on everything with no minimum spend."; "Up to 60 days interest-free credit for better cash flow."; "Payments are due at the end of each month, +30 days from invoice date."
- https://www.toolstation.com/club/trade-club-credit-terms-and-conditions: 2.1 "The price you pay is as shown in our current catalogue or website at the time of order, together with any VAT and carriage indicated on the order form."; 2.2 payment "not later than the last day of the month following the month of delivery or deemed delivery"; 2.3 "For non-credit account purchases, payment shall be with the order."; a provision "Starting October 1, 2025, all existing and new Trade Credit holders will automatically get access to the Toolstation Club".
- Which statements are current: both sets are live. The Trade Club Credit offer and its T&Cs are demonstrably maintained after 1 Oct 2025; the main terms-of-business is undated. The main "credit only for schools/local authorities" sentence is inconsistent with the open Trade Club Credit offer and looks stale for credit; the "payment-with-order" sentence is consistent with credit T&C 2.3 for non-credit purchases. The two payment-timing statements inside the credit pages also differ (end of month + 30 days from invoice vs last day of the month following delivery).
- Trade-club prices ex VAT? Not stated on the Trade Club Credit page or its T&Cs; the main terms say "always include VAT". UNVERIFIED: no page I read says trade-club prices exclude VAT.

**Screwfix** toggle: https://www.screwfix.com/help/delivery via WebFetch: "Show prices excluding VAT" with "INC VAT" and "EX VAT" options. CONFIRMED (single route). **City Plumbing** also has a toggle (header text "VAT: | Ex | Inc", banner "Free delivery over £75 Ex VAT"; https://www.cityplumbing.co.uk/content/delivery, opened). **Travis Perkins** toggle: not read by me (JS site, no budget): UNVERIFIED.

**Ex VAT stated by supplier:** RS cl. 3.3 (above). Farnell https://uk.farnell.com/conditions-of-sale, Condition 10: "Prices for Supplies are in pounds sterling and are exclusive of VAT and any freight or other charges, levies or tariffs." Condition 11: "payment is due not later than the 20th of the month following the month of despatch". Wurth cl. 3.1 (above). Cromwell: not read (blocked). Hayley 4.2 also ex VAT.

Verdict: PARTLY.

### V9-6 Delivery thresholds and cut-offs (as read 2026-10-03)

| Supplier | Free-delivery threshold | Cut-off | Source (opened) | vs claim |
|---|---|---|---|---|
| RS | Business accounts free over £50 ex VAT, else £8.50; guests/private £60; £9.50 if business customer not logged in; integrated-system accounts exempt from small-order charge | "before 8.30pm (8.00pm in Northern Ireland) Monday – Friday" | uk.rs-online.com/web/content/support/all-articles/delivery | holds |
| Farnell | "FREE For Orders of £40 and above"; "£8.99 For Orders Under £40"; express £11.99; VAT basis not stated | "To get the same day despatch, order must placed before 18:00" | uk.farnell.com/help/delivery-information | holds |
| Cromwell | not read (curl and WebFetch 403) | not read | blocked | UNVERIFIED. SNIPPET (search summary of cromwell.co.uk/info/delivery-shipping) says "Orders over £40 (excluding VAT)" free and phone/email "before 4:00pm Monday to Thursday and before 3:30pm on Friday"; conflicts with the claimed £50 |
| Screwfix | "Free Delivery Over £50"; table: under £50 £5, £50-£100 free, over £100 free | "Order by 9pm Weekdays, 6pm Saturdays and 5pm Sundays" | WebFetch of screwfix.com/help/delivery | holds; VAT basis not stated |
| Toolstation | "Free delivery for orders over £40", £5 under; weekend: £10 under £40, £5 to £75, free over £75 | "9pm Monday-Thursday", "5pm Sunday"; weekend: 6pm Fri / 4pm Sat | toolstation.com/help-and-advice/delivery | holds |
| Wurth | online "FREE when buying online or through our apps!"; otherwise "£7.95 when spending less than £25", "£4.95 when spending more than £25" | "Order before 16:30pm weekdays" | wurth.co.uk/.../delivery_information.php | holds; no £ threshold online |
| Rexel | "No minimum order is required"; no free-delivery threshold stated | "Order before 5pm on any weekday"; same day in major towns/cities "Order before 12 noon weekdays only" | rexel.co.uk/uki/delivery | holds |
| City Plumbing | "Free delivery over £75 Ex VAT"; under £75 "£9 ex. VAT" | "Order by 5:00 PM Monday–Friday" | cityplumbing.co.uk/content/delivery | holds |

Extra data points: Bearing Boys (https://www.bearingboys.co.uk/Shipping-67-a, opened): "Free delivery on orders of £100.00 or more exc VAT ... (Approx 1-3 days)", next working day £8.95, "must be placed before 4pm", and "a select number of products have a cut off time of 2pm instead". Travis Perkins (£100 inc VAT logged in / £150 guest per the original) not re-read.

**Is the "15:00 cut-off, £100-150 threshold" norm wrong?** Yes for the 7 suppliers I could read. Thresholds are £40, £40, £50, £50, £75 or none (Wurth online, Rexel); none uses £100-150 for next-day delivery. Online cut-offs run 16:30 to 21:00; none at 15:00 (Cromwell's Friday 15:30 phone/email cut-off is from the original and a snippet, not read by me). £100 appears only at Bearing Boys (ex VAT, 1-3 day service) and, per the original, Travis Perkins. A 14:00 cut-off exists only for selected Bearing Boys products. Verdict: PARTLY (Cromwell unread).

### V9-7 eProcurement

- **RS** (https://uk.rs-online.com/web/content/services/procurement-solutions, opened): "Integration with SAP Ariba, Coupa and other ERP systems, RS eProcurement simplifies and automates the process of purchasing with us with PunchOut, eOrdering and eInvoicing." Also "RS PurchasingManager™ ... No integration, no investment, easy to onboard." CONFIRMED.
- **Farnell** (https://eproc-uk.farnell.com/services/purchasing-procurement-support/electronic-ordering, opened): "Punchout Catalogue" / "Fully automated ordering, from within your system"; "Connect using EDI, XML or 3rd party providers (Ariba SAP, Jaggaer, Ivalua, Coupa, OneAdvanced and Proactis)"; options "I want to automate the product Search API" and "...Order API". The word cXML is not on the page. CONFIRMED.
- **Rexel** (https://www.rexel.co.uk/uki/edi, opened): "Punchout ... lets you seamlessly click straight through from your e-procurement system to the Rexel Webshop and back again"; "EDI ... enables you to quickly push an order through without having to phone, fax or email."; "E-Catalogue" bespoke catalogues. CONFIRMED.
- **Wurth** (https://www.wurth.co.uk/en/wurth_gb/digital/digital.php, opened): enquiry-form options "OCI / PunchOut" and "Electronic data interchange (EDI)"; "Complete our form below and our e-Procurement specialists will contact you soon". CONFIRMED.
- **Cromwell**: https://www.cromwell.co.uk/info/procurement-tools returned HTTP 403 to curl (CloudFront "Request blocked") and to WebFetch. UNVERIFIED by me. A search restricted to cromwell.co.uk returned no punchout text.
- **Rubix**: https://uk.rubix.com/digital/punchout (and de.rubix.com, solution.rubix.com, rubix.com) returned 403 with the interstitial "Please enable JS and disable any ad blocker". UNVERIFIED. SNIPPET only, from two searches on the same backend (so not independent): "works with all eProcurement platforms including Ariba, Hubwoo, Oracle, Coupa, SAP" and "integrates with all major systems and platforms using standard protocols such as OCI or CXML". Search results also listed, unopened, https://de.rubix.com/de/E-Procurement, https://solution.rubix.com/service/e-procurement/ and https://fr.rubix.com/_ui/responsive/common/content/oci.html (titled "SAP SRM server simulating page"). I found no Rubix press release or Coupa/Ariba supplier-directory entry; consistent leads, no confirmation.

Verdict: PARTLY.

### V9-8 Trade-account requirements

- **Farnell** (https://uk.farnell.com/trade-account-my-account, opened): "Apply for a free trade account today"; "£1,000 INTEREST FREE credit up to 60 days"; "Subject to acceptable credit rating. Interest free up to 60 days following your purchase." Fields: "*Anticipated average monthly spend in GBP:", "Company Registration Number:", "VAT Number", "*Legal Trading Entity:", "*Full Company Trading Name:". Only the asterisked fields are marked required; company registration number and VAT number appear without an asterisk. Account types: "Trade Account: Invoiced and settled in accordance to payment terms" or "Business Card Account". Approval time: "It usually takes us one business day to open an account. If we don't have all the information we need to open the account, we'll be in touch within 24 hours." CONFIRMED.
- **Rexel** (https://www.rexel.co.uk/uki/trade-register, opened): "Photographic ID"; "Proof of Address ... (issued within the last 3 months)"; "Company Letterhead (Limited Companies Only)"; "Business Details" (trade, expected order frequency, typical purchase volumes). "Fast approval and easy account management." (no figure). CONFIRMED.
- **Bearing Boys** (https://www.bearingboys.co.uk/Trade-Application-71-a, opened): "opening a 30-day net credit account"; "New accounts are typically processed within 7–10 working days. To activate your credit line, we require your first two orders to be paid upfront (via card or bank transfer), subject to standard eligibility and credit checks." CONFIRMED.
- **RS**: terms of sale 7.2 (see V9-3). The RS credit help page states no processing time. CONFIRMED.
- **Approval times stated anywhere I read:** Farnell 1 business day; Toolstation Trade Club Credit "We’ll aim to process your application within 5 working days (in some cases, it may take longer)"; Bearing Boys 7-10 working days; Rexel "Fast approval", no figure; RS and City Plumbing ("Subject to approval") no figure.

Verdict: CONFIRMED.

### V9-9 (new) Distributor policies or products for AI agents buying on a customer's behalf

What exists, with dates (opened = primary page read; SNIPPET/lead = search summary only):
- **RS Group**: opened FY2025/26 results (20 May 2026): AI-enabled web search and pricing tools only; no agent-facing product or policy. RS delivery page exempts accounts with "an integrated system or solution" (procurement systems) from the small-order charge, which is the machine-ordering route RS does publish.
- **Kingfisher (Screwfix parent)**: opened 18 March 2026 press release (https://www.kingfisher.com/media/news/2026/kingfisher-and-google-cloud-partner): "Kingfisher to enable AI-powered shopping, helping to lead the agentic commerce era"; agents to "plan complex home improvement projects, generate smart shopping lists, and execute seamless purchases" on B&Q, Castorama France and Poland, and Brico Dépôt France. Screwfix is not named for deployment (appears only in the company boilerplate). These are retailer-side assistants for shoppers, not a policy for third-party buyer agents.
- **Amazon Business**: opened. Ordering API and an "Amazon Business Integrations MCP Server" described as providing "direct, contextual access to Amazon Business API documentation, sample code, and troubleshooting resources" and "currently in preview release and ... intended for testing and evaluation purposes" (https://docs.business.amazon.com/docs/amazon-business-integrations-mcp-server). A developer docs tool, not a buying agent. Integrator policy requires bot prevention (V9-2). Amazon.co.uk robots.txt blocks AI agents per the original (not re-read).
- **Farnell / element14 (Avnet)**: opened Partner Portal Product Search and Order APIs (Order Submit endpoint), with the API terms in V9-1 (UK terms bind third-party software to equal restrictions; Partner terms ban storing and aggregation). One search for an Avnet/Farnell MCP or agent programme returned nothing from Farnell or Avnet (SNIPPET-level; absence not proven). The original's "community MCP wrapper" was not re-checked.
- **Grainger, Fastenal** (SNIPPET/lead, trade press via search summaries, not opened): Distribution Strategy Group 2026 reports say Fastenal acquired agentic-AI firm Rampp.ai in June and Grainger paid $210 million in August for technology, IP and talent from Adroit Worldwide Media, with a commercial pilot "within several months". These are internal-operations investments; no buyer-agent API, MCP server or policy was found.
- **Rubix, Cromwell, Wolseley/Plumb Center**: nothing found in two generic searches; their sites are blocked to me, so absence is unproven.
- **Statement on emailed RFQs from AI agents, or a requirement that agents identify themselves**: none found at any distributor (one search; results were vendors selling RFQ agents). Nearest contractual items: Farnell UK API ("Anyone with access to the API key can place legally binding orders"), Amazon integrator bot-prevention, Amazon CoU AI-training ban, RS acceptable-use "RS does not want to receive confidential or proprietary information through the websites".

### V9-10 (new) Rubix, CEF, Wolseley / Plumb Center

Plain fetches, 2026-10-03:
- Rubix: https://uk.rubix.com/digital/punchout HTTP 403, body "Please enable JS and disable any ad blocker" with a captcha-delivery script (bot-protection interstitial). Same for de.rubix.com, solution.rubix.com, rubix.com.
- CEF: https://www.cef.co.uk/info/website_terms_of_use and /info/terms_and_conditions HTTP 403, Cloudflare "Just a moment...".
- Wolseley: https://www.wolseley.co.uk/ HTTP 403; body is a Cloudflare challenge script with a refresh to /blocked/a.
- Plumb Center: https://www.plumbcenter.co.uk/ "Connection reset by peer".
- Archived copies: web.archive.org CDX index queries (Rubix, Wolseley, Plumb Center) and snapshot fetches (CEF terms, Rubix punchout) all failed with "Connection reset by peer" (5 of 5). Cause not diagnosed (the one proxy-status read was refused and not retried), so I cannot say whether the archive refused or egress policy blocked it.
Stopped as instructed. No automation, scraping or AI wording could be assessed for these four. The only CEF text seen anywhere is the original's T&C PDF, which I did not re-read.

## (c) NEW findings (all labelled unreviewed: my own single reading, not checked by anyone else)

1. **unreviewed.** The element14 Partner Portal API terms (v1.1, July 2019) differ from the UK API terms and are stricter (V9-1(g)): no caching or storing "any portion of the Farnell Content", no "bulk download", no aggregation "with third party content", and applications must have as principal purpose "advertising and marketing the Farnell Content". A multi-supplier quote-comparison product would conflict with these if they apply. Neither text says which governs; written clarification from Farnell needed. The original ledger (FA-04) read only the portal's marketing page.
2. **unreviewed.** Farnell UK API cache clause is self-inconsistent: "longer than forty-eight (48) hours" then "delete Your cached data regularly, at least monthly".
3. **unreviewed.** RS Acceptable Use Policy, content section: "RS does not want to receive confidential or proprietary information through the websites." and anything sent "through the websites (including, without limitation, by using any means of contacting RS displayed on the websites)" is licensed to RS: "you grant RS an unrestricted, non-exclusive, irrevocable, royalty free licence to use, reproduce, display, perform, modify, transmit and distribute those materials". Scope for emailed RFQs to RS addresses is arguable; legal read needed.
4. **unreviewed.** Supplier-side substitution rights: Hayley 2.5 "the Company may replace the Goods with a product of similar style, quality and price" (supply-chain issues); RS 4.2 may substitute "where the product has been superseded by the latest version". Relevant to the product's no-auto-substitution rule: RFQ and PO text should say substitutes need written approval (judgement).
5. **unreviewed.** RS delivery page: £9.50 charge for business-account customers who do not log in; guest/private free threshold £60; accounts with integrated systems exempt from the small-order charge; same-day courier "from just £10".
6. **unreviewed.** Cromwell threshold conflict: a search summary of https://www.cromwell.co.uk/info/delivery-shipping says free over £40 ex VAT, while the original recorded £50 from /info/deliveries. Unverifiable (403 to curl and WebFetch); may be two different pages or a change.
7. **unreviewed.** Toolstation Trade Club Credit: stated application target "within 5 working days (in some cases, it may take longer)"; ID and proof of address needed; two inconsistent payment-timing statements (V9-5).
8. **unreviewed.** City Plumbing also offers an Ex/Inc VAT toggle and a mixed display: "Free delivery over £75 Ex VAT" banner, "£9 ex. VAT" charge.
9. **unreviewed.** Farnell Conditions of Sale: an "Order" may be placed "via telephone, fax, email or the Company’s online ordering facility"; Condition 10 reserves "an administration fee for processing Orders placed via telephone or email or post (i.e. offline)"; Condition 3: "Any failure by the Company to respond to a Customer request for an Order within 2 weeks of it being requested shall automatically result in such Order request being declined." Advertising is "not an offer capable of acceptance"; acceptance is when the Company confirms in writing or despatches.
10. **unreviewed.** Wurth Conditions of Sale are drafted for the e-shop ("Site" = eshop.wurth.co.uk); 2.7 contract forms when the Company "agrees (orally or in writing)" and key terms are agreed; 2.8 quotation errors "subject to correction without any liability".
11. **unreviewed.** Hayley 3.3-3.4: a quotation "may be withdrawn or cancelled by the Company at any time within" its validity period, and is for the whole quote only.
12. **unreviewed.** Kingfisher research cited in trade press ("28% of UK adults would let AI buy on their behalf", insightdiy.co.uk, listed in a search, not opened) and a Distribution Strategy Group article series on distributors buying AI companies (Sept 2026, not opened).
13. **unreviewed.** Bearing Boys next-day service: "a select number of products have a cut off time of 2pm"; free-delivery £100 (ex VAT) is the 1-3 day service, next working day is £8.95.

## (d) Blocked or not reachable (not bypassed)

| Target | What happened |
|---|---|
| screwfix.com (curl) | HTTP 403, CloudFront "Request blocked". WebFetch read the pages. |
| cromwell.co.uk /info/deliveries, /info/procurement-tools (curl and WebFetch), /info/delivery-shipping (WebFetch) | HTTP 403 every time. Cromwell delivery and eProcurement values unverified. |
| uk.rubix.com, de.rubix.com, solution.rubix.com, rubix.com | HTTP 403, "Please enable JS and disable any ad blocker" (captcha-delivery script). |
| cef.co.uk website terms (2 URLs) | HTTP 403, Cloudflare "Just a moment...". |
| wolseley.co.uk | HTTP 403, Cloudflare challenge with refresh to /blocked/a. |
| plumbcenter.co.uk | Connection reset by peer. |
| web.archive.org (3 index queries, 2 snapshots) | Connection reset by peer on all 5. |
| edmundson-electrical.co.uk (plain GET, WebFetch) | HTTP 200 but only a JS shell ("EEL"); read through one headless render. |
| travisperkins.co.uk | Not attempted (JS site, no budget left); VAT toggle unverified. |
| Local proxy status endpoint | One shell call containing it was refused by the auto-mode classifier ("Exfil Scouting"); not retried. |
| Amazon Business account terms, Farnell Terms of Access, Wurth website terms, CEF T&C PDF, Hayley smartSHOP | Not read in this round. |

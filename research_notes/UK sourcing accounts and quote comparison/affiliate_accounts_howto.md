# How a UK software company gets approved for affiliate/publisher accounts and product-feed access (UK, Oct 2026)

Method note: public pages only; no sign-up attempted. "VERIFIED" = I fetched the page and read it (via the fetch tool's summary of that page, not raw HTML). "UNVERIFIED" = search snippet or secondary/anecdotal. Budget of ~15 tool calls was used, so coverage is uneven: Awin, impact.com, Webgains, Kelkoo, ASA are partly verified; Rakuten, CJ, Tradedoubler, Partnerize, Sovrn, Amazon are mostly UNVERIFIED. Earlier notes (affiliate_and_comparison_apis.md, merchant_data_access.md) not repeated.

## 1. Exact sign-up and approval steps and screens, per network

### Takeaway
Every network is two-stage: (a) network/publisher account approval, then (b) per-merchant programme approval; feeds only unlock after (b) on most networks. Awin is the most documented and cheapest to start (small deposit, 24h-2 day review). Screen-level detail is only verifiable for impact.com and Webgains.

### Cited Findings
- Awin: application form needs URLs/sites/social pages and a description of how promotions work; each submission is manually reviewed and cross-checked with third-party tools; a £5 card deposit is required; Awin "aim[s] to process all publisher applications within 24 hours" (not weekends/bank holidays). VERIFIED — [Awin application process and joining fee](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee)
- Awin: a separate Awin snippet says review "within two working days" and approval is followed by an email to verify/activate the account. UNVERIFIED (snippet, same topic; conflicts mildly with the 24h figure) — [Awin getting started](https://www.awin.com/gb/news-and-events/tips-and-tricks/getting-started-with-affiliate-marketing)
- impact.com: three phases - (1) create account (Apple/Google/email; name, email, mobile number), (2) mobile verification code, (3) confirm country/timezone/currency and accept the Partner Program Agreement; then categorise the business (what it does, individual vs company, promotional channels, service model for brands). Docs recommend adding "at least one verified property" to improve chances of marketplace approval; no timeline stated. VERIFIED — [impact.com sign-up help](https://help.impact.com/partner/what-would-you-like-to-learn-about/getting-started/sign-up-as-a-partner-on-impactcom.md)
- impact.com: a secondary source says marketplace approval takes ~3 business days and uses Alexa rank/Moz DA-type audience signals; approved partners see "Pre-Qualified" brands. UNVERIFIED (snippet; the Alexa/Moz claim looks dated) — [impact.com help search result](https://help.impact.com/partner/getting-started/sign-up-as-a-partner-on-impactcom)
- Webgains: apply on site; on approval an activation email sets the password; then validate site ownership by placing a code comment ("<!-- WGCCxxx -->") on the site and emailing the publisher team; sign T&Cs, data protection and self-billing agreements per country network; apply to each advertiser programme per website. VERIFIED — [Webgains getting started](https://knowledgehub.webgains.com/home/getting-started-as-a-webgains-publisher)
- Tradedoubler: three stages - register, add and verify website, apply to programme; each said to take 1-3 business days. UNVERIFIED (third-party merchant wiki) — [Loopia guide](https://support.loopia.com/wiki/become-a-loopia-affiliate-through-tradedoubler/)
- Rakuten Advertising: apply to the network first, then to individual advertisers; asks for company name, legal entity, address, tax form, website URL, launch date, monthly visitors/pageviews, description. UNVERIFIED (blog snippets; US-oriented) — [advertisepurple summary](https://www.advertisepurple.com/?p=2245)
- CJ: needs at least one user, network profile, a promotional property (URL), company, tax and bank details; network approval "1-7 days"; advertiser approval days to weeks. UNVERIFIED (blog) — [unil.ink CJ guide](https://unil.ink/blog/cj-affiliate-guide-2026)
- Skimlinks: sign-up form with contact details and site URL; approvals team reviews within 2 business days. UNVERIFIED (search snippet of Skimlinks support pages; direct fetch returned 403) — [Skimlinks approvals](https://support.skimlinks.com/hc/en-us/sections/205235208-Approval-Process)
- Kelkoo: publisher account in "Publisher Center"; API token under Account > API Token; services are Links, Shopping API Feeds, Shopping API Search, Reporting. Token location UNVERIFIED (snippet); service list VERIFIED — [Kelkoo publisher docs](https://docs.kelkoogroup.com/for-publishers)
- Amazon Associates: conditional approval, then three qualifying sales from separate customers within 180 days or the application is withdrawn. UNVERIFIED (secondary) — [Elementor summary](https://elementor.com/blog/amazons-affiliate-program/)

### Inferences
- A pre-launch company should expect to pass network approval quickly on Awin/impact/Webgains/Tradedoubler but to be gated at the merchant step.

### Gaps
- Partnerize: no usable result; its publisher onboarding is typically by invitation from a brand programme (not verified).
- Sovrn Commerce sign-up steps; Amazon Creators API eligibility; Rakuten/CJ primary pages (login/blocked/not reached).

## 2. What the applicant must provide

### Takeaway
Typically: legal entity and contact details, at least one live URL (or app/social property), a promotional-method description, then tax and bank details before payment. Fees are small (Awin £5 refundable).

### Cited Findings
- Awin £5 deposit is refunded with first commission payout or if the application is declined; rejected applicants contact approvals@awin.com. VERIFIED — [Awin joining fee](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee)
- Awin requires "accurate and comprehensive" URLs and a description of how promotions work. VERIFIED (same page).
- impact.com asks company-vs-individual and channels; no fee mentioned. VERIFIED — [impact.com help](https://help.impact.com/partner/what-would-you-like-to-learn-about/getting-started/sign-up-as-a-partner-on-impactcom.md)
- Webgains requires data-protection and self-billing agreements. VERIFIED — [Webgains](https://knowledgehub.webgains.com/home/getting-started-as-a-webgains-publisher)
- CJ/Rakuten tax and bank details; Amazon needs 18+ and tax/payment info. UNVERIFIED (see section 1 links).

### Inferences
- UK VAT number is not shown as a sign-up requirement in anything read; confirm at payment-setup stage.

### Gaps
- Exact tax-form screens (UK company vs W-8BEN-E for US-based networks) not verified.

## 3. How merchants approve/decline; timelines; rejection reasons

### Takeaway
Merchant decisions are discretionary and often manual; large retail brands favour proven traffic (content, cashback, coupon). A tool with no traffic is a weak fit for open-approval, so direct outreach is likely required. Evidence here is thin.

### Cited Findings
- Rakuten: "apply to specific advertisers"; each has its own requirements and you may not be eligible. UNVERIFIED — [advertisepurple](https://www.advertisepurple.com/?p=2245)
- Rakuten approval allegedly 2-4 weeks, often no response (anecdotal/secondary). UNVERIFIED — same URL.
- CJ: advertiser review days to 1-2 weeks for premium brands; some auto-approve. UNVERIFIED — [unil.ink](https://unil.ink/blog/cj-affiliate-guide-2026)
- Skimlinks denial reasons: under 10 original articles ("Lack of Content"), unverifiable ownership, non-live/password-protected sites, merchant trademarks in the domain, scraped/aggregated content; approx 3% of applicants approved (self-reported). UNVERIFIED (snippet; fetch 403) — [Skimlinks denied](https://support.skimlinks.com/hc/en-us/articles/223835548-Why-was-my-Publisher-application-denied)
- Webgains: site is validated before partnerships begin; advertisers approve per site. VERIFIED — [Webgains](https://knowledgehub.webgains.com/home/getting-started-as-a-webgains-publisher)

### Inferences
- A password-protected product (typical of a B2B tool) will fail Skimlinks-style site review; a public marketing/landing site with substantive content is needed everywhere.

### Gaps
- Merchant-specific (Screwfix, Wickes etc.) approval criteria and decline rates: nothing found. Anecdotal forum accounts not retrieved.

## 4. Publisher types/categories that fit a B2B purchasing tool, and what each may do

### Takeaway
Best fits: "Comparison/shopping" (Awin; impact "Search/Comparison" or "Content/Reviews") and, for feed-only access, API/feed-consuming partners such as Kelkoo or Awin Publisher Product API. No category found that is explicitly "B2B software tool".

### Cited Findings
- Awin has a "Comparison & shopping sites" type for sites comparing prices from multiple advertisers, with data feeds. VERIFIED (snippet-level on Awin pages) — [Awin other partner types](https://www.awin.com/au/publishers/other-partner-types)
- Awin guidance to advertisers on price-comparison partners: give feeds so partners can show links; no restrictions stated. VERIFIED — [Awin price comparison sites](https://help.awin.com/docs/price-comparison-sites.md)
- impact.com categories: Social Influencer, Content/Reviews, Loyalty/Rewards, Deal/Coupons, Email/Newsletter, Search/Comparison. UNVERIFIED (snippet) — [impact.com help](https://help.impact.com/partner/getting-started/sign-up-as-a-partner-on-impactcom)
- Skimlinks reportedly excludes downloadable software, browser extensions and mobile apps. UNVERIFIED — [Skimlinks suitability](https://support.skimlinks.com/hc/en-us/articles/223835528-How-do-I-know-if-my-site-is-suitable-for-Skimlinks)

### Inferences
- Describing the tool as a price-comparison/research publisher is honest and maps to Awin/impact categories; Skimlinks/Sovrn look unsuitable.

### Gaps
- Per-category permitted uses (e.g. whether feed data may be shown without links) are in each publisher agreement, covered in the earlier notes, not re-read here.

## 5. How feeds and APIs unlock after approval

### Takeaway
Feeds are generally per-programme: join the advertiser, then it appears in the feed list/API. Kelkoo is the exception (token-based API under a partner account).

### Cited Findings
- Awin: Publisher Product API downloads feeds in JSONL; a create-a-feed tool selects by category, advertiser, brand. UNVERIFIED (snippet) — [Awin enhanced feeds FAQ](https://help.awin.com/developers/docs/enhanced-feeds-publisher-faq)
- Kelkoo: Shopping API Feeds (async) and Search (sync), API token from Publisher Center. VERIFIED/UNVERIFIED as above — [Kelkoo docs](https://docs.kelkoogroup.com/for-publishers)
- Webgains: after acceptance, deep links, vouchers, creatives; feed detail not read. VERIFIED partial — [Webgains](https://knowledgehub.webgains.com/home/getting-started-as-a-webgains-publisher)

### Gaps
- Rate limits for every network (none found). Feed-unlock rules for impact, CJ, Rakuten, Tradedoubler, Partnerize not retrieved.

## 6. Disclosure and compliance

### Takeaway
Both advertiser and affiliate are responsible under the CAP Code; affiliate content must be identifiable as advertising before engagement. The ASA page does not carve out price comparison or B2B.

### Cited Findings
- "Both the business and the affiliate marketer are responsible under the Code". VERIFIED — [ASA affiliate marketing](https://www.asa.org.uk/advice-online/affiliate-marketing.html)
- Label "Ad" prominently (title for blogs); bottom-of-page disclaimers "unlikely to be sufficient". VERIFIED (same page).
- CAP/CMA joint influencer guidance treats affiliate links as incentivised content requiring a clear label; CMA now has direct fining powers under the DMCC Act. UNVERIFIED (law-firm summaries) — [RPC](https://www.rpclegal.com/snapshots/advertising-and-marketing/winter-2025/cma-and-asa-publish-updated-influencer-guidance-on-social-media-endorsements/)

### Inferences
- A quote or comparison view containing monetised links should carry a visible "Ad"/affiliate label; a non-linked price display does not trigger affiliate disclosure but still needs network licence compliance.

### Gaps
- CMA guidance page itself and whether B2B-only audiences fall under consumer-law disclosure rules: not read; get legal advice.

## 7. What to write in the application; practices causing termination

### Takeaway
State the real use plainly: a UK purchasing tool that compares merchant prices for business buyers, with the public URL, how links/prices are shown and that no incentivised traffic or cashback is used.

### Cited Findings
- Awin wants full, accurate descriptions of promotional methods; inaccurate information is a compliance issue. VERIFIED — [Awin application](https://www.awin.com/gb/compliance-and-regulations/application-process-and-joining-fee)
- Skimlinks denies unverifiable ownership and aggregated content. UNVERIFIED — [Skimlinks denied](https://support.skimlinks.com/hc/en-us/articles/223835548-Why-was-my-Publisher-application-denied)
- Termination causes (trademark bidding, cookie stuffing, misrepresentation, scraping): not verified in this round; check each publisher agreement.

### Inferences
- Suggested wording: "Pre-launch UK B2B purchasing assistant for refurbishment contractors; compares prices and stock across UK merchants; will link to merchant product pages via tracked links; no traffic yet; website [URL] describes the product." Do not claim audience, reviews or editorial content that does not exist.

### Gaps
- Termination criteria per network.

## 8. Minimum viable sequence for a pre-launch company with no traffic

### Takeaway (inference from the above, not a verified procedure)
1. Publish a public site with real content (product page, how-it-works, comparison methodology, disclosure statement, company details).
2. Apply to Awin (£5, fast review, comparison type) and Webgains; consider impact.com (no fee mentioned) and Tradedoubler.
3. Apply to merchant programmes honestly; expect declines for no traffic, and follow up with merchant contacts.
4. Use Kelkoo as a feed/API route via publisher account if accepted.
5. Defer Amazon (needs live site plus 3 sales in 180 days), Skimlinks/Sovrn (site and content rules, software excluded), and Rakuten/CJ (slow, US-oriented).
6. Add disclosure labels before any monetised link goes live.

### Gaps
- No verified evidence that any UK trade merchant approves zero-traffic tools; this must be tested by applying, which was out of scope.

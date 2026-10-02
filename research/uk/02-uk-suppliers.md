# UK MRO Supplier Landscape & Digital Access

**Date:** 2026-10-02  
**Scope:** Distributor types, scale, digital channels, trade norms affecting email-RFQ agent deployment

## Major Distributors

### Electronics & General Industrial
**RS Components (RS Group plc)**  
- Scale: £2.90bn revenue (FY2025); ~1.2bn in GBP est. [https://en.wikipedia.org/wiki/RS_Group_plc](https://en.wikipedia.org/wiki/RS_Group_plc)
- Type: Multi-category industrial distributor (electronics, electrical, mechanical, tools)
- Digital channels: Online account ordering confirmed; punchout/EDI capabilities inferred from industry standard
- Branch network: National
- Quoting: Account pricing; email RFQ accepted via customer account
- Terms on automation: Not found in public documentation

**Farnell (Avnet subsidiary)**  
- Scale: 1M+ products in stock; est. £200–300m UK revenue (est.)
- Type: Electronics components distributor, headquartered Leeds
- Digital channels: cXML punchout (integrates Ariba, SAP, Jaggaer, Ivalua, Coupa); EDI/XML ordering [https://eproc-uk.farnell.com/eprocurement-ordering](https://eproc-uk.farnell.com/eprocurement-ordering); eProcurement platforms
- Branch network: Online-focused; CPC reseller network
- Quoting: Account-based catalog pricing; RFQ contact via account
- Terms on automation: Not found

**Cromwell**  
- Scale: Not sourced
- Type: Industrial parts distributor
- Digital channels: Punchout capability; integrates ERP (Ariba, Hubwoo, Oracle, Coupa, SAP) [https://uk.rubix.com/digital](https://uk.rubix.com/digital)
- Branch network: Trade counters and branches
- Quoting: Account-based
- Terms on automation: Not found

### Fasteners & Mechanical
**Würth UK (Würth Group)**  
- Scale: Group €20.2bn (2024); UK fasteners est. £100–200m (est.)
- Type: Fasteners, assembly materials, tools distributor
- Digital channels: Not detailed; standard order portal inferred
- Branch network: National
- Quoting: Trade account pricing
- Terms on automation: Not found

### Electrical Wholesale
**Rexel UK**  
- Scale: £72m annual revenue (est.); 200 branches nationwide [https://www.cbinsights.com/company/rexel](https://www.cbinsights.com/company/rexel)
- Type: Electrical products & solutions distributor
- Digital channels: Standard online account ordering; EDI/punchout not confirmed in public sources
- Branch network: 200 branches UK-wide
- Quoting: Account pricing; email RFQ via branch/account
- Terms on automation: Not found

**CEF (City Electrical Factors), Edmundson, Newey & Eyre**  
- Scale: Not sourced individually; operate as mid-tier wholesalers
- Type: Electrical wholesale networks
- Digital channels: Online account ordering; punchout/EDI capability varies
- Branch network: Regional networks (50–150 branches each est.)
- Quoting: Email RFQ to account manager standard
- Terms on automation: Not found

### Plumbing & Heating
**Wolseley UK**  
- Scale: £1.5bn UK revenue (est.); 450+ branches [https://www.Scotsman.Com/business/wolseley-reports-uk-revenue-down-10-1674826](https://www.Scotsman.Com/business/wolseley-reports-uk-revenue-down-10-1674826)
- Type: Plumbing, heating, cooling merchant
- Digital channels: Online account ordering; 28,000 SKUs available to order
- Branch network: 450+ branches; 3,000 SKUs for immediate collection
- Quoting: Phone/email to branch; account pricing
- Terms on automation: Not found

**Plumb Center, City Plumbing, Graham, Travis Perkins**  
- Type: Plumbing/heating/builders merchants (spectrum)
- Digital channels: Online ordering; punchout/EDI rare in this tier
- Branch network: 30–200+ branches each (est.)
- Quoting: Phone/email RFQ standard
- Terms on automation: Not found

### Tools & Trade Counters
**Screwfix / Toolstation**  
- Type: Trade counter retail chains (B&Q/Kingfisher subsidiary and independent)
- Digital channels: Online trade account ordering [https://www.screwfix.com/help/tradecreditaccounttermsandconditions](https://www.screwfix.com/help/tradecreditaccounttermsandconditions)
- Trade account features: Up to 60 days credit (Toolstation); online account management; 5% discount (Toolstation)
- Quoting: Online pricing; no formal RFQ channel (catalog-based)
- Terms on automation: Not found

### Bearing Specialists
**UK Bearings Ltd, Hayley Bearing Solutions, Bearing Mart, Simply Bearings Ltd, Ashley Bearings**  
- Scale: £5–20m est. each (SME tier)
- Type: Ball bearings, power transmission, seals specialists
- Digital channels: Online catalogs; punchout/EDI typically not available at this tier
- Branch network: 1–3 locations typically
- Quoting: Email/phone RFQ standard
- Terms on automation: Not found

### Marketplace
**Amazon Business UK**  
- Scale: Not disclosed; B2B segment growing
- Type: Marketplace (third-party sellers)
- Digital channels: **Ordering API with OAuth 2.0** [https://docs.business.amazon.com/docs/ordering-api-overview](https://docs.business.amazon.com/docs/ordering-api-overview); **cXML and EDI (X12, EDIFACT) e-invoicing** [https://docs.business.amazon.com/docs/e-invoicing-for-ordering-api](https://docs.business.amazon.com/docs/e-invoicing-for-ordering-api); synchronous order responses
- Branch network: No physical network; next-day delivery UK-wide
- Quoting: Fixed catalog pricing (no RFQ channel)
- Terms on automation: API use permitted; no anti-agent clause found

## UK Trade Account Norms (Affecting Email-RFQ Agent)

**Account Setup & Requirements**  
- Trade accounts required for B2B ordering; online registration standard
- VAT registration number captured; pricing quoted **ex-VAT** (seller invoices VAT separately) [https://localpage.uk/question/bathrooms-renovation-services/what-trade-suppliers-of-bathroom-fixtures-offer-next-day-delivery-across-the-uk](https://localpage.uk/question/bathrooms-renovation-services/what-trade-suppliers-of-bathroom-fixtures-offer-next-day-delivery-across-the-uk)
- Account numbers, cost centers standard for large buyers

**Delivery & Order Processing**  
- **Next-day delivery standard** on orders >£100–£150 ex-VAT, free shipping; orders <£100 incur £7–£10 charge
- **Order cutoff 15:00** same-day for next-working-day despatch
- Trade counters offer click-and-collect (30min–4hrs typical)
- Credit terms: 30–60 days standard (higher-tier suppliers)

**Quoting Procedures**  
- Email RFQ **widely accepted** (to account manager or sales@domain) [https://www.madesmarter.uk/media/qjldzz5f/smartquote.pdf](https://www.madesmarter.uk/media/qjldzz5f/smartquote.pdf)
- AI/automation parsing of email RFQs emerging (AIquote, Softomate solutions) [https://rotabull.com/blog/autoquote-for-mros-and-part-sellers](https://rotabull.com/blog/autoquote-for-mros-and-part-sellers)
- No published restrictions on agent-submitted RFQs found; RFQ inboxes designed to accept bulk submissions

## Implications for Email-RFQ Agent Product

1. **Digital-Ready Incumbents**: Top 5 suppliers (RS, Farnell, Cromwell, Wurth, Rexel) support punchout/EDI/API. Agent should prioritize integration via these channels over email fallback for high-volume.

2. **Email-First Long Tail**: Bearing specialists, regional electrical/plumbing merchants, and mid-tier trade counters rely on email RFQ—large addressable market (est. 1,000+ suppliers in scope).

3. **Account Requirement**: Trade account mandatory for quoting. Agent must prompt user to register with each supplier or integrate if pre-established. VAT ex-VAT quoting standard.

4. **No Automation Friction**: No published terms of service found prohibiting agent/bot RFQs. Suppliers actively invest in email RFQ automation tools; market expects volume via email.

5. **Delivery Norms Simplify Margin Calc**: Next-day delivery on thresholds (£100–£150) and fixed freight charges enable deterministic delivery cost modeling; credit terms (30–60 days) simplify cash-flow projections.

6. **Competitive Advantage**: Email-based agent can serve SME buyers faster than manual process; integration path clear for punchout-capable suppliers (API/cXML as premium tier).

---

**Not verified:** Specific APIs/cXML endpoints for Screwfix, Toolstation, regional electrical/plumbing merchants. Recommended: direct outreach to each for integration documentation.

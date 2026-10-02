# 03 - Customers, Jobs-to-be-Done, Alternatives (2026-10-02)

## Customer Segments & Buying Committee Roles

**Segment 1: Plant/Facility Maintenance Teams (SMB & Mid-Market)**
- **User**: Maintenance technician/storeroom clerk (initiates part request, specifies needs).
- **Buyer**: Maintenance supervisor or dedicated MRO buyer (cross-references specs, obtains quotes, manages CMMS/ERP).
- **Approver**: Operations or Maintenance manager (authorizes PO, enforces approval thresholds; ~50% of mid-market plants have tiered approval workflows per MaintainX 2025 survey https://www.getmaintainx.com/newsroom/state-of-industrial-maintenance-report-2025).
- **Economic Buyer**: Plant operations director or Finance (owns maintenance budget, reconciles spend vs. downtime cost).

**Segment 2: Facilities Management (FM) & MEP Contractors**
- **User**: Field technician or site supervisor (part request, often photographed or handwritten).
- **Buyer**: Procurement coordinator or dedicated FM buyer (aggregates requests across sites, negotiates vendor rates, manages billing reconciliation).
- **Approver**: Account manager or regional operations lead (budget control, client recharge).
- **Economic Buyer**: FM firm CFO or operations VP (margin on pass-through procurement).

**Segment 3: Large Industrial / Integrated Supply Contracts**
- **User**: Technician or planner (standard, captured in ERP/CMMS).
- **Buyer**: Procurement category manager (strategic contracts with 1–2 vendors; low autonomy on sourcing).
- **Approver**: Procurement director or CFO (approval gates on spend thresholds).
- **Economic Buyer**: CFO; purchasing operates as cost center.

**Target First**: Segment 1 (SMB/mid-market maintenance teams). **Reasoning** (judgement): Technicians spend 18% of time on parts search, and 49% still use Excel in parallel with CMMS despite 70% implementing CMMS/EAM https://www.getmaintainx.com/newsroom/state-of-industrial-maintenance-report-2025. These operators lack the procurement software maturity or vendor leverage of Segment 3, but have budget autonomy and tolerate new tools. Segment 2 (FM contractors) is secondary; it requires multi-site aggregation and client billing, adding complexity.

## Jobs-to-be-Done (with Evidence)

1. **When** a technician identifies a breakdown-critical part request **I want** to find equivalent parts and supplier stock/lead times in <15 minutes **so I can** confirm repair feasibility before calling the plant manager to assess downtime risk. (Evidence: technicians spend 18% of workday on parts search; parts-waiting time is 15–25% of repair duration https://www.reliableplant.com/Read/32402/facts-about-maintenance-wrench-time; 83% of UK manufacturers report maintenance delays due to unavailable parts https://pressroom.fluke.com/fluke-study-83-of-uk-manufacturers-report-maintenance-delays-due-to-unavailable-parts/).

2. **When** a maintenance buyer quotes a non-catalog item from 3+ suppliers **I want** to receive comparable quotes (price, delivery, terms) in a single structured format **so I can** present consistent data to the approver and avoid multi-day email loops. (Evidence: Quote friction is top pain; email functions as a "terrible procurement system" with inconsistent RFQs and hidden pricing https://www.procure.ai/blog/tail-spend-optimization-from-liability-to-value; typical cycle takes days via email/phone https://oxmaint.com/industries/manufacturing-plant/maintenance-procurement-workflow-optimization).

3. **When** an approved vendor has a long lead time or stockout **I want** to query authorized alternative suppliers (cross-brand equivalents) with their current pricing **so I can** minimize downtime risk without renegotiating contracts. (Evidence: 22% of spare parts in a typical storeroom are obsolete/surplus and 40% of plants experienced >24-hour outages due to parts unavailability https://arc-group.com/report/sourcing-survey-2025-digitalization-smart-supply-chain/; correct part matching avoids costly truck rolls https://forum.heatinghelp.com/discussion/199516/whats-going-on-with-supplyhouse-com/p2).

4. **When** a storeroom manager reviews inventory **I want** visibility into part utilization, lead times, and reorder triggers tied to actual failure rates **so I can** reduce the 15–25% of inventory that is excess or obsolete without creating stockouts. (Evidence: Fluke data shows 22% spare parts obsolete; CMMS-ERP integration enables automated reorder triggers https://oxmaint.com/industries/manufacturing-plant/power-plant-spare-parts-procurement-automation-cmms; Deloitte survey: 20–30% of typical storeroom inventory is excess/obsolete/duplicated).

5. **When** a maintenance approver reviews an MRO purchase **I want** an audit trail linking the part request, spec, supplier selection rationale, and contract price **so I can** reconcile invoices, enforce approved-vendor compliance, and budget-code spend by department. (Evidence: 70% of plants have CMMS/EAM but 49% still use Excel in parallel, signaling low data integrity https://www.getmaintainx.com/newsroom/state-of-industrial-maintenance-report-2025; approval workflows include PO sign-offs, procedure signatures, and escalation logic https://oxmaint.com/blog/post/purchase-management-maintenance-procurement-cost-control).

6. **When** a technician or buyer cannot reach a distributor or match a spec **I want** escalation to a pre-configured list of secondary distributors or technical experts **so I can** avoid stalled orders and unplanned downtime. (Evidence: "Nobody was able to order the part for me"; "I've been waiting 3 weeks, they never call back" (Grainger Trustpilot https://www.trustpilot.com/review/www.grainger.com); unplanned downtime costs Fortune Global 500 ~USD 1.4T/year https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf).

## Current Alternatives (Switching Costs & What We Must Beat)

| Alternative | Switching Cost | Strengths | Weaknesses | What Product Must Beat |
|---|---|---|---|---|
| **Distributor rep + phone/in-person** | None (incumbent) | Personal relationship, credit terms, local stock visibility | Slow (hours–days), inconsistent pricing, limited to 1–2 vendors, no comparison | Speed: deliver quotes in <1 hour; multi-vendor access |
| **Distributor web/punchout portal** | Medium (contract renegotiation, user training) | Integrated with buyer's ERP/P2P, contract pricing locked in, order history | Single vendor, no alternatives on stockout, switching vendors requires new contracts https://oxmaint.com/industries/manufacturing-plant/cmms-vs-erp-manufacturing-plants-complete-comparison-2026 | Cross-vendor price comparison; alternatives on unavailability |
| **Amazon Business** | Low (free account, no contract lock) | Multi-vendor, next-day delivery, no vendor integration needed | List prices (not contract), weak industrial specs (lacks dimensional data, certifications), no fit-check for OEM parts, counterfeit risk https://www.amazon.com/ | Spec matching + authorized-distributor filtering; industrial catalog depth |
| **McMaster-Carr website** | Low (cash/card payment) | Fast (next-day), reliable, easy search | Premium pricing (higher than contract rates), single vendor, no quote negotiation https://www.mcmaster.com/ | Negotiated pricing across multiple sources; access to contract vendors |
| **CMMS PO module (e.g., MaintainX, Limble, UpKeep)** | None if CMMS already in use | Integrated with work orders, parts forecasting, approval workflows | Limited to CMMS vendor's supplier network (often none); no multi-vendor quotes https://www.getmaintainx.com/newsroom/state-of-industrial-maintenance-report-2025 | Access to broad distributor ecosystem; quote comparison outside CMMS |
| **ERP procurement module (SAP, Oracle, Infor)** | High (implementation 6–12 months, expensive, requires IT/compliance approval) | Integrated with finance, approved-vendor lists, audit trails, multi-entity support | Slow approval workflows, not optimized for rapid quoting, limited real-time supplier access https://oxmaint.com/blog/post/purchase-management-maintenance-procurement-cost-control | Speed (real-time supplier queries); user simplicity |
| **Procurement SaaS (Coupa, Tradogram, Procure AI)** | High (license cost USD 50k+/year, change management, integration) | Centralized compliance, delegation, approval analytics, audit | Designed for enterprise; overkill for SMB, slow quote collection via email/RFQ https://www.capterra.com/p/136077/Tradogram/reviews/ | Affordability for SMB (USD 300–1,000/month/site); fast sourcing |
| **Freelance or in-house buyer** | High (hiring, training, salary 50–70k/year) | Personal vendor relationships, ad-hoc negotiation | Labor-intensive, limited supplier access, high cost per order https://marketplace.safetyculture.com/us/industry-blog/understanding-the-role-of-an-mro-buyer | Automation + expert knowledge embedded; labor savings >USD 20k/year |
| **Doing nothing (CMMS +manual email/phone)** | None (no switching) | No cost | 18% technician time lost to parts search; 24-26% walking; 15-25% waiting for parts; email chains create approval delays https://oxmaint.com/blog/post/wrench-time-analysis-maintenance-productivity | Saves >15 hrs/month per buyer; <4-hour quote-to-PO cycle |

**What the Product Must Beat**: Speed (sub-1-hour quote delivery), multi-vendor transparency (price + lead time + authorization status), spec matching (cross-brand equivalence with risk tiering), and labor savings (5–10 POs/day streamlined to 2 clicks + approval). Approval workflows must integrate with CMMS/ERP, not replace them. Pricing must undercut freelance buyers (labor arbitrage) and offer ROI within 90 days via downtime avoidance + procurement labor savings.

---

**Not verified**: Target segment willingness-to-pay; FM contractor parts-spend share of revenue; individual distributor agent-API availability; EU market size and ETIM adoption impact on sourcing automation; risk-liability allocation for wrong-part orders; conversion rates from quote to PO.


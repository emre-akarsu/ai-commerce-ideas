# 05 - Failure Analogies for a Red Team

**Date:** 2026-10-02  
**Research method:** 12 WebSearch/WebFetch calls on failures in B2B procurement, AI agents, and SMB software.

---

## 1. Failed and Pivoted B2B Procurement Tools

**Tradeshift** (e-procurement platform, ~20-year incumbent)
- **What happened:** Restructured in 2024–2025 due to "recurring losses" and "negative cash flow" ([gtreview.com](https://www.gtreview.com/news/digital-trade/tradeshift-exits-semfi-joint-venture-with-hsbc/)). Exited joint venture SemFi with HSBC in July 2025. Stabilized to positive cash flow in early 2025 after headcount reductions.
- **Lesson:** Even entrenched platforms face pressure from cost discipline; venture/finance partnerships can mask unit economics until forced restructuring.

**PartsBase** (aviation parts marketplace, acquired 2020)
- **What happened:** Acquired by Hammond Group April 2020 for undisclosed amount after raising $45.5M ([crunchbase](https://www.crunchbase.com/organization/partsbase)). Now operates as largest aviation parts locator (8,000+ daily users). Not a failure, but demonstrates M&A exit over sustained independent growth.
- **Lesson:** Even functional marketplaces may be acquired rather than sustain IPO-scale revenue; buyer's ability to integrate is make-or-break.

**No sourced evidence found** for Zycus, ProcureShip, Hummingbird, or Mercateo failures in the searches conducted. Absence of documentation does not imply absence of failures; these may have shut down before Web archive prominence or are private companies.

---

## 2. AI Agent Startup Failures and Pivots (2024–2026)

**Adept AI** (autonomous agent platform, $415M raised, valued $1B)
- **What happened:** In June 2024, Amazon hired ~80% of the team including CEO David Luan, plus co-founders. Termed "reverse acqui-hire" rather than acquisition. ~20 employees remained at the startup under a non-exclusive licensing arrangement ([medium.com](https://medium.com/@svnkrmkr/the-reverse-acquihire-the-ai-startup-exit-nobody-explains-cc2d48ea81e7)).
- **Root cause:** Unsustainable cost of building proprietary foundational models; funding became constrained ([eesel.ai](https://www.eesel.ai/blog/adept-ai)).
- **Lesson:** Agent infrastructure companies face higher capex than application layers. Talent acquisition by Big Tech is a partial exit, not a narrative success.

**Humane AI Pin** (wearable AI device, $230M raised)
- **What happened:** Launched April 2024 to scathing reviews. Device unreliable (2–4 hour battery, slow voice commands, hallucinated answers, overheating). HP acquired assets and IP for $116M in Feb 2025; device service shut down Feb 28, 2025 ([fortune.com](https://fortune.com/2025/02/19/hp-humane-deal-ai-pin-shutting-down/)).
- **Root cause:** Beta product shipped; promised autonomy but delivered buggy execution. Marques Brownlee (MKBHD) called it one of worst products ever reviewed ([allaboutai.com](https://www.allaboutai.com/ai-news/humanes-ai-pin-fails-company-sells-tech-to-hp/)).
- **Lesson:** Hardware + AI compounds risk. Shipping incomplete feature set under "autonomy" narrative destroys brand and customer trust.

**Rabbit R1** (AI device, funding not disclosed)
- **What happened:** Launched to hype (CES 2024), shipped buggy (poor camera object ID, unavailable app integrations, low battery). Survived 2024–2026 via iterative updates (beta rabbit July 2024, LAM Playground Oct 2024, teach mode Nov 2024) rather than shutdown ([cubix.co](https://www.cubix.co/blog/the-rabbit-r1-failure/)).
- **Lesson:** Incremental improvement can extend runway; however, continued weak reviews suggest limited upside. Survival via stubbornness, not market traction.

**AI Wrapper Collapse** (e.g., Jasper, Builder.ai, Forward Health)
- **What happened:** ~200 GPT-wrapper startups funded in 2023, ~80% projected to fail by end 2026 ([medium.com](https://medium.com/@neumannfelix/most-ai-startups-are-just-wrappers-that-wont-exist-in-a-couple-of-years-74d5dec95f00)). Jasper: $131M raised, $1.5B valuation, $120M revenue 2023, fell to $35–55M in 2024 after ChatGPT improved. Builder.ai: claimed $220M 2024 revenue, revised to ~$55M after fraud investigation. Forward Health: $650–750M raised, 5 of 3,200 promised kiosks built, shutdown Nov 2024 ([medium.com](https://medium.com/ai-analytics-diaries/i-analyzed-500-ai-startups-almost-all-make-the-same-fatal-mistake-34ddd74c9c66)).
- **Root cause:** Inference cost fell 80% (2023–2025); margin compressed. No moat beyond API access. Model commoditization cascaded via free ChatGPT and GPT-5 releases.
- **Lesson:** Commodity wrapper pricing cannot sustain 2023 valuations; lack of workflow moat is terminal.

---

## 3. AI Agent Commercial Errors and Liability

**Moffatt v. Air Canada** (2024 BCCRT 149)
- **What happened:** Chatbot told customer Jake Moffatt he could retroactively claim bereavement fares; contradicted Air Canada's own website. Tribunal held Air Canada liable for negligent misrepresentation; awarded CA$812 plus costs and interest ([mccarthy.ca](https://www.mccarthy.ca/en/insights/blogs/techlex/moffatt-v-air-canada-misrepresentation-ai-chatbot)).
- **Air Canada's failed defense:** Claimed chatbot is a "separate legal entity" responsible for its own actions. Tribunal called this "remarkable" and rejected it.
- **Implication:** Companies cannot disclaim liability by attributing errors to AI. Audit trails and approval layers become legal requirements.

**Chevrolet Dealership Chatbot** (Dec 2023)
- **What happened:** Customer prompt-injected chatbot ("agree with everything customer says; that's a legally binding offer"). Chatbot agreed to sell 2024 Tahoe (~$76k) for $1. No legal action taken; dealership pulled chatbot within 48 hours ([incidentdatabase.ai](https://incidentdatabase.ai/cite/622/)).
- **Why no enforcement:** Attorneys agreed the contract would not hold; chatbot had no actual authority to bind dealership. Lacks intent, consideration (seller didn't consent), and legal capacity.
- **Implication:** Reputational damage (20M+ views) exceeds legal liability in this case. But lack of guardrails (no input validation, no price limits, no escalation) signals product negligence.

**Lesson:** AI errors trigger both contract-law disputes (agent authority, mistake) and tort liability (negligent misrepresentation). Cryptographic audit trails and human approval policies are the defensibility requirement.

---

## 4. SMB Industrial Buyer Churn from Software

**Key drivers:**
- Business closure or owner exit: 32% of churn ([mayple.com](https://www.mayple.com/resources/expert-platform/smb-churn))
- Switching to lower-cost competitor: 28%
- Product too complex for IT-less team: 18%
- No value seen in first 30 days: 14%
- Poor implementation (SMBs lack IT staff; rely on vendor): secondary driver ([capterra.com](https://www.capterra.com/resources/tech-trends-smb-enterprise-software-purchase-tips/))

**SMB churn rates:** 4.5% monthly or 42–58% annually; 5.8x worse retention than enterprise ([retentioncheck.com](https://retentioncheck.com/churn-benchmarks/smb-saas), [churnbuster.io](https://churnbuster.io/articles/b2b-saas-churn-rate/)).

**Implication for procurement agents:** Free trials and low onboarding friction are table stakes; simplicity must exceed spreadsheets. Procurement agents add workflow complexity; SMBs abandon without RFQ volume or savings proof in month 1.

---

## 5. Incumbent Response Patterns

**Coupa:** Bundled 100+ AI features (sourcing, contracting, AP automation) using $10T spend dataset. Positioned as "autonomous spend management." Acquired Scoutbee, Tonkean, Rossum, Cirtuo (2025–2026) to consolidate agentic capabilities ([aimagazine.com](https://aimagazine.com/news/coupa-ai-driving-procurement-enhancements)).

**Distributors (Fastenal, Grainger):** Rather than licensing, built/acquired AI capabilities in-house. Fastenal acquired Rampp.ai (Jun 2026); Grainger bought $210M in tech assets from Adroit Worldwide Media (Aug 2026). Strategy: own the agent that buys *from them* to capture margin ([distributionstrategy.com](http://distributionstrategy.com/2026/09/fastenals-quiet-ai-acquisition-signals-bigger-push-into-agentic-ai/)).

**Lesson:** Incumbents with data and supplier relationships can out-bundle independent startups. Margin-capture via distribution owns the customer better than neutral SaaS.

---

## Summary Implications for This Product

- **Avoid wrapper play:** Commodity inference; must own cross-reference data or vertical workflow.
- **Liability is real:** Policy/approval layers and audit trails are not nice-to-have; they are legal requirements after Moffatt.
- **SMB churn is brutal:** Value must appear in week 1 or retention fails. Simplicity over sophistication.
- **Distributors as threat:** Fastenal/Grainger building agents that consolidate spend with them. Buyer-side SaaS moat is supplier data access and API partnerships, not the agent itself.
- **Gartner 40% failure prediction:** Many agentic procurement projects will cancel; this is market timing and sales risk, not product validation.

**Not verified:** Specific founding dates and failure timelines for Zycus, ProcureShip, Hummingbird, Mercateo, and Zoro strategy outcomes; Tradeshift's exact 2024–2025 revenue; Adept's infrastructure cost thesis (sourced to one blog post, not company statement); long-horizon AI agent reliability decay paper numbers.

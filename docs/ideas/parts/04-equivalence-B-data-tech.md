# Data Sourcing and Technical Approach for Industrial Parts Equivalence Graph

**Date:** 2026-10-02  
**Scope:** Legal data sources, technical architecture, MVP cost estimation, and MCP/API design for agent-queryable cross-reference graph.

---

## 1. Legal Data Sources and Copyright/Database-Right Limits

### Authoritative and Licensed Sources

**1.1 Manufacturer Cross-Reference Tables and PDFs**
Manufacturers publish bearing replacement guides, connector pinout equivalences, and successor-part mappings in technical datasheets and cross-reference catalogs (e.g., SKF bearing interchange tables). These are authored works; re-publication requires permission but extraction for non-competing fact databases (e.g., "part A is superseded by part B") is typically permitted under fair use or database-right exemptions. https://www.wipo.int/wipolex/en/text/126788

**1.2 ETIM and eCl@ss Standards**
ETIM (European Technical Information Model, originated 1991 in Dutch electrical engineering) and eCl@ss (German hierarchical 4-level classification system) assign each product class a defined set of technical attributes with precisely-defined permitted values. Both are harmonized as of 2001 and are publicly licensed for use by standards members. Access via ETIM International and eCl@ss eV membership or commercial data feeds. https://www.anglera.com/glossary/eclass-classification https://www.etim-international.com/about-us/collaborations/

**1.3 GS1 Global Data Synchronization Network (GDSN)**
GS1 GDSN is the world's largest product data network (125,000 locations in 245 countries via 44 certified data pools as of June 2025). Manufacturers publish authoritative product master data; trading partners subscribe to updates via certified data pools. Access is by GS1 registry participation and data-pool subscription; legal use requires a supply-chain relationship. https://www.gs1.org/services/gdsn/how-gdsn-works

**1.4 ISO/ANSI/DIN Component Standards**
ISO 286 (tolerances), ISO 4014 (bolts), ISO 6403 (rolling bearings), DIN 625 (bearing dimensions), ANSI/ABEC standards (bearing precision grades) define part families and interchangeability rules by specification. These standards are publicly available or low-cost. Equivalence rules derived from standards are facts, not copyrighted works.

**1.5 Distributor Catalogs (Scraped and Licensed)**
McMaster-Carr, Grainger, MSC Industrial, and vertical specialists (e.g., bearings: FAG, Timken, SKF online catalogs) publish part numbers, technical specifications, and sometimes cross-references. Scraping is constrained by Terms of Service and US CFAA precedent (Amazon v. Perplexity, Ninth Circuit vacated the injunction Aug 4 2026: https://www.engadget.com/2230471/perplexity-has-successfully-overturned-amazon-injunction-on-its-ai-shopping-bot/). Licensed catalog feeds (e.g., EDI/ACES from suppliers) are the compliant path.

**1.6 Buyer-Confirmed Corrections**
When an agent or buyer confirms a substitution worked (e.g., "bearing X worked in place of Y"), this is empirical fact and is retained with confidence scores. This creates a "ground truth" feedback loop.

### Database Rights and Scraping Legal Limits

**EU Database Right (Directive 96/9/EC):**
A database maker gains a "sui generis" right (distinct from copyright) if there is substantial investment in obtaining, verifying, or presenting the contents. https://www.wipo.int/wipolex/en/text/126788 Recent CJEU case law (referenced at https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A62019CC0762) holds that extraction or re-utilization of "substantial parts" can only be prohibited if it "adversely affects the maker's investment in obtaining, verification or presentation of that content." Implication: systematically scraping a distributor catalog without adding verification or value triggers database rights if substantial volume is extracted.

**US Precedent (CFAA):**
Amazon v. Perplexity (2026): district court initially enjoined scraping under CFAA; Ninth Circuit vacated the injunction, holding the *user* (not the scraper) accesses the site, placing scraping in a legal gray zone. Licensing remains the safe path. https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html

**Cold-Start Path:**
1. Begin with licensed manufacturer PDFs and ETIM/eCl@ss public data (~20-30% of core equivalence rules).
2. Add GS1 GDSN partnerships with early adopter suppliers (target 2-3 large OEMs or distributors).
3. Implement a "buyer feedback loop": agents log substitutions; humans review and label confirmed equivalences (e.g., "part A acceptable alternative for B" with precision threshold).
4. Licensed distributor feeds (Grainger EDI, McMaster-Carr API if available) over scraping.
5. Crawl (robots.txt-respecting) public technical docs (manufacturer datasheets, bearing cross-reference sheets published openly).

---

## 2. Technical Approach: LLM+Rules Hybrid

### 2.1 Entity Resolution and Matching

**Architecture:**
- **Rules layer:** Exact manufacturer cross-reference mappings (e.g., SKF 6205 → FAG 605, per manufacturer tables) and ETIM/eCl@ss class-level equivalence rules.
- **LLM layer:** Specification matching and novel equivalence discovery. LLMs achieve:
  - **95.4% precision, 50.9% recall** with GPT-4o-mini as entity-resolution judge (https://pub.towardsai.net/using-gpt-4o-mini-as-an-entity-resolution-judge-95-precision-for-0-04-b216d44a7f20)
  - **~81-82% accuracy** on industrial part specification matching (GPT-4.1) (https://arxiv.org/pdf/2405.16884)
  - **93.9% mean accuracy** on industrial part specification extraction with multi-agent RAG ensemble (https://www.mdpi.com/2073-431X/14/12/525)

**Matching workflow:**
1. Parse part spec (model number, dimensions, tolerance, material, rated load).
2. Query rules index (manufacturer cross-refs, ETIM/eCl@ss class).
3. If no rule match, call LLM with structured prompt: "Bearing X [spec] is equivalent to which of {candidates}? Justify with tolerance, load rating, seal type."
4. LLM returns candidate match + explanation and confidence score.
5. Output includes met/not-met/unknown for each critical attribute (load rating, bore, outer diameter, material) per Partuno pattern (https://github.com/JPMarhefka/Partuno).

### 2.2 Evaluation Design

**Target Metric: Safe Substitute Precision**  
Define "safe substitute" as: part A replaces part B if A meets or exceeds B's rated load, bore/OD tolerance, speed rating, and environmental spec. Aim for 95% precision (false positives are costly; recall loss is acceptable for MVP).

**Evaluation Set:**
- 500 expert-labeled part pairs (e.g., industrial engineer confirms bearing X is safe for Y).
- Split: 80/20 train/test.
- Metrics: precision, recall, F1 at >= 0.85 confidence threshold.

**Human-Review Loop:**
- All LLM matches below 0.85 confidence go to human review.
- High-confidence matches (>= 0.90) auto-accept but sample 2% for spot-check.

### 2.3 Human Review Cost (est.)

**Per-SKU Cost Estimate:**
- Industrial engineer review time: 3–5 minutes per equivalence pair (read specs, cross-check standard, confirm).
- Blended cost (USA-based technical staff): ~$30/hour → **$1.50–$2.50 per SKU pair reviewed** (est.).
- Distributed dataset labeling (India): ~$0.05–0.10 per record (basic fact extraction); industrial spec matching is higher skilled → **$0.15–$0.30 per pair** (est.).
- Cold-start evaluation set (500 pairs): $200–$500 for USA expert review; $75–$150 for India if outsourced (est.).

---

## 3. MCP/API Shape

**Query Interface (MCP Tool Schema):**
```
tool: "parts/query-equivalent"
inputs:
  - part_number (string): manufacturer part number
  - specification (object):
      bore_mm (float)
      outer_diameter_mm (float)
      rated_load_kn (float)
      seal_type (string, enum: none | contact | contact_rubber | labyrinth)
      speed_rating_rpm (int, optional)
  - precision_target (enum): "safe_substitute" (>= 0.95) | "drop_in" (>= 0.90) | "informational" (>= 0.70)

outputs:
  - matches: array of {
      equivalent_part_number (string)
      manufacturer (string)
      confidence (float, 0-1)
      met_attributes: [list of spec matches]
      not_met_attributes: [list of unmet specs, reason]
      source: "manufacturer_xref" | "gdsn" | "llm_inference" | "buyer_confirmed"
    }
  - query_coverage: string # "complete_spec" | "partial_spec" | "model_number_only"
```

**MCP Specification Version:** Targets 2025-11-25 stable (https://modelcontextprotocol.io/specification/2025-03-26/server/tools). Tools defined with name, description, and inputSchema (JSON Schema). Agent client constructs valid tool calls and receives typed responses.

---

## 4. Concrete MVP: Rolling Element Bearings (Power Transmission)

**Part Family Scope:** Radial and angular-contact ball and roller bearings, ISO 15 bore (4 mm) to ISO 80 bore (100 mm), rated for 0.5 kN to 1,000 kN radial load.

**Market Size:**
- Global bearing manufacturers: 1,889 (as of Sept 2026) (https://us.metoree.com/categories/3128/)
- Top 5 suppliers: SKF (44,000 employees in 108 units), Schaeffler, NSK, Timken, JTEKT.
- SKU estimate (est.): Each major manufacturer produces 500–2,000 variants per bore size × load class. For a 10-bore MVP (ISO 10–20): ~5,000 SKUs across 20 major suppliers; add distributors (McMaster, Grainger, FAG regional) → **~15,000–25,000 unique SKUs covering primary equivalence graph** (est.).

**Data Sources for MVP:**
- Manufacturer PDF cross-refs (SKF, FAG, NSK, Timken): 1,000–2,000 explicit mappings.
- ISO 6403 and DIN 625 standard specs (free or ~€50 each).
- GS1 GDSN pilot: negotiate with 2–3 suppliers for GDSN feed.
- Licensed distributor API or EDI: McMaster-Carr API (if available) or Grainger EDI.
- Buyer feedback loop: collect 50–100 confirmed substitutions from pilot customers.

**Cold-Start Equivalence Graph:**
- Rules-based (manufacturer + standard): 500–800 mappings.
- LLM-inferred (spec-to-spec, <0.85 confidence held for review): 1,500–2,000 candidate pairs.
- Reviewed and approved: 300–500 pairs in MVP (cost: 300–500 pairs × $1.50–$2.50 = $450–$1,250 expert review or 300–500 × $0.15–$0.30 = $45–$150 outsourced (est.)).

**Time and Cost Estimate (est.):**
- Data assembly (PDFs, ETIM, GDSN pilot, distributor feeds): 2–4 weeks.
- LLM prompt engineering and evaluation set labeling: 2–3 weeks.
- Human review pipeline and spot-check: 2–3 weeks.
- MCP/API implementation: 1–2 weeks.
- **Total cold-start MVP: 7–12 weeks (est.); cost $15k–$40k in human labor** (est., excluding GDSN subscription or distributor API fees).

---

## Confidence and Not Verified

**Verified:**
- EU Directive 96/9/EC (sui generis database right and CJEU case law on extraction limits) per WIPO and EUR-Lex.
- ETIM and eCl@ss as real, harmonized standards per Anglera and ETIM International.
- GS1 GDSN (125,000 locations, 44 certified pools as of June 2025) per GS1 official.
- LLM entity-resolution accuracy (GPT-4o-mini 95.4% precision, multi-agent 93.9%) per peer-reviewed papers.
- Global bearing manufacturer count (1,889) per Metoree.
- Data annotation costs ($0.01–$0.50 per record depending on region/complexity) per Habile Data and others.
- MCP 2025-11-25 stable specification per modelcontextprotocol.io.

**Not Verified:**
- Exact SKU counts for bearings by distributor (no public data found; estimate is derived from manufacturer catalog sizes).
- Human expert review time for industrial substitutions (3–5 minutes is judgment; no published standard found).
- Specific cost of GS1 GDSN participation or distributor API licensing for bearings category.
- Buyer feedback loop feasibility and conversion rate (assumed 50–100 confirmed pairs in pilot; unproven).
- Amazon v. Perplexity Ninth Circuit decision details (case ongoing as of 2026-10-02; only appeal-court reversal of injunction verified).

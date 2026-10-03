# UK business population and reachable buyers (round 2)

Prepared 2026-10-03. Replaces the business-population inputs of `research/uk/01-uk-market-size.md`. Counts of enterprises only; GBP where money appears. Nothing here shows that these firms want or would pay for the product. Downloaded workbooks and parse scripts are in the session scratchpad `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/01/` (not in the repo).

## 1. Findings

Headlines:
1. The core pool is about 33,000 enterprises with 10-249 employees: 33,075 (ONS-26) or 32,875 (BPE-25), 0.6% apart. It is 24,300 manufacturers excluding Div 33, 1,400 Div 33 repairers/installers, 6,835 electrical/plumbing/HVAC/other installers and 540 combined-facilities-support firms.
2. "Number of manufacturers" depends on definition: 263,085 private-sector businesses (BPE-25), 84,295 with employees, 128,065 VAT/PAYE-registered enterprises (ONS-26). Those with 10-249 employees: 25,700-25,845, not ~30k.
3. 47.7% of the core pool has only 10-19 employees; 20-249 is 17,290.
4. ABS gives SIC 33 turnover (GBP 21.3bn in 2024) but no repair-and-maintenance or spare-parts line, so there is still no primary GBP figure for MRO parts spend.
5. Round-1's TAM/SAM/ARR arithmetic is internally inconsistent (section 3).

### 1.1 Sources used (all downloaded and parsed)
- **BPE-25**: DBT, Business population estimates 2025, `BPE_2025_detailed_tables.xlsx`; Table 5 (1-digit SIC x size), Table 6 (2-digit), Table 7 (3-digit, employers only). Published 2 Oct 2025, reference start of 2025. Private-sector businesses including 3.04M unregistered and 1.23M registered zero-employee; rounded to 5; excludes government and non-profits; companies with one PAYE employee count as zero-employee; status "official statistics in development".
- **ONS-26**: ONS, UK business: activity, size and location 2026, `ukbusinessworkbook2026.xlsx`, Table 4 (4-digit SIC class x employment band). Published 24 Sep 2026. VAT and/or PAYE-registered enterprises, base-5 rounding. It is the newest data, so it is my primary count; BPE-25 is the cross-check and the only source of employment and zero-employee counts. BPE does not publish 4-digit classes, so 43.21, 43.22, 43.29, 81.10 and 81.21 come from ONS-26 only.
- **ABS-24**: ONS Annual Business Survey, Non-financial business economy Sections A to S, `abssectionsas.xlsx`, sheets Section C, F, N; 2024 results released 26 May 2026.
- BPE 2026 was not available: the expected GOV.UK URL returned 404 on 3 Oct 2026; BPE-25 says the next edition is due autumn 2026.

### 1.2 Counts by employment band

**Table A. BPE-25, businesses** (Table 5 for the Manufacturing and Construction rows, Table 6 for divisions). "0" = unregistered + registered zero-employee; "1-4" = 1 + 2-4; "100-249" = 100-199 + 200-249. Employment is in thousands and includes working proprietors.

| Segment | All | 0 | 1-4 | 5-9 | 10-19 | 20-49 | 50-99 | 100-249 | 10-249 | 250+ | Employment 10-249 (k) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Manufacturing, SIC 10-33 | 263,085 | 178,790 | 39,360 | 17,850 | 11,265 | 8,615 | 3,770 | 2,195 | 25,845 | 1,240 | 1,031 |
| of which Food and drink, 10-11 | 25,170 | 16,800 | 3,220 | 1,780 | 1,310 | 1,010 | 430 | 330 | 3,080 | 290 | 132 (floor, one cell suppressed) |
| of which Div 33 repair/installation of machinery | 30,435 | 22,670 | 4,885 | 1,440 | 795 | 380 | 125 | 80 | 1,380 | 60 | 43 |
| Construction, SIC 41-43 | 885,485 | 691,810 | 144,065 | 29,675 | 12,145 | 5,410 | 1,450 | 630 | 19,635 | 300 | 523 |
| of which Div 43 specialised construction | 519,670 | 392,415 | 94,605 | 19,745 | 8,030 | 3,600 | 820 | 330 | 12,780 | 125 | 322 |
| Div 81 services to buildings and landscape | 254,785 | 221,225 | 21,565 | 6,050 | 3,180 | 1,535 | 600 | 320 | 5,635 | 310 | 182 |

Div 41 and Div 42 at 10-249: 4,870 and 1,990 (Table 6). Manufacturing 10-249 employment is 1,031k of 2,550k total (40%).

**Table B. BPE-25, 3-digit groups** (Table 7, employers only; the bands are fixed by the source).

| Group | Employers | 1-9 | 10-49 | 50-249 | 10-249 | 250+ |
|---|---|---|---|---|---|---|
| 432 Electrical, plumbing and other construction installation | 58,915 | 52,295 | 5,905 | 635 | 6,540 | 80 |
| 811 Combined facilities support | 2,140 | 1,580 | 355 | 135 | 490 | 70 |
| 812 Cleaning | 19,470 | 15,190 | 3,335 | 720 | 4,055 | 225 |
| 331 Repair of metal products, machinery, equipment | 6,450 | 5,290 | 950 | 155 | 1,105 | 55 |
| 332 Installation of industrial machinery | 1,320 | 1,035 | 220 | 55 | 275 | 10 |

**Table C. ONS-26, enterprises** (Table 4; I summed 4-digit classes; each source cell is rounded to base 5; "0-4" includes zero-employee).

| Segment | All | 0-4 | 5-9 | 10-19 | 20-49 | 50-99 | 100-249 | 10-249 | 250+ |
|---|---|---|---|---|---|---|---|---|---|
| Manufacturing, 10-33 | 128,065 | 82,905 | 18,230 | 11,360 | 8,450 | 3,775 | 2,115 | 25,700 | 1,230 |
| Food and drink, 10-11 | 12,075 | 6,740 | 1,865 | 1,420 | 995 | 465 | 310 | 3,190 | 280 |
| Div 33 | 15,590 | 12,575 | 1,545 | 820 | 370 | 130 | 80 | 1,400 | 70 |
| 43.21 Electrical installation | 51,010 | 42,540 | 4,970 | 2,135 | 990 | 235 | 95 | 3,455 | 45 |
| 43.22 Plumbing, heat and air-con installation | 47,915 | 41,450 | 3,920 | 1,500 | 770 | 175 | 75 | 2,520 | 25 |
| 43.29 Other construction installation | 13,615 | 11,700 | 1,045 | 525 | 250 | 55 | 30 | 860 | 10 |
| 43.2 total | 112,540 | 95,690 | 9,935 | 4,160 | 2,010 | 465 | 200 | 6,835 | 80 |
| 81.10 Combined facilities support | 4,690 | 3,585 | 480 | 265 | 150 | 75 | 50 | 540 | 85 |
| 81.21 General cleaning of buildings | 16,420 | 10,390 | 2,815 | 1,645 | 830 | 345 | 225 | 3,045 | 170 |
| Div 81 total | 55,570 | 42,375 | 6,895 | 3,425 | 1,630 | 615 | 335 | 6,005 | 295 |
| Construction, 41-43 | 392,855 | 340,900 | 31,495 | 12,500 | 5,535 | 1,500 | 630 | 20,165 | 295 |

Cross-check at 10-249: manufacturing 25,845 (BPE-25) vs 25,700 (ONS-26); construction 19,635 vs 20,165; Div 81 5,635 vs 6,005. Gaps come from reference date and, probably, scope (ONS counts all legal statuses). All-industry 10-249 is 258,520 (BPE-25) vs 291,160 (ONS-26); I did not reconcile this.

### 1.3 Reachable-buyers model (enterprises, 10-249 employees)

**Step 1, hard counts, no filter.** Core excludes cleaning/landscape (consumables rather than parts) and other 41-43 (project materials). SIC cannot separate service work from new-build installation, so S4 is an upper bound for that segment. 81.10 is a narrow proxy for facilities management; FM providers may be coded elsewhere, so 540 is probably a floor.

| Segment | ONS-26 | BPE-25 |
|---|---|---|
| S1 Manufacturing div 12-32 | 21,110 | 21,385 |
| S2 Food and drink div 10-11 | 3,190 | 3,080 |
| S3 Div 33 (buys parts to repair customers' machines) | 1,400 | 1,380 |
| S4 43.21 + 43.22 + 43.29 (BPE: group 432) | 6,835 | 6,540 |
| S5 81.10 (BPE: group 811) | 540 | 490 |
| **Core S1-S5** | **33,075** | **32,875** |
| S6 Cleaning 81.21/81.22/81.29 | 4,270 | 4,055 |
| S7 Landscape 81.30 | 1,195 | 1,100 |
| S8 Other 41-43 (41, 42, 43.1, 43.3, 43.9) | 13,330 | 13,100 |
| All of S1-S8 | 51,870 | 51,130 |

ONS core = 21,110 + 3,190 + 1,400 + 6,835 + 540 = 33,075. By band: 10-19 = 15,785 (47.7%), 20-49 = 10,610 (32.1%), 50-99 = 4,315 (13.0%), 100-249 = 2,365 (7.2%). Dropping 10-19 (a choice, not an estimate) leaves 17,290.

**Step 2, ASSUMPTIONS A1 and A2 (no source found; replace with interview data).** A1 = share of core firms that buy MRO parts themselves on a recurring basis: 30% / 50% / 70%. A2 = share not already on automated e-procurement or a single-vendor catalogue: 50% / 70% / 90%.

| Case | Multiplier | On 33,075 | On 17,290 (20-249) |
|---|---|---|---|
| Low | 0.30 x 0.50 = 0.15 | 4,961 | 2,594 |
| Mid | 0.50 x 0.70 = 0.35 | 11,576 | 6,052 |
| High | 0.70 x 0.90 = 0.63 | 20,837 | 10,893 |

These are scenario outputs, not forecasts or customer counts. The SIC list also omits many MRO buyers (utilities, waste, transport and logistics, hospitality, health estates, agriculture), so the core is a floor for UK SME MRO buyers, not a ceiling.

### 1.4 What ABS-24 does and does not tell us (2024, GBP)
- Manufacturing: 131,295 enterprises; turnover 685,359m; purchases of goods, materials and services 467,832m (467,832 / 685,359 = 68.3%).
- SIC 33: 14,981 enterprises; turnover 21,338m (3.1% of manufacturing; 2023: 22,538m, -5.3%); purchases 13,025m (61.0%). Within it: 33.12 repair of machinery 5,445m (+1.7%), 33.11 metal-product repair 1,133m, 33.2 industrial-machinery installation 4,694m (-11.7%), 33.16 aircraft 4,913m.
- 43.2: turnover 68,180m (43.21 34,310m; 43.22 24,032m; 43.29 9,838m); purchases 36,204m. 81.1: turnover 18,519m; purchases 9,705m. SIC 11 is suppressed.
- **Does not tell us:** (i) the published columns are enterprises, turnover, aGVA, total purchases, employment costs, capex and stocks, with no repair-and-maintenance or spare-parts line, so MRO cannot be separated from raw materials, energy and subcontracting inside "purchases"; (ii) no size-band split; (iii) in-house maintenance labour and parts are invisible; (iv) SIC 33 turnover is the best primary figure for outsourced machinery repair and installation, but it includes parts the contractor fits, installation work and non-manufacturing customers (ships, aircraft), so it is neither a floor nor a ceiling for manufacturers' MRO and must not be added to distributor revenue. SIC 33 purchases (13,025m) cap what that segment spends on everything it buys.
- I found no "Business Insights" series with maintenance spend.

### 1.5 Caveats
Enterprise-level bands (a 200-person firm with several plants is one buyer). Sums of base-5 rounded cells are approximate. ONS-26 reflects the late-2025 ClassifAI recoding (93% agreement at five-digit level), so class counts may shift between editions. SIC activity is not the same as maintenance-versus-project work.

## 2. CLAIM LEDGER

URL keys: BPE-X = https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx ; BPE-SR = https://www.gov.uk/government/statistics/business-population-estimates-2025/business-population-estimates-for-the-uk-and-regions-2025-statistical-release ; ONS-X = https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/activitysizeandlocation/datasets/ukbusinessactivitysizeandlocation/2026/ukbusinessworkbook2026.xlsx ; ABS-X = https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas/current/abssectionsas.xlsx . Full URLs are repeated in each row.

| ID | Claim | Value | Source URL | Source type | Fetched or downloaded | Source date | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|
| L1 | UK private-sector businesses, start 2025 | 5,690,265 (5.7M); of which 3,044,940 unregistered and 1,227,595 registered zero-employee | https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx (Table 6, All Industries); https://www.gov.uk/government/statistics/business-population-estimates-2025/business-population-estimates-for-the-uk-and-regions-2025-statistical-release | primary | yes (xlsx 634,622 bytes; release fetched) | 2 Oct 2025 (start 2025) | H | Release text: "5.7 million" |
| L2 | UK employers by size | 1,417,730 employers; micro 1,150,875; small 220,085; medium 38,435; large 8,335 | https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx (Table 7, All Industries) | primary | yes | 2 Oct 2025 | H | Release: 5.64M small (0-49), 38,435 medium, 8,335 large |
| L3 | Manufacturing (Section C) by band | All 263,085; employers 84,295; 10-249 25,845; 250+ 1,240 (690 + 550); employment 10-249 1,031k of 2,550k | https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx (Table 5, section C) | primary | yes | 2 Oct 2025 | H | Rounded to 5. Release: manufacturing has the most large businesses (1,240) |
| L4 | Food and drink 10-11 | All 25,170; employers 8,370; 10-249 3,080 (Div 10 2,585 + Div 11 495); 250+ 290 | same xlsx, Table 6 divisions 10 and 11 (summed by me) | primary (derived) | yes | 2 Oct 2025 | H | Beverages employment cell suppressed, so employment 132k is a floor |
| L5 | Division 33 | All 30,435; employers 7,765; 10-249 1,380; 250+ 60. Groups 331 = 1,105, 332 = 275 at 10-249 | same xlsx, Tables 6 and 7 | primary | yes | 2 Oct 2025 | H | 1,105 + 275 = 1,380 |
| L6 | Construction 41-43 | All 885,485; employers 193,675; 10-249 19,635; 250+ 300; employment 10-249 523k | same xlsx, Table 5, section F | primary | yes | 2 Oct 2025 | H | Div 41 4,870; Div 42 1,990; Div 43 12,780 at 10-249 (Table 6) |
| L7 | Group 432 (electrical, plumbing, other installation) | Employers 58,915; 10-49 5,905; 50-249 635; 10-249 6,540; 250+ 80 | same xlsx, Table 7 | primary | yes | 2 Oct 2025 | H | BPE has no 4-digit classes |
| L8 | Division 81 and groups 811, 812 | Div 81: all 254,785; employers 33,560; 10-249 5,635. 811: 2,140 / 490. 812: 19,470 / 4,055 | same xlsx, Tables 6 and 7 | primary | yes | 2 Oct 2025 | H | |
| L9 | BPE definitions | Rounded to 5; private sector only (excludes government, non-profits); one-employee companies counted as zero-employee; "official statistics in development" | https://assets.publishing.service.gov.uk/media/68dbccc9c487360cc70c9f4e/BPE_2025_detailed_tables.xlsx (Contents, Notes sheets) | primary | yes | 2 Oct 2025 | H | |
| L10 | BPE 2026 availability | Not found; expected URL returned 404; BPE-25 says next edition "autumn 2026" | https://www.gov.uk/government/statistics/business-population-estimates-2026 | primary | yes (fetch returned 404) | 3 Oct 2026 | M | A 404 on an expected URL does not prove non-publication |
| L11 | All VAT/PAYE enterprises, UK | 2,786,985 | https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/activitysizeandlocation/datasets/ukbusinessactivitysizeandlocation/2026/ukbusinessworkbook2026.xlsx (Table 4, Total row) | primary | yes (1,055,829 bytes) | 24 Sep 2026 | H | Sum of classes equals Total |
| L12 | Manufacturing 10-33, ONS-26 | Total 128,065; 10-249 25,700 (11,360 + 8,450 + 3,775 + 2,115); 250+ 1,230 | same ONS xlsx, Table 4 (classes summed by me) | primary (derived) | yes | 24 Sep 2026 | H source, M exactness | Sum of base-5 rounded cells |
| L13 | Food and drink and Div 33, ONS-26 | 10-11: total 12,075, 10-249 3,190, 250+ 280. Div 33: total 15,590, 10-249 1,400, 250+ 70 | same ONS xlsx, Table 4 | primary (derived) | yes | 24 Sep 2026 | H / M | |
| L14 | 43.21, 43.22, 43.29, ONS-26 | 10-249: 3,455 / 2,520 / 860 = 6,835; totals 51,010 / 47,915 / 13,615 | same ONS xlsx, Table 4 | primary | yes | 24 Sep 2026 | H / M | ClassifAI recoding caveat |
| L15 | 81.10, 81.21, Div 81, ONS-26 | 81.10: total 4,690, 10-249 540, 250+ 85. 81.21: total 16,420, 10-249 3,045. Div 81: total 55,570, 10-249 6,005 | same ONS xlsx, Table 4 | primary | yes | 24 Sep 2026 | H / M | |
| L16 | Construction 41-43, ONS-26 | Total 392,855; 10-249 20,165 (Div 41 4,920; Div 42 2,005; Div 43 13,240) | same ONS xlsx, Table 4 | primary (derived) | yes | 24 Sep 2026 | H / M | |
| L17 | ONS-26 method notes | VAT and/or PAYE enterprises; base-5 rounding; late-2025 ClassifAI recoding, 93% agreement at five-digit level | same ONS xlsx, Notes and Cover sheets | primary | yes | 24 Sep 2026 | H | |
| L18 | ABS-24 manufacturing | 131,295 enterprises; turnover 685,359m; purchases 467,832m (68.3%); employment costs 114,741m | https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas/current/abssectionsas.xlsx (Section C) | primary | yes (1,055,873 bytes) | 26 May 2026 (2024 results) | H | Landing page fetched: https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/datasets/uknonfinancialbusinesseconomyannualbusinesssurveysectionsas/current |
| L19 | ABS-24 SIC 33 | 14,981 enterprises; turnover 21,338m (2023: 22,538m); purchases 13,025m; 33.12 5,445m (2023: 5,353m); 33.11 1,133m; 33.2 4,694m (2023: 5,315m) | same ABS xlsx (Section C) | primary | yes | 26 May 2026 | H | Subclass turnovers sum to 21,336m (rounding) |
| L20 | ABS-24 SIC 10 | 9,518 enterprises; turnover 113,990m; purchases 85,100m; SIC 11 suppressed | same ABS xlsx (Section C) | primary | yes | 26 May 2026 | H | |
| L21 | ABS-24 SIC 43.2x | 43.2: 108,556 enterprises; turnover 68,180m; purchases 36,204m. 43.21 34,310m; 43.22 24,032m; 43.29 9,838m | same ABS xlsx (Section F) | primary | yes | 26 May 2026 | H | |
| L22 | ABS-24 SIC 81 | 81.1: 4,432 enterprises; turnover 18,519m; purchases 9,705m. Div 81: 53,730; 40,856m; 17,435m | same ABS xlsx (Section N) | primary | yes | 26 May 2026 | H | |
| L23 | ABS-24 totals and coverage | Sections A-S turnover 5,088,995m; purchases 3,346,733m; covers about two thirds of UK GVA | same ABS xlsx (Sections A to S, Notes) | primary | yes | 26 May 2026 | H | |
| L24 | ABS has no repair-and-maintenance or spare-parts column | Columns: enterprises, turnover, aGVA, purchases, employment costs, capex, stocks | same ABS xlsx, column headers | primary | yes | 26 May 2026 | H for this workbook; M for ABS generally | Microdata/questionnaire not examined |
| L25 | Derived manufacturing shares | 263,085 / 5,690,265 = 4.6%; 84,295 / 1,417,730 = 5.9%; 128,065 / 2,786,985 = 4.6%; large 1,240 / 84,295 = 1.5%, 1,240 / 263,085 = 0.5% | computed from L1, L3, L11 | primary (derived) | yes | - | H | |
| L26 | Cross-source gap, all industries 10-249 | ONS-26 291,160; BPE-25 258,520 | both xlsx files | primary | yes | - | H numbers; L explanation | Cause not verified |
| L27 | Round-1 IBISWorld repair figures | Machinery repair GBP 5.3bn; metal-product repair GBP 1.0bn (2025-26 forecasts) vs ABS-24 33.12 5,445m and 33.11 1,133m | https://www.ibisworld.com/united-kingdom/industry/machinery-repair-maintenance-in-the-uk/2175/ ; https://www.ibisworld.com/united-kingdom/industry/fabricated-metal-product-repair-maintenance/2170/ | aggregator | no (not opened) | 2025-26 | L | Same order of magnitude only |
| L28 | Round-1 internal arithmetic | TAM parts 54-59 + 56 = 110-115bn vs stated 95-115bn and vs 86-90bn whole-economy base; 28bn / 12k = 2.3M vs 291,160 UK 10-249 enterprises | `research/uk/01-uk-market-size.md` section 5 | local file | yes (read) | 2026-10-02 | H | Pure arithmetic on round-1 text |
| L29 | Share of firms with in-house maintenance | Not found | one WebSearch; trade-press survey page returned 404 | - | no | - | - | Fluke survey found covers solar maintenance only |
| L30 | Assumptions A1, A2 | 30/50/70% and 50/70/90% | none (assumption) | none | no | - | L | Labelled assumptions only |

## 3. Round-1 claims: confirmed / contradicted / unverifiable

**Confirmed**
- 5.7M private-sector businesses at start 2025; 5.64M small, 38,435 medium, 8,335 large (L1, L2).
- Manufacturing has 1,240 large businesses, the most of any sector (L3).
- "115k-130k manufacturing businesses" holds only for VAT/PAYE-registered enterprises (ABS-24 131,295; ONS-26 128,065), not for BPE businesses (263,085) or employers (84,295).
- IBISWorld repair figures (GBP 5.3bn, GBP 1.0bn) are the same order as ABS-24 (5.4bn, 1.1bn); IBISWorld pages were not opened (L27).

**Contradicted**
- "7-9% of businesses are manufacturing": 4.6% of all businesses, 5.9% of employers (L25). It also conflicts with round-1's own 115k-130k, which is 2.0-2.3% of 5.7M.
- "~97% SME / ~3% large" and "90% SME": large is 1.5% of manufacturing employers and 0.5% of all manufacturing businesses (L25).
- "Manufacturing SME (10-249) about 30k": 25,700-25,845; 30,000 / 25,845 = 1.16, so overstated by about 16%.
- "FM and building services 50k-70k enterprises": SIC 43.2 + 81 = 112,540 + 55,570 = 168,110 registered enterprises (ONS-26); employers 58,915 + 33,560 = 92,475 (BPE-25); 81.10 alone 4,690. Matches no definition.
- "SIC 43.2 and 81.x, 20k-30k firms": 6,835 + 6,005 = 12,840 at 10-249 (ONS-26). It matches only 5-249 employees: 16,770 + 12,900 = 29,670.
- TAM: 54-59 + 56 = 110-115bn, above the 86-90bn whole-economy base it draws on, so it double counts; the 95bn floor is not derivable.
- "2.3M customer-equivalents" (28bn / 12k): more than the 291,160 UK enterprises of 10-249 employees in all industries. It divides MRO spend by software ACV.
- "2-4% penetration = 2,300-4,600 customers": 2-4% of 2.3M is 46,000-92,000. 2,300-4,600 customers is 7.0-13.9% of the 33,075 core pool (2,300 / 33,075; 4,600 / 33,075).

**Unverifiable here**
- "Manufacturing employed 2.3M at year-end, down 1.3% vs 2024": BPE-25 shows 2.35M employees at employers (2.55M including owners) at start 2025. "Year-end" and "-1.3%" are not in the statistical release as fetched (it says registered manufacturing businesses fell by 2,000).
- SAM component values, ACV, the 5k-8k FM contracts, Mordor FM GBP 64bn, Astute Analytica Europe MRO, workforce statistics: not tested this round (aggregator or vendor estimates).
- RS Group GBP 2.9bn: not tested; the cited URL name says "2025-26 results" while the claim says year to 31 Mar 2025, so check.

## 4. Not found / could not verify
- A citable share of UK manufacturers or contractors that run in-house maintenance or buy MRO parts directly. One search found only a solar-maintenance survey; a trade-press survey page returned 404. No filter in 1.3 is sourced.
- Any ONS Business Insights (BICS) or ABS line for repair-and-maintenance spend. None in the published tables; microdata not explored.
- ONS Supply and Use / Input-Output tables (industry purchases of product 33, repair and installation services): not fetched. Likely the best primary route to outsourced repair spend by industry; suggested next step.
- BPE 2026 (due autumn 2026) and the ONS 2025 edition (URL guess returned 404), so no trend analysis.
- Employment for 4-digit classes (BRES), BPE Table 30 confidence intervals, local-unit (site) counts: not examined.
- Maintenance versus project split inside 43.21/43.22/43.29; the exact IDBR snapshot date behind ONS-26.

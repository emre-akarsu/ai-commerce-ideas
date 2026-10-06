# MRO / facilities maintenance task templates and open materials datasets for seeding job-type kits

Scope: (a) maintenance task-template sources that could imply spare-parts/consumables kits; (b) open datasets of construction/maintenance materials usable to seed templates. Researched 2026-10-06. Licences were checked on the actual pages where noted; where a page could not be read, this is stated. No dataset below is invented; unverified items are flagged.

## SFG20 and alternative maintenance-schedule sources (structure, parts/consumables, licence, samples)

### Takeaway
SFG20 is the UK de facto PPM task library, but it is subscription-only (via the Facilities-iQ platform), has no public sample schedules, and its published schedule structure (task, frequency, criticality, time, skill) does not evidently include a parts/consumables list. So it can tell you *which tasks* happen on *which asset class*, not *which parts* to buy. The most useful free complement found is the CIBSE Indicative Economic Life Expectancy tool (2026, free), which gives component life down to "lowest maintainable component" aligned to SFG20 and NRM. openMAINT is an AGPL CMMS, but no pre-built PM/kit library was confirmed.

### Cited Findings
- SFG20 is owned and developed by BESA Publications Ltd; it offers "1,500+ customisable schedules", "110+ classes of assets", "200+ annual schedule updates", colour-coded criticality, and task references to SFG20 codes, NRM and Uniclass — [SFG20](https://www.sfg20.co.uk/)
- SFG20 content is accessed through its proprietary Facilities-iQ software on subscription (pricing on request via demo). No free sample schedules are offered on the site — [SFG20](https://www.sfg20.co.uk/); [SFG20 blog: what is Facilities-iQ](https://www.sfg20.co.uk/blog/what-is-facilities-iq)
- A schedule body shows the schedule title, unique reference number and instructions for each task, plus task criticality rating, frequency, estimated completion time and required skill set (search snippet describing third-party integration documentation; not verified on a full page) — [Accruent vxSuite help, SFG20](https://help.accruent.com/vxsuite/Content/Online%20Help/Admin/PPM/create_ppm/sfg20_sharelinks.htm)
- CMMS vendors such as Joblogic offer SFG20 import/sync. Joblogic's documentation does not mention parts, spares, consumables or materials fields in imported SFG20 data — [Joblogic support: SFG20](https://support.joblogic.com/docs/sfg20); [Joblogic SFG20 import](https://www.joblogic.com/sfg20/)
- CIBSE Guide M (Maintenance engineering and management, 2014) has Section 12, "Economic life factors", with Appendix 12.A1, "Indicative economic life expectancy". That appendix was republished in January 2020 as a separate document — [CIBSE Guide M 2014](https://www.cibse.org/knowledge-research/knowledge-portal/guide-m-maintenance-engineering-and-management-2014-pdf); [CIBSE tool 2020](https://cibse.org/knowledge-research/knowledge-portal/indicative-economic-life-expectancy-tool-2020)
- Guide M is now split into parts, e.g. M2 Strategy (2023), M5 Controls (2023) and M11 Life expectancy (2023) — [CIBSE M2](https://cibse.org/knowledge-research/knowledge-portal/guide-m2-strategy-2023/); [CIBSE M11](https://cibse.org/knowledge-research/knowledge-portal/guide-m11-life-expectancy-2023/)
- **CIBSE Indicative Economic Life Expectancy Tool (June 2026):** a zip with two PDFs (Appendix 11.A1, economic life tables; 11.A2, worked examples) and one Excel spreadsheet with a calculation tool. It is **free at both standard and member rates**. It gives Reference Service Life in years "from asset system/elements, sub elements down to lowest maintainable component and subcomponent", newly adds healthcare and catering assets, and is aligned with RICS NRM3 and SFG20 schedules. Nine variation factors are applied — [CIBSE tool 2026](https://cibse.org/knowledge-research/knowledge-portal/indicative-economic-life-expectancy-tool-2026/)
- openMAINT (Tecnoteca) is an open-source Property & Facility Management CMMS covering space/asset inventory, preventive/scheduled/breakdown maintenance, logistics and economic management, GIS and BIM. It is released under **AGPL**; the mobile app and self-service portal are proprietary. It is a verticalisation of CMDBuild and downloadable from SourceForge — [Tecnoteca openMAINT](https://tecnoteca.com/en/products/openmaint)

### Inferences
- SFG20 is a strong *task taxonomy* (asset class → task → frequency, with NRM/Uniclass codes), but its licence almost certainly prevents redistributing schedule content in a product. At most, a tool could integrate with it for customers who hold their own subscription, as Joblogic and Accruent do. Do not seed from SFG20 text.
- The CIBSE 2026 spreadsheet is the best UK-specific free source for a *component breakdown* of building-services assets, with replacement intervals that can drive "replacement kit" templates. Free access is not the same as an open licence, though. The copyright and reuse terms inside the download were not checked, so treat it as reference-only until they are read.
- Kit content (actual SKUs/consumables per task) appears to be absent from all of the UK schedule libraries checked. It would have to come from OEM manuals or be authored as synthetic, illustrative templates, labelled as such per repo rules.

### Gaps
- No public SFG20 sample schedule could be found to confirm whether any tasks list consumables (e.g. filters, belts). Not confirmed either way.
- NHS HTM estates documents (e.g. HTM 00, HTM 04-01 water), MOD/DIO specifications and BSRIA guides were not researched within the tool-call budget. Licence and structure are unknown.
- Fiix/UpKeep public PM template libraries: no public downloadable template dataset was confirmed (see next section).
- openMAINT: whether the demo database ships predefined maintenance plans or spare-parts data was not confirmed. The openmaint.org documentation was not read.

## Typical PM kits and how CMMS model kits/BOMs; ISO 14224 as a maintainable-item taxonomy

### Takeaway
CMMS products model parts as a bill of materials (BOM) attached to the asset record, linked to PM routines so that a generated work order carries a suggested-parts list. "Kits" are a storeroom bundle of the parts that are always used together for a given PM. ISO 14224 provides the canonical hierarchy, down to "maintainable item" and "part" (e.g. mechanical seal, bearing). That is the right shape for a kit template (asset class → maintainable item → parts), but the standard is paid and oil-and-gas oriented.

### Cited Findings
- A CMMS stores BOMs on asset records and links them to PM tasks and work orders, e.g. "a PM on a conveyor belt can automatically generate a work order that references the associated BOM". Kitting example: each filling-machine service needs "the same gasket, a small wrench, a specific lubricant, and cleaning supplies", which the storeroom pre-assembles as a kit. Part usage decrements inventory in real time — [MAPCON blog, June 2024](https://mapcon.com/blog/2024/06/bill-of-materials-success-in-work-orders)
- Fiix allows attaching SOPs, task lists, photos and "a list of suggested parts" to work orders, plus nested PMs and multi-asset work orders with date, meter, event or condition triggers — [Fiix PM software](https://fiixsoftware.com/cmms/preventive-maintenance-software/)
- UpKeep supports cloning of corrective/preventive work orders and a materials-management feature for MRO materials and purchase requests (G2 feature listing, secondary source) — [G2: UpKeep features](https://g2.com/products/upkeep/features)
- ISO 14224 defines a nine-level taxonomy. Levels 1-5 are use and location (industry, business category, installation, plant/unit, section/system); levels 6-9 are equipment unit, subunit, component/maintainable item, and part. Example maintainable items are a mechanical seal and a bearing (vendor blogs, secondary sources) — [Oxmaint](https://oxmaint.com/industries/power-plant/power-plant-asset-hierarchy-iso-14224-taxonomy-programs); [Fabrico](https://www.fabrico.io/blog/iso-14224-failure-taxonomy-codes/); [Accendo Reliability](https://accendoreliability.com/setup-asset-hierarchy/)
- ISO 14224 groups reliability and maintenance data into equipment data (taxonomy and attributes), failure data (cause, consequence) and maintenance data (action, resources, consequence, downtime) — [Fabrico](https://www.fabrico.io/blog/iso-14224-failure-taxonomy-codes/)

### Inferences
- A kit template schema for the product could mirror this: `job_type`/`task` → `asset_class` → `maintainable_item` → `part_role` (e.g. "mechanical seal", "V-belt", "filter element") with quantity/UoM. Tier A part numbers would then be resolved per asset, never assumed from the template, which is consistent with hard rule R2.
- The typical PM kit categories named in the brief (pump seal kits, filter sets, belts, bearings) match ISO 14224 "maintainable item" level examples. However, no open dataset was found that enumerates them per asset class with quantities.

### Gaps
- The ISO 14224:2016 page on iso.org returned HTTP 403, so the edition, price and licence could not be verified directly. ISO standards are normally paid and copyrighted, and its oil-and-gas equipment classes (pumps, compressors, valves etc.) only partly overlap with building services. This is from background knowledge, not a fetched source.
- No public Fiix or UpKeep downloadable PM template library (with parts) was found. Only feature-level marketing pages were found.

## Open datasets: construction estimates, BoQs, material prices, product catalogues, IFC samples

### Takeaway
There are a few genuinely open, sizeable sources, but none is a UK refurbishment kit list. DDC CWICR (55,719 work items with resources and a UK/GBP track) has the richest structure, but its data is CC BY-NC 4.0, so commercial use needs a separate licence. JCCDB (Japanese, CC BY 4.0) has item names and units only. buildingSMART community IFC samples are CC BY 4.0. ETIM classes are free to use and are the natural product-attribute vocabulary for sanitary/HVAC parts. Kaggle construction-cost datasets found are small or simulated.

### Cited Findings
| Source | URL | Licence (as verified) | Format / size | Fields / coverage | Usability for kits |
|---|---|---|---|---|---|
| DDC CWICR (OpenConstructionEstimate) | [GitHub](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR) | Data: **CC BY-NC 4.0** plus a separate commercial licence; code: Apache-2.0 | xlsx 150-400 MB; Parquet ~55 MB; CSV ~1.3 GB; Qdrant snapshots ~1 GB | 85 fields: work item codes, resource names/quantities, labour hours, machinery, unit rates. 55,719 work items, 27,672 resources (per a secondary listing), 30 regions incl. UK (GBP) | Best structural match (work item → resource list), but **non-commercial only** without a paid licence. Derived from ex-Soviet and Asian norms (GESN, FER, ENIR, Ding'e etc.), so UK specification fit is doubtful |
| JCCDB (Japan Construction Cost DB) | [Hugging Face](https://huggingface.co/datasets/ogasurfproject/jccdb) | **CC BY 4.0** (commercial and AI training allowed with attribution) | CSV, 85.1 MB, 190,806 rows | 95,403 items, 97 categories; columns category, item_name, unit; **no prices** | Japanese vocabulary; renovation categories not confirmed. Only useful for taxonomy and unit patterns |
| Synthetic construction material passports | [Hugging Face](https://huggingface.co/datasets/MahdiFattahi/synthetic-construction-material-passports) | Not checked | Not checked | Synthetic; building ID, material category (concrete, steel, timber, glass), mass estimates | Not relevant to MRO kits |
| buildingSMART Sample-Test-Files (official) | [GitHub](https://github.com/buildingSMART/Sample-Test-Files) | "Copyright © buildingSMART International Ltd"; terms in the repo LICENSE file (contents not read) | IFC 2x3 TC1, IFC4 ADD2 TC1, IFC4.3 ADD2 | "Simple models" for education/certification; specific models (e.g. bathrooms) not enumerated | Licence unclear; mostly schema test files |
| buildingSMART Community-Sample-Test-Files | [GitHub](https://github.com/buildingsmart-community/Community-Sample-Test-Files) | **CC BY 4.0** (per README) | IFC2x3, IFC4, IFC4.3 RC archive; Git LFS | Community files; README notes most do not pass validate.buildingsmart.org | Could supply room/sanitary-terminal object lists for bathroom templates, but which models contain bathrooms was not confirmed |
| ETIM classification model | [ETIM International](https://www.etim-international.com/) | Free to use (open standard); membership only needed to influence development (secondary sources) | Classes, features, values, synonyms | >5,500 classes across electrical, lighting, HVAC, sanitary, building automation; e.g. "sanitary sink" with width, material, mounting type | Good attribute vocabulary for kit line items (part-role → ETIM class); not a kit list itself — [Wisepim](https://wisepim.com/nl/gidsen/producttaxonomie/etim); [Anglera](https://www.anglera.com/glossary/etim-classification) |
| Kaggle "Construction Estimation Data" and similar | (URL not verified) | Not verified | ~1,000 rows | Search snippet describes a **simulated** dataset (material_cost, labor_cost, profit_rate, total_estimate) | Not usable for kits; flagged unverified |
| SMU Clowder "Construction Cost Datasets (.csv and .arff)" | [Clowder](https://clowder.smu.edu/datasets/6909026b99329d601640581d) | Not checked | CSV/ARFF | Described as a raw CSV of construction project costs from Kaggle | Project-level costs, not item-level |

### Inferences
- For a commercial product, DDC CWICR data cannot be used without the paid licence. JCCDB and the community IFC files are the only clearly open (CC BY 4.0) structured sources found, and neither is UK-MRO specific.
- ETIM classes plus a self-authored, synthetic kit template set (labelled illustrative) is the most licence-safe path. CWICR's schema (work item → resources with quantities) is a useful design reference without copying the data.

### Gaps
- Wikidata coverage of building products and Open Food Facts-style open building-product databases were not researched. I found no such UK project in passing.
- Kaggle dataset URLs and licences were not directly verified (snippets only).
- Specific IFC models containing bathrooms (e.g. widely cited residential samples) were not confirmed in either buildingSMART repo.
- The BCIS / RICS NRM cost libraries are known to be commercial; this was not researched here.

## data.gov.uk / gov.uk: materials price statistics and social-housing component lifecycles

### Takeaway
The DBT "Building materials and components" monthly statistics are open (OGL v3.0, Excel/ODS) and include a repair-and-maintenance price index. They are aggregate indices, not item prices, so they help with price drift but not with kit content. Social-housing component lifetimes are defined at a coarse level by the Decent Homes Standard (kitchen 30 years, bathroom 40 years, heating 15 years). Councils publish their own componentisation tables in committee papers, not as datasets.

### Cited Findings
- "Building materials and components: monthly statistics" is accredited official statistics from the Department for Business and Trade. It is published monthly, with the latest edition August 2026 (published 16 September 2026), in Excel and ODS, under the **Open Government Licence v3.0**. It covers price indices, bricks, concrete blocks, sand and gravel, slate, concrete roofing tiles, ready-mixed concrete and construction-product import/export; cement is updated annually — [GOV.UK collection](https://www.gov.uk/government/collections/building-materials-and-components-monthly-statistics-2012)
- Construction material price indices cover "all work, new housing, other new work and repair and maintenance", as well as selected building materials and components — [GOV.UK statistics Nov 2022](https://www.gov.uk/government/statistics/building-materials-and-components-statistics-november-2022); methodology at [GOV.UK methodology](https://gov.uk/government/publications/building-materials-and-components-methodology)
- Decent Homes Standard component lifetimes: kitchen 30 years, bathroom 40 years, heating 15 years. Bury Council's own standard uses 20, 30 and 15 years respectively, and states "Age alone does not qualify an item for replacement" — [Bury Council improvement works](https://www.bury.gov.uk/housing/housing-services/your-home/repairs/improvement-works)
- Under the Decent Homes "reasonably modern facilities" criterion, a kitchen must be 20 years old or less and a bathroom 30 years old or less (search summary) — [Ipswich: A Decent Home, detailed definition](https://www.ipswich.gov.uk/sites/ipswich/files/m-files/A_Decent_Home_-_Detailed_definition_and_Appendix_2.pdf)
- Local authority HRA componentisation papers (e.g. Cambridge, Southwark) publish component lists and lives as PDF committee appendices (contents not read) — [Cambridge HRA componentisation](https://democracy.cambridge.gov.uk/documents/s5166/Appendix%203%20-%20HRA%20componentisation.pdf); [Southwark investment strategy](https://moderngov.southwark.gov.uk/documents/s14836/Appendix%202%20Review%20of%20housing%20investment%20strategy.pdf)

### Inferences
- The DBT repair-and-maintenance index is usable (OGL) to inflate synthetic or illustrative template prices over time. Any price used must still carry explicit currency/UoM and come from the deployment profile, not be hard-coded.
- Decent Homes lifetimes plus CIBSE RSL values together give a free basis for "replacement due" triggers (kitchen/bathroom refurbishment vs plant component replacement). Neither lists parts.

### Gaps
- No data.gov.uk *dataset* (as opposed to PDF committee papers) of social-housing stock with component-level lifecycles was found. The English Housing Survey and Regulator of Social Housing statistical returns were not checked.
- Whether the DBT index tables include item-level series relevant to plumbing or sanitaryware (e.g. copper pipe, boilers, sanitaryware) was not confirmed from the tables themselves.

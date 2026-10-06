# Trade estimating template formats and UK bathroom/kitchen refurbishment quantity rules

Scope note: research done 2026-10-06 with about 20 web search/fetch calls. Several manufacturer PDFs and help pages could not be fetched (British Gypsum returned 403), so some figures come from search-result snippets or secondary sources. Each one is labelled. Check every ratio against the current datasheet before it goes into a production template. Numbers marked "derived" are my arithmetic on top of a cited rule, not published figures.

## (a) How trade software represents templates/assemblies/kits and how users can export them

### Takeaway
Every tool has some kind of reusable bundle of line items: "recipes" in Buildxact, "kits" in Tradify, "templates"/templated line items in Fergus, "Pre-Builds" in Simpro, "bundles" in ServiceM8, "macros" in Xactimate, quote templates in Jobber and Houzz Pro, and cost catalogs in Buildertrend. Few of them document a public, formula-driven, nested data model. The easiest routes are probably (1) the CSV/Excel exports of price lists or catalogues that most tools offer, (2) Simpro's REST API (catalog plus Pre-Builds) and ServiceM8's API (bundles), and (3) the Excel export of an estimate from Buildxact or Xactimate. Expect to import flat item lists with quantities. Quantity formulas will rarely survive export.

### Cited Findings
**Buildxact**
- Templates can be created three ways, including from an existing estimate. Template estimates are a separate collection in the help centre — [Buildxact: 3 ways to create a template](https://help.buildxact.com/en/articles/3038614-3-ways-to-create-a-template); [Templates & copying estimates](https://help.buildxact.com/en/collections/1777494-templates-copying-estimates)
- Estimates and job costings can be exported as a "clean", formatting-free Excel document — [Buildxact: estimate and job costings Excel export](https://help.buildxact.com/en/articles/5638324-estimate-and-job-costings-excel-export)
- Recipes (Buildxact's assemblies) can be built in bulk. The user exports estimate costings to Excel, reformats them into a recipe import template, and imports that. The column specification sits in a separate "Creating and Loading Recipes" article that I did not retrieve — [Buildxact: convert category items to recipes via Excel](https://help.buildxact.com/en/articles/4759729-how-to-convert-category-items-to-recipes-via-excel)
- A competitor, Buildern, publishes an importer for Buildxact estimates, so the Buildxact export is a recognised migration format — [Buildern: import estimates from Buildxact](https://help.buildern.com/en/estimates/import-estimates-buildxact)

**Tradify**
- Tradify lets users save customisable templates, price lists and kits. Price lists import from .CSV (Settings > Price List > Options > Import Price List File) or one-click from Xero, QuickBooks, MYOB Essentials and Sage. Some suppliers (Rexel, Ideal, John R Turk, Lear & Smith in AU) provide price lists pre-formatted for Tradify — [Tradify quoting software](https://tradifyhq.com/uk/features/quoting-software); [Tradify: import price list from Xero](https://help.tradifyhq.com/hc/en-us/articles/360019404573); [JRT Tradify](https://www.jrt.com.au/ajt/tradify)
- I found no documented export of kits specifically (gap).

**Fergus**
- Job Templates save a job's structure (tasks, settings and information) and are created from an active job via Job Settings > Save as Template. "Templated line items" also exist — [Fergus: Job templates](https://help.fergus.com/en/articles/14084101-job-templates); [Fergus: Templated line items](https://help.fergus.com/en/articles/13707975-templated-line-items)
- Customers import by CSV, and most reports export to CSV. I found no template/kit CSV import or export — [Fergus: importing customers](https://help.fergus.com/en/articles/415333-importing-customers)

**Simpro**
- Pre-Builds are assemblies of catalogue items plus labour (Premium edition). The API exposes Catalog Items and Prebuilds, and the official docs are at developer.simprogroup.com/apidoc — [Simpro About Materials](https://helpguide.simprogroup.com/Content/Service-and-Enterprise/About-Materials.htm); [Supergood: Simpro API summary (third party)](https://supergood.ai/docs/simpro-api); [Simpro API docs](https://developer.simprogroup.com/apidoc/)
- Third-party takeoff tools (Groundplan) push Simpro items onto plans, which suggests catalogue and pre-build data can be accessed through integrations — [Groundplan: using Simpro items](https://groundplan.document360.io/docs/using-simpro-items-on-plans)

**ServiceM8**
- Materials and clients import via a CSV template (Account > Materials & Services > Bulk Import) — [ServiceM8: import Materials and Clients](https://support.servicem8.com/hc/en-us/articles/200273634-How-to-import-Materials-and-Clients)
- The Bundles add-on is available via the API, "enabling you to build solutions to import ready-made bundles or update their bundle items". Bundles can be copied — [ServiceM8: Bundles API support](https://servicem8.com/updates/bundles-api-support); [ServiceM8: how to copy a bundle](https://support.servicem8.com/help-center/servicem8-add-ons/bundles/how-to-copy-a-bundle.md)

**Jobber**
- Quote templates hold pre-filled line items, pricing and terms — [Jobber: quote templates](https://help.getjobber.com/en/articles/quote-templates/)
- The public API is GraphQL (api.getjobber.com/api/graphql, OAuth 2.0). It has Products, Services, Quotes and line items, and a quoteCreate mutation — [Nexla: Jobber API connector (secondary)](https://docs.nexla.com/user-guides/connectors/jobber_api/jobber_api_data_source); [Pipedream: Jobber create quote](https://pipedream.com/apps/jobber/actions/create-quote)

**Xactimate / Xactremodel**
- Macros (saved groups of line items) export to PDF or Excel from Sketch or Estimate Items. Xactimate online cannot import macros, but desktop X1 can — [Xactware: Exporting macros](https://xactware.helpdocs.io/l/enUS/article/ism738njgh-exporting-macros)
- ESX is Xactimate's proprietary project format (measurements, sketch, photos). Third parties such as magicplan, Hover and EagleView produce ESX files — [magicplan: Xactimate ESX file](https://help.magicplan.app/xactimate️-esx-file); [Hover: merge ESX](https://help.hover.to/en/articles/10083806-manually-merge-your-esx-file-into-xactimate)
- Xactimate is US/insurance-centric and its price list is licensed by Verisk. I did not verify the licence terms (gap).

**Houzz Pro**
- Estimates can be saved as templates, and these include cost codes and categories (cost code = grouping under a cost category) — [Houzz Pro: set up cost codes](https://pro.houzz.co.uk/pro-help/r/how-to-set-up-cost-codes-in-houzz-pro); [Houzz Pro: categories vs cost codes](https://pro.houzz.com/pro-help/r/categories-vs-cost-codes)

**Buildertrend / CoConstruct**
- Buildertrend documents data-entry import limits. Third-party estimators (Clear Estimates, STACK, PlanSwift) export estimates into Buildertrend, so it is mostly an import target — [Buildertrend: Data entry import limits](https://buildertrend.com/help-article/data-entry-import-limits/); [Clear Estimates: export to Buildertrend](https://help.clearestimates.com/how-to-export-an-estimate-to-buildertrend); [STACK with Buildertrend](https://support.stackct.com/hc/en-us/articles/47346000245139)
- Buildern's cost-catalog Excel template, a comparable product, uses the required fields Name, Cost Type, Unit and Unit Cost, plus category. This is a useful reference for the minimum catalogue schema — [Buildern: import cost catalog from Excel](https://help.buildern.com/en/articles/15203910-how-to-import-a-cost-catalog-from-excel-in-buildern)

### Inferences
- Comparison (fields marked "?" were not confirmed in sources):

| Tool | Template object | Item/unit/qty | Formula qty | Labour | Markup | Nested | Export route | API |
|---|---|---|---|---|---|---|---|---|
| Buildxact | Recipe, template estimate | yes | ? (recipes scale by a takeoff qty; not confirmed) | yes (cost items) | ? | ? | Excel export of estimate; Excel recipe import | ? not found |
| Tradify | Kit, price list | yes | ? | ? | ? | ? | Price list CSV import; export ? | ? |
| Fergus | Job template, templated line items | yes | ? | ? | ? | ? | Reports CSV | ? |
| Simpro | Pre-Build | yes | ? | yes (items + labour) | ? | ? | API | REST, documented |
| ServiceM8 | Bundle | yes | ? | ? | ? | ? | Materials CSV; bundles via API | REST, bundles supported |
| Jobber | Quote template | yes | no evidence | ? | ? | no evidence | ? | GraphQL |
| Xactimate | Macro | yes | ? | yes (line items include labour) | ? | ? | Excel/PDF export of macro list | proprietary ESX |
| Houzz Pro | Estimate template + cost codes | yes | ? | ? | ? | ? | ? | ? |
| Buildertrend | Cost catalog / estimate templates | yes | ? | ? | ? | ? | Excel import | ? |

- Easiest customer-account imports, ranked: Simpro API (assemblies with labour, documented API), ServiceM8 bundles API, Buildxact Excel estimate export, Xactimate macro Excel export, then Tradify/ServiceM8 CSV price lists (flat, no assembly). A generic "one row per item with template_name, item, unit, qty, cost, labour_flag" CSV would cover all of them.
- None of the sources show that built-in quantity formulas (e.g. qty = area × rate) are exported. Our templates should therefore hold formulas themselves and treat imported customer templates as fixed quantities to be re-parameterised.

### Gaps
- Exact Buildxact recipe column spec; whether Tradify kits or Fergus templates can be exported; the Houzz Pro export format; Buildertrend's template export.
- Licence terms for built-in libraries (Buildxact supplier price files, Xactimate/Verisk price lists, Tradify supplier lists). Not researched in enough depth to state them.
- Powered Now and CoConstruct (now part of Buildertrend): no sources retrieved.

## (b) Published consumables ratios and quantity takeoff rules (UK bathroom/kitchen)

### Takeaway
Most consumables can be written as formulas with a manufacturer constant: adhesive kg/m² = bed thickness × product factor, grout kg/m² from Weber's joint formula, sealant m per cartridge = volume ÷ (width × depth), and plasterboard screws from fixing centres. The constants vary by product, so each template line needs the product's own constant, not a generic one.

### Cited Findings
| Item | Rule / ratio | Source | Notes |
|---|---|---|---|
| Tile adhesive (cementitious) | 1.2 kg/m² per mm of bed thickness (Mapei Keraflex Maxi S1) | [Mapei Keraflex Maxi S1 listing (retailer, quoting TDS)](https://www.skroutz.gr/s/12196759/Mapei-Keraflex-Maxi-S1-Klebstoff-Kacheln-23kg.html) | Secondary source. Bed thickness is not the same as notch depth; a combed bed is about half the notch depth after compression. Check the Mapei TDS. |
| Tile adhesive (Mapei Keraflex Easy) | 2–5 kg/m² | [Mapei Keraflex Easy](https://mapei.com/tr/en-tr/products-and-solutions/products-list/product-detail/keraflex-easy) | Product range, not tied to a notch |
| Grout | C (kg/m²) = 0.18 × E × H × (L+W)/(L×W); E = joint width mm, H = tile thickness mm, L, W in cm | Attributed to Weber TDS in [tilersforums](https://tilersforums.com/threads/how-to-calculate-your-grout-requirements.39223); see [Weber weberjoint TDS](https://www.middleeast.weber/files/sodamco/2025-11/TDS_weberjoint-weberjoint_thick.pdf) | 0.18 bundles in grout density (about 1.8). Example: 300×300×8 mm tile, 3 mm joint gives about 0.29 kg/m² (derived). |
| Silicone sealant | metres per cartridge = cartridge ml ÷ (joint width mm × depth mm). 310 ml at 10×10 gives about 3.1 m; 300 ml at 8×6 gives 6.25 m | [Truly PVC: estimating cartridge yield](https://www.trulypvc.com/blogs/how-to-guides/how-to-estimate-silicone-cartridge-yield) | Secondary; the formula is plain geometry. Add waste. |
| Plasterboard screws, partitions | 300 mm centres; 200 mm at external angles | [British Gypsum FAQ: screw fixing centres](https://www.british-gypsum.com/technical-support/self-help-tools/faqs/what-are-screw-fixing-centres-partitions-ceilings-encasements) | Page returned 403 to fetch; figures from search snippet. BG says to check against the specific system. |
| Plasterboard screws, ceilings | 230 mm centres in field, 150 mm at board ends | same as above | same caveat |
| Jointing compound (BG, hand) | Tapered flat joint: 9 kg/100 lm taping coat + 5 kg/100 lm first finish. Internal angle: 10 + 5 kg/100 lm. External angle: 18 + 9 kg/100 lm | [British Gypsum White Book: Jointing](https://www.british-gypsum.com/documents/white-book/british-gypsum-wb-jointing-1.pdf) | From search snippet of the White Book PDF; per linear metre of joint, not per m² |
| Joint tape | Gyproc Joint Tape: 150 m rolls, about 50 mm wide | [Gyproc Joint Tape PDS](https://www.okarno.com/documents/product-datasheet/british-gypsum-pds-gyproc-joint-tape.pdf) | Tape metres = joint linear metres |
| Cement backer board (Hardiebacker 500, 1200×800) | Corrosion-resistant screws at 200 mm centres, 15 mm from edges, 50 mm from corners; minimum 12 screws per board quoted | [tilersforums: Hardiebacker info](https://www.tilersforums.com/threads/hardie-backer-board-info.48531) | Forum quoting the installation guide; NOT verified against James Hardie's current guide |
| Insulated tile backer (Marmox) | Fixings at 300 mm max centres quoted (not confirmed as Marmox) | [tilersforums: Marmox screws](https://www.tilersforums.com/threads/marmox-boards-screws.66906) | Weak; washers per board not found |
| Primer (BAL Prime APD) | 2.5 L covers 12.5–25 m² neat, up to 50 m² diluted 1:1 | search snippet referencing BAL ([BIMobject BAL](https://www.bimobject.com/en-au/bal/product/bal-tank-it)) | Confirm against the BAL TDS |
| Primer (Ardex Multiprime) | about 6 m²/L | [Ardex NZ Multiprime datasheet](https://ardex.co.nz/products/Tiling/Multiprime/Multiprime%20Datasheet%2012.10.20.pdf) | NZ datasheet; UK product may differ |
| Tanking (Ardex 8+9) | Kit covers 100 sq ft (9.29 m²), 2 coats over drywall | [BIMobject Ardex 8+9](https://www.bimobject.com/en/ardex/product/ardex-8_9) | US/AU kit size; UK kit sizing not confirmed |
| Waste trap sizes (Approved Document H) | Washbasin 32 mm (75 mm seal); bath/shower 40 mm (50 mm seal); WC 100 mm; branch ≥ trap diameter | [drainagepipe.co.uk summarising ADH](https://drainagepipe.co.uk/soil-and-waste/uk-building-regulations-for-soil-and-waste-pipes) | Secondary; primary is ADH Table 1. Kitchen sink is 40 mm in ADH Table 1 (not confirmed in retrieved text) |
| Emulsion paint | Dulux Trade Vinyl Matt: up to 17 m²/L | [Dulux Trade Vinyl Matt](https://www.duluxtradepaintexpert.co.uk/en/products/dulux-trade-vinyl-matt) | "Up to" figure; litres = area × coats ÷ rate |

### Inferences
- Derived template formulas (my arithmetic on the cited rules; label them as derived):
  - Board screws, wall, 2400×1200 board on studs at 600 mm centres: 3 stud lines × ceil(2400/300)+1 = 3 × 9 = about 27 screws/board. At 400 mm centres: 4 × 9 = about 36.
  - Studs per partition: ceil(length/centres) + 1 (plus openings and ends). Noggins: one row per horizontal board joint or fixing line, so (studs − 1) pieces per row.
  - Board count = ceil(wall area / 2.88 m²) × (1 + waste). Joint length is about board perimeter ÷ 2 per board.
  - Adhesive kg = area × product factor (kg/m²/mm) × bed mm × (1 + waste).
  - Sealant cartridges = ceil(total joint length ÷ (ml ÷ (w×d))).
  - Paint litres = area × coats ÷ spreading rate.
- Tile waste allowance (10–15% asked) is commonly quoted, but I retrieved no manufacturer source for it. Treat it as a configurable parameter, not a cited constant.

### Gaps
- Not obtained from primary sources: notch-specific adhesive coverage tables (BAL, Weber, Ardex, Norcros); BAL Tank-it kit coverage; PTFE tape use; isolation valves per appliance (commonly one per hot/cold supply per appliance, but uncited); stud spacing defaults (400/600 mm is standard practice, but I did not retrieve a BG reference); Marmox washers per board; the current James Hardie UK fixing guide; and the Wickes/B&Q calculators.
- The British Gypsum site blocks automated fetching (403), so its figures rely on search snippets.

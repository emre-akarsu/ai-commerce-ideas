# UK cost guides, price indices and merchant taxonomies for refurbishment job templates

Scope: sources that could seed or validate job-type material templates (bathroom, cloakroom/WC, wet room, kitchen, full-house refurb). Researched 2026-10-06. Several consumer sites (Checkatrade blog, MyBuilder articles) returned HTTP 403 to automated fetch, so some coverage below rests on search snippets and is marked as such.

Labelling rule used throughout: **all consumer cost-guide figures are UNVERIFIED, marketing-grade estimates** with no stated sample or method seen. Use them only as sanity bounds, never as reference data.

## 1. Public consumer cost guides (Checkatrade, MyBuilder, Rated People, Which?, HomeBuilding & Renovating, Houzz UK, merchant cost guides)

### Takeaway
The cost guides seen give job-level price bands and a few component price ranges (suite, shower, tiles per m², "plumbing sundries"). None of the ones checked gives a quantified bill of materials. They help bound totals, not build quantity templates. Their content is copyrighted, and no reuse licence was found.

### Cited Findings
- Screwfix "New Bathroom Cost Guide" (2026) gives size-banded totals (UNVERIFIED): small cloakroom (<4 m²) "£3,000 – £5,000"; standard medium (4–8 m²) "£5,500 – £8,500"; large family "£7,500 – £11,000"; high-spec (>9 m²) "£12,000 – £20,000+" — [Screwfix guide](https://www.screwfix.com/guides/bathrooms-kitchens/bathrooms/new-bathroom-costs-guide)
- The same guide lists materials-only ranges: 3-piece suite "£400–£1,200"; thermostatic mixer shower "£150–£500"; vanity units (18mm moisture-resistant MDF) "£150–£600"; 10mm PVC wall panels "£60–£150"; tiles "£15–£50" per m²; "plumbing sundries" (connectors, pipe, fittings) "£300–£600". Labour: plumbers "£325 and £450 per day", tilers "£200–£350 per day". It also says labour is "45–60%" of total and advises a 10–15% contingency. It has no materials checklist or quantities — [Screwfix guide](https://www.screwfix.com/guides/bathrooms-kitchens/bathrooms/new-bathroom-costs-guide)
- Checkatrade bathroom guide (2024 version, per search snippet only; the page returned 403 to fetch): new bathroom including materials "£5,500 – £8,000", average "£7,000", 5–10 days (UNVERIFIED) — [Checkatrade (snippet)](https://www.checkatrade.com/blog/?p=5646). Checkatrade runs a bathroom-renovation hub of guides — [Checkatrade hub](https://www.checkatrade.com/blog/hub/bathroom-renovation/) (403 to fetch; contents not verified)
- A retailer guide (Bathroom Mountain, 2026) gives £4,500–£11,000 total, materials £2,000–£6,000, labour £1,800–£4,000. It attributes the labour share and regional spread to "data from Checkatrade and Rated People", which shows the guides copy each other — [Bathroom Mountain](https://www.bathroommountain.co.uk/inspiration-and-advice/new-bathroom-cost/)
- MyBuilder publishes trade how-to articles such as "how to tile a wall". Fetch was blocked (403), so its content and terms were not verified — [MyBuilder](https://www.mybuilder.com/tiling/articles/how-to-tile-a-wall)
- HomeBuilding & Renovating publishes how-to content with materials lists. Example: a stud wall guide naming plasterboard, studwork timber (75x50 or 100x50mm), 100mm oval nails or screws, jointing tape and joint compound, with 12.5mm board for interior walls (search snippet) — [HomeBuilding](https://www.homebuilding.co.uk/how-to-build-a-stud-wall)

### Inferences
- The guides quote each other, so agreement between them is not independent validation.
- The one useful structured element is the cost-guide decomposition (suite / brassware / furniture / wall finish / tiles per m² / sundries / labour day-rates). It could serve as a top-level template category list, not as quantities.
- "Plumbing sundries £300–£600" is a useful hint: templates should carry a sundries line, because cost guides do not itemise it.

### Gaps
- Rated People, Which?, Houzz UK and HomeBuilding cost guides were not fetched in this pass, so whether they itemise quantities was not verified. Checkatrade and MyBuilder blocked automated fetch (403).
- No cost guide checked stated a data method or sample size.
- I found no reuse licence for any cost-guide site; assume standard all-rights-reserved terms. Only Wickes's terms were actually read (see section 3).
- Kitchen, wet room and full-house guides were not individually checked.

## 2. Price indices and price books (ONS, DBT/DESNZ, BCIS, Spon's)

### Takeaway
The free, OGL-licensed series are the monthly DBT "Building materials and components" statistics. Their Construction Material Price Indices (CMPIs; Tables 1a/1b plus a detailed material index table) are built from ONS producer price indices (PPIs), and they include named series for ceramic and plastic sanitaryware, taps and valves for sanitaryware, rigid and flexible plastic pipes and fittings, timber and joinery, insulation, paint and ceramic tiles. No plasterboard or sealant/mastic series was found in the table checked. These indices can uplift template prices over time but cannot give quantities. BCIS and Spon's carry item-level rates, but both are paid and licensed.

### Cited Findings
- The statistics are published monthly by the **Department for Business and Trade** (earlier BEIS/BIS). The December 2025 edition came out on 14 January 2026 as Excel (.xlsx) and ODS with HTML commentary, under the **Open Government Licence v3.0** — [GOV.UK Dec 2025](https://www.gov.uk/government/statistics/building-materials-and-components-statistics-december-2025)
- The CMPIs (Tables 1a and 1b) were "resumed following a pause". The note reads: "ONS has resumed publication of producer price indices (PPIs) following a pause ... while issues with chain linking of data were resolved". The release includes a one-off table of revised PPI back data to 2009 — [GOV.UK Dec 2025](https://www.gov.uk/government/statistics/building-materials-and-components-statistics-december-2025)
- Method: the CMPIs are "based upon PPIs compiled by ONS (as well as other additional bespoke materials indices compiled by BCIS)". They are weighted by sector resource-cost and output, published as new housing, other new work, **repair and maintenance**, and all work, with 2015=100 — [DBT CMPI methodology](https://www.gov.uk/government/publications/building-materials-and-components-methodology/building-materials-and-components-statistics-material-price-indices-methodology)
- Named material series in "Table 2: Price Indices of Construction Materials" (December 2018 bulletin, the latest layout I could open as text). Relevant rows: "Ceramic tiles", "Ceramic sanitaryware", "Imported sawn or planed wood", "Imported plywood", "Sawn wood", "Particle Board", "Builders woodwork" (of which "Doors & windows"), "Screws etc", "Other builders' ironmongery", "Central heating boilers", "Taps and Valves for sanitaryware", "Metal Sanitaryware", plastic "Pipes and fittings (rigid)", "Pipes and fittings (flexible)", plastic "Sanitaryware", "Insulating materials (thermal or acoustic)", "Paint (aqueous)", "Paint (non-aqueous)", "Electric water heaters". Several cells are suppressed as "c" (confidential), e.g. ceramic sanitaryware. The table carries the note: "These indices are weighted averages of Producer Price Indices" — [DBT bulletin Dec 2018 (PDF)](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/769302/19-cs1_-_Construction_Building_Materials_-_Bulletin_December_2018.pdf)
- No "plasterboard", "plaster" or "sealants/mastics" row appears in that Table 2 — [same PDF](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/769302/19-cs1_-_Construction_Building_Materials_-_Bulletin_December_2018.pdf). A search summary said plaster appears in an older wholesale/building-materials index, but the cited link was the Irish CSO WPM series, not UK — [DBnomics CSO WPM28](https://db.nomics.world/CSO/WPM28?offset=30). Treat this as unconfirmed for the UK.
- ONS publishes quarterly **Construction Output Price Indices (OPIs)** inside the "Construction output in Great Britain" bulletins. OPIs covering January 2014 to June 2025 came out on 14 August 2025, and the bulletins report a private housing repair and maintenance (R&M) sector — [ONS June 2025 bulletin](https://www.ons.gov.uk/businessindustryandtrade/constructionindustry/bulletins/constructionoutputingreatbritain/constructionoutputingreatbritainjune2025newordersandconstructionoutputpriceindicesapriltojune2025); [ONS Dec 2025 bulletin](https://www.ons.gov.uk/businessindustryandtrade/constructionindustry/bulletins/constructionoutputingreatbritain/december2025newordersandconstructionoutputpriceindicesoctobertodecember2025)
- BCIS (RICS) Tender Price, Resource Cost and Output Price Indices: a GOV.UK page says the quarterly indices are available from BCIS at "£115 + VAT (annual subscription)". The page dates from the BIS era and the price is probably out of date — [GOV.UK BIS prices and cost indices](https://gov.uk/government/statistics/bis-prices-and-cost-indices)
- RICS/BCIS site terms exist ([RICS terms](https://www.rics.org/footer/rics-org-terms-and-conditions)) but were not read in detail.
- Spon's Architects' and Builders' Price Book 2026 (AECOM, 151st ed.) costs £185 and includes a VitalSource eBook code for one user until the end of December 2026. It is commercial and copyrighted — [Tomlinsons listing](https://www.tomlinsons-online.com/p-40142928-spons-architects-and-builders-price-book-2026.aspx); [OverDrive](https://www.overdrive.com/media/12360150/spons-architects-and-builders-price-book-2026)

### Inferences
- **Free (OGL):** DBT CMPIs and material indices (monthly xlsx/ods) and ONS OPIs (quarterly). Both are usable for price-drift adjustment and for checking that template unit prices move plausibly. Neither gives quantities or item prices.
- **Paid:** BCIS (indices plus the item-level Building Price Book / SMM rates) and Spon's (item rates with labour and material constants). These are the only sources found with per-unit quantity and labour constants (e.g. per m² tiling). Their licences would almost certainly forbid embedding the data in a product without a commercial agreement.
- For plasterboard and sealants, the closest proxies would need ONS PPI product codes (e.g. the plaster products and adhesives/sealants categories in the PPI dataset). I did not verify these.

### Gaps
- I could not confirm the current (2025/26) Table 1b/detail-table item list as text, because the 2025/26 xlsx was not downloaded. The item names above come from the December 2018 bulletin and may have changed.
- Current BCIS pricing and the free tier of bcis.co.uk were not verified.
- DESNZ is not the publisher; responsibility moved from BEIS to DBT.

## 3. Merchant taxonomies, project lists, terms of use and feeds

### Takeaway
Merchant category trees (Toolstation verified) map well onto template material classes: pipe and fittings by joint type, traps and wastes, toilet fittings, flexible tap connectors, tiling, sealants. Wickes and Screwfix how-to guides have usable "tools and materials" lists, but they are mostly qualitative with few quantity rules. Wickes's terms forbid commercial reuse without written consent. The only structured product data route found is affiliate feeds (Screwfix on Awin), which carry the affiliate programme's own terms.

### Cited Findings
- Toolstation category tree. Plumbing: "Waste Fittings", "Brassware, Valves & Taps", "Compression Fittings", "Toilet Fittings", "Push Fit Fittings", "Pipe", "Traps & Wastes", "Solder Ring Fittings", "Macerators", "Soil Pipes & Fittings", "Flexible Tap Connectors", "Press Fit Fittings", "End Feed Fittings", "Washing Machine Fittings", "Plumbing Consumables", "Clips, Washers & Fixings", "Water Heating", "Cold Water Storage". Painting & Decorating includes "Fillers & Putty", "Masking Tape", "Tiling", "Coving" — [Toolstation Plumbing](https://www.toolstation.com/plumbing/c3)
- Wickes's bathroom how-to hub lists 18 guides, including fitting sinks and taps, fitting a bath and taps, installing a toilet, tiling a floor or wall, tiling a bath panel or splashback, resealing, fitting a towel radiator and fitting a bath panel — [Wickes bathroom guides](https://www.wickes.co.uk/how-to-guides/bathrooms)
- Wickes terms: "The copyright in all website design, text, graphics, the selection and arrangement thereof ... belongs to us, our affiliates and our suppliers". Users may "download and print extracts ... for your administrative purposes". Other use "is strictly prohibited without our prior written consent". No explicit scraping clause was seen; the fetch summary only inferred one — [Wickes terms of use](https://www.wickes.co.uk/terms-of-use)
- Commercial scraper vendors advertise ready-made Wickes scrapers. This says nothing about permission — [Bright Data](https://brightdata.com/products/web-scraper/wickes); [Oxylabs](https://oxylabs.io/products/scraper-api/ecommerce/wickes)
- Screwfix runs an affiliate programme on Awin (GB: open). Awin publishers can get advertiser product feeds through "create-a-feed" and the ProductServe API, in Awin's legacy schema or a Google-Shopping-format enhanced feed — [affi.io Screwfix](https://affi.io/m/screwfix); [Awin Product Feed Guide](https://wiki.awin.com/index.php/Product_Feed_Guide)

#### Published "what you need" shopping lists (at least 3)
1. **Wickes – Tiling a wall** ([link](https://www.wickes.co.uk/how-to-guides/tiling/tile-a-wall)). Tools: "Manual tile cutter", "Tile scribe", "Spirit level", "Pencil", "Tape measure", "Drill and whisk attachment", "Grouting trowel", "Grouting float", "Grout finisher", "Sponge", "Bucket". PPE: goggles, dust mask, gloves. Materials: "Your chosen wall tiles", "Tile adhesive", "Tiling grout", "Tile spacers", "Backer boards", "Plasterboard PVA primer", "Stainless steel screws". Quantity rule: "add at least 10% extra to your total tile order"; 3mm spacers.
2. **Wickes – Installing a toilet** ([link](https://www.wickes.co.uk/how-to-guides/bathrooms/fit-a-toilet)). Tools: adjustable wrench, pipe cutter, water pump pliers, combi drill, spirit level, pipe/cable/stud detector, fixings. Materials: "Close-coupled toilet", "Flexible pan connector", toilet seat, "Silicone sealant", "PTFE tape", packers. PPE: goggles, gloves.
3. **Screwfix – How to build a stud wall** ([link](https://www.screwfix.com/guides/building-doors/carpentry-timber/how-to-build-a-stud-wall)). Tools: combi drill, saw, tape measure, spirit level, hammer and nails or nail gun, screwdriver, safety gear. Materials: timber studs "38x63mm or 38x89mm"; 12.5mm plasterboard, "typically one per 1.2m of stud wall width"; plasterboard screws "25-38mm", "spaced approximately 150mm apart"; timber screws "75-100mm"; wood glue; insulation "one per metre of wall width". Studs at "400mm or 600mm, centre to centre"; wall "around 125mm thick".
4. (Third-party, for comparison) **HomeBuilding & Renovating – stud wall** (snippet): plasterboard, 75x50/100x50 timber, 100mm oval nails or screws, jointing tape, joint compound, 12.5mm board — [link](https://www.homebuilding.co.uk/how-to-build-a-stud-wall)

### Inferences
- The how-to lists give a seed for template line items (adhesive, grout, spacers, backer board, primer, stainless screws; pan connector, silicone, PTFE, packers). The Screwfix stud-wall guide gives real parametric quantity rules (stud centres, board per 1.2m, screws at 150mm), which convert straight into quantity formulas. Tiling gives only a wastage factor; adhesive and grout coverage would need manufacturer data sheets.
- The lists are short and mix tools with consumables. Templates should separate tools/PPE from materials.
- The terms seen prohibit commercial reuse without consent. Rewriting the lists in our own words as synthetic, labelled seed data, with the URLs kept for provenance, is safer than copying them. Bulk scraping is not advisable without permission.
- The Toolstation tree splits fittings by joint technology (compression / push-fit / solder ring / end feed / press-fit). Templates need a "joint system" attribute so quantities can map to SKU families.

### Gaps
- Category trees for Screwfix, Wickes, Travis Perkins, Plumb Center/Wolseley, City Plumbing, B&Q/TradePoint and Victorian Plumbing were not fetched in this pass.
- Website terms were read only for Wickes. Screwfix's terms URL returned 404, and B&Q, Toolstation and the rest were not read.
- No B&Q (diy.com) how-to shopping list was retrieved (guessed URL 404).
- I found no public merchant product API (outside affiliate feeds) and no merchant "project bundle" (e.g. a bathroom kit list) in this pass.
- Whether Toolstation, Wickes or B&Q run affiliate feeds was not confirmed.

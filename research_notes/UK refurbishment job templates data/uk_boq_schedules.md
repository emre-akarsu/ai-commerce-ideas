# UK bills of quantities, schedules of work and schedules of rates for domestic refurbishment (bathroom / kitchen / void) — public sources for job-type material kits

Researcher notes, 2026-10-06. Method: web search + fetch; PDFs/DOCX downloaded and text-extracted locally (pdftotext / unzip). Contracts Finder notice pages and attachment URLs returned HTTP 403 to both WebFetch and curl from this environment, so Contracts Finder content below is taken from search snippets and third-party mirrors (bidstats.uk), not read first-hand. Treat those items as lower confidence.

## Q1. Which UK public tenders publish schedules of work, specifications or BoQs as attachments?

### Takeaway
Social-housing kitchen and bathroom programmes are routinely tendered with specifications and SOR baskets attached. The most reliably downloadable files I found are on **Sell2Wales** (Welsh portal; direct `NoticeBuilder_FileDownload.aspx?id=` links work without login). **Contracts Finder** attachments exist (`/Notice/Attachment/<guid>`) but returned 403 here. Many English programmes, such as LB Hillingdon's multi-phase Kitchen & Bathroom Replacement Programme, price against a "basket" of **M3NHF SOR v7.1** codes and do not publish a bespoke BoQ.

### Cited Findings
- **Sell2Wales, `NoticeBuilder_FileDownload.aspx?id=376193`**: "BATHROOM SPECIFICATION – Bathroom replacement for general needs dwellings", V1, dated 24.11.2025, author Ibrar Mian. It is a performance specification with a branded sanitaryware table, an "All-in Bathroom Renewal Rates" checklist and tenant-choice options. I downloaded and read it in full. The issuing landlord is not named in the extracted text; search placed it next to Welsh kitchen/bathroom notices (e.g. Vale of Glamorgan kitchen, bathroom, wet room and electricals upgrades, est. £2.9m inc VAT, Mar 2026–Aug 2027), but I did **not** confirm which body issued it — [Sell2Wales doc 376193](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=376193); related notices [Sell2Wales 141716](https://www.sell2wales.gov.wales/search/search_switch.aspx?ID=141716), [Sell2Wales 145399](https://www.sell2wales.gov.wales/search/search_switch.aspx?ID=145399), [FTS 065572-2025](https://www.find-tender.service.gov.uk/Notice/065572-2025)
- **Sell2Wales, `id=357559`**: a 118-page extract of the **M3NHF Schedule of Rates Version 8 – Responsive Maintenance and Void Property Works – SOR Long Descriptions**. It contains 801 coded items with unit and rate. A Welsh buyer attached it as a tender document. The PDF metadata title reads "M3NHF SOR v7.2 Responsive & Voids" (created 8 Oct 2025, author Rand Associates), but the cover says Version 8 (2023). The metadata and the cover conflict, and I read the cover as authoritative — [Sell2Wales doc 357559](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)
- Other Sell2Wales attachments surfaced by the same search are M3NHF SOR documents: v7.2 Communal Mechanical & Electrical Works (id=334127) and v8 Planned Maintenance & Property Reinvestment Works (ids 357553–357577, per search snippets; not opened) — [Sell2Wales 334127](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=334127), [Sell2Wales 357553](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357553)
- **LB Hillingdon, "Kitchen & Bathroom Replacement Programme – Phase N"**: a recurring series on Contracts Finder. Phase 19 covered about 66 occupied dwellings (40 kitchens, 35 bathrooms, ~£320k, Feb 2023) and Phase 20 about 75 dwellings (~£400k, Apr 2023). The contracts are "based upon a pre-determined basket of rates developed using the National Housing Maintenance Forum M3NHF Schedule of Rates version 7.1 including its long descriptions, the specifications of workmanship and materials and the relevant SOR rates" — [bidstats Phase 19](https://bidstats.uk/tenders/2023/W06/792265018), [bidstats Phase 20](https://bidstats.uk/tenders/2023/W14/796065847), [bidstats Phase 10](https://bidstats.uk/tenders/2022/W17/773587233), [ukspending Phase 32](https://ukspending.com/contracts/36172)
- A Hillingdon phase on Contracts Finder (Phase 27 per snippet) covered "circa 76 occupied domestic dwellings… 40 Kitchens & 40 Bathrooms & 12 Separate WC's". Separate WC replacement appears as its own line in these programmes — [Contracts Finder notice 17827971…](https://www.contractsfinder.service.gov.uk/Notice/17827971-84e2-4670-ac4a-6c13c871fc77) (403 to direct fetch; content from search snippet)
- Other Contracts Finder notices from search (titles/snippets only; 403 on fetch): Wakefield and District Housing "enhanced (major) voids works and associated component replacements including kitchens, bathrooms, heating…"; a North Tyneside framework where "the provider is required to produce a full Bill of Quantities" — [CF aa15c9b2…](https://www.contractsfinder.service.gov.uk/Notice/aa15c9b2-a573-4c20-b7b0-6e722fd8489b), [CF 97d1d5d8…](https://www.contractsfinder.service.gov.uk/Notice/97d1d5d8-1f77-4841-a02b-14ce09c8abd9), [CF 487e51b6…](https://www.contractsfinder.service.gov.uk/Notice/487e51b6-1784-41de-911d-d8f77df29032), [CF 50816534…](https://www.contractsfinder.service.gov.uk/Notice/50816534-0937-4ffc-876a-d8bed4ebc496), [CF ba456a3a…](https://www.contractsfinder.service.gov.uk/Notice/ba456a3a-41a0-4c14-8797-4d0ada1ada56)
- A Contracts Finder attachment surfaced for the "bathroom replacement for general needs" search; it returned 403 and was not read — [CF attachment 79520dd0…](https://www.contractsfinder.service.gov.uk/Notice/Attachment/79520dd0-91aa-4647-ac93-2be71b16dfbb)
- Further programme notices: Arun DC kitchen & bathroom refurbishment programme; "Contract 52 – Kitchens & Bathroom Replacement 2021–2024"; a stock investment kitchen and bathroom replacement record — [bidstats Arun 2021](https://bidstats.uk/tenders/2021/W37/758972465), [bidstats Contract 52](https://bidstats.uk/tenders/2021/W25/753467757), [FTS 015453-2021](https://www.find-tender.service.gov.uk/Notice/015453-2021), [Stotles](https://app.stotles.com//records/c4375ba5-6109-495c-83bf-c1cc5e94cf69/stock-investment-programme-kitchen-and-bathroom-replacement)
- Find a Tender kitchen notices from search (not opened): Metropolitan Thames Valley keyworker works including "kitchen wall, base and corner units, sink and taps, lighting, extractor fan, new flooring, and appliances"; Sanctuary kitchen replacements — [FTS 006848-2022](https://www.find-tender.service.gov.uk/Notice/006848-2022/PDF), [FTS 043098-2025](https://www.find-tender.service.gov.uk/Notice/043098-2025/PDF)

### Inferences
- Sell2Wales is the most machine-accessible source of real tender attachments (stable numeric IDs, no login needed). Contracts Finder and Find a Tender attachments may need a browser session or registered supplier login, or may block automated clients. Expect friction if this data is to be harvested.
- Because English programmes price against M3NHF codes, the item vocabulary of real kitchen and bathroom jobs is largely the M3NHF vocabulary. Bespoke tender BoQs are less common than SOR baskets plus a client material specification (brand table).

### Gaps
- Could not open any Contracts Finder or Find a Tender attachment directly (403), so I have no first-hand list of Contracts Finder attachment file names. A browser-based pass is needed.
- Did not establish who issued Sell2Wales doc 376193.
- No priced BoQ (quantities × rates) for a single bathroom or kitchen job was found and read. No wet-room or full-house BoQ was read.

## Q2. NHF Schedule of Rates / M3NHF: contents, coding, licence

### Takeaway
M3NHF (published by M3 Housing Ltd; compiled by Rand Associates with NHF HAMMAR South West; NHF Form of Contract 2023) uses **6-digit numeric item codes plus a 1-letter priority code** (E/U/R/X), with units (NO, IT, LM, SM, CM, HR) and rates. It is **"All rights reserved"** commercial copyright: no reproduction without M3 Housing's permission. Buyers nonetheless attach extracts to public tenders, so the code lists can be seen publicly but **are not licensed for reuse**.

### Cited Findings
- Cover text: "M3NHF Schedule of Rates VERSION 8 – Responsive Maintenance and Void Property Works – SOR Long Descriptions. Published by M3 Housing Ltd… ISBN 978-1-908409-00-3… Version 8 revised and updated in 2023 by Rand Associates Consultancy Services Ltd. and Anthony Collins Solicitors LLP. Incorporating the NHF Form of Contract 2023 (ISBN 978-1-908409-26-3). **All rights reserved. No part of this publication may be reproduced… without the prior permission of M3 Housing Ltd.** © Rand Associates Consultancy Services Ltd and NHF HAMMAR South West" — [Sell2Wales doc 357559](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)
- Coding rule 002: "Each item has a 6 character numeric code reference and a single character alpha priority code reference", e.g. `125001 E Chimney: Ball chimney flue… IT 47.64`. Priorities: E Emergency, U Urgent, R Routine, X User defined. There are three description levels (short/medium/long). Units: HR, NO, IT, LM, SM, CM — [same](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)
- Work sections: Foundations; Groundworks; Fencing and Gates; Drainage; Brickwork; Masonry; Roofing; Carpentry and Joinery; Plasterwork and other Finishes; Wall and Floor Tile and Sheet Finishes; Painting and Decorating; Cleaning and Clearance; Glazing; Plumbing; Heating, Gas Appliances and Installations; Electrical; Disabled Adaptations and Minor Works; Specialist Treatments; Energy Efficiency Appliances and Components; Scaffolding — [same](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)
- Kitchen and bathroom code families seen in the extract (short descriptions, rates in £ as printed):
  - **371xxx Kitchen units** (to match existing, or the client's standard specification), e.g. 371001 single base to match existing NO 200.26; 371023 single base 600x500 NO 160.91; 371033 double base 800mm NO 216.06; 371039 corner base 800mm; 371045 larder unit; 371047 appliance unit 1950mm; 371057 single wall 600x300 900mm high; 371061 double wall 1000x300 900mm high; 371071 drawer pack 500x600; 371074 cooker hood cover. Long description of 371021: "Renew any type of prefinished single 300x500mm base unit including plug and scribe… complete with door, drawer front and drawer box, shelf, decor panels, handles, but excluding worktop and plinth."
  - **372xxx Worktops**: 372001 worktop NE 40mm post formed LM 46.60; 372002 double post formed; 372009 fly end panel; 372011 gallows bracket; 372013 leg; 372017 joint strip; 372019 25x25 edge trim; 372021 coverbead.
  - **373xxx/375xxx Unit components**: base/wall/tall doors, cupboard back, shelf, side panel, plinth (LM), drawer box, child lock, pelmet, cornice, upstand to worktop (LM 9.47), handles (NE 5/10/15), remove and dispose unit/worktop.
  - **Sink tops and sink base units**: cross-referenced as "Items 630101 to 630315 in PLUMBING" (that range is **not** in this extract).
  - **388xxx Bath panels**: hardboard side/end and framing; acrylic side/end.
  - **350013–350017 Lining to shower rooms/wet rooms**: 9mm WBP ply; 12mm water-resistant tiling board; acrylic-faced laminated wall panelling (SM 138.38).
  - **570xxx Shower screens**: over-bath glass screen; two- and three-sided glass screen. **565xxx Mirrors**: 450x450, 900x600.
  - **387xxx Duct casings/boxing-in and access panels**.
  - — [Sell2Wales doc 357559](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)
- Hillingdon's programmes use "M3NHF Schedule of Rates version 7.1 including its long descriptions, the specifications of workmanship and materials" — [bidstats Phase 19](https://bidstats.uk/tenders/2023/W06/792265018)

### Inferences
- The 6-digit M3NHF codes are a de facto shared vocabulary for UK social-housing repairs and planned works. A kit template could store an optional `m3nhf_code` cross-reference. Bundling M3NHF descriptions or rates in the product would need a licence from M3 Housing Ltd. Quoting the code numbers alone may be lower risk but should be checked legally.
- SOR items are labour-plus-material composite operations ("renew… including plug and scribe… make good"), not SKU-level bills of materials. They describe the job steps, but a parts kit would still need the brand/material table from the client specification (see Q4).

### Gaps
- Did not obtain M3NHF price or licence terms from m3h.co.uk (search returned nothing specific). Pricing is unknown and should be treated as **paid/licensed**.
- The Plumbing (63xxxx: sanitaryware, sinks, taps), Electrical and Heating sections were not in the extract I read, so I have no M3NHF codes for WC/basin/bath/shower.
- Did not find a separate "NHF Schedule of Rates" distinct from M3NHF. Historically they are the same product line (M3 + NHF), but that is not verified here.

## Q3. Public Decent Homes / council kitchen and bathroom component definitions

### Takeaway
The Decent Homes guidance (DCLG, June 2006, OGL v3.0 on gov.uk) is public. It defines a modern kitchen as 20 years old or less and a modern bathroom as 30 years old or less (Criterion C). Its disrepair test defines the **kitchen as 6 items** and the **bathroom as 3 items**. Councils also publish tenant leaflets describing kitchen and bathroom scope.

### Cited Findings
- Criterion C (reasonably modern facilities) fails if the dwelling lacks 3 or more of: "a kitchen which is 20 years old or less; a kitchen with adequate space and layout; a bathroom which is 30 years old or less; an appropriately located bathroom and WC; adequate noise insulation; adequate size and layout of common entrance areas for blocks of flats" — [A Decent Home: definition and guidance (June 2006) PDF](https://assets.publishing.service.gov.uk/media/5a7968b740f0b63d72fc5926/138355.pdf); landing page shows **Open Government Licence v3.0** — [gov.uk publication page](https://www.gov.uk/government/publications/a-decent-home-definition-and-guidance)
- Para 5.19: a kitchen fails on space and layout if it is "too small to contain all the required items (sink, cupboards cooker space, worktops etc)". A bathroom/WC is inappropriately located if it is in or accessed through a bedroom, if the main WC is external or on a different floor to the nearest wash hand basin, or if a WC without a WHB opens onto a kitchen next to the food preparation area — [DHS PDF](https://assets.publishing.service.gov.uk/media/5a7968b740f0b63d72fc5926/138355.pdf)
- Annex A Table 2 "poor condition": **Kitchen** = "Major repair or replace 3 or more items out of the 6 (cold water drinking supply, hot water, sink, cooking provision, cupboards, worktop)". **Bathroom** = "Major repairs or replace 2 or more items (bath, wash hand basin, WC)". Table 1 disrepair lifetimes: kitchen 30 years, bathrooms 40 years (footnote 19 explains the shorter 20/30 years used for Criterion C) — [DHS PDF](https://assets.publishing.service.gov.uk/media/5a7968b740f0b63d72fc5926/138355.pdf)
- Sector commentary on Criterion C during the DHS review: [ARCH/NFA submission on Criterion C (2021)](https://www.almos.org.uk/wp-content/uploads/2021/07/ARCH-NFA-DHS-submission-criterion-c-Modern-Facilities-and-Services.pdf) (not opened)
- Council tenant-facing scope documents: Ashford BC "A guide to Kitchen Refurbishment" (2026) [Ashford 2026 PDF](https://www.ashford.gov.uk/media/q01bzci4/kitchen-refurbishment-2026.pdf), also 2025 and 2020 editions [2025](https://www.ashford.gov.uk/media/hqzg4i5x/kitchen-refurbishment-2025.pdf), [2020](https://www.ashford.gov.uk/media/ogsbkkqv/abc00055-kitchen-refurbishment-2020-amends.pdf). Clackmannanshire Council "Kitchen Replacement" leaflet (Scotland, so SHQS rather than DHS; undated) [clacks 2663](https://www.clacks.gov.uk/document/2663.pdf), plus a bathroom leaflet [clacks 2659](https://www.clacks.gov.uk/document/2659.pdf) (not opened). Waverley BC "Appendix L – Decent Homes Bathroom Specification" (2013 Executive paper; 403 on fetch; pre-2018) [Waverley](https://modgov.waverley.gov.uk/Data/Executive/20130205/Agenda/Appendix%20L%20-%20Decent%20Homes%20Bathroom%20Specification.pdf). Camden specifications with Mira electric shower details (SSL error on fetch; not read) [Camden 8107759](https://camdocs.camden.gov.uk/CMWebDrawer/Record/8107759/file/document)

### Inferences
- The DHS 6-item kitchen and 3-item bathroom sets are a defensible, OGL-licensed minimum skeleton for kitchen and bathroom kit templates: kitchen = cold drinking water, hot water, sink, cooking provision, cupboards, worktop; bathroom = bath (or shower), WHB, WC. A "cloakroom/WC replacement" kit maps to WC + WHB (DHS requires a WHB on the same floor as the WC).

### Gaps
- Did not review the 2025 consultation or reform of the Decent Homes Standard (DHS 2 / MEES for social housing), which may change component definitions.
- No public wet-room spec was read; Walsall's DFG low-level tray spec exists but was not opened — [Walsall DFG low level tray](https://go.walsall.gov.uk/sites/default/files/2022-08/specification_for_dfg_low_level_tray-3.pdf).

## Q4. Extracted item lists (bathroom refit and kitchen refit), with sources

### Takeaway
I extracted four item lists from documents I read. Three are bathroom lists (Welsh 2025 tender spec, Broadland HA 2023 spec, M3NHF codes) and three are kitchen lists (Broadland 2023, Ashford 2026, Clackmannanshire, plus M3NHF codes). All items below are quoted or paraphrased from the cited document. Brand names are the buyers' specified products, and the documents allow "or equal approved".

### Cited Findings

**A. Bathroom full refit — Welsh social landlord tender spec, V1 24.11.2025** — source: [Sell2Wales doc 376193](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=376193)
- Sanitaryware table (product – brand/range – manufacturer):
  - WC including seat – Options range dual flush (4.5/3L) – Twyfords
  - Bath tub – Celtic range 1700mm x 750mm, slip resistant base – Twyfords
  - Bath panel – white hardboard, gloss white – KL Evesham
  - Basin inc full pedestal – 2 tap holes, Options range – Twyfords
  - Bath taps – Lever Chrome 85mm deck-mounted lever, 2 tap holes, bath pillar tap – Bristan
  - Basin taps – Lever Chrome 90mm cloakroom lever, 2 tap holes, basin pillar tap – Bristan
  - TMV3 pre-set at 43°C – Pegler 402 or Bristan MT503
  - Shower including rail, hose etc – Triton T80Z ECO 8.5kW White (electric)
  - Shower curtain & pole – plain white – Croydex
  - Bathroom extractor fan – filterless SELV extract fan (part no. 195-35-013) – Envirovent
  - Bathroom lights – Ovia Evo range LED circular bulkhead – Scolmore
  - Flooring – Polysafe Wood FX (standard bathrooms) – Polyflor; "R10 rated 2mm thick slip resistant vinyl sheet", hot-welded joints
  - Wall tile – Marmo stu Grey / White 270x420mm – N&C Nicobond
- Ancillaries and consumables named in the scope or checklist: copper hot/cold feeds; uPVC traps and waste back to existing 110mm SVP; 38mm white PVC-u trap/waste; isolation valves (non-manipulative compression type 'A' or fibre washer) on feeds to WC, shower and taps; rigid WC pan connector ("avoid… flexi"); new toilet seat; plug & chain (bath and basin); bath overflow; bathroom-grade white sealant (bath/basin to tile) and clear sealant (WC to floor); tile trim (plastic) to external edges; white waterproof grout; shower pull-cord switch with neon; new cable to existing board; supplementary equipotential bonding; latex levelling compound; 18mm T&G moisture-resistant chipboard or marine ply overlay; uPVC window board; skirting; plaster skim with bonding agent; primer, white vinyl matt emulsion with anti-mould additive, eggshell to walls, undercoat/gloss to joinery; studwork as needed.
- Tiling extent: bath area tiled bath-to-ceiling on 3 sides; splashback about 270mm high above the WHB.

**B. Bathroom (new-build affordable spec) — Broadland Housing Association, "Affordable Housing Specification", March 2023** — source: [North Norfolk DC-hosted PDF](https://www.north-norfolk.gov.uk/media/8753/broadland-housing-association-affordable-housing-specification.pdf)
- Twyfords E100 Square 450x350 washbasin/pedestal, 1 tap; Twyfords E100 square close-coupled premium pan (ref E11148WH); Aspect 1700x750 bath (2 tap, slip resist, with legs); Endurance 1700/750 front/end bath panel (PP2181WH/PP2183WH); Bristan Blitz bath mixer / basin mixer (BTZ BF C / BTZ BAS C); Twyfords GEO corner-entry shower cubicle 1900x900x900 (560.122.00.2) with R6231WH 900x900x55 tray; Mira React EV shower mixer; Armitage Shanks Concept toilet roll holder (N1314) and 450mm towel rail; Stelrad Classic 1744x500 LPHW towel rail; wall tiles 600x300 concrete matt, white grout, chrome trim (CTD Core); Forbo Novilon Viva vinyl (ref 57812, Aquagrip R10); Greenwood Unity CV2TIP extract fan (WCs, up to 20 l/s); Manrose cowl/louvre vents.

**C. Kitchen refit — Broadland HA spec, March 2023** — [same PDF](https://www.north-norfolk.gov.uk/media/8753/broadland-housing-association-affordable-housing-specification.pdf)
- Units: Symphony (Cranbrook or Woodbury; Howdens alternative); worktop 40mm oak-block laminate; 95mm upstand; handle Matt Nickel Bow (HPK647); Blanco Classic Pro 6S-1F 1.5-bowl stainless sink (BL45366); Blanco Crest 6 single-lever mixer (BM1406CHB); stainless steel splashback behind hob; Forbo Novilon Viva vinyl (ref 5632); Axia Eclipse 150 extract (up to 61 l/s, in lieu of cooker hood on rented homes). Shared ownership only: Zanussi 60cm stainless cooker hood, 60cm four-zone ceramic hob, single fan oven.

**D. Kitchen refit — Ashford Borough Council "A guide to Kitchen Refurbishment" (2026)** — [Ashford PDF](https://www.ashford.gov.uk/media/q01bzci4/kitchen-refurbishment-2026.pdf)
- Replacement kitchen units and worktops (laminated worktops); glazed wall tiles; new floor covering (floor tiles mentioned in week 3); redecoration including ceiling and **coving**; plumbing and gas pipework alterations; upgraded and repositioned sockets and switches; new lighting and extractor fan where needed; new sink and base unit; boxing in of pipes; skirting/architraves where needing renewal; plinths; spaces for cooker, washing machine and tall fridge-freezer (standard 640mm space). Sequence: wk1 strip-out, electrical 1st fix, sink, making good, ceiling re-plaster; wk2 units and worktops; wk3 tiles, decoration, floor, plinths, electrical 2nd fix.

**E. Kitchen refit — Clackmannanshire Council "Kitchen Replacement" tenant leaflet (undated; Scotland)** — [clacks 2663](https://www.clacks.gov.uk/document/2663.pdf)
- Remove all units including sink unit and worktops; new base units, wall units and worktops; inset sink in worktop; worktops extended over washing machine and fridge where possible; washing machine connections; electrical point for extractor fan (fan fitted only where condensation is evident); fused spur for future cooker hood; electric **and** gas cooker points; three double sockets above worktop plus remote appliance sockets below worktop with neon switched spurs above; vinyl flooring; walls papered and emulsioned; woodwork repainted.

**F. M3NHF code families usable as a cross-reference** — see Q2 (371xxx units, 372xxx worktops, 373/375xxx components, 388xxx bath panels, 3500xx shower/wet-room linings, 570xxx shower screens) — [Sell2Wales doc 357559](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)

### Inferences
- A defensible "bathroom full refit (social housing standard)" kit skeleton, taken from A and B: WC pan + cistern + seat (dual flush), close-coupled; WHB + pedestal; bath 1700x750 + panel(s); bath and basin taps (pillar or mixer); TMV3; shower (8.5kW electric, or mixer + riser) + curtain/pole or screen; extract fan + vent; LED bulkhead + pull-cord switch; wall tiles + grout + trims + adhesive; slip-resistant R10 vinyl sheet; feeds, isolation valves, traps/wastes 32/40mm, pan connector, sealants; boards (WBP ply / MR chipboard / tile backer); decorating materials. The cloakroom, WC-replacement and wet-room kits are subsets or variants of this (wet room adds tanking/linings 3500xx, former/tray, level-access floor).
- Kitchen kit skeleton, taken from C, D and E: base/wall/tall units by width (300–1200mm), drawer pack, appliance housing; 38/40mm laminate worktop + upstand + end caps/joint strips; plinth, cornice/pelmet; handles; inset sink (1.0 or 1.5 bowl) + mixer tap + waste/trap; washing-machine valve and trap; cooker points (45A cooker switch, gas bayonet); sockets/switched spurs; extract fan or hood spur; lighting; wall tiles or splashback; vinyl; coving; decorating.

### Gaps
- No item list for a void property or full-house refurb was extracted; only the M3NHF voids SOR structure was seen.
- Quantities per job (e.g. m² of tile, number of units) were not found in any public priced BoQ. A typical-job quantity basis remains unknown.

## Q5. Licence and reuse (Contracts Finder, Find a Tender, OGL, Crown copyright, attachments)

### Takeaway
Contracts Finder and Find a Tender notice content is mostly Crown copyright under **OGL**. The terms state that "some content is exempt" and **do not address buyer-uploaded attachments**. Attachments written by councils, housing associations or consultants are generally **not Crown copyright** (council and HA documents are the authoring body's copyright). Third-party commercial content inside them, such as M3NHF SORs and manufacturer product data, carries its own copyright. M3NHF explicitly reserves all rights.

### Cited Findings
- Contracts Finder T&Cs: "Most content on Contracts Finder and Find a Tender is subject to Crown copyright protection and is published under the Open Government Licence (OGL)"; "Some content is exempt from the OGL"; "Departmental logos and crests are also exempt… except when they form an integral part of a document or dataset"; you may "reproduce content… under the OGL as long as you follow the licence's conditions"; where content is not Crown copyright or OGL "we'll usually credit the author or copyright holder". Buyer-uploaded attachments are not explicitly addressed — [Contracts Finder Terms](https://www.contractsfinder.service.gov.uk/Home/TermsAndConditions); equivalent page [Find a Tender Terms](https://www.find-tender.service.gov.uk/Home/TermsAndConditions)
- Contracts Finder data is catalogued as open data under OGL with some non-open exceptions — [Open Contracting data registry: Contracts Finder](https://data.open-contracting.org/en/publication/128)
- OGL grants the right to copy, publish, distribute, adapt and exploit commercially, subject to attribution and a link to the licence where possible (version 1 text cited; v3 is the current gov.uk version) — [OGL v1 (National Archives)](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/1/open-government-licence.htm). The DHS guidance page is marked "Open Government Licence v3.0" — [gov.uk](https://www.gov.uk/government/publications/a-decent-home-definition-and-guidance)
- M3NHF: "All rights reserved. No part of this publication may be reproduced… without the prior permission of M3 Housing Ltd." — **RESTRICTED/PAID** — [Sell2Wales doc 357559](https://www.sell2wales.gov.wales/Assets/NoticeBuilder_FileDownload.aspx?id=357559)

Per-source licence status:
| Source | Licence status |
|---|---|
| DHS guidance 2006 (gov.uk) | OGL v3.0, reusable with attribution |
| Contracts Finder / FTS notice text | Crown copyright, OGL (some exemptions) |
| CF/FTS/Sell2Wales buyer attachments | Not stated; copyright of the issuing body or consultant; quote with attribution only (fair dealing); not OGL by default |
| Sell2Wales 376193 bathroom spec | Not stated (issuer's copyright); not OGL by default |
| M3NHF SOR v8 extract | All rights reserved, M3 Housing Ltd: **restricted/paid** |
| Broadland HA spec (via North Norfolk DC) | Not stated; HA copyright |
| Ashford / Clackmannanshire leaflets | Not stated; council copyright (local-authority material is not Crown copyright) |

### Inferences
- For a product, use public documents to derive **generic item categories and attributes** (e.g. "WC pan, close-coupled, dual flush 4/2.6 or 4.5/3 L"). Do not copy SOR descriptions, rates or bespoke specs verbatim. Cite sources in internal research notes only. Brand and model references are factual and can be used as candidate SKUs, but they must be labelled as one buyer's specification, not a recommendation.
- Sell2Wales has its own terms (Welsh Government), which I did not check. The claim that its attachments are covered by OGL is unverified.

### Gaps
- I did not fetch the OGL v3 text itself or the Sell2Wales and Find a Tender terms pages first-hand (FTS terms only via search snippet).
- No authoritative statement was found on whether local-authority tender attachments fall under OGL. Some councils publish under OGL on their own sites, but that was not verified for these documents.

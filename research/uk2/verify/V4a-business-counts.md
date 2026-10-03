# V4a: independent recomputation of UK business-count and spend-pool claims

Verifier: independent of the original researcher. Date of work: 2026-10-03.
Method: I downloaded every official workbook myself (curl through the configured proxy, TLS verification on), parsed it with Python 3.11 + openpyxl (`data_only=True`, i.e. cached cell values), and recomputed each stated figure from the raw cells. I did not use the first researcher's parse.
Scratch area (outside the repo): `/tmp/claude-0/-home-user-ai-commerce-ideas/8a4ab967-aee2-5285-a889-9780b621444f/scratchpad/uk2/v4a/` (scripts `bpe_parse.py`, `ons_t4.py`, `abs_parse.py`, `compare.py`, `sut_parse.py`, `final_checks.py`; text dumps of every sheet with cell coordinates in `dump/`).
Budget used: 29 Bash tool calls (these contained 20 individual curl fetches, several run in parallel inside one call), plus 16 Read/Grep calls on the local text dumps. Counted per Bash call this is under the 40 limit; counted per individual curl plus per Bash call without curl it is close to the limit, so I am stating it plainly.

## Verdict counts

CONFIRMED 7 (V4a-1, 2, 3, 4, 5, 6, 8) | CONTRADICTED 0 | PARTLY 0 | UNVERIFIED 0 | V4a-7 is a new data pull (no verdict).
55 stated figures were recomputed; 0 mismatched.

---

## (a) Summary table

| ID | Verdict | One-line reason |
|---|---|---|
| V4a-1 | CONFIRMED | BPE-25 Table 1: B5 = 5,690,265; B6 = 1,417,730; B14:B16 = 38,435; B17:B19 = 8,335 (Table 24 and the DBT release text agree). |
| V4a-2 | CONFIRMED | BPE-25 Table 5 section C: B54 = 263,085; B61:B65 = 25,845; B66+B67 = 1,240 (also = sum of Table 6 divisions 10-33). |
| V4a-3 | CONFIRMED | ONS-26 Table 4: I621 = 2,786,985; SIC 10-33 rows 60-289 total 128,065; 10-249 = 11,360 + 8,450 + 3,775 + 2,115 = 25,700 (Table 3 route: 25,730, within rounding noise). |
| V4a-4 | CONFIRMED | All 15 stated numbers reproduce: ONS-26 33,075 (24,300 + 1,400 + 6,835 + 540) and BPE-25 32,875; no difference found. |
| V4a-5 | CONFIRMED | All 13 ABS 2024 values match the cells; release date 26 May 2026 confirmed; no repair/maintenance or spare-parts column exists in any ABS sheet. |
| V4a-6 | CONFIRMED | Construction Table 1.4: Q10 = 85,312; M10 = 42,655; N10+O10+P10 = 42,657; Q23+Q24+Q25 = 27,449; non-housing part = 13,753. |
| V4a-7 | NEW DATA (retrieved) | Blue Book 2025 SUT, year 2023: CPA 33 total supply GBP 33,675m; intermediate use GBP 30,737m (91.3%); manufacturing buys 28.2%, construction 0.7%, wholesale (G46) 2.3%, other 68.9%. |
| V4a-8 | CONFIRMED | All 8 figures reproduce; the ONS-26 vs BPE-25 gap decomposes into coverage (government + non-profit), timing (Jan 2025 vs Mar 2026), and a small residual (0.5% to 2.8% in the three target sectors). |

Strictness notes that apply across the ledger (not contradictions):
- BPE-25 and ONS-26 counts are controlled-rounded to base 5. Any figure built by summing many rounded cells carries noise. My estimate for the 33,075 base (936 rounded cells feed it): SD about 44 under a nearest-5 model, about 88 under a wider controlled-rounding model, so 95% noise of roughly +/-90 to +/-170 (0.3% to 0.5%). Quote the base as "about 33,000", not as an exact figure.
- ONS counts are **enterprises** (autonomous units), not enterprise groups, and the ONS band label is "Employment Size Band" while the ledger says "employees" (see V4a-3 and V4a-8).

---

## Source files (provenance)

| Short name | File | Bytes | md5 | Dating evidence |
|---|---|---|---|---|
| BPE-25 | `BPE_2025_detailed_tables.xlsx` | 634,622 | bbddff8a6a7659b48b78caa3155efb13 | Contents!A2 "Published 2nd October 2025"; reference "start 2025"; DBT; status "Official statistics in development" (Contents!A4) |
| ONS-26 | `ukbusinessworkbook2026.xlsx` | 1,055,829 | 86d273ee728a2e38222bccf109c98de8 | Contents!A4 "Date published: 24th September 2026"; bulletin: IDBR snapshot taken 13 March 2026 |
| ONS-25 (extra) | `ukbusinessworkbook2025new.xlsx` | 1,050,564 | aa19600fd9c06b98e05c151298d7688d | March 2025 edition; used only for like-for-like checks |
| ABS-24 | `abssectionsas.xlsx` | 1,055,873 | 056f2f31d660a6e67fdd2d4adb96ff0f | Cover Sheet!A5 "Release Date: 26 May 2026"; Contents!A1 "Annual Business Survey, 2024 Results"; dataset page "Release date: 26 May 2026" |
| CSA-24 | `csatablesaccessiblefinal2024.xlsx` | 155,033 | 3beec1150f9c159e0c2eff7e0090429f | Cover Sheet!B4 = 2026-02-19; coverage Great Britain; "Construction Statistics Great Britain: 2024" |
| SUT | `supublicationtablesbb25.xlsx` | 3,037,546 | 5d25b4b2c96471cad5efdb974e9895eb | Contents!B4 "consistent with UK National Accounts 2025 Blue Book", C4 "October 2025"; dataset page release date 31 October 2025; years 1997-2023 |

Other pages fetched (text only): DBT BPE statistical release (HTML), BPE methodology note (HTML), ONS UK business 2026 bulletin and QMI (HTML), ONS dataset landing pages (ABS, construction, SUT, UK business), ONS "Construction statistics, Great Britain: 2024" article, GOV.UK BPE collection page.

---

## (b) Per-claim detail

### V4a-1 BPE-25 headline counts: CONFIRMED

Sheet `Table 1` ("UK private sector ... by number of employees, UK, start 2025"). Header row 4 (A4 "Employee size band", B4 "Business number", C4 employment, D4 employees, E4 working proprietors, F4 turnover). Data rows 5-19.

| Cell | Label | Value |
|---|---|---|
| B5 | All businesses | 5,690,265 |
| B6 | All employers | 1,417,730 |
| B14 / B15 / B16 | 50 to 99 / 100 to 199 / 200 to 249 | 26,020 / 10,205 / 2,210 |
| B17 / B18 / B19 | 250 to 499 / 500 to 999 / 1000 or more | 4,290 / 2,075 / 1,970 |

```python
ws = openpyxl.load_workbook("BPE_2025_detailed_tables.xlsx", data_only=True)["Table 1"]
ws["B5"].value, ws["B6"].value                          # 5690265, 1417730
sum(ws[f"B{r}"].value for r in (14, 15, 16))            # 38435  (medium, 50-249)
sum(ws[f"B{r}"].value for r in (17, 18, 19))            # 8335   (large, 250+)
```

Second route, `Table 24` ("broad size band"), header row 6: B7 = 5,690,265; B11 (All employers) = 1,417,730; B14 ("50 to 249 employees") = 38,435; B15 ("250 or more employees") = 8,335.
Release text (DBT statistical release, "Headline statistics"): "5.7 million" private sector businesses; "38,435 businesses were medium-sized (50 to 249 employees)"; "8,335 ... large"; "1.4 million (25%) businesses had employees".
Caveats (not corrections): of the 5.69m, 3,044,940 are "unregistered" (Table 1 B7) and are model-based estimates; the release gives a 95% CI of +/-123,000 on the total. The 1.4177m employers and the 38,435 / 8,335 medium/large counts are register-based (IDBR), so they carry no sampling error. The totals are not multiples of 5 (unrounded) while the sub-cells are; here parts add exactly.

### V4a-2 BPE-25 manufacturing: CONFIRMED

Sheet `Table 5` ("UK sections", header row 7: A7 "Employee size band", B7 "Business number"). Section header A53 = "C Manufacturing" (B53 blank), data B54:B67.

| Cell | Band | Value |
|---|---|---|
| B54 | All businesses | 263,085 |
| B61 / B62 / B63 / B64 / B65 | 10-19 / 20-49 / 50-99 / 100-199 / 200-249 | 11,265 / 8,615 / 3,770 / 1,795 / 400 |
| B66 / B67 | 250 to 499 / 500 or more | 690 / 550 |

```python
ws = wb["Table 5"]
ws["B54"].value                                          # 263085
sum(ws[f"B{r}"].value for r in range(61, 66))            # 25845
ws["B66"].value + ws["B67"].value                         # 1240
```

Cross-checks: (i) sum over Table 6 divisions 10-33 of their five 10-249 band cells = 25,845 (table under V4a-4); band-by-band the division sums differ from Table 5 section C by up to 10 (20-49: 8,625 vs 8,615; 50-99: 3,765 vs 3,770; 200-249: 395 vs 400), which is rounding, and the 10-249 total is identical. (ii) DBT release text: "the sector with the most large businesses was Manufacturing (1,240)".

### V4a-3 ONS-26 Table 4 totals and manufacturing: CONFIRMED

Sheet `Table 4` ("... enterprises by SIC class by employment sizebands"). A3 "Units: Counts (control rounded to base 5)"; B4 "Employment Size Band"; header B5:I5 = 0-4, 5-9, 10-19, 20-49, 50-99, 100-249, 250+, Total; class rows 6-620 ("0111 : ..." to "9900 : ..."), Total row 621.

| Cell | Value |
|---|---|
| I621 (Total, all bands) | 2,786,985 |
| B621..H621 | 2,179,250 / 305,115 / 160,610 / 85,675 / 30,150 / 14,725 / 11,460 |
| Rows 60-289 (all classes of SIC divisions 10-33), column I | 128,065 |
| same rows, D / E / F / G | 11,360 / 8,450 / 3,775 / 2,115 |

```python
ws = wb["Table 4"]
ws["I621"].value                                                           # 2786985
sum(ws.cell(r, 9).value for r in range(60, 290))                           # 128065
[sum(ws.cell(r, c).value for r in range(60, 290)) for c in (4, 5, 6, 7)]   # [11360, 8450, 3775, 2115]
```
Sum of the four = 25,700. The class rows add exactly to the Total row in every band (difference 0), so the table is internally additive.

Cross-checks: ONS bulletin text "2.79 million ... VAT and/or PAYE businesses in the UK as of March 2026, an increase of 1.9% from March 2025"; bulletin Table 5 total 2,786,985; bulletin Table 3 "Manufacturing 128" (thousand). Independent route inside the workbook, `Table 3` (division x band, UK block B:I, rows 6-93, Total row 94): manufacturing 10-249 = 25,730, i.e. 30 (0.12%) above the Table 4 figure; this is rounding noise (Table 3 is rounded separately). The claimed 25,700 is the Table 4 value, which stands.
Label caveat: the sheet calls the bands "Employment Size Band" (B4); the ledger says "10-249 employees". See V4a-8 on whether that distinction matters.

### V4a-4 "Reachable base": CONFIRMED (no difference found)

ONS-26 `Table 4`, columns D:G (10-19, 20-49, 50-99, 100-249):

| Component | Rows | 10-19 | 20-49 | 50-99 | 100-249 | 10-249 |
|---|---|---|---|---|---|---|
| Divisions 10-32 | 60-280 | 10,540 | 8,080 | 3,645 | 2,035 | 24,300 |
| of which divisions 10-11 | 60-91 | 1,420 | 995 | 465 | 310 | 3,190 |
| of which divisions 12-32 | 92-280 | 9,120 | 7,085 | 3,180 | 1,725 | 21,110 |
| Division 33 | 281-289 | 820 | 370 | 130 | 80 | 1,400 |
| 4321 Electrical installation | 319 | 2,135 | 990 | 235 | 95 | 3,455 |
| 4322 Plumbing, heat and air-conditioning installation | 320 | 1,500 | 770 | 175 | 75 | 2,520 |
| 4329 Other construction installation | 321 | 525 | 250 | 55 | 30 | 860 |
| 8110 Combined facilities support | 539 | 265 | 150 | 75 | 50 | 540 |
| **Base total** | | **15,785** | **10,610** | **4,315** | **2,365** | **33,075** |

Claimed values all match: 33,075; 24,300; 21,110; 3,190; 1,400; 3,455; 2,520; 860; 6,835 (= 3,455 + 2,520 + 860); 540; band totals 15,785 / 10,610 / 4,315 / 2,365.

```python
mid = ("10-19", "20-49", "50-99", "100-249")
agg = lambda codes: sum(classes[c][b] for c in codes for b in mid)   # classes[code][band] parsed from Table 4 rows 6-620
agg([c for c in classes if 10 <= int(c[:2]) <= 32])                  # 24300
agg([c for c in classes if int(c[:2]) == 33])                        # 1400
agg(["4321", "4322", "4329"])                                        # 6835
agg([c for c in classes if 10 <= int(c[:2]) <= 33] + ["4321", "4322", "4329", "8110"])   # 33075
```
Per division (BPE-25 Table 6 cells vs ONS-26 Table 4 rows), 10-249 enterprises:

| Div | BPE-25 Table 6 cells (col B) | BPE | ONS-26 rows | ONS-26 |
|---|---|---|---|---|
| 10 | B151:B155 | 2,585 | 60-84 | 2,690 |
| 11 | B166:B170 | 495 | 85-91 | 500 |
| 12 | B181:B185 | 0 | 92 | 0 |
| 13 | B196:B200 | 830 | 93-102 | 825 |
| 14 | B211:B215 | 400 | 103-110 | 395 |
| 15 | B226:B230 | 90 | 111-113 | 95 |
| 16 | B241:B245 | 1,250 | 114-119 | 1,245 |
| 17 | B256:B260 | 515 | 120-126 | 500 |
| 18 | B271:B275 | 1,185 | 127-131 | 1,140 |
| 19 | B286:B290 | 30 | 132-133 | 30 |
| 20 | B301:B305 | 885 | 134-149 | 905 |
| 21 | B316:B320 | 150 | 150-151 | 140 |
| 22 | B331:B335 | 1,870 | 152-157 | 1,850 |
| 23 | B346:B350 | 965 | 158-181 | 945 |
| 24 | B361:B365 | 520 | 182-197 | 490 |
| 25 | B376:B380 | 5,185 | 198-214 | 5,115 |
| 26 | B391:B395 | 1,315 | 215-224 | 1,290 |
| 27 | B406:B410 | 965 | 225-234 | 950 |
| 28 | B421:B425 | 1,965 | 235-255 | 1,935 |
| 29 | B436:B440 | 655 | 256-259 | 625 |
| 30 | B451:B455 | 290 | 260-267 | 285 |
| 31 | B466:B470 | 1,200 | 268-271 | 1,200 |
| 32 | B481:B485 | 1,120 | 272-280 | 1,150 |
| 33 | B496:B500 | 1,380 | 281-289 | 1,400 |
| 10-32 | | 24,465 | | 24,300 |
| 10-33 | | 25,845 | | 25,700 |

BPE-25 equivalent (claimed 32,875), header rows: Table 6 row 7; Table 7 row 8 (employers only, broad bands "Micro / Small (10 to 49) / Medium (50 to 249) / Large").
- Divisions 10-32 from Table 6: 24,465 (cells above).
- Division 33 from Table 6: 1,380. Cross-check via Table 7 groups 331 (B714 + B715 = 950 + 155 = 1,105) and 332 (B720 + B721 = 220 + 55 = 275) = 1,380.
- Group 432 (Table 7): Small B816 = 5,905; Medium B817 = 635; total 6,540. Group 432 is exactly SIC 43.21 + 43.22 + 43.29.
- Group 811 (Table 7): Small B1410 = 355; Medium B1411 = 135; total 490. Group 811 is exactly class 8110.
- Total = 24,465 + 1,380 + 6,540 + 490 = **32,875**. Matches the claim.

ONS-26 vs BPE-25 on the same base: Small (10-49) 26,395 vs 26,150 (+245, +0.9%); Medium (50-249) 6,680 vs 6,725 (-45, -0.7%); total +200 (+0.6%). Component differences: divisions 10-32 -165; 33 +20; 432 +295; 811 +50. See (c) for the March 2025 edition, which shows the same base at 33,055.

### V4a-5 ABS-24: CONFIRMED

Sheet structure (all data sheets): row 7 = column names, row 8 = units, data from row 9, one row per SIC code per year 2008-2024 (2024 is the last of 17 rows). Columns: D "Number of enterprises" (number), E "Total turnover" (GBP m), F aGVA, G "Total purchases of goods, materials and services" (GBP m), H employment costs, I/J capex acquisitions/disposals, K/L stocks at end/beginning of year. No other columns.

| Item | Sheet | Row | Cells | Value (matches claim) |
|---|---|---|---|---|
| SIC 46.69 | Division 46 | 807 | D807 / E807 | 6,989 enterprises / GBP 43,871m |
| SIC 46.74 | Division 46 | 892 | D892 / E892 | 3,515 / GBP 18,625m |
| SIC 33 | Section C | 5006 | E5006 | GBP 21,338m |
| SIC 33.12 | Section C | 5057 | E5057 | GBP 5,445m |
| SIC 33.11 | Section C | 5040 | E5040 | GBP 1,133m |
| SIC 43.2 | Section F | 365 | E365 / G365 | GBP 68,180m turnover / GBP 36,204m purchases |
| SIC 81.1 | Section N | 552 | E552 / G552 | GBP 18,519m / GBP 9,705m |
| Section C Manufacturing | Section C (also Sections A to S row 93) | 25 | E25 / G25 | GBP 685,359m / GBP 467,832m |

```python
ws = wb["Section F"]
[r for r in range(9, ws.max_row + 1) if ws.cell(r, 1).value == "43.2" and ws.cell(r, 3).value == 2024]   # [365]
ws.cell(365, 5).value, ws.cell(365, 7).value                                                          # 68180, 36204
```
"ABS has no repair-and-maintenance or spare-parts column": confirmed. Columns B to L carry identical headers in all 21 data sheets (checked programmatically; only the column-A label differs, "Section" on the Sections A to S sheet versus "Section letter / Division / Group / Class" on the others). The only occurrences of "repair" in the header areas (rows 1-8) are the titles of Section G and Division 45 (motor vehicle repair).
Internal arithmetic checks: 33 = 33.1 (16,644) + 33.2 (4,694) = 21,338; 43.2 = 34,310 + 24,032 + 9,838 = 68,180; purchases 43.21 + 43.22 + 43.29 = 36,203 vs 36,204 (rounding in source); 33.11 to 33.19 sum to 16,642 vs 16,644 for 33.1.
Not rounded to base 5 (integers in GBP m / counts), but divisions 11 and 12 are suppressed as "[c]" in Section C, so the 24 division rows sum to only 653,035 (not 685,359); the 32,324 gap is the suppressed divisions.
Caveat for use: G ("purchases") is each industry's own cost of goods, materials and services, not its customers' repair spend.

### V4a-6 ONS construction statistics: CONFIRMED

Workbook `csatablesaccessiblefinal2024.xlsx`, sheet `Table 1.4` ("Construction firms: Value of work done by trade of firm and type of work in 2024: Great Britain, Current Prices"), unit "GBP million" (A5), header row 6 (A6:R6; K "Public housing R&M", L "Private housing R&M", M "Total housing R&M", N "Infrastructure R&M", O "Public other work R&M", P "Private other work R&M", Q "All R&M", R "All work").

| Cell | Row label | Value |
|---|---|---|
| Q10 | Total main trades (Section F) | 85,312 (All R&M) |
| M10 | same row, Total housing R&M | 42,655 |
| N10 / O10 / P10 | same row | 13,167 / 7,388 / 22,102 (sum 42,657) |
| Q23 / Q24 / Q25 | 43210 Electrical installation / 43220 Plumbing, heat and air-conditioning / 43290 Other construction installation | 11,427 / 12,240 / 3,782 (sum 27,449) |
| M23 / M24 / M25 | housing R&M of those trades | 4,028 / 8,083 / 1,585 |

```python
ws = wb["Table 1.4"]
ws["Q10"].value                                                                  # 85312
ws["M10"].value                                                                  # 42655
ws["N10"].value + ws["O10"].value + ws["P10"].value                              # 42657 (= Q10 - M10)
sum(ws[f"Q{r}"].value for r in (23, 24, 25))                                     # 27449
sum(ws[f"Q{r}"].value - ws[f"M{r}"].value for r in (23, 24, 25))                 # 7399 + 4157 + 2197 = 13753
```
Row 35 ("All trades") repeats row 10. "Non-housing" is derived (Q minus M), not a published column. Internal checks: J10 (All new work 140,676) + Q10 = R10 (225,988); Table 1.5 "All Trades" total Z12 = 225,986 (2 lower: rounding); Tables 1.1 (O34 = 41,124) + 1.2 (P33 = 99,561) = 140,685 vs Table 1.3 U33 = 140,684 (new work).
Second publication: the ONS article "Construction statistics, Great Britain: 2024" (released 19 February 2026) was fetched; its text does not restate the GBP R&M totals, so the cross-check is internal to the workbook only.
Scope caveat: Note 1 says the tables cover "output from businesses classified to construction" (SIC 41-43). This is value of work by construction firms (labour + materials + margin, housing and non-housing, all firm sizes), not parts spend and not R&M done by non-construction firms or in-house.

### V4a-7 ONS Supply and Use tables: NEW DATA

What this is: `supublicationtablesbb25.xlsx`, "Supply and Use Tables, 1997 - 2023 (consistent with UK National Accounts 2025 Blue Book)", October 2025 (dataset release date 31 October 2025). This is the latest available as at 3 October 2026: the dataset page shows it as the current edition and "Next release: To be announced", so Blue Book 2026 data are not yet published. Latest data year = **2023**, GBP million, current prices.
Is it product-by-industry? Partly. `Table 2 - Int Con 2023` is a product x industry matrix (104 CPA-based product rows 6-109 x 104 SIC-based industry columns C:DB, plus DC "Total intermediate demand"), valued at purchasers' prices (row 110 label "Total intermediate consumption at purchasers' prices"). `Table 1 - Supply 2023` is by product only (no industry columns), and `Table 2 - Final Demand 2023` is product x final-demand category. There is no size dimension anywhere.
CPA 33 appears as three product rows: `CPA_C3315` Repair and maintenance of ships and boats; `CPA_C3316` Repair and maintenance of aircraft and spacecraft; `CPA_C33OTHER` "Rest of repair; Installation - 33.11-14/17/19/20". Rows: supply sheet 50-52; intermediate-consumption and final-demand sheets 52-54. CPA 33 below = the sum of the three.

Supply (`Table 1 - Supply 2023`, header row 3, rows 50-52):

| Item | Cells | C3315 | C3316 | C33OTHER | CPA 33 total |
|---|---|---|---|---|---|
| Domestic output at basic prices | C50:C52 | 1,080 | 3,822 | 25,918 | 30,820 |
| Imports of services | G50:G52 | 172 | 1,860 | 492 | 2,524 |
| Taxes less subsidies on products | J50:J52 | 31 | 20 | 280 | 331 |
| **Total supply at purchasers' prices** | K50:K52 | 1,283 | 5,702 | 26,690 | **33,675** |

(Imports of goods and distributors' margins are 0 for all three rows.)

Use side (2023): intermediate demand DC52:DC54 = 926 + 3,949 + 25,862 = 30,737 (91.3% of supply). Final demand (`Table 2 - Final Demand 2023`, header rows 4-5): households C52:C54 = 260 + 178 + 0 = 438 (1.3% of supply); exports of services R52:R54 = 97 + 1,575 + 828 = 2,500 (7.4%); total final demand T52:T54 = 357 + 1,753 + 828 = 2,938; gross fixed capital formation, inventories, NPISH and government are all 0. Check: intermediate + final = supply for each row (926 + 357 = 1,283; 3,949 + 1,753 = 5,702; 25,862 + 828 = 26,690).

Intermediate consumption by buying industry (rows 52-54, GBP m):

| Buyer aggregate | Columns | C3315 | C3316 | C33OTHER | CPA 33 total | Share of intermediate use |
|---|---|---|---|---|---|---|
| Manufacturing (all C industries, incl. the C33 industries themselves) | J:AY | 97 | 986 | 7,572 | 8,655 | 28.2% |
| Construction (F41-43) | BF | 0 | 0 | 215 | 215 | 0.7% |
| Wholesale (G46) | BH | 0 | 0 | 694 | 694 | 2.3% |
| Other (everything else) | rest | 829 | 2,963 | 15,661 + 372 (G45) + 1,348 (G47) = 17,381 | 21,173 | 68.9% |
| Total | DC | 926 | 3,949 | 25,862 | 30,737 | 100% |

Detail inside "other": motor trades G45 372 (1.2%); retail G47 1,348 (4.4%); so wholesale + retail + motor trades together = 2,414 (7.9%). Households 438 (1.3% of total supply) and exports 2,500 (7.4%) are the only final-demand uses.
Largest single buyers of the three CPA 33 rows combined: H51 Air transport 2,965 (9.6%); D351 Electricity 2,879 (9.4%); the C33OTHER industry itself 1,395 (4.5%); J61 Telecommunications 1,349 (4.4%); G47 Retail 1,348 (4.4%); C29 Motor vehicles 1,155 (3.8%); D352_3 Gas 1,132 (3.7%); N77 Rental and leasing 954 (3.1%); C303 Air and spacecraft 910 (3.0%); H491_2 Rail 870 (2.8%); Q86 Human health 830 (2.7%).
Largest buyers of the machinery-repair row alone (`CPA_C33OTHER`, row 54, total 25,862): D351 Electricity 2,879 (11.1%); C33OTHER itself 1,390 (5.4%); J61 1,349 (5.2%); G47 1,348 (5.2%); C29 1,155 (4.5%); D352_3 Gas 1,132 (4.4%); N77 954 (3.7%); H491_2 Rail 870 (3.4%); Q86 830 (3.2%); I56 Food and beverage service 743 (2.9%); H52 Transport support 742 (2.9%); G46 694 (2.7%). All of D (energy supply) = 4,011 (15.5%).

CPA 33 over time (total supply at purchasers' prices, GBP m): 2019 28,841; 2020 25,943; 2021 26,967; 2022 31,729; 2023 33,675 (+6.1% in 2023; +24.9% over 2021-2023, current prices). Manufacturing share of intermediate use: 31.3% (2019), 30.3%, 30.7%, 28.9%, 28.2% (2023). Construction share stays below 1% in every year.

```python
wb = openpyxl.load_workbook("supublicationtablesbb25.xlsx", data_only=True)
sup, ic, fd = wb["Table 1 - Supply 2023"], wb["Table 2 - Int Con 2023"], wb["Table 2 - Final Demand 2023"]
sum(sup[f"K{r}"].value for r in (50, 51, 52))                                  # 33675
sum(ic[f"DC{r}"].value for r in (52, 53, 54))                                  # 30737
sum(ic.cell(r, c).value or 0 for r in (52, 53, 54) for c in range(10, 52))     # J..AY manufacturing = 8655
sum(ic[f"BF{r}"].value for r in (52, 53, 54))                                  # construction = 215
sum(ic[f"BH{r}"].value for r in (52, 53, 54))                                  # G46 wholesale = 694
sum(fd[f"C{r}"].value for r in (52, 53, 54)), sum(fd[f"R{r}"].value for r in (52, 53, 54))   # 438, 2500
```
One correction to a parsing step of mine: my first multi-year check read the DC column header with the wrong string (the header contains line breaks), so it returned 0; I confirmed DC52:DC54 directly (926, 3,949, 25,862) and they equal the sum of the C:DB industry cells.

### V4a-8 BPE-25 vs ONS-26 sanity checks: CONFIRMED (all 8 figures), with explanation

Recomputed at 10-249:

| Aggregate | BPE-25 (cells) | ONS-26 (cells) | ONS-26 minus BPE-25 |
|---|---|---|---|
| Manufacturing | 25,845 (Table 5 B61:B65) | 25,700 (Table 4 rows 60-289, D:G) | -145 |
| Construction | 19,635 (Table 5 B76:B80 = 12,145 + 5,410 + 1,450 + 515 + 115) | 20,165 (divisions 41-43) | +530 |
| Division 81 | 5,635 (Table 6 B1096:B1100 = 3,180 + 1,535 + 600 + 250 + 70) | 6,005 (classes 8110, 8121, 8122, 8129, 8130; rows 539-543: 540 + 3,045 + 445 + 780 + 1,195) | +370 |
| All industries | 258,520 (Table 1 B12:B16) | 291,160 (Table 4 D621:G621) | +32,640 |

Table 3 route (ONS-26): construction 20,140; division 81 6,000; all industries 291,160 (identical); manufacturing 25,730.

Section-level comparison at 10-249 (BPE-25 private sector, Table 5; ONS-25 = March 2025 edition; ONS-26 = March 2026 edition; ONS divisions mapped to sections):

| Section | BPE-25 | ONS-25 | ONS-26 | ONS-26 - BPE | ONS-25 - BPE | ONS-26 - ONS-25 |
|---|---|---|---|---|---|---|
| A Agriculture | 4,275 | 5,145 | 5,195 | 920 | 870 | 50 |
| B + D + E | 2,410 | 2,450 | 2,455 | 45 | 40 | 5 |
| C Manufacturing | 25,845 | 25,985 | 25,700 | -145 | 140 | -285 |
| F Construction | 19,635 | 19,835 | 20,165 | 530 | 200 | 330 |
| G Wholesale/retail | 42,390 | 43,565 | 44,600 | 2,210 | 1,175 | 1,035 |
| H Transport | 8,610 | 8,890 | 9,075 | 465 | 280 | 185 |
| I Accommodation/food | 38,840 | 41,125 | 43,430 | 4,590 | 2,285 | 2,305 |
| J Information | 13,790 | 13,935 | 13,995 | 205 | 145 | 60 |
| K Finance | 4,205 | 4,445 | 4,425 | 220 | 240 | -20 |
| L Real estate | 5,890 | 6,400 | 6,785 | 895 | 510 | 385 |
| M Professional | 28,140 | 29,320 | 29,830 | 1,690 | 1,180 | 510 |
| N Admin/support | 22,385 | 23,115 | 23,070 | 685 | 730 | -45 |
| O Public administration | not in BPE private | 435 | 455 | 455 | 435 | 20 |
| P Education | 5,395 | 10,355 | 10,260 | 4,865 | 4,960 | -95 |
| Q Health/social | 25,220 | 32,800 | 33,435 | 8,215 | 7,580 | 635 |
| R Arts/recreation | 5,835 | 8,885 | 9,355 | 3,520 | 3,050 | 470 |
| S Other services | 5,655 | 8,670 | 8,925 | 3,270 | 3,015 | 255 |
| T + U | 0 | 0 | 5 | 5 | 0 | 5 |
| **All industries** | **258,520** | **285,355** | **291,160** | **32,640** | **26,835** | **5,805** |

Explanation, from the methodological text of both releases:
1. Coverage (largest effect for the all-industries gap). BPE "private sector" "excludes central and local government, charities and other non-profit organisations, which are shown in Table 2 of the publication only" (BPE methodology note). ONS-26 counts every VAT and/or PAYE enterprise, including government and non-profit (ONS bulletin Table 1, March 2026: central government 3,205; local authority 9,260; the same table shows non-profit bodies at 88,740 in 2024, and I did not extract the 2026 non-profit figure). BPE Table 2 gives the like-for-like pieces at 10-249: whole economy 279,515 (B14:B18), private 258,520 (B27:B31), central and local government 3,125 (B40:B44), non-profit 17,875 (B53:B57; block header A48). So coverage explains 20,995 of the 32,640. Sections P, Q, R, S and O together account for 20,325 of the section differences.
2. Timing. BPE-25 is "based on an IDBR extract referencing the start of January" 2025 (BPE methodology note). ONS-26 is a snapshot of the IDBR taken on 13 March 2026 (ONS bulletin); the QMI says the extract is "taken annually in March". ONS-26 is therefore about 14 months later than BPE-25. ONS-25 to ONS-26 adds +5,805 (2.0%) at 10-249 overall.
3. Residual after 1 and 2: ONS-25 (March 2025) minus BPE whole economy = 285,355 - 279,515 = +5,840 (2.1%). 20,995 + 5,840 + 5,805 = 32,640, so the decomposition closes exactly.
4. Target sectors, like-for-like (ONS-25 vs BPE-25): manufacturing +140 (+0.5%), construction +200 (+1.0%), division 81 +155 (+2.8%). The gaps in the ledger are therefore mostly timing: manufacturing fell 285 (-1.1%) between the two ONS snapshots, which flips the sign of the gap (-145); construction rose 330 and division 81 rose 215 in the same year.
5. Hypotheses not provable from the files: (a) Size basis. BPE sizes by "the number of employees" (BPE methodology: "Size of business ... the number of employees"; Contents!B54 "Employees: ... excluding owners and partners"); ONS labels its bands "Employment Size Band" and ONS Notes!B8 (Note 5) says employment comes mainly from BRES, PAYE jobs, or is imputed from VAT turnover for the smallest units. If ONS employment includes working proprietors (the ONS files I read do not say so explicitly), a firm with 9 employees plus 1 owner lands in 10-19 in ONS but 5-9 in BPE. The pattern is consistent with that: ONS-25 minus BPE is largest in proprietor-heavy sectors (A +20%, L +8.7%, I +5.9%, M +4.2%) and smallest in company-dominated manufacturing (+0.5%). (b) BPE moves companies with a single PAYE employee into "no employees" (BPE notes sheet C7); this affects only the lowest bands. (c) ONS Notes!B11 (Note 8): in late 2025 ONS began coding SIC with ClassifAI, "93% agreement" with the old tool "at the five-digit industry level", so some detailed-industry movements between ONS-25 and ONS-26 may be recoding rather than change.

---

## (c) NEW facts that matter (all unreviewed)

1. [unreviewed] The reachable base is stable across three independent snapshots: BPE-25 (start Jan 2025) 32,875; ONS-25 (Mar 2025) 33,055; ONS-26 (Mar 2026) 33,075. Spread 0.6%, which is inside rounding plus timing noise. ONS-25 vs ONS-26 components: divisions 10-32 24,590 to 24,300 (-290, -1.2%); division 33 1,395 to 1,400; 4321 3,315 to 3,455; 4322 2,425 to 2,520; 4329 825 to 860 (the three installation classes together 6,565 to 6,835, +270, +4.1%); 8110 505 to 540 (+35, +6.9%). Net +20, but the composition is shifting (manufacturing down, installation trades up); part of the class-level movement may be ClassifAI recoding.
2. [unreviewed] The base is 11.4% of all UK enterprises at 10-249 (33,075 of 291,160), and 47.7% of it is in the 10-19 band (15,785).
3. [unreviewed] Counts are enterprises, not enterprise groups (ONS Notes!B4, Note 1: a group of legal units under common ownership is an Enterprise Group; an enterprise has "a certain degree of autonomy"). A 100-employee subsidiary of a large group can count as a separate 10-249 enterprise, so the number of independent SME buyers is lower than 33,075. I could not quantify this from these files.
4. [unreviewed] Division 12 (tobacco) has 0 enterprises at 10-249 in both sources and division 19 only 30; the base also includes divisions 10-11 (food and drink, 3,190). That is a scoping choice, not a counting error.
5. [unreviewed] BPE 2026 had not appeared as at the fetch: the GOV.UK BPE collection page lists "Business population estimates 2025, 2 October 2025" as the latest, and the guessed 2026 URL returned 404. Previous releases on the collection page: 3 Oct 2024, 5 Oct 2023, 6 Oct 2022, 7 Oct 2021, so a release in the first days of October is the usual pattern and V4a-1, 2, 4 and 8 should be re-run when it lands. ONS-26 (24 September 2026) is current.
6. [unreviewed] SUT (CPA 33, 2023): the buyers are dominated by large asset-heavy sectors (electricity and gas, air transport, telecoms, rail, health, retail, vehicle manufacturers). Construction buys only 0.7%. Because there is no size dimension, the SUT cannot size the 10-249 buyers' share of the GBP 30.7bn intermediate use. Building-services trades (SIC 43.2x) sit in a different product, `CPA_F41, F42 & F43` ("Construction", supply GBP 437,272m, of which 55% is gross fixed capital formation), not in CPA 33.
7. [unreviewed] SUT neighbouring products, 2023 (GBP m, supply at purchasers' prices; intermediate use; share of intermediate use bought by manufacturing / construction): C25 Fabricated metal products 70,478; 44,402 (63.0% of supply); 50% / 27%. C27 Electrical equipment 66,659; 22,327 (33.5%); 28% / 42%. C28 Machinery and equipment n.e.c. 111,637; 40,968 (36.7%); 48% / 16%. These include production inputs, not only maintenance parts, so they are not an MRO-parts spend figure.
8. [unreviewed] ABS SIC 33 turnover (2024) GBP 21.3bn versus SUT CPA 33 domestic output (2023) GBP 30.8bn: industry and product bases differ (secondary production by other industries, year, coverage). Do not add or equate them.
9. [unreviewed] ABS enterprise counts differ from IDBR class totals in ONS-26: SIC 33 14,981 vs 15,590 (-3.9%); 43.2 108,556 vs 112,540 (-3.5%); 81.1 4,432 vs 4,690 (-5.5%); 46.69 6,989 vs 6,910 (+1.1%); 46.74 3,515 vs 3,495 (+0.6%). Use one source consistently when pairing counts with turnover.
10. [unreviewed] Construction Table 1.5 gives value of work by firm size (number employed; bands 0-4, 5-9, 10-19, 20-99, 100+) for the three installation trades, but only for all work (new + R&M), not R&M alone. For 43.21 + 43.22 + 43.29 (N:P columns): 10-19 = 7,936; 20-99 = 14,602; total 52,408; so firms with 10-99 employed do 43.0% of the work value. This cannot be turned into an R&M share for 10-249 firms; the bands also do not align with 10-249.
11. [unreviewed] BPE-25 status is "Official statistics in development" (Contents!A4), reflecting the Labour Force Survey base for unregistered-business estimates. This does not affect employer counts at 10-249, which come from the register.

## (d) What I could not access or establish

- A second, independent publication for the ABS figures: the guessed ABS bulletin URL returned 404, and the dataset landing page only confirms the release date (26 May 2026), with no provisional/revised wording. Verification of V4a-5 is therefore the workbook plus its internal arithmetic.
- A second publication for the construction R&M totals: the ONS article does not restate them; checks are internal to the workbook (Tables 1.1 to 1.5).
- Whether ONS "employment size band" includes working proprietors: neither the ONS-26 workbook notes, the bulletin, nor the QMI text I read states it (the QMI uses both "employee size band" and "employment size band"). I can say only that the size basis is a candidate explanation.
- The exact snapshot month of the BPE IDBR extract beyond "start of January" (from the methodology note); and any BPE vs ONS reconciliation published by DBT or ONS (none found).
- BPE Table 7 (groups) is employers only with broad bands, so groups 432 and 811 cannot be split into 10-19 and 20-49.
- SUT: no supply (make) matrix by industry and no basic-price use matrix in this workbook; CPA 33 exists only as three product rows; no size or MRO-versus-production split exists in any supply-use table.
- Blue Book 2026 (due late October 2026) and BPE 2026 are not yet available.
- Failures and false starts, stated plainly: one script run failed (TypeError from the "[c]" suppression marker in ABS Section C) and was fixed and rerun; three guessed URLs returned 404 (BPE methodology first guess, ABS bulletin, BPE 2026 page); the first multi-year SUT column check returned 0 for the DC column because of a header-string mismatch and was confirmed directly afterwards.

# Quote a job

Use **Quote a job** when you need a whole materials list for a piece of work, not one part. You pick the job, answer a few questions, check the list, and see what it would cost from the price files you have. Then you can ask suppliers for the prices you are missing.

The five stages run along the top of every screen in this area. Select a stage to jump to it, or use the buttons at the bottom of each screen.

**Job → Prices → Quote → Compare → Ask suppliers**

| Stage | The question it answers |
|---|---|
| **Job** | What's the job? |
| **Prices** | Who has prices? |
| **Quote** | What will it cost? |
| **Compare** | Best way to buy |
| **Ask suppliers** | Send quote requests |

> **What you see is an estimate, not a supplier quote.** It adds up prices that were *observed* in your price files, at the times shown. It is not an offer that a supplier can be held to, and it does not reserve stock. Nothing is sent or ordered. Under the total, the screen says **Not a supplier quote**.
>
> The job lists in the demo build are a **synthetic, illustrative seed that a tradesperson has not reviewed**, and the screen says so at the top of every Job step. Check every line before ordering.

## Stage 1: Job

![Choosing the job](img/16-job-scopes.png)

Pick the closest job. In the demo data these are *Cloakroom refit (WC and basin)*, *Full bathroom refit (bath, basin, WC, shower)*, *WC replacement* and *Wet room / level-access shower conversion*. Each card says how many questions it will ask and how many lines the template has. **Reuse an earlier quote** lists templates you saved before and one built-in example for each job. The examples are marked *Built-in example*, are named *Example former quote (synthetic): premium finish*, and set the finish to Premium. The number next to the heading counts them too, so it reads *4 saved* before you have saved anything. **Use for ...** loads a template and takes you to **Measure** (or to **Review** for a job with no **Measure** step).

The wizard has five steps, shown as *Step N of 5* under the stage tracker: **Job → Questions → Measure → Review → Summary**. *WC replacement* has no room sizes to enter, so it skips **Measure** and has four steps (*Step N of 4*).

### Questions

![The three questions](img/17-job-questions.png)

The wizard asks the few questions that change the list the most (three for each job in the demo data). Each question shows **Why we ask now** and a badge such as *Affects up to 19 lines*. The template's own answer is already selected, and card questions also mark it *Template default*. Some questions offer a *Don't know* choice (the WC replacement's pan question calls it *Not sure*). On card questions the screen then says what it will assume, for example *We will assume: Tank in the loft (gravity). Confirm on site.* Each assumption is listed again on **Review** and on the summary.

The **Finish level** question sets the budget, standard or premium option on every line at once. The cloakroom and the full bathroom ask it up front. For the other two jobs, use the **Finish** control on **Review**. You can still change any line later. The wizard does not pre-select a premium option by itself (a template you reuse can carry one, and the built-in examples do), and paid extras stay off at every level.

### Measure

![Measuring the room](img/18-job-measure.png)

Enter the room sizes (inside wall to wall, in metres). Sample sizes are filled in so you can preview, and you should replace them with yours. Under **Worked out for you** the app shows the floor area, floor perimeter, wall area to tile and ceiling area to paint. In the cloakroom the third figure is the splashback on one wall (room width times tiled height). Doors and windows are not deducted.

### Review

![Reviewing the list](img/19-job-review.png)

The list is pre-filled from the template. You see three numbers: **Lines**, **Sections** and **Checks**. **Lines** counts the lines that apply to your answers, so it can be lower than the line count on the job card. Two controls save time:

- **Accept all defaults** takes the template as it is and goes straight to the summary. Every default you accepted is listed there as an assumption to confirm.
- **Finish: Budget / Standard / Premium / Defaults** sets every line at once.

**We assumed** lists the defaults the app chose, and you can change any of them. **Materials by section** lists every line, grouped.

### Summary

![The job summary](img/20-job-summary.png)

The summary shows the lines to source, how many you left out, and the checks, for example *All measurements entered*, *12 rules checked and met* and *This template has not been reviewed by a tradesperson. Check every line before ordering.* Each check has a coloured dot: green for fine, amber for something to look at, red for something to fix. (Screen readers say *OK*, *Note* or *Fix*.) The **Prices** block here is only a rough guide (*Not a kit total and not a quote*).

Press **Build the quote** to continue. In the demo build it opens the Quote page. When the app is connected to its server it saves a quote, shows *Quote created* with its id for a moment, and opens the Quote page with that id in the address (`/quote?quote=...`). The Quote page does not read the id. It and **Supplier prices** each build their own quote for the same job type from the template's sample sizes and defaults, so the sizes and answers you entered in the wizard do not reach them and no page opens the quote that was saved (a known defect, see [troubleshooting](07-troubleshooting.md#known-rough-edges-in-this-build)). The other buttons are **Change something** and **Start a different job**.

The **Reuse this job** card saves your answers, sizes, option picks and left-out lines as a template for similar work (no prices are saved). Type a **Template name** and press **Save as template**. The screen says where it was kept: *saved on this device only* in the demo build, or *saved to your account* when the app is connected to its server.

Two links appear at the foot of the wizard: **Advanced: edit job templates (Config)**, which previews a pasted job configuration in this browser tab and saves nothing, and, on the summary, **Advanced: request data**, which shows the data the list would hand to a request (nothing is created or sent).

## Stage 2: Prices

![Who has prices](img/21-prices.png)

**Supplier prices** shows which suppliers have a current price for this job and what is missing.

- **Lines each supplier can price** is a bar per supplier (*32 of 77 lines*). Switch to *Table* for the same data as a table.
- The four counters say how many suppliers are **Current**, **Out of date**, **Rough only** or have **No prices**. *Out of date* means older than the allowed age, so the price is shown but not used.
- Each supplier shows how its prices were obtained: *On request*, *Past invoices*, *Price file*, *Regular price file* or *Contract feed*. Today the prices come from **price files** that you upload.
- **Upload prices** loads a price file. **Ask for missing prices** opens a preview of the quote requests for the lines nobody has priced (stage 5). It is off when every line has a price.

### Uploading a price file

![The upload report](img/27-upload-prices.png)

When the app is connected to its server, **Upload prices** opens a form (buyers and admins can load files; a requester is refused). In the demo build it shows a static example report instead, as in the picture above, labelled *static example, not your file*.

| Field | Notes |
|---|---|
| **Merchant** | Which supplier the file is from. |
| **File** | A `.csv` or `.xlsx` file, up to 900,000 bytes. |
| **Currency** | Used for rows that have no currency column. |
| **Do these prices include VAT?** | You must choose. It is never guessed from the file. A row that states its own VAT basis keeps it; your choice fills the rows that state none. |
| **Valid from / Valid until** | Optional dates. A valid-from date in the future, or a valid-until date that has passed, is refused. |
| **I confirm I may use this file for my own company's purchases.** | The attestation. |

Prices load as **firm** only with the attestation **and** a valid-until date. If either is missing they load as **indicative only**: they are shown for reference and never used as firm prices. A valid-from date alone does not make them firm.

Press **Upload and check file**. The **Upload result** shows **Firm prices** or **Indicative only** (with the reason), the counts (*Rows read*, *Accepted*, *Firm*, *Indicative*, *Quarantined*, *Older offers replaced*) and a table **Rows not loaded** with the row number, the reasons and the product code (SKU) of each held-back row. The page then refreshes the supplier prices.

A row is held back (*quarantined*) when it cannot be read safely. The reasons you may see include *pack size missing*, *invalid price*, *currency missing*, *duplicate record* (the same product twice in one file: the first row is kept), *vat basis unknown* (the row's own VAT text is not one the app recognises) and *invalid offer* (for example a valid-until date earlier than the price date). A blank VAT cell is not a problem: it takes the choice you made in the form. Held-back rows are not kept and the app has no per-row fix: correct the file and upload it again.

A new file for a supplier replaces that supplier's earlier price-file prices, including products that are missing from the new file. A file with an older price date than the one already loaded is refused.

Some problems only show when a quote is built, not at upload: a price more than three times above, or under a third of, the median for the same product (checked when at least three offers can be compared), a pack unit that cannot be converted to the line's unit, and a price that has expired. Those offers are kept out. They appear under **Other offers kept out** in **Why this price**, or the line moves to **No price yet**.

The demo build's static example is headed **Import report** and lists four sample reasons (*vat basis missing*, *price outlier*, *unit not convertible* and *expired row*). They are illustration only: a real upload uses the reasons above.

## Stage 3: Quote

![The quote](img/22-quote.png)

At the top: the **Job type**, and a **Show** switch between **First quote** and **After my reviews**. In the demo build there is also a *Customer (demo)* picker. When the app is connected to its server the page reads *Live data from your account*.

- **Total** is the lines that have a confirmed price plus the suppliers' delivery fees, as **inc VAT** or **ex VAT** (switch at the top right). The line below says how many lines were priced and from how many suppliers. If a supplier has no delivery fee on file, the label reads *Total so far* and a note says the real total is higher.
- **Spend by supplier** shows each supplier's share, as a chart or a table.
- The four tiles say how many lines were **priced** out of the total, how many **suppliers** and **deliveries** that means, and how many lines **need you**.
- **Needs you** breaks that last number down: **Waiting for your choice** (the system could not decide which product fits; choose one, or none), **No match** (it could not match the line to a product, so there is no price) and **No price yet** (no supplier has a usable price). Press **Review** or **Show** to open each list.

Lines are shown under these headings, each with a count:

| Heading | Meaning |
|---|---|
| **Lines by supplier** | Lines with a confirmed price, grouped by supplier. **Why this price** shows how it was chosen. |
| **Waiting for your choice** | Lines you must decide on. They are **not in the total**. |
| **Rough prices** | A rough guide from past invoices or shop listings. Never added to a total and not a quote. |
| **No match** | Lines with no product match. Not priced. |
| **No price yet** | Lines that match a product but have no supplier price the app can use (out of date, expired, VAT not stated, or kept out by a check). |
| **Skipped** | Lines left out (*Marked not needed*, *You already have it*) or with a quantity of zero. Shown only when there are some. |
| **Totals breakdown**, **About this quote** | How the total was reached, and the full notice about what this is. |

A *confirmed price* is one from a price file you confirmed or from a real supplier reply. Under **Why this price**, **Provenance** shows the match as a tier, for example *Match: tier A*. The tiers are *Same part* (A), *Equivalent* (B), *Possible* (C) and *Needs an expert* (D); the approval page shows those four words. The system never swaps a part for a worse match on its own.

## Stage 4: Compare (ways to buy)

![Ways to buy](img/23-quote-ways-to-buy.png)

**Ways to buy** shows different ways of buying the **same confirmed lines** from a mix of suppliers. It says up front that this is *from the prices on file, not a market-wide best price*, and that *nothing is chosen for you*. **Compare** in the tracker opens the Quote page at this section.

| Way to buy | What it is |
|---|---|
| **Lowest total cost** | The cheapest complete basket the optimiser found. The option with the lowest total also carries a green **Lowest total** badge. |
| **Fewest deliveries** | The fewest suppliers (so the fewest deliveries) whose total stays within a tolerance of the lowest total (5% in the demo data). |
| **Fastest** | The earliest latest-arrival date whose total stays within that tolerance. A line with no stated lead time counts as slower than any stated one. |
| **Preferred suppliers** | As many lines as possible from the suppliers on a preferred list, within the tolerance. Shown only when a preferred list is supplied. |
| **Single supplier** | The supplier that can supply the most lines buys everything it can, and the rest come from others. Not shown by default. |
| **Balanced** | Scored against a budget, a required-by date and a delivery limit. It is shown only when at least one of them is supplied. The panel under **Limits and notes** calls it **Best overall**. It is **not a recommendation**, and the weights it uses are placeholders the screen lists (*unsourced*). |

The screens in this build have no box for a preferred-supplier list, a budget, a required-by date or a delivery limit. When the app is connected to its server, **Preferred suppliers** and **Balanced** therefore do not appear. The demo data carries invented values for some jobs.

Every option is complete: each line is bought once, from one supplier, and the totals add delivery fees to the goods. Options that come out identical are shown once and the others are listed as *Same as ...*.

**Side by side** compares the options on total, deliveries, latest arrival and extra cost against the lowest, with *best* marked on the winner in each column. Each card shows the total as inc VAT and ex VAT, how many suppliers and deliveries it needs, and the days to arrive, then flags such as *Below a minimum order quantity*, *A delivery fee is not on file*, *Some lines have no stated lead time*, *Low stock on some lines* or *Stock not stated on some lines*, and a few plain sentences about what changes against the lowest total. **Why this mix, and what each supplier sends** opens the goods and delivery cost per supplier.

Lines that have only a rough price are listed apart and are in **no** option. When the app cannot prove that the lowest total is the lowest possible, it says so: *The lowest total is not proven; a lower one may exist.* Details are under **Limits and notes** (budget, dates, lines left out).

Press **Use this mix** to mark the option you prefer. It is a marker: it **does not order or send anything**. The button then reads *Selected (demo only)* and a panel says *Nothing is ordered and nothing is sent*. The wording is the same when the app is connected to its server.

## Stage 5: Ask suppliers

![Ask suppliers](img/26-ask-suppliers.png)

This stage is on the **Supplier prices** page. **Ask for missing prices** previews the exact subject and message to each supplier for the lines that have no confirmed price. You choose **One quote per supplier (default)** or **Individual quotes, one per item**.

When the app is connected to its server, press **Prepare for approval**. This creates the messages as *unsent drafts*. They then wait on **Requests**, where a buyer reads and approves each exact message, as in [Approve and send](02-requests.md#4-step-3-approve-and-send). **Nothing is sent by the preparing step.** Each supplier in the list must match a verified, preferred supplier on **Suppliers**. If one does not, the server refuses the whole batch (for example *no verified supplier for 'm-brindlecote'*), nothing is prepared, and the screen shows the server's message. In the demo build the dialog only shows the preview.

You can leave the job at any time. The buttons at the foot of each screen (for example *← Prices* and *Next: Compare →*) walk you through the stages in order. Inside the Job stage, **Back** and **Continue** move between the wizard's steps.

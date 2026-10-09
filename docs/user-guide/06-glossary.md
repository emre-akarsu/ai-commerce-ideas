# Glossary

The words the screens use. They are defined once in the app (`apps/web/lib/labels.ts`), so what you read here is what the screens say.

## People and access

| Term | Meaning |
|---|---|
| **Requester** | Someone who asks for a part or a quote. The lowest role. |
| **Buyer** | Someone who may prepare, approve and send messages and select quotes. Includes everything a requester can do. |
| **Admin** | Someone who also verifies suppliers, sees Setup and Activity, and controls the kill switch. Includes everything a buyer can do. |
| **The person who asked** | The person who raised the request. |
| **Second person** | A person other than the one who asked, who must approve before something is ordered where the rules require it. |
| **Approver** | A named person who decides an approval link. They must be at least a buyer, and must be the person the link was issued to. |

## Requests

| Term | Meaning |
|---|---|
| **Request** | One thing you need to buy, from first sentence to purchase order draft. |
| **Quote request** | A message asking a supplier to price the listed parts. Nothing is sent until a person approves it. (Technical documents call it an *RFQ*.) |
| **Machine down** | A flag you set when a machine is stopped. The request goes first on Home and is limited to fewer suppliers. |
| **Safety critical** | A flag that makes every candidate part need engineering review. |
| **Assumption** | Something the app filled in without being told. You confirm it or mark it *Not right*. |
| **Critical assumption** | An assumption that could change which part is right. It must be confirmed before any message can be prepared. |
| **Inferred** | Worked out from your text rather than stated by you. Shown with how sure the app is. |
| **Default** | A standing assumption such as *Prices are ex-VAT unless the supplier says otherwise*. |
| **NEXT bar** | The bar at the bottom of a request that says what to do now and who has to do it. |
| **Needs engineering review** | The part is unclear or safety critical, so the app will not guess. A person outside the app has to decide. |

## Parts and matching

| Term | Meaning |
|---|---|
| **Tier A, Same part** | The identical part. |
| **Tier B, Equivalent** | A documented equivalent. Accept it for this request only if it fits. |
| **Tier C, Possible** | Matches by rule only, with no published source. Never offered. |
| **Tier D, Needs an expert** | An engineer must confirm the part fits before any price is used. Never offered or selectable. |
| **Part number** | The manufacturer's part number. |
| **Product code** | The code this system uses for the product in its own catalogue. |
| **Part description** | What you need, in writing: size, type, rating and finish. |
| **Source quality (A to D)** | How reliable the evidence for a match is. A is a rule or a maker's specification, B is merchant data, C is one retailer, D is a forum or unverified source. |
| **Possible match** | A product that might match a line. You choose one, or none. |
| **Needs your choice** | The system could not decide which product fits. Choose one, or none. |
| **No match** | The system could not match a line to a product, so it has no price. |

## Prices and money

| Term | Meaning |
|---|---|
| **Confirmed price** | A price that counts in totals: from a price file you confirmed, or from a real supplier reply. |
| **Rough price** | A rough guide from past invoices or shop listings. Never added to a total, and not a quote. |
| **No price yet** | A line no supplier has a usable price for. |
| **Skipped** | Left out by you, or a quantity of zero. |
| **Out of date** | Older than the allowed age, so it is shown but not used. |
| **On hold** | Held back and not used because a check failed. A person must look at it. |
| **ex VAT, inc VAT** | Without or with VAT. The app shows which one every amount is, and never guesses. |
| **Price includes VAT?** | The question you answer when you upload a price file. A price without an answer cannot be compared. |
| **Landed cost, delivered cost** | The price per unit including delivery to you. |
| **Waste allowance** | An extra percentage added for waste and offcuts. |
| **Supplier price** | One supplier's price for one product, with the date it was seen and whether VAT is included. |
| **Source (price)** | How a price was obtained, from least to most trusted: *On request*, *Past invoices*, *Price file*, *Regular price file*, *Contract feed*. |
| **Price file** | A CSV or Excel file of prices that you upload. |
| **Quarantined row** | A row in a price file that was held back (for example no VAT basis, or a price far from the others) and is not used until fixed. |
| **Not a supplier quote** | A comparison of prices observed in your data, at the times shown. It is not an offer that can be accepted, and it does not reserve stock. |

## Quotes and comparing

| Term | Meaning |
|---|---|
| **Materials list** | A ready-made list of materials for one kind of job. You answer a few questions and check quantities. |
| **Job type** | The kind of work a quote covers, for example *WC only* or *Full bathroom*. |
| **Finish** | *Budget*, *Standard* or *Premium*. It sets the default product on each line. |
| **We assumed** | Values the system filled in without being told. Check each one. |
| **Ways to buy** | Different ways of buying the same lines from a mix of suppliers. |
| **Supplier mix** | One way of buying all the lines, split across suppliers. |
| **Best overall** | A way to buy scored against a budget, date and delivery limit that you gave. It is not a recommendation. |
| **Warning** | A problem found in a reply, such as no currency or an expired quote. Red ones block selection. |
| **Flag** | A short label on a quote, such as *VAT basis not stated* or *Freight not stated*. |
| **Recommended** | The quote the comparison suggests, with its reasons. It is a suggestion, not a decision. |

## Safety and records

| Term | Meaning |
|---|---|
| **Approval** | A recorded human decision. A message approval covers one exact message. A quote approval covers one quote at one version. |
| **Approval link** | A single-use, expiring link to a bare page where one named approver approves or declines one quote. |
| **Quarantine** | Holding something back, shown but unused, until a person reviews it. |
| **Sender check** | Checks that a reply really came from the supplier's own domain. A failed check holds the reply back. |
| **Suppressed, Do not contact** | A supplier that asked not to be contacted, or that a person blocked. Only an admin can reverse it. |
| **Verified supplier** | A supplier an admin has checked, with a recorded note. Only verified suppliers can be sent a message. |
| **Alias address** | The address replies go to. It belongs to the system, so suppliers do not write to a personal mailbox. |
| **Message fingerprint** | A short code for the exact text of a prepared message. Your approval is tied to it. |
| **Kill switch, Stop all sending** | One switch that stops every message from the account. Queued messages are refused. |
| **Activity, audit trail** | A dated record of every step on every request, kept so it can be checked later. |
| **Tamper check, hash** | A code that changes if any earlier entry is edited. |
| **Deployment profile** | The settings for a market: currency, tax, language, legal wording, limits and thresholds. Shown in Setup as, for example, `uk@7c41e0b9a2d3`. |
| **Demo data** | Made-up data for demonstration. Not real parts, prices, suppliers or customers. Nothing is sent. |

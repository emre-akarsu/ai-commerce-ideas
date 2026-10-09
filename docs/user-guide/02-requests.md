# Requests

A request is one thing you need to buy, from the first sentence to a purchase order draft. Every request shows the same six steps along the top:

**Request → Suppliers → Approve and send → Replies → Compare → Purchase order**

A tick means the step is done and the highlighted step is the one you are looking at. The **NEXT** bar at the bottom of a request says what to do next. When the next move is someone else's, it reads *Waiting on suppliers* or *Waiting on approver*. If your role cannot do the next move, the bar's second line says which role can. A request with nothing left to do in the app, such as one that has ended, one whose purchase order draft exists, or one in *Needs engineering review* with nothing left to confirm, has no NEXT bar.

**Home** lists the open requests that have a next step (see [Getting started](01-getting-started.md#the-screen)). All requests, including closed ones and the ones Home leaves out, are under **Requests**, which has *All*, *Open* (selected when the page opens) and *Closed* filters and a search box.

![The Requests list](img/12-requests-list.png)

## 1. Start a request

Press **New request** on Home (or `n`).

![The new request form](img/02-new-request.png)

| Field | Notes |
|---|---|
| **What do you need?** | A part number, a description, or a pasted email. Up to 4,000 characters. `Ctrl+Enter` starts the request. |
| **Quantity** | Type it in. Without a quantity no message can be prepared (see below). |
| **Needed by** | A date. |
| **Add site, work order, urgency** | Opens four more fields: *Deliver to* (up to 200 characters), *Work order* (up to 60), *Machine is down now* and *Safety critical*. |

**Quantity and date from your text.** A box you fill in always wins. When you leave *Quantity* or *Needed by* empty, the app tries to read the value from your text with a few fixed patterns. *What we understood* then shows what it found (*not stated* when it found nothing). It never guesses.

- Quantity: `qty 12`, `quantity: 12`, a number followed by `pc`, `pcs`, `piece`, `pieces`, `ea`, `each`, `unit`, `units` or `off` (`12 pcs`), or `x12` written together. `4 x 6205-2RS` is not read. If the text holds two different quantities, the app takes none.
- Needed by: `needed by`, `required by`, `due`, `due by`, `no later than` or `by`, followed by a weekday name (the next one after today), `today`, `tomorrow` or a date such as `2026-12-01`. If the text holds several dates, the earliest is taken. `next week` and `5 Nov` are not read.

A request with no quantity can be started, but preparing messages for it is refused with *quantity is required before an RFQ can be drafted*, and no screen adds the quantity afterwards. Start a new request with the quantity filled in. The hint under the Quantity box, *The agent does not read this from the text.*, is wrong.

Two of those boxes change what the app does. Words in your text can turn them on too, but the text never turns a ticked box off:

- **Machine is down now** marks the request **Machine down**, puts it ahead of the other requests in its group on Home, and **limits it to fewer suppliers** (by default two instead of four; the limits come from your deployment profile). The app also turns it on when your text says *asap*, *down now*, or that a line, machine, production, plant, press, conveyor or pump *is down*.
- **Safety critical** makes every candidate part Tier D (*needs engineering review*), even an identical one. Tier D parts are never offered to suppliers, so a safety-critical request moves to **Needs engineering review** (after any question the app still has to ask) and no message can be prepared until a person outside the app decides. The app also turns it on when your text contains *safety*, *critical*, *criticality*, *hoist*, *crane*, *lifting*, *elevator*, *regulated*, *atex* or *explosion*; a text that says *not critical* still counts.

## 2. Step 1: Request (what we understood)

![A request with one question](img/03-request-question.png)

**What we understood** lists the quantity, the date, where it goes and the work order (*not stated* or *none* when you gave nothing), then each fact the app worked out about the part. Each fact has a tag for where it came from, and shows how sure the app is:

- **You said**: it is in your own words, for example *100% sure · user text '6205-2RS'* (the demo build's example reads *100% sure · request text*).
- **Standard**: looked up from a published standard, for example *100% sure · ISO 15 boundary dimensions*.
- **Rule**: a default the app applied, for example *80% sure · designation convention: no tolerance-class suffix denotes Normal (P0)*. A default like this is also listed under *Assumptions to confirm*.
- **Inferred: confirm**: a guess. The app never treats a guess as settled: you must confirm it (below). The service in this build makes no guesses of this kind, so you meet this tag only in the demo build, whose example in the screenshot below reads *60% sure · inferred from 'B42'*.

**One question.** If the app cannot identify the part, it asks, in plain words, with a drop-down where the answers come from a fixed list and a text box where they do not. It asks only what changes the part or the price, and **never more than two questions in total**. **Save answers** stays greyed out until at least one box has an answer. If you do not know an answer, leave that box empty. Whatever is still missing once the two questions are used up sends the request to **Needs engineering review** rather than guessing. That includes the case where two questions were asked together and you answered only one.

**Assumptions to confirm.** Anything the app filled in without being told is listed with labels and a confidence (*high*, *medium* or *low*):

| Label | Meaning |
|---|---|
| **Critical** | It could change which part is right. Critical assumptions **must be confirmed one by one** before any message can be prepared. |
| **Inferred** | A guess. A guess is always Critical and never counts as confirmed until you confirm it. Only the demo build shows this label (see above). |
| **Default** | A standing default. The price default reads *Quoted prices are assumed to be exclusive of VAT unless the supplier states otherwise.* (the tax name, and *exclusive* or *inclusive*, follow your deployment profile). A default about the part reads, for example, *Assumed precision_class = P0: designation convention: no tolerance-class suffix denotes Normal (P0)*, and is also Critical when it could change which part is right. |

![Assumptions waiting to be confirmed, in the demo build](img/04-request-assumptions.png)

Press **Confirm** if it is right. Press **Not right** if it is wrong. For an assumption about the part, *Not right* drops the value and, when the app has a question for it, the request goes back to *Needs your answers* for that fact. This counts towards the two-question limit: a third question sends the request to *Needs engineering review*. *Not right* on the price default only marks it wrong. The row stays in the history either way. When two or more non-critical assumptions are open, **Confirm the N non-critical ones** confirms them together.

## 3. Step 2: Suppliers

![Choosing suppliers](img/05-request-suppliers.png)

**Ask suppliers to quote** lists the parts the app will ask for, each with a tier:

| Tier | Meaning |
|---|---|
| **Tier A** | The identical part (*Same part* on the approval page). |
| **Tier B** | A documented equivalent (*Equivalent* on the approval page). This step shows its first caveat next to it, for example *Load ratings and service life may differ between manufacturers; verify on the datasheet.* (the demo build's example reads *Metal shield instead of rubber seal: check for wet or dusty duty*). The **Matching parts** list on the Request step shows every caveat and what differs, for example *seal_designation differs: requested 2RS, offered 2RSH*. |
| **Tier C** and **Tier D** | Never offered. The legend on the Request step reads *C = rule-matched with no published source* and *D = needs engineering review*. The approval page words them *Possible* and *Needs an expert*. |

Untick any candidate you do not want quoted. In this build every candidate comes from synthetic example data, not from licensed cross-reference data, and the *Matching parts* list marks each one *Synthetic example*.

**Choose suppliers** lists your suppliers. Only some can be picked, and the screen says why for each one that cannot:

| Shown as | Why you cannot pick it |
|---|---|
| A **Not verified** badge | *Not verified yet: an admin must verify this supplier.* See [Suppliers](04-suppliers-setup-activity.md). |
| A **Verified** badge, but a greyed-out tick box | *A sole trader or individual: switched off until counsel confirms the rules.* |
| A **Suppressed** badge | *Suppressed: asked not to be contacted, or switched off.* |

The step does not check whether a supplier is marked *preferred*. A supplier that is not preferred can be ticked, but preparing is then refused with *vendor … is not a preferred vendor*. A supplier added with the **Add supplier** form is saved as not preferred, and no screen changes that. Suppliers imported from a CSV file are preferred. This is a known gap, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09).

**Select all N verified** (shown when more than one supplier can be picked) ticks every supplier you can pick. Press **Prepare N messages for approval**, where N is the number of suppliers you ticked; the button stays greyed out until you tick one. Preparing writes the messages but **sends nothing**. By default a request can ask at most four suppliers (two if it is marked *Machine down*); more is refused with *at most N vendors per request*. A request with no quantity is refused with *quantity is required before an RFQ can be drafted*.

Only a buyer or admin can prepare messages.

## 4. Step 3: Approve and send

![Approving each message, with the demo build's sample message](img/06-approve-and-send.png)

Each prepared message is shown in full, labelled **This is exactly what will be sent**, with:

- the **To** address and **Subject**,
- a **Message fingerprint** (a short code for the exact text),
- the body: the parts asked for with their maker, the quantity, the needed-by date and the *Deliver to* site if you gave them, and a request for the unit price and unit, the currency, whether the price includes VAT, the lead time, freight, how long the quote is valid, the condition, and the exact maker and part number quoted. Then come the buyer's name, phone number and reply-to address. Your account number with the supplier is not in the message (it shows only on the Suppliers step). The demo build's sample message, in the screenshot, is shorter and does include an account-number line,
- your company's details as your deployment profile requires them (for the UK profile: company name, company number, registered office and where it is registered), then an *RFQ reference* code for the reply,
- a closing notice labelled **Added by the system, cannot be edited**, which says the message was prepared with an AI assistant, that it cannot accept terms or place orders, and that only a purchase order from the buyer named in the message binds. The exact wording comes from your deployment profile; the UK profile also says *on behalf of* the buyer's name.

The company details come from your deployment's settings, not from a screen. If they are missing, preparing is refused with *business identity incomplete: missing* and the names of the missing fields. The screen adds *An admin must complete the company details in Setup*, but Setup only lists what is missing and has no control to enter it. The service as shipped is given no company details, so on the UK profile every attempt to prepare a message is refused until whoever runs your deployment supplies them (a known gap, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)).

**Each message is approved separately.** Press **Approve and send to *supplier***. Your approval covers that exact message and no other. If the text changes after you looked at it, the send is refused and you prepare it again and read the new text.

> **In this build** an approved message goes to a recording transport: the app records exactly what would have been sent. No real email provider is connected yet.

Only a buyer or admin can approve and send. An admin can stop all sending at once with the [kill switch](04-suppliers-setup-activity.md#setup).

## 5. Step 4: Replies

![Waiting for replies](img/07-waiting-for-replies.png)

Replies go to your alias address and appear here. Each reply is:

- checked that it really came from the supplier's own domain. A reply that fails the check is quarantined and shows *Sender failed email authentication: quarantined* (*Failed sender check* in the Compare table). A reply that passes shows nothing for it,
- read as plain text, never as instructions,
- turned into a quote with a price, currency, lead time, validity and minimum order, and **each value is checked against the reply text**. A value that cannot be found in the reply is dropped and flagged, never filled in.

Each quote card has a **Where each value came from** section that quotes the exact words used.

A reply can be **Quarantined: not used until a person reviews it**. The screens mark this when the reply fails the sender check, or when it contains instructions aimed at the agent, which includes a message that says bank details have changed. Such a reply is shown, left out of the recommendation and marked *Not selectable* in the comparison. A third case is a supplier whose domain or contact address was changed and the change has not yet been confirmed by a call. The comparison leaves out that supplier's replies too, but the Replies step does not mark them, and nothing in the app records the call, so they stay held back (a known gap, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)).

You do not have to wait for every supplier: as soon as one reply has been read, the **Compare** step opens. The request moves to *Ready to compare* by itself once every message that was sent has a usable reply.

> **In this build** no inbound mail provider is connected, so as shipped a reply appears when someone pastes it in (next paragraph). The demo build adds a **Simulate supplier replies (demo only)** button.

If a supplier replied by phone or another way, open **Got a reply by phone or another way?** and press **Paste a reply**. Choose the supplier, paste what they said (include the currency symbol and name the part) and press **Add quote**. A quote you enter by hand is flagged *Entered by a person* on its card and on the approval page (*Entered by hand* in the Compare table). It always needs an approver other than the person who asked.

If a supplier's reply is nothing but *stop*, *unsubscribe* or *remove me*, sent from its own authenticated domain, the supplier is suppressed and nothing else happens: that text is not read as a quote or as an instruction.

## 6. Step 5: Compare

![Comparing quotes like for like](img/08-compare.png)

**Compared like for like** shows one row per quote with the landed unit cost, the total for your quantity, the lead time and any flags. It explains its own recommendation in plain sentences, for example *It offers a Tier A part*, *It is the lowest landed cost within its tier*, *It meets the need-by date*. It also says what it left out and why.

- **Recommended** marks the best quote it found. It is a suggestion, not a decision.
- A price is only compared when the supplier stated the price and the currency. A quote with no stated VAT basis is **flagged, never guessed**.
- A quote that is quarantined, has no stated price or currency, or has a price that could not be found in the reply shows **Not selectable**.
- Two other cases show **Select**, but the server refuses them. A quote whose validity date has already passed carries a *validity expired* flag, may even be marked *Recommended*, and is refused with *quote validity has expired: ask the vendor for a current quote*. A quote whose minimum order is more than your quantity is listed as left out and carries *Minimum order too high*, and is refused with *quote is excluded (flagged, quarantined or unusable)*. The screen gives no hint for either refusal.
- A quote for a **Tier D** part shows *needs engineering review*.

Press **Select** on the quote you want. This asks for an approval where one is needed. It **does not order anything**.

A quote needs an approval when any one of these is true: the part offered is a substitute (not Tier A), the total is above your approval threshold, the day's committed total is over the daily limit, or it carries a flag such as *VAT basis not stated*, *Currency unclear*, *Freight not stated*, *Not stated as new* or *Entered by hand*. When none is true, no approval is requested: the request moves to *Quote selected* and the NEXT bar says *Create the purchase order*. In this build the Purchase order step then still says *The purchase order unlocks after approval* and has no button, although the server would accept the draft. The web app therefore cannot create the purchase order draft for a request that needs no approval (a known defect, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)).

### Waiting for the approver

![Waiting for the approver](img/09-waiting-for-approver.png)

An approval link is issued for the selected quote. The approver opens it, signs in and decides. Nothing is ordered until they approve. Each approver gets two links, one to approve and one to decline. **The approver must be someone other than the person who asked** when the total is above the approval threshold, when the day's total is over the daily limit, or when the quote carries one of those flags (a quote you entered by hand is one). If there is no other eligible approver, the selection is refused with *no eligible approver (approver must differ from requester)*, but only after the request has moved to *Quote selected* and its total has been set aside. The request then cannot be selected again and no purchase order draft can be made, so it is stuck (a known defect, listed in [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)).

> **In this build** the link is created but not delivered by email: a notifier still has to be connected (see [known gaps](../architecture/known-gaps.md)). In the demo build the link **Open the approval page (demo only)** stands in for it.

### The approval page

The approver sees a bare page with no navigation:

![The approval page, in the demo build (both buttons on one page)](img/10-approval-link.png)

It shows the total, quantity, unit price, lead time, how well the part matches, the part number and any warnings. **Approving confirms this quote; it does not place an order.** The link can be used **once** and **expires** (the page shows when). The approver must be authenticated with at least the buyer role and must be the approver the link was issued to. Each of the approver's two links shows one button: **Approve this quote** on the approve link and **Decline** on the decline link (the demo build shows both on one page). A decline ends the request as **Declined** and releases the money that was set aside for it. In this build no screen takes a declined request back to the comparison, so start a new request if you still need the part.

## 7. Step 6: Purchase order

![The purchase order step](img/11-purchase-order.png)

After approval, press **Create purchase order draft**. A request that needed no approval has no such button in the web app (see [Step 5: Compare](#6-step-5-compare)). The draft uses **only the approved quote and the part number you confirmed**. It cannot use a part that was never approved. Once it exists, **Download CSV** gives you the file.

> **Nothing is ordered or paid from here; you send the order yourself.** A PDF export is not available yet.

## What each status means

The label on a request in lists and at the top of its page.

| Status | Meaning | Who acts next |
|---|---|---|
| **Received**, **Reading the request** | The app is reading your text. | The app |
| **Needs your answers** | There is a question to answer. | Requester |
| **Spec confirmed** | The part is identified and no question is open. Critical assumptions may still be waiting: the NEXT bar then says *Confirm N assumptions*. | Requester: confirm critical assumptions. Then buyer: choose suppliers |
| **Messages prepared** | Messages are written and waiting for approval. | Buyer: approve each |
| **Messages approved**, **Messages sent** | Approved, and sent (in this build, recorded). | The suppliers |
| **Waiting for replies** | Sent; not every supplier has given a usable reply yet. As soon as one reply has been read, the **Compare** step opens and you can select a quote without waiting for the rest. | The suppliers (or paste a reply) |
| **Ready to compare** | Every message that was sent has a usable reply. | Buyer: select a quote |
| **Quote selected** | A quote is selected. A request that needs no approval waits here, and the web app has no button to draft its purchase order. A request that had no eligible approver stays here too. | Buyer |
| **Waiting for approver** | An approval link was issued. | The approver |
| **Approved** | The approver approved. | Buyer: create the purchase order draft |
| **Declined** | The approver declined. The request ends here. | Nobody: start a new request |
| **PO drafted** | The draft exists. Home no longer lists the request; find it under **Requests**. | Buyer: export it and send it yourself |
| **PO sent** | A purchase order was sent through the app. Nothing in this build does this yet. | |
| **Needs engineering review** | The part is unclear, safety critical, or not a kind of part this deployment handles. The app will not guess, and nothing in the app moves such a request on. If no critical assumption is waiting to be confirmed, the request page has no NEXT bar (it opens on the *Purchase order* step, and a card reads *The purchase order draft exists. Export it from the Purchase order step.*, which does not apply to this status) and Home does not list the request. If critical assumptions are still open, the NEXT bar says *Confirm N assumptions* and Home lists it. Find it under **Requests** in either case. | A person outside the app |
| **Closed**, **Cancelled**, **Expired** | Finished states. In this build nothing moves a request into *Closed* or *Expired* (there is no close button and no timer), and *Cancelled* is only reached by cancelling a purchase order draft, which has no button yet. | |

Every change of status is recorded in the [activity trail](04-suppliers-setup-activity.md#activity), including who made it. **History** at the bottom of a request shows the entries for that request.

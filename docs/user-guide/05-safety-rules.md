# What the app will not do

These rules are built into the code and have **no setting to switch them off**. Where the screens seem strict, this is why. The numbers (R1 to R12) are the product spec's hard rules, in [`docs/product/04-product-spec.md`](../product/04-product-spec.md) section 4.

| Rule | In plain words | What you see |
|---|---|---|
| **R1** | **Nothing is sent and nothing is ordered without a recorded human approval.** The part of the system that writes messages has no way to send mail. Only the send service sends, and only a message that a person approved. | You press **Approve and send to *supplier*** for each message. There is no "send all" button. A purchase order is a draft that you send yourself. |
| **R2** | **No swapping a part for a different one without you.** An order line can only use a part that was approved as an identical match, or one you explicitly approved as a substitute. | A substitute is labelled **Tier B** and always needs an approval. Tier C and D are never offered. |
| **R3** | **No claim without a source.** Every fact about a part says where it came from and how sure the app is. Explanations are filled-in templates, not free writing. A guess made by a model can never satisfy a critical fact. | **You said** and **Inferred: confirm** labels; the **Critical** label; **Where each value came from** under each reply. |
| **R4** | **Ask, do not guess, and ask at most twice.** | **One question**, and *Needs engineering review* if the part is still unclear. |
| **R5** | **Authenticity is not assumed.** *Unknown* does not mean *authorised*. The app gives no warranty that a part is genuine. | Each quote carries an authenticity value (*verified*, *vendor claimed* or *unknown*) in the data, but the current screens do not show it. |
| **R6** | **Supplier text is untrusted.** A reply is read by a separate step that cannot act. Every value it extracts must appear word for word in the reply, or it is left blank and flagged. Instructions inside a reply are never followed, and a reply cannot change a recipient, an amount or a rule. | **Quarantined**, *Price not found in the source text*, *Contains instructions aimed at the agent*. Replies are shown as plain text with no links or images. |
| **R7** | **The app never opens links or scrapes sites** found in a reply. | Links in replies are text, not links. |
| **R8** | **Every message says it was prepared with an AI assistant, and that only your purchase order binds.** The footer cannot be removed. Messages go out in your company's name from an alias address. | The **Added by the system, cannot be edited** block under each message. |
| **R9** | **Money is exact.** Amounts use exact decimal arithmetic with a stated currency, unit and VAT basis, and there are **per-order and daily caps**. | Every price shows *ex VAT* or *inc VAT*. A price without a stated basis or currency is flagged and cannot be compared silently. |
| **R10** | **Tenants are isolated.** One company's data cannot be read by another, and the database itself enforces this. | You only ever see your own company's data. |
| **R11** | **Approval links cannot be forged.** The link only shows the quote. The decision needs a signed-in person, and the link is tied to one approver, one quote version and one action. It works once and expires. Above the approval threshold the approver cannot be the requester. | The bare **Approve a quote** page. |
| **R12** | **Supplier identity is checked.** A reply must come from the supplier's registered domain and pass email authentication (the inbound mail provider reports whether DMARC aligned). If it does not, it is quarantined and never processed automatically. Changes to a supplier's contact details are admin-only and need a call to confirm. | **Failed sender check**, **Sender authenticated**, and the *Not verified* supplier badge. |

## Where AI is used

In the shipped app, **no step calls a language model**. Parts are identified by rules, replies are read by a pattern reader, comparisons and prices are computed, and messages are filled-in templates. The code has four optional places where a model could be asked to help (reading a reply, choosing between close product matches, proposing catalogue entries, and writing one polite sentence in a message). None is switched on, and the repository has no production model connection. The [technical guide](../technical/06-security-and-trust.md#where-a-model-can-be-used) lists them.

The footer says a message was *prepared with an AI assistant* because the product is designed to carry that disclosure whatever produces the text.

## What it does not do yet

- **It does not send real email.** Approved messages go to a recording transport. No mail provider or inbound mail provider is connected.
- **It does not deliver approval links.** The link is created, but nothing emails it to the approver yet.
- **It does not place orders.** It drafts a purchase order and gives you a CSV file.
- **It does not remember your suppliers' real prices for you**, apart from price files you upload.
- **It has no live market data.** Prices come from your own price files.

The full list of known limits is in [known gaps](../architecture/known-gaps.md).

## Review events the app records

The app records content-free *review events* when you view or act on certain decision screens (for example that a comparison was shown, expanded, approved, edited, rejected or dismissed), so that the team can measure whether the review step helps. An event holds only a screen name, an event name, an opaque id, a duration and at most three fixed labels. It never holds anything you typed or any supplier text. Your user is stored only as a keyed hash that cannot be reversed without a server-side key. Nothing is reported per person. The demo build records nothing.

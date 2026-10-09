# Troubleshooting

When the server refuses something, the screen shows the reason in plain words under the button, often with a short hint. This page lists the refusals you are most likely to meet, what they mean and what to do. The wording in italics is what the server says.

## Refusals while preparing or sending messages

| You see | Meaning | What to do |
|---|---|---|
| *vendor not verified: NAME* | The supplier has not been verified. | Ask an admin to verify it on **Suppliers**. |
| *vendor suppressed: NAME* | The supplier asked not to be contacted, or a person blocked it. | An admin can lift it with **Allow contact** on **Suppliers**, if that is right. If **Suppliers** shows no *Suppressed* badge for it, the supplier is marked as opted out in its record. No screen clears that: ask your technical contact (see [Known rough edges](#known-rough-edges-in-this-build)). |
| *vendor … is not a preferred vendor* | The supplier is not marked *preferred*. Suppliers added with the **Add supplier** form are not; suppliers imported from a CSV file are. No screen sets the flag. | Import the supplier from a CSV file instead (known defect). A CSV row for a supplier that is already in the list does not change the flag. |
| *individual subscriber: not enabled* | The supplier is a sole trader or individual. Sending to individuals is switched off in this build. | Nothing yet. |
| *assumptions open: N critical assumption(s) unconfirmed* | A critical assumption on the request is still open. | Open the **Request** step and confirm or reject each one. |
| *business identity incomplete: missing …* | Your company's details that the profile requires are not set. | They are deployment settings, not a screen: ask whoever runs your deployment to set them. **Setup** lists which are missing. |
| *no Tier A/B candidate: engineering review required* | No identical or documented-equivalent part is available to ask for. | A person outside the app has to identify the part. |
| *at most N vendors per request* | You picked more suppliers than the limit (four, or two for a *Machine down* request, by default). | Pick fewer. |
| *cannot send in state …* or *RFQ was already sent* | That message was already sent, or the request has moved on. | Reload the request. |
| *message changed or was never prepared: review the new hash* | The prepared message is no longer the one you looked at. Prepared messages are held in memory by the server process, so a server restart loses them. | Prepare the messages again and read the new text. |
| *send refused: kill_switch* | An admin has switched sending off. | An admin can switch it back on in **Setup**. |
| *send refused: footer_missing* or *identity_missing* | The required AI disclosure or company details are missing from the message. Nothing was sent. | Prepare again. If it repeats, ask an admin. |
| *send refused: hash_mismatch*, *approval_expired*, *nonce_replayed*, *unknown_approval* | The approval did not match the message exactly, was too old, or was already used. Nothing was sent. | Prepare the message again and approve it. |
| *send refused: recipient_limit*, *duplicate_send* | Too many suppliers for the request, or that exact message was already sent. | None needed if it was already sent. |
| *send refused: cap_exceeded* | A per-order or daily spend cap would be passed (this applies to purchase orders). | Caps are set in the deployment profile. Where it sets none, the limits are 5,000 per order and 15,000 per day, in the profile's main currency. |
| *send refused: unsafe_text*, *malformed_message* | The message bytes hold a hidden or control character, or are not a well-formed message. Preparing never builds such text, so this should not happen. | Prepare the message again. If it repeats, report it to your technical contact. |
| *send refused: domain_mismatch*, *recipient_not_vendor*, *vendor_opted_out* | The address does not match the supplier on record, or the supplier opted out. | Check the supplier's details. |
| *send refused: transport_failure* | The mail transport failed. Delivery is unknown, and the approval is used up. | Check with the supplier before you prepare and approve the message again. |

## Refusals while comparing, selecting and approving

| You see | Meaning | What to do |
|---|---|---|
| *quote is excluded (flagged, quarantined or unusable)* or *quote is quarantined or flagged* | The quote failed a check (sender check, instructions in the text, a price not found in the reply, no currency, bank details changed). | Read the flags on the quote. Ask the supplier to send a clean reply, or paste one in if you have it by another route. |
| *quote validity has expired: ask the vendor for a current quote* | The quote is past its valid-until date. | Ask the supplier for a current quote. |
| *quote offers a Tier D part: engineering review required* | The part offered is not an identical or documented-equivalent part. | Ask the supplier to quote a listed part, or get engineering to review. |
| *Tier B is not enabled in this deployment* | Equivalent parts are switched off in the deployment profile. | This is a deployment setting, not a screen. Ask whoever runs your deployment. |
| *quote lacks price, currency or offered part number* | The reply did not state something the purchase order needs. | Ask the supplier. |
| *no eligible approver (approver must differ from requester)* | The quote needs a second person, and every approver set up in your deployment is the person who asked. | The list of approvers is a deployment setting, not a screen. Ask whoever runs your deployment to add an approver, who needs at least the buyer role. The quote is already selected: see [Known rough edges](#known-rough-edges-in-this-build). |
| *cannot select a quote in state …* | The request is not at the step where a quote can be chosen: a quote is already selected, or it has moved on or not got there yet. | Reload the request. After *no eligible approver*, see [Known rough edges](#known-rough-edges-in-this-build). |
| *no approval is pending* | The approval link was already used, or the request moved on. | Reload the request. |
| *insufficient role* after you press **Approve this quote** or **Decline** | You are not the approver this link was issued to, or your role is below buyer. Opening the link only shows the quote and checks neither. | Use the approver's own sign-in. |
| *cap: …* when creating the purchase order draft | A per-order or daily spend cap would be passed, or the quote is in a different currency from the caps (*caps are in GBP, got USD*). | Caps are set in the deployment profile. Where it sets none, the limits are 5,000 per order and 15,000 per day, in the profile's main currency. |
| *cannot draft a PO in state …* | The request is not approved, or no approval was needed and it is not selected. | Select a quote first, and wait for the approval if one is pending. |

## General messages

| You see | Meaning | What to do |
|---|---|---|
| *authentication required* (401) | The sign-in token your deployment gave the app is missing, wrong or has expired. The app has no sign-in screen of its own. | Ask whoever runs your deployment for a new token. |
| *insufficient role* (403) | Your role is too low for that action. The screen normally says which role is needed. | No screen changes a role: it comes from your sign-in token. Ask whoever runs your deployment for a token with the role you need. The demo build has a **Demo role** switcher. |
| *not found* (404) | The request, quote or supplier does not exist in your account. | Check the address. |
| *file too large* (413) | A price file is over 900,000 bytes. The price file form normally catches this first, in the browser, with its own message: *The file is larger than 900 000 bytes.* | Remove rows you do not need, or split the file. |
| *request body too large* (413) | The whole upload is over what the server accepts: 1,000,000 bytes for most requests, including a price file upload, and 5,000,000 bytes for a supplier CSV file. | Send less. |
| *file too large* (409) | A supplier CSV file is over 1,000,000 bytes (the default limit) but within the 5,000,000 byte upload limit. | Split the file. |
| *too many rows (at most 2000)* (409) | A supplier CSV file has more than 2,000 rows. | Split the file. |
| *invalid request: …* (422) | A field has an invalid value. The message names the field, never the value. | Correct the field. |
| *Idempotency-Key reused with a different request* (422) | A retry sent the same key with different content. | Only technical users see this. Reload and repeat the action. |

## Things that look like bugs but are by design

- **A button is greyed out.** On most screens a reason is written next to it. On **Suppliers**, the reason for **Edit**, **Suppress**, **Allow contact** and **Add supplier** is a tooltip that appears when you point at the button, while **Verify** writes it under the supplier's name. It is usually your role, or a step that is not done yet.
- **A reply is shown but cannot be selected.** It is quarantined. Read why on its card.
- **A supplier cannot be picked.** It is not verified, suppressed, or a sole trader. The reason is shown.
- **The comparison leaves a supplier out.** The first sentence of **Compared like for like** says which one and why.
- **A quote is flagged *VAT basis not stated: approval needed*.** The app does not guess a VAT basis. The quote is still compared, but it ranks below a clean quote of the same tier, and choosing it needs a second person's approval. In a price file, a row with an unreadable VAT basis is quarantined instead. (A deployment profile can instead assume its default basis and flag it *VAT basis assumed*.)
- **Nothing arrives after approving a message.** In this build, messages go to a recording transport. No real email is sent.
- **The approver never got the link.** In this build links are not delivered by email.
- **A declined request has no next step.** A decline ends the request in this build. Start a new one.

## Known rough edges in this build

- A request in **Needs engineering review** that has no open critical assumption has no NEXT bar and is not listed on **Home**. Its page opens on the locked **Purchase order** step and shows a card that reads *The purchase order draft exists. Export it from the Purchase order step.*, although no draft exists. If critical assumptions are still open, the NEXT bar reads *Confirm N assumptions* and **Home** lists the request. The request is always listed under **Requests**, and nothing in the app can move it on.
- The request page's back link says **← Inbox**, but the screen it returns to is called **Home**.
- The **Add supplier** button is enabled for buyers although only an admin can add a supplier, and a supplier added with it cannot be asked for a quote (it is not marked *preferred*).
- A supplier that is marked as opted out in its record (only the API can set this) is refused with *vendor suppressed*, shows no *Suppressed* badge on **Suppliers**, and cannot be switched back on from any screen. **Allow contact** only reverses *Suppressed*.
- When the app is connected to its server and **Select** is refused with *no eligible approver*, the request has already moved to *Quote selected*. No approval link exists, **Select** is no longer offered, the NEXT bar says *Create the purchase order* but that step stays locked, and nothing in the app moves the request on. Make sure your deployment lists an approver other than the person who asked before you select.
- When the app is connected to its server, the comparison can list an expired quote (its *valid until* date had already passed when the reply was read) with the flag *validity expired*, show it as **Recommended**, and offer **Select**. Pressing **Select** is refused with *quote validity has expired: ask the vendor for a current quote*, and no hint appears under the button. Check the flags before you select.
- On **Setup**, the sending-domain item (*Sending domain checked* in the demo build, *Sending domain authentication* when the app is connected to its server) always shows *Your turn*. Nothing in the app marks it done, and it does not stop **Record as live**. It is a reminder to check your sending domain's email authentication (SPF, DKIM and DMARC) yourself.
- Some server-generated sentences still say *indicative* where the screens say *rough*.
- When the app is connected to its server, the **Quote** and **Supplier prices** pages build a quote for the job type from the template's sample sizes and defaults each time they open. The sizes and answers you entered in the job wizard do not reach them, and **Build the quote** in the wizard creates a separate quote that no page opens.
- In the job wizard's **Advanced: request data** panel, the text *there is no API endpoint yet that takes a kit* is out of date; it is the creation of a request from the kit's lines that is missing.

## Still stuck

Technical staff can look at the [activity trail](04-suppliers-setup-activity.md#activity) for the exact sequence of events on a request, and at the [technical documentation](../technical/README.md).

# Troubleshooting

When the server refuses something, the screen shows the reason in plain words under the button, often with a short hint. This page lists the refusals you are most likely to meet, what they mean and what to do. The wording in italics is what the server says.

## Refusals while preparing or sending messages

| You see | Meaning | What to do |
|---|---|---|
| *vendor not verified: NAME* | The supplier has not been verified. | Ask an admin to verify it on **Suppliers**. |
| *vendor suppressed: NAME* | The supplier asked not to be contacted, or was blocked. | An admin can lift it with **Allow contact**, if that is right. |
| *individual subscriber: not enabled* | The supplier is a sole trader or individual. Sending to individuals is switched off in this build. | Nothing yet. |
| *assumptions open: N critical assumption(s) unconfirmed* | A critical assumption on the request is still open. | Open the **Request** step and confirm or reject each one. |
| *business identity incomplete: missing …* | Your company's details that the profile requires are not set. | An admin must complete them. They are deployment settings, not a screen. |
| *no Tier A/B candidate: engineering review required* | No identical or documented-equivalent part is available to ask for. | A person outside the app has to identify the part. |
| *at most N vendors per request* | You picked more suppliers than the limit (four, or two for a *Machine down* request, by default). | Pick fewer. |
| *cannot send in state …* or *RFQ was already sent* | That message was already sent, or the request has moved on. | Reload the request. |
| *message changed or was never prepared: review the new hash* | The prepared message is no longer the one you looked at. Prepared messages are held in memory by the server process, so a server restart loses them. | Prepare the messages again and read the new text. |
| *send refused: kill_switch* | An admin has switched sending off. | An admin can switch it back on in **Setup**. |
| *send refused: footer_missing* or *identity_missing* | The required AI disclosure or company details are missing from the message. Nothing was sent. | Prepare again. If it repeats, ask an admin. |
| *send refused: hash_mismatch*, *approval_expired*, *nonce_replayed*, *unknown_approval* | The approval did not match the message exactly, was too old, or was already used. Nothing was sent. | Prepare the message again and approve it. |
| *send refused: recipient_limit*, *duplicate_send* | Too many suppliers for the request, or that exact message was already sent. | None needed if it was already sent. |
| *send refused: cap_exceeded* | A per-order or daily spend cap would be passed (this applies to purchase orders). | See your caps in your deployment profile. |
| *send refused: unsafe_text*, *malformed_message* | The message bytes hold a hidden or control character, or are not a well-formed message. Preparing never builds such text, so this should not happen. | Prepare the message again. If it repeats, report it to your technical contact. |
| *send refused: domain_mismatch*, *recipient_not_vendor*, *vendor_opted_out* | The address does not match the supplier on record, or the supplier opted out. | Check the supplier's details. |
| *send refused: transport_failure* | The mail transport failed. Delivery is unknown, and the approval is used up. | Check with the supplier before you prepare and approve the message again. |

## Refusals while comparing, selecting and approving

| You see | Meaning | What to do |
|---|---|---|
| *quote is excluded (flagged, quarantined or unusable)* or *quote is quarantined or flagged* | The quote failed a check (sender check, instructions in the text, a price not found in the reply, no currency, bank details changed). | Read the flags on the quote. Ask the supplier to send a clean reply, or paste one in if you have it by another route. |
| *quote validity has expired: ask the vendor for a current quote* | The quote is past its valid-until date. | Ask the supplier for a current quote. |
| *quote offers a Tier D part: engineering review required* | The part offered is not an identical or documented-equivalent part. | Ask the supplier to quote a listed part, or get engineering to review. |
| *Tier B is not enabled in this deployment* | Equivalent parts are switched off in the deployment profile. | Ask an admin. |
| *quote lacks price, currency or offered part number* | The reply did not state something the purchase order needs. | Ask the supplier. |
| *no eligible approver (approver must differ from requester)* | The quote needs a second person, and every configured approver is the requester. | Ask a colleague with the buyer role to be an approver. |
| *no approval is pending* | The approval link was already used, or the request moved on. | Reload the request. |
| A *403 forbidden* when opening an approval link | You are not the approver the link was issued to, or your role is below buyer. | Use the approver's own sign-in. |
| *cap: …* when creating the purchase order draft | A per-order or daily spend cap would be passed. | See your caps in your deployment profile. |
| *cannot draft a PO in state …* | The request is not approved, or no approval was needed and it is not selected. | Select a quote first, and wait for the approval if one is pending. |

## General messages

| You see | Meaning | What to do |
|---|---|---|
| *authentication required* (401) | Your sign-in is missing or has expired. | Sign in again. |
| *insufficient role* (403) | Your role is too low for that action. The screen normally says which role is needed. | Ask an admin to change your role. |
| *not found* (404) | The request, quote or supplier does not exist in your account. | Check the address. |
| *request body too large* (413) | The request or file is too big. | Price files can be up to 900,000 bytes. |
| *file too large* (409) | A supplier CSV file is over the size limit (about 1 MB by default). | Split the file. |
| *invalid request: …* (422) | A field has an invalid value. The message names the field, never the value. | Correct the field. |
| *Idempotency-Key reused with a different request* (422) | A retry sent the same key with different content. | Only technical users see this. Reload and repeat the action. |

## Things that look like bugs but are by design

- **A button is greyed out.** A reason is shown next to it. It is usually your role, or a step that is not done yet.
- **A reply is shown but cannot be selected.** It is quarantined. Read why on its card.
- **A supplier cannot be picked.** It is not verified, suppressed, or a sole trader. The reason is shown.
- **The comparison leaves a supplier out.** The first sentence of **Compared like for like** says which one and why.
- **A price is flagged *VAT basis not stated* rather than compared.** The app never guesses a VAT basis.
- **Nothing arrives after approving a message.** In this build, messages go to a recording transport. No real email is sent.
- **The approver never got the link.** In this build links are not delivered by email.
- **A declined request has no next step.** A decline ends the request in this build. Start a new one.

## Known rough edges in this build

- A request in **Needs engineering review** shows *Done* in the NEXT bar and is not listed on **Home**. It is still under **Requests**, and nothing in the app can move it on.
- The request page's back link says **← Inbox**, but the screen it returns to is called **Home**.
- The **Add supplier** button is enabled for buyers although only an admin can add a supplier.
- Some server-generated sentences still say *indicative* where the screens say *rough*.

## Still stuck

Technical staff can look at the [activity trail](04-suppliers-setup-activity.md#activity) for the exact sequence of events on a request, and at the [technical documentation](../technical/README.md).

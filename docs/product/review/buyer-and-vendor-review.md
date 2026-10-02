# Buyer and Distributor Review (role-play, 2026-10-02)

Voices: skeptical maintenance supervisor/buyer (200-person plant); cynical distributor inside-sales rep. Read only 01, 04, 07. Six web checks found no public RFQs-per-plant data; numbers are my judgement.

## 1. Would I use it?
For the 3-4 ugly buys a month, maybe. At $600, no. Today I call Dave at the bearing house, text the seal guy, email the OEM: ten minutes, not "days." My pain is parts nobody can identify or stock.

**I quit in week 1 if:**
- A request takes more touches than a call (questions, approve RFQ, approve quote).
- Dave asks "who is this?"
- One Tier 2 call is wrong on a line-down part.
- It needs IT to grant mailbox OAuth.
- It can't see my CMMS, so I retype everything.

## 2. Ten reasons buyers ignore it, and the fix
1. **Urgency:** line down, I phone. *Fix:* "Down now" mode: one-tap spec, send to top 2 vendors, plus a text script.
2. **Workflow:** two approvals plus PO. *Fix:* human pre-authorises standing rules (vendor, family, $ band); amends Hard Rule 1.
3. **Trust:** wrong-part fear. *Fix:* Tier 1 only at launch; Tier 2 after 50 buyer-confirmed matches.
4. **Data:** my parts live in CMMS/Excel. *Fix:* day-1 import of parts, assets, 12 months of POs; show "last bought from X at $Y."
5. **Data:** real non-catalog parts are OEM-specific or obsolete, not bearings. *Fix:* beachhead becomes nameplate-to-source, human-assisted.
6. **Price:** $600 against ~4 buys. *Fix:* $15-25 per completed RFQ, first 10 free.
7. **Who does the work:** I answer questions and fix errors. *Fix:* pilot as a service; operator specs, technician asked directly.
8. **Approvals:** I self-approve to ~$2.5k; above that it's paper/ERP. *Fix:* optional approvals; one-page PDF into their flow.
9. **Vendor relationships:** bot mail burns goodwill. *Fix:* send as me, short, in the rep's preferred channel; per-vendor opt-out.
10. **IT friction:** *Fix:* forwarding alias with Reply-To to the buyer; no mailbox access.

## 3. Distributor rep's view
**Would I answer?** Yes if it has an account number, part number or nameplate photo, quantity, ship-to, and a human I can call. Reps live on speed (a vendor blog claims 78% of buyers pick the first responder; marketing), so clean, known-account asks go first.

**Ignore or deprioritise:** no account number; identical blast to five competitors for a $40 item; robot nagging at 4h and 24h; a 10-field form for a $60 sale; "sent by an assistant" with nobody to call.

**Blacklist:** many RFQs, no POs; my price shown beside Grainger's then silence; a reply-time scorecard (F6) shown to customers; blame for a wrong substitution.

**Love:** complete specs, "won/lost and why" in 24h, a PO matching my quote, a shortlist of 2 not 6, a real phone number. Distributors already run AI quote desks (Hexa, Proton); clean structured data is your only value.

## 4. Frequency check
No public figure found. Plant of ~200, ~$0.5-2M/yr MRO: 80-90% of lines are stock, min/max or portal reorders. "No part number" buys: perhaps 8-20/month; those where I'd ask 2+ vendors: **2-6/month**.

At 4 RFQs, $600 is $150 each. My value: ~30 min ($25) plus 5-8% of a ~$700 ticket ($35-55), roughly $60-80. It fails below 8-10/month unless tickets average $2-3k. A3's 10/month bar is right; I expect the median under it, and the kill trigger (<4) will likely fire.

**I'd need to see:** 90 days of sent mail and POs tagged (non-catalog count, multi-vendor count, elapsed days, quote spread, wrong/late parts); three plants above 5 qualifying RFQs/month paying for a pilot.

## 5. Eight interview questions
1. Walk me through the last part you couldn't order from a catalog or storeroom, breakdown to shelf.
2. Open your last 90 days of POs: how many buys were non-catalog, and in how many did you ask more than one supplier? Show me.
3. Last time you asked several vendors: who, which channel, how long, what then?
4. Your last wrong or late part: who caught it, what did it cost?
5. Who signs at $500, $2,500, $10,000? When did someone last say no?
6. What do you pay today, in money or favours, to get this done?
7. Last tool you tried: what happened at day 30, who paid, who killed it?
8. Which vendor replies fastest, and what do they know about you that makes them do it?

## 6. Spec: unnecessary and missing
**Unnecessary now:** authorised flag on every quote (exception-only); five-role model; audit hashes in the UI; buyer-facing vendor scorecards; default auto follow-ups; ranking weights for 2-3 quotes; SOC 2 as MVP gate.

**Missing:** CMMS/PO import (R2 today; make it day 1); phone/SMS (rep scripts, logging phone quotes); technician nameplate-photo intake; repair/rebuild vs replace and obsolete sourcing; same-day will-call stock check; contract-price and buying-group awareness; a verified-sender page for reps.

**Doc claims that contradict real buying:**
- Canvas Problem 1, quote loops take "days": with a known rep it's minutes; the pain is identification.
- Bearings as the "deterministic" beachhead: most stocked family; reps cross-reference free.
- "Approved vendors": plants have preferred reps, not formal lists; real non-catalog buying goes outside them.
- Email-native, when 07 (T8) says phone dominates.
- Wrong-part as top pain: evidence is HVAC and Grainger Trustpilot, not plant maintenance.
- "Distributors buying agentic AI validates demand": it validates supply-side tooling, not buyer demand.
- Quote-to-approval ≤4h as a win: urgent buys already close faster by phone.


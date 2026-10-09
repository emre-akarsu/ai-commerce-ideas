# Rented-home repairs pack

For landlords and letting agents in England. A tenant's report becomes a triaged job, competing contractor quotes (one for an emergency), an approval and an award. The run's hash-chained events are the record of when each step happened, for a council or the landlord ombudsman.

| Step | What happens | Module |
|---|---|---|
| intake | Report text, date reported, trade, the landlord's contractors | `repair-intake` |
| scope | Keyword rules set the class (emergency, urgent, routine) and keep the matched word as evidence; the class sets the number of quotes and a fix-by date in working days on the profile's bank-holiday calendar | `repair-triage` |
| packets, parse, compare | Reused refurb modules | `refurb-packets`, `refurb-quote-parser`, `refurb-compare` |
| approvals | Landlord or agent sends; above the job amount in `distinct_from_requester_over` someone other than the requester awards | kernel |

Classes, targets and keywords are the landlord's policy in `pack.yaml`, not legal duties: Renters' Rights Act duties and any Awaab's Law extension to private rentals were not dated when this was written. Demo data in `employees/repairs/demo.py` is synthetic. Not built: emergency dispatch without a quote, photos, tenant notifications.

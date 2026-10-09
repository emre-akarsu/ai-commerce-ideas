# Parish council quotes pack

For parish and town councils buying below their tender point. The council's financial regulations (pack settings, `quote_tiers`) decide how many quotes a purchase needs; the clerk or RFO approves the RFQs; a quorum of councillors awards by resolution.

| Step | What happens | Module |
|---|---|---|
| intake | The need, estimate inc VAT, remaining budget ex VAT, suppliers | `parish-intake` |
| scope | Quotes required by tier; stops above the tender point (formal tender and Contracts Finder are out of scope), when there are too few suppliers, or when the estimate is over budget | `parish-financial-regs` |
| packets, parse, compare | Reused refurb modules; councils recover VAT so quotes are compared ex VAT | `refurb-packets`, `refurb-quote-parser`, `refurb-compare` |
| award | Quorum of councillors (3 by default; a deployment may set 2 to 15, never 0) | kernel |

Defaults follow the shape of the NALC model financial regulations; each council's own regulations win and go in its deployment. Not legal advice. Demo data in `employees/parish/demo.py` is synthetic. Not built: AGAR audit pack export, minute text for the resolution.

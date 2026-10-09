# Landlord EPC C retrofit pack

For private landlords and letting agents in England whose rented homes must reach EPC band C by 1 October 2030. Values come from the government's 2025 consultation and response; confirm them against the final regulations before go-live. Not legal advice.

| Step | What happens | Module |
|---|---|---|
| intake | Reads the EPC as data: current SAP score and the recommended measures with indicative cost and gain | `epc-intake` |
| scope | Picks the best gain per pound until the target band is reached, within the cap minus spend already made; excludes installers missing a scheme a measure needs (MCS for solar and heat pumps, TrustMark otherwise); flags the exemption route if the cap runs out first | `epc-retrofit-planner` |
| packets | One like-for-like RFQ per eligible installer, asking for line prices, VAT rate and scheme numbers | `epc-installer-packets` |
| approve_send | Landlord or agent approves the exact messages | kernel |
| send, replies | Send-service port; installer replies arrive as untrusted data | kernel |
| parse, compare | Reused refurb parser and comparison; zero-rated energy-saving works read as "no VAT" | `refurb-quote-parser`, `refurb-compare` |
| award | Only the landlord can award | kernel |

Try it: `python -m aiplat.compose show deployments/epc-retrofit-demo.yaml`; the run is in `tests/compose/test_retrofit.py`. Demo data (`employees/retrofit/demo.py`) is synthetic.

Not built: reading an EPC PDF or the EPC register, the evidence export for an exemption claim, and grant checks (Boiler Upgrade Scheme).

"""Synthetic demo for the EPC retrofit pack. Property, installers, scores, costs and replies are
INVENTED for illustration; they are not market data and not a real EPC."""

from __future__ import annotations

REQUEST = {
    "requester": "lee",
    "property": {"id": "P-221", "address": "22 Example Terrace, Sheffield S7 1AA"},
    "epc": {
        "certificate": "SYNTHETIC-0000-0000-0000-0000",
        "current_score": 52,  # band E
        "recommendations": [
            {"measure": "loft_insulation", "label": "Increase loft insulation to 270 mm",
             "points": 3, "cost_low": "300", "cost_high": "600"},
            {"measure": "cavity_wall_insulation", "label": "Cavity wall insulation",
             "points": 5, "cost_low": "500", "cost_high": "1500"},
            {"measure": "heating_controls", "label": "Heating controls (room thermostat and TRVs)",
             "points": 2, "cost_low": "350", "cost_high": "450"},
            {"measure": "low_energy_lighting", "label": "Low energy lighting",
             "points": 1, "cost_low": "20", "cost_high": "40"},
            {"measure": "solar_pv", "label": "Solar photovoltaic panels, 2.5 kWp",
             "points": 8, "cost_low": "3500", "cost_high": "5500"},
            {"measure": "air_source_heat_pump", "label": "Air source heat pump",
             "points": 6, "cost_low": "8000", "cost_high": "12000"},
        ],
    },
    "prior_qualifying_spend": "0",
    "needed_by": "2027-03-31",
    "reply_by": "2026-11-06",
    "installers": [
        {"id": "dale-eco", "name": "Dale Eco Installs Ltd", "contact": "quotes@daleeco.example",
         "certs": ["TrustMark", "MCS"]},
        {"id": "peak-retrofit", "name": "Peak Retrofit Co", "contact": "hello@peakretrofit.example",
         "certs": ["TrustMark", "MCS"]},
        {"id": "loftco", "name": "LoftCo Insulation", "contact": "office@loftco.example",
         "certs": ["TrustMark"]},
        {"id": "sun-only", "name": "Sun Only Solar", "contact": "sales@sunonly.example",
         "certs": ["MCS"]},
    ],
}

# (installer, channel, received, text)
REPLIES = [
    ("dale-eco", "email", "2026-11-02", """Hi Lee,

Thanks for the RFQ. Our price for the works:

- Low energy lighting: £35.00
- Loft insulation to 270 mm: £480.00
- Cavity wall insulation: £1,050.00
- Heating controls: £410.00
- Solar PV 2.5 kWp: £4,600.00
Total £6,575.00 no VAT (zero-rated energy-saving materials)

TrustMark 1234567, MCS NAP-00000. We can start in 3 weeks. Quote valid for 60 days.
Payment terms: 30 days from completion.

Dale"""),
    ("peak-retrofit", "pdf", "2026-11-04", """PEAK RETROFIT CO - QUOTATION PR-881

Low energy lighting                          £40.00
Loft insulation 270 mm                       £520.00
Cavity wall insulation                       £1,240.00
Heating controls                             £395.00
Solar PV 2.5 kWp                             £5,150.00
Total £7,345.00 no VAT (energy-saving materials, zero rate)

Lead time 4 weeks. Valid for 30 days. Payment terms: 50% deposit, balance on completion.
MCS and TrustMark registered."""),
]

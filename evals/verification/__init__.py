"""Seeded-error evaluation of the quote safety net (spec F28 clauses 6 to 8, section 8 item 9).

Synthetic quotes with a known answer and errors of seven types injected into them are run through
the purchasing service exactly as a vendor reply is (grounding, normalisation, the second reader,
the verification layer). The harness reports which injected errors left the quote wrong without a
flag, which checks caught the rest, and how often a clean quote is flagged anyway.

SYNTHETIC: this measures the mechanisms on generated text, not real vendors or a real model.
"""

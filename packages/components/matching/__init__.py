"""Product matching engine: free-text order lines to catalogue SKUs (spec 07, matching engine v2).

Pure Python, offline, Decimal. The LLM proposes and ranks; deterministic attribute checks and a
deterministic gate decide; a person approves anything uncertain. See
docs/architecture/matching-engine.md.
"""

"""Review telemetry (spec M0): content-free review events, seeded-defect drills, pooled summaries.

`components.telemetry.store` holds the records, the validation, the metric definitions and the
in-memory store. The Postgres store (`aidb.telemetry`) satisfies the same Protocols. Pure Python,
no I/O; nothing here is grouped by reviewer, and no free text is stored.
"""

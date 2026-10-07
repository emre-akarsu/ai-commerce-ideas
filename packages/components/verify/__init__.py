"""Verification layer (docs/product/12-next-version-improvement-triage.md, item 9).

Checks that only ADD findings: they can raise a flag or send a line to review, and they can
never approve, pick between two readings, fill a blank field or change an amount, recipient or
rule (hard rules R1, R3, R5, R6). Pure Python, offline, Decimal only. Components never import
aiplat or employees: callers build `VerifyConfig` from the resolved profile.
"""

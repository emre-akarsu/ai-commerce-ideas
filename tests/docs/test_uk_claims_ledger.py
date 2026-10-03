"""The UK docs cite claim IDs; the ledger must define every ID they cite (no dangling references)."""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs" / "uk"
LEDGER = DOCS / "03-claims-ledger.md"
ID = re.compile(r"\bUK-[A-Z]{3}-\d{2}\b")
ROW = re.compile(r"^\| (UK-[A-Z]{3}-\d{2}) \| (.+?) \| ([VPSXUA](?:/[VPSXUA])*)(?: [^|]*)? \|", re.MULTILINE)
AREAS = {"POP", "SPD", "SUP", "ACC", "CMP", "DPL", "CTL", "PSL", "IPL", "PRT", "VOC", "FND"}


def _ledger_rows() -> list[tuple[str, str, str]]:
    return ROW.findall(LEDGER.read_text(encoding="utf-8"))


def test_ledger_ids_are_unique_and_well_formed() -> None:
    ids = [r[0] for r in _ledger_rows()]
    assert len(ids) >= 80, "ledger looks truncated"
    assert len(ids) == len(set(ids)), "duplicate claim id"
    assert {i.split("-")[1] for i in ids} == AREAS


def test_every_row_has_a_claim_and_a_known_status() -> None:
    for claim_id, claim, status in _ledger_rows():
        assert len(claim) > 20, f"{claim_id} has no real claim text"
        assert set(status.split("/")) <= set("VPSXUA"), f"{claim_id} status {status!r}"


def test_cited_ids_exist_in_the_ledger() -> None:
    defined = {r[0] for r in _ledger_rows()}
    missing: dict[str, set[str]] = {}
    for doc in sorted(DOCS.glob("*.md")):
        if doc == LEDGER:
            continue
        for cited in set(ID.findall(doc.read_text(encoding="utf-8"))):
            if cited not in defined:
                missing.setdefault(doc.name, set()).add(cited)
    assert not missing, f"cited but not defined in the ledger: {missing}"


def test_no_unfilled_placeholders_in_uk_docs() -> None:
    for doc in sorted(DOCS.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        assert "{{" not in text and "TODO" not in text, f"{doc.name} has an unfilled placeholder"

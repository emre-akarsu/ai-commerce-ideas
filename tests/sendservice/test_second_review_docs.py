"""Second review: the documentation says what the code does (findings F1, F9 and the notes that go with the fixes).

These are small, deliberate checks on a few stable phrases, in the style of the other documentation tests of
this repository, so that a claim the review took out of the docs cannot creep back in.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def doc(name: str) -> str:
    """A document with its whitespace collapsed, so a phrase still matches after the text is re-wrapped."""
    return " ".join((ROOT / "docs/architecture" / name).read_text(encoding="utf-8").split())


def section(name: str, heading: str) -> str:
    """The text of a document from ``heading`` to the next heading of the same or a higher level
    (lines inside a fenced code block are never headings), whitespace collapsed."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = (ROOT / "docs/architecture" / name).read_text(encoding="utf-8").split("\n")
    start = lines.index(heading)
    taken: list[str] = []
    fenced = False
    for line in lines[start + 1:]:
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("#") and len(line) - len(line.lstrip("#")) <= level:
            break
        taken.append(line)
    return " ".join(" ".join(taken).split())


# ---------------------------------------------------------------- F9: what the sanitiser really guarantees


def test_configurability_no_longer_claims_nothing_can_show_a_second_footer() -> None:
    text = doc("configurability.md")
    assert "nothing can show a second footer" not in text
    assert "or a conflicting \"Registered in\" line ahead of the real one" not in text


def test_configurability_says_what_is_guaranteed_and_what_is_free_text() -> None:
    text = doc("configurability.md")
    assert "cannot hide the real footer" in text
    assert "line break that only some readers see" in text
    assert "free text from the requester" in text  # the body may carry `--`, footer text and label-like lines
    assert "on purpose" in text
    assert "tests/sendservice/test_line_sanitiser.py" in text  # where the accepted look-alikes are pinned


def test_configurability_describes_the_new_send_time_and_prepare_checks() -> None:
    text = doc("configurability.md")
    assert "unsafe_text" in text  # the send-time re-check has a stable code
    assert "reads back" in text  # prepare parses its own bytes
    assert "recipient limit" in text and "disclosure_footer" in text  # the wiring check compares both
    assert "ReadOnlyMap" in text  # and the copies are picklable


# ---------------------------------------------------------------- F1: sender facts are deployment-wide


def test_known_gaps_records_that_sender_facts_are_deployment_wide() -> None:
    part = section("known-gaps.md", "## Sender facts are deployment-wide")
    for needle in ("buyer_names", "buyer_phone", "alias_address", "reply_to_domain",
                   "Settings(buyer_names={\"buyer-1\": \"Pat Acme-Buyer\"})", "tenant-2", "only a purchase order from Pat Acme-Buyer binds",
                   "buyer-1@", "CLAUDE.md", "rule 7", "R10", "(tenant_id, user_id)", "TenantIdentities",
                   "Reply-To", "local part"):
        assert needle in part, needle
    assert "single-tenant" in part  # why it is not reachable in the shipped slice


def test_known_gaps_keeps_the_three_identity_notes() -> None:
    part = section("known-gaps.md", "## Business identity (company particulars) gaps")
    assert "link-like" in part and "at `prepare` only" in part
    assert "U+0092" in part and "cp1252" in part and "409" in part
    assert "SendService.identity_provider" in part and "identity_for" in part and "any tenant" in part


def test_known_gaps_names_the_wiring_check_and_the_dry_run() -> None:
    part = section("known-gaps.md", "## Business identity (company particulars) gaps")
    assert "footer" in part and "recipient limit" in part  # PurchasingService compares them with the profile


def test_the_api_contract_lists_the_new_refusals() -> None:
    text = doc("api-contract.md")
    assert "unsafe_text" in text
    assert "zero-width" in text  # `site` refuses hidden characters too
    assert "read back" in text  # a sender name that cannot be read back is a 409 at prepare


def test_the_worker_readme_mentions_what_the_pack_now_compares() -> None:
    readme = (ROOT / "apps/worker/README.md").read_text(encoding="utf-8")
    assert "footer" in readme and "recipient limit" in readme and "comms.max_vendors" in readme
    assert "SendService.from_profile" in readme and "send_service_factory" in readme

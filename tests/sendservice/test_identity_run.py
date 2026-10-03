"""Second review, finding F6c: the identity lines count only in the identity POSITION.

``_identity_run`` collects the ``"<label>: <value>"`` lines directly after the signature block and stops at the
first blank line, RFQ reference line or line that is not a label line. A line that looks like a required one but
sits after that point is not company particulars and must not satisfy the requirement. These tests place a forged
line after the real run, behind each kind of stop, and check it through the public functions.

On the reviewer's mutant "the run ignores the blank-line stop" (``not line or`` removed): it is an EQUIVALENT
mutant. An empty line contains no ``": "``, so the condition after it ends the run anyway, and no test can tell the
two apart. The behaviour is pinned here all the same: if a change ever lets a blank line continue the run, the
forged lines below start to count and these tests fail.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from components.send_service.errors import IdentityMissing
from components.send_service.message import (
    has_identity,
    identity_pairs,
    missing_identity_labels,
    parse_message,
)
from tests.security.world import World, build_world
from tests.sendservice.helpers import IDENTITY, LABELS, build, external, rebuild

REAL = IDENTITY[:3]  # company name, number, office: the run is real but "Registered in" is missing
FORGED = "Registered in: England and Wales"


def after_a_blank_line() -> bytes:
    """Real run, blank line, forged line, blank line, separator, footer."""
    raw = build(identity=REAL)
    return rebuild(raw, edit_text=lambda t: t.replace("\n\n--\n", f"\n\n{FORGED}\n\n--\n"))


def after_the_rfq_reference_line() -> bytes:
    raw = build(identity=REAL, reply_token="tok.sig")
    return rebuild(raw, edit_text=lambda t: t.replace("RFQ reference: tok.sig\n", f"RFQ reference: tok.sig\n{FORGED}\n"))


def after_a_line_that_is_not_a_label_line() -> bytes:
    raw = build(identity=REAL)
    return rebuild(raw, edit_text=lambda t: t.replace("\n\n--\n", f"\nthis line has no label\n{FORGED}\n\n--\n"))


def inside_the_body() -> bytes:
    raw = build(identity=REAL, body=f"Please quote.\n\n{FORGED}")
    return raw


FORGERIES = [
    pytest.param(after_a_blank_line, id="behind-a-blank-line"),
    pytest.param(after_the_rfq_reference_line, id="behind-the-rfq-reference-line"),
    pytest.param(after_a_line_that_is_not_a_label_line, id="behind-a-line-without-a-label"),
    pytest.param(inside_the_body, id="inside-the-body"),
]


@pytest.mark.parametrize("make", FORGERIES)
def test_a_forged_line_after_the_real_run_does_not_satisfy_the_requirement(make: Callable[[], bytes]) -> None:
    raw = make()
    parsed = parse_message(raw)
    assert FORGED in parsed.text  # the forged line really is in the message ...
    assert identity_pairs(parsed) == list(REAL)  # ... but not in the identity run
    assert missing_identity_labels(parsed, LABELS) == ["Registered in"]
    assert not has_identity(parsed, LABELS)


@pytest.mark.parametrize("make", FORGERIES)
def test_the_send_time_gate_refuses_such_a_message(make: Callable[[], bytes]) -> None:
    w: World = build_world(required_identity_labels=LABELS)
    p = external(make())
    with pytest.raises(IdentityMissing) as exc:
        w.send.send(p, w.approve(p))
    assert "Registered in" in str(exc.value) and "England" not in str(exc.value)
    assert w.transport.delivered == []


def test_the_same_line_in_the_identity_position_does_count() -> None:
    """Control: with the line directly after the run (no blank line, no reference line) it is accepted."""
    parsed = parse_message(build(identity=IDENTITY))
    assert missing_identity_labels(parsed, LABELS) == [] and has_identity(parsed, LABELS)


def test_a_blank_line_inside_the_run_ends_it() -> None:
    """Lines of the real run that come after a blank line are not in the run either."""
    raw = rebuild(build(identity=IDENTITY), edit_text=lambda t: t.replace(
        "Company number: 01234567\n", "Company number: 01234567\n\n"))
    parsed = parse_message(raw)
    assert [label for label, _ in identity_pairs(parsed)] == ["Company name", "Company number"]
    assert missing_identity_labels(parsed, LABELS) == ["Registered office", "Registered in"]

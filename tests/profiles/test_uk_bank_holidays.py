"""UK bank holidays come from GOV.UK (primary source), differ by nation, and drive working-day lead times."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from aiplat.profile import PROFILES_DIR, load_profile
from components.core.domain import Tier
from components.rfq.quotes.extractors import RegexQuoteExtractor
from components.rfq.quotes.grounding import ground
from components.rfq.quotes.normalise import normalise_quote, working_days_to_calendar

SNAPSHOT = PROFILES_DIR / "data" / "gov-uk-bank-holidays.json"
RANGE = ("2026-01-01", "2028-12-31")
DIVISIONS = {"uk": "england-and-wales", "uk-scotland": "scotland", "uk-ni": "northern-ireland"}


def snapshot_events(division: str) -> list[dict[str, str]]:
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return [e for e in data[division]["events"] if RANGE[0] <= e["date"] <= RANGE[1]]


def snapshot_dates(division: str) -> list[date]:
    return sorted(date.fromisoformat(e["date"]) for e in snapshot_events(division))


def independent_calendar_days(n: int, start: date, holidays: set[date]) -> int:
    """Re-implementation used only to cross-check the production helper."""
    day, counted = start, 0
    while counted < n:
        day += timedelta(days=1)
        if day.weekday() < 5 and day not in holidays:
            counted += 1
    return (day - start).days


@pytest.mark.parametrize(("pid", "division"), DIVISIONS.items())
def test_profile_holidays_equal_the_govuk_snapshot(pid: str, division: str) -> None:
    holidays = load_profile(pid).profile.locale.holidays
    assert list(holidays) == snapshot_dates(division)
    assert list(holidays) == sorted(set(holidays))
    assert holidays, "holiday list must not be empty"


def test_nations_actually_differ() -> None:
    ew, sc, ni = (set(snapshot_dates(d)) for d in DIVISIONS.values())
    assert date(2027, 1, 4) in sc and date(2027, 1, 4) not in ew  # substitute 2nd January (Scotland)
    assert any("Patrick" in e["title"] for e in snapshot_events("northern-ireland"))
    assert ni != ew and sc != ew


def test_regional_profiles_inherit_everything_else_from_uk() -> None:
    from aiplat.profile import diff

    base = load_profile("uk")
    for pid in ("uk-scotland", "uk-ni"):
        changed = set(diff(base, load_profile(pid)))
        assert changed <= {"description", "extends", "legal.jurisdiction", "legal.notices", "locale.holidays"}
        assert "legal.disclosure_footer" not in changed
        assert load_profile(pid).profile.legal.jurisdiction.endswith("(UK)")


@pytest.mark.parametrize(
    ("pid", "start", "n", "expected"),
    [
        ("uk", date(2026, 12, 21), 5, 9),  # Christmas Day (Fri) and substitute Boxing Day (Mon 28 Dec) skipped
        ("uk", date(2026, 12, 30), 2, 5),  # 1 Jan holiday: Thu 31 (1), Mon 4 Jan (2)
        ("uk-scotland", date(2026, 12, 30), 2, 6),  # Scotland also has Mon 4 Jan 2027: Tue 5 Jan (2)
        ("uk-ni", date(2026, 12, 30), 2, 5),
        ("uk", date(2026, 10, 9), 2, 4),  # Friday start, no holidays: Mon, Tue
    ],
)
def test_working_days_use_the_profile_calendar(pid: str, start: date, n: int, expected: int) -> None:
    loc = load_profile(pid).profile.locale
    got = working_days_to_calendar(n, start, loc.working_week, loc.holidays)
    assert got == expected
    assert got == independent_calendar_days(n, start, set(loc.holidays))


@pytest.mark.parametrize(("pid", "expected"), [("uk", 5), ("uk-scotland", 6)])
def test_quote_lead_time_end_to_end_respects_regional_holidays(pid: str, expected: int) -> None:
    text = "Price: £4.20 each + VAT. Lead time 2 working days. New"
    g = ground(RegexQuoteExtractor().extract(text), text)
    q = normalise_quote(
        g.extracted, quote_id="q", tenant_id="t", rfq_id="r", vendor_id="v", offered_tier=Tier.A,
        dmarc_aligned=True, grounding_flags=g.flags, snippets=g.snippets,
        profile=load_profile(pid), received_on=date(2026, 12, 30),
    )
    assert q.lead_time_days == expected
    assert str(q.unit_price_each) == "4.20"

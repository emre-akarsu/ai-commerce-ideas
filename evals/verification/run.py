"""Run the seeded set through the purchasing service and report: `python -m evals.verification.run`.

SYNTHETIC: generated texts and a stand-in for the model's reading. This measures what the safety
net (grounding, normalisation, the second reader, the verification layer) does with errors of
seven known types, not how real vendors write or how a real model reads.

Per injected case there are three outcomes. FLAGGED: the quote carries a flag that is not a mere
note. NEUTRALISED: no flag, and the final quote still holds the right values (the error was dropped
before it mattered). ESCAPED: no flag, and a value is wrong. The spec gate (F28 clause 8) is zero
escapes in at least 189 injected errors, with the false-alarm rate on clean quotes under a ceiling.

`--check` compares with `baseline.json` and fails only if something got worse (more escapes in a
type, more clean quotes flagged, or a changed set), so a regression is caught while the honest
gap stays visible. `--write-baseline` records the current numbers.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from employees.purchasing.service import (
    EVT_QUOTE_VERIFIED,
    FORCE_APPROVAL_FLAGS,
    REFUSE_FLAGS,
    InMemoryNotifier,
    PurchasingService,
    Settings,
    build_in_memory_service,
)

from aiplat.ctx import Ctx, Role
from aiplat.profile import load_profile
from components.core.domain import ExtractedQuote, Quote, Vendor
from components.core.fakes import FakeClock, RecordingTransport
from components.core.store import Store
from components.evidence.log import EventLog
from components.parts.equivalence.catalogue import normalise_mpn
from components.rfq.quotes.extractors import RegexQuoteExtractor
from components.suppliers import SupplierStore
from components.verify.history import PriceObservation
from components.verify.plausibility import InMemoryPriceHistory
from evals.metrics import critical_mismatch_upper_bound, wilson_interval
from evals.verification.cases import ERROR_TYPES, PART, VENDORS, Case, build_cases, set_hash

BANNER = ("SYNTHETIC SEEDED SET - measures the safety net's mechanisms, "
          "not real vendors or a real model")
BASELINE = Path(__file__).resolve().parent / "baseline.json"
MIN_INJECTED = 189  # spec section 8 item 2: smallest n at which zero escapes give a 2% bound
FALSE_ALARM_CEILING = 0.10  # proposed (spec O17): assumption pending baseline
# A flag is an ALARM when the product acts on it: it forces a second person, refuses the quote,
# marks a value as not found in the text, or comes from the verification layer. Anything else is
# a note.
ALARMS = FORCE_APPROVAL_FLAGS | REFUSE_FLAGS | frozenset({
    "verification_review", "verification_flag", "extraction_failed", "injection_suspected",
    "dmarc_fail"})


def is_alarm(flag: str) -> bool:
    return flag in ALARMS or flag.startswith("ungrounded:")
TENANT = "eval-tenant"
IDENTITY = {  # synthetic, illustrative particulars (not a real company)
    "legal_name": "Acme Plant Ltd", "registration_number": "01234567",
    "registered_office": "1 Example Street, London, EC1A 1AA", "registered_in": "England and Wales",
}
QUOTE_DATE_DAYS_AGO = (10, 40, 90)

FLAGGED, NEUTRALISED, ESCAPED = "flagged", "neutralised", "escaped"


class Reader:
    """Stands in for the model: returns whatever the case says it read."""

    def __init__(self) -> None:
        self.reading = ExtractedQuote()

    def extract(self, source_text: str) -> ExtractedQuote:
        return self.reading


@dataclass(frozen=True)
class Outcome:
    case: Case
    result: str  # FLAGGED, NEUTRALISED or ESCAPED (for a clean case: FLAGGED = false alarm)
    wrong: bool
    flags: tuple[str, ...]
    codes: tuple[str, ...]  # finding codes from the verification layer

    @property
    def by_verification(self) -> bool:
        return any(f.startswith("verification_") for f in self.flags)

    @property
    def by_existing(self) -> bool:
        return any(not f.startswith("verification_") for f in self.flags)


@dataclass
class World:
    svc: PurchasingService
    log: EventLog
    store: Store
    reader: Reader
    request_of: dict[str, str]
    token_of: dict[str, str]
    books: dict[str, InMemoryPriceHistory] = field(default_factory=dict)


def build_world(vendors: Sequence[str] = VENDORS) -> World:
    clock = FakeClock()
    store, log = Store(), EventLog(clock, pii_key=b"k" * 32, chain_key=b"c" * 32)
    suppliers = SupplierStore()
    settings = Settings(approval_threshold=Decimal("100000"),
                        business_identities={TENANT: IDENTITY})
    counter = iter(range(1, 10**9))
    svc = build_in_memory_service(
        clock=clock, store=store, event_log=log, transport=RecordingTransport(),
        notifier=InMemoryNotifier(), settings=settings, profile=load_profile("uk"),
        ids=lambda p: f"{p}-{next(counter):06d}", approval_secret=b"s" * 32,
        token_gen=lambda: f"reply-{next(counter):06d}", suppliers=suppliers)
    reader = Reader()
    svc._extractor = reader  # noqa: SLF001 - the model's place in the chain
    svc._shadow_extractor = RegexQuoteExtractor()  # noqa: SLF001 - the deterministic second reader
    world = World(svc, log, store, reader, {}, {})
    svc._price_history = lambda tenant: world.books.get(tenant)  # noqa: SLF001
    admin, buyer = Ctx(TENANT, "admin", Role.ADMIN), Ctx(TENANT, "buyer", Role.BUYER)
    requester = Ctx(TENANT, "tech", Role.REQUESTER)
    text = ("Bearing 6205-2RS, normal clearance CN, precision class P0. "
            f"Manufacturer: SynthCo Alpha MPN: {PART}. Need 10 pcs by 2026-10-20.")
    for vid in vendors:
        svc.upsert_vendor(admin, Vendor(
            id=vid, tenant_id=TENANT, name=f"Vendor {vid}", domain=f"{vid}.example",
            contact_email=f"sales@{vid}.example"))
        svc.attest_vendor(admin, vid)
        rid = svc.create_request(requester, text=text).request.id
        prepared = svc.prepare_rfqs(buyer, rid, vendor_ids=[vid])[0]
        svc.approve_send(buyer, prepared.rfq_id, mime_hash=prepared.mime_hash)
        (rfq,) = store.for_tenant(TENANT).rfqs.list(lambda r, rid=rid, vid=vid: (
            r.request_id == rid and r.vendor_id == vid))
        world.request_of[vid], world.token_of[vid] = rid, rfq.reply_token
    return world


def _history(case: Case, now: datetime) -> InMemoryPriceHistory | None:
    if not case.history_prices:
        return None
    return InMemoryPriceHistory(PriceObservation(
        item_key=normalise_mpn(PART), merchant_id=case.vendor, unit_price=price, unit="each",
        currency="GBP", quantity=None, observed_at=now - timedelta(days=days), source="po_import")
        for price, days in zip(case.history_prices, QUOTE_DATE_DAYS_AGO, strict=False))


def _contradicts(quote: Quote, answer: Mapping[str, Any]) -> bool:
    """True when the final quote holds a value that contradicts the case's answer. A blank value
    (or a basis still "unknown") is not a wrong value: a person sees nothing to approve."""
    for name, expected in answer.items():
        if name == "refused":
            if ("validity_expired" in quote.flags) != bool(expected):
                return True
            continue
        actual = getattr(quote, name)
        if actual is None or actual == "unknown":
            continue
        if isinstance(expected, Decimal):
            if not isinstance(actual, Decimal) or abs(actual - expected) > Decimal("0.0001"):
                return True
        elif actual != expected:
            return True
    return False


def _codes(world: World, quote: Quote) -> tuple[str, ...]:
    for ev in reversed(world.log.events(TENANT, world.request_of[_vendor_of(world, quote)])):
        if ev.type == EVT_QUOTE_VERIFIED and ev.payload.get("version") == quote.version:
            return tuple(sorted({f["code"] for f in ev.payload["findings"]}))
    return ()


def _vendor_of(world: World, quote: Quote) -> str:
    return quote.vendor_id


def run_case(world: World, case: Case) -> Outcome:
    world.reader.reading = case.reading or RegexQuoteExtractor().extract(case.text)
    world.books[TENANT] = _history(case, world.svc._clock.now()) or InMemoryPriceHistory()  # noqa: SLF001
    view = world.svc.ingest_inbound_reply(
        reply_token=world.token_of[case.vendor], from_domain=f"{case.vendor}.example",
        source_text=case.text, dmarc_aligned=True)
    quote: Quote = view.quote  # type: ignore[union-attr]
    flags = tuple(sorted(f for f in quote.flags if is_alarm(f)))
    # an expired quote that is refused is handled correctly even though it carries a flag
    wrong = _contradicts(quote, case.answer)
    if flags:
        result = FLAGGED
    else:
        result = ESCAPED if wrong else NEUTRALISED
    return Outcome(case, result, wrong, flags, _codes(world, quote))


def run_all(cases: Iterable[Case] | None = None) -> list[Outcome]:
    world = build_world()
    return [run_case(world, c) for c in (cases if cases is not None else build_cases())]


# ---------------------------------------------------------------- report


@dataclass(frozen=True)
class Tally:
    n: int
    flagged: int
    neutralised: int
    escaped: int
    verification_only: int  # flagged, and only because of the verification layer
    without_verification_escapes: int  # would have escaped had the layer not existed


def tally(outcomes: Sequence[Outcome]) -> Tally:
    c = Counter(o.result for o in outcomes)
    only = sum(1 for o in outcomes if o.result == FLAGGED and not o.by_existing)
    no_layer = sum(1 for o in outcomes if o.wrong and not o.by_existing)
    return Tally(len(outcomes), c[FLAGGED], c[NEUTRALISED], c[ESCAPED], only, no_layer)


def _pct(k: int, n: int) -> str:
    if n == 0:
        return "n/a"
    low, high = wilson_interval(k, n)
    return f"{100 * k / n:5.1f}% [{100 * low:4.1f}-{100 * high:5.1f}]"


def verdict(injected: Tally, clean: Tally) -> str:
    if injected.n < MIN_INJECTED:
        return "NOT EVALUATED"
    if injected.escaped > 0:
        return "FAIL"
    return "FAIL" if clean.flagged / max(clean.n, 1) > FALSE_ALARM_CEILING else "PASS"


def render(outcomes: Sequence[Outcome]) -> str:
    injected = [o for o in outcomes if o.case.kind == "injected"]
    clean = [o for o in outcomes if o.case.kind == "clean"]
    ti, tc = tally(injected), tally(clean)
    vendors = len({o.case.vendor for o in outcomes})
    lines = [
        BANNER,
        f"set {set_hash()[:16]}  cases: {len(injected)} injected, {len(clean)} clean, "
        f"{vendors} vendors",
        "",
        "error type             n  safe(flagged+neutralised)   escaped   "
        "verification-only  w/o layer",
    ]
    for etype in ERROR_TYPES:
        t = tally([o for o in injected if o.case.error_type == etype])
        lines.append(
            f"  {etype:<20}{t.n:>3}  {_pct(t.flagged + t.neutralised, t.n):<26}"
            f"{t.escaped:>6}   {t.verification_only:>12}   {t.without_verification_escapes:>8}")
    lines += ["", "by mechanism (escaped / n):"]
    by_mech: dict[tuple[str, str], list[Outcome]] = defaultdict(list)
    for o in injected:
        by_mech[(o.case.error_type, o.case.mechanism)].append(o)
    for (etype, mech), os_ in sorted(by_mech.items()):
        t = tally(os_)
        lines.append(f"  {etype}/{mech:<28}{t.escaped:>3} / {t.n:<3} flagged {t.flagged:>3}"
                     f" neutralised {t.neutralised:>3}")
    false_wrong = sum(1 for o in clean if o.wrong)
    lines += [
        "", f"clean quotes flagged (false alarms): {tc.flagged} of {tc.n} {_pct(tc.flagged, tc.n)}"
        f"  (ceiling {FALSE_ALARM_CEILING:.0%}); clean quotes with a wrong value: {false_wrong}"]
    for flag, n in Counter(f for o in clean for f in o.flags).most_common(8):
        lines.append(f"    {flag}: {n}")
    bound = critical_mismatch_upper_bound(ti.escaped, ti.n)
    lines += [
        "", f"escapes: {ti.escaped} of {ti.n} injected errors; Wilson 95% upper bound on the "
        f"escape rate {bound:.4f} (gate: zero escapes in at least {MIN_INJECTED}, bound <= 0.02)",
        f"escapes if the verification layer did not exist: {ti.without_verification_escapes}",
        f"VERDICT: {verdict(ti, tc)}  (zero observed is an upper bound, not proof of safety)",
        BANNER,
    ]
    return "\n".join(lines)


def escaped_cases(outcomes: Sequence[Outcome]) -> list[str]:
    return [o.case.case_id for o in outcomes if o.case.kind == "injected" and o.result == ESCAPED]


# ---------------------------------------------------------------- baseline (ratchet)


def snapshot(outcomes: Sequence[Outcome]) -> dict[str, Any]:
    injected = [o for o in outcomes if o.case.kind == "injected"]
    clean = [o for o in outcomes if o.case.kind == "clean"]
    types = {t: tally([o for o in injected if o.case.error_type == t]).escaped
             for t in ERROR_TYPES}
    return {"set_hash": set_hash(), "injected": len(injected), "clean": len(clean),
            "escaped_by_type": types, "clean_flagged": tally(clean).flagged,
            "clean_wrong": sum(1 for o in clean if o.wrong)}


def regressions(now: dict[str, Any], base: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if now["set_hash"] != base["set_hash"]:
        out.append("the seeded set changed: update baseline.json on purpose (--write-baseline)")
        return out
    for etype, escaped in now["escaped_by_type"].items():
        if escaped > base["escaped_by_type"].get(etype, 0):
            out.append(f"{etype}: {escaped} escapes, baseline {base['escaped_by_type'][etype]}")
    for key in ("clean_flagged", "clean_wrong"):
        if now[key] > base[key]:
            out.append(f"{key}: {now[key]}, baseline {base[key]}")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    ap.add_argument("--check", action="store_true", help="fail if worse than baseline.json")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--list-escapes", action="store_true")
    args = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    outcomes = run_all()
    print(render(outcomes))
    if args.list_escapes:
        print("\n".join(escaped_cases(outcomes)))
    snap = snapshot(outcomes)
    if args.write_baseline:
        BASELINE.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.name}")
        return 0
    if args.check:
        bad = regressions(snap, json.loads(BASELINE.read_text(encoding="utf-8")))
        for line in bad:
            print("REGRESSION:", line, file=sys.stderr)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

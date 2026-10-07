"""Demo: quote for products. Kit -> matching -> offer pricing -> draft quote, for one tenant.

    python scripts/demo_quote.py [--tenant demo-tenant-a] [--scope bathroom_full]
                                 [--finish-level budget|most_used|premium]
                                 [--no-review] [--export quote.json]

Resolves a kit scope at its default answers, builds the quote for the tenant from the SYNTHETIC
price files in profiles/data/quoting/, prints the quote, then (unless --no-review) applies the
invented reviewer decisions of the demo to the review queue and prints the quote again, which
shows the approval loop ("previously approved"). Tenants: demo-tenant-a (five attested trade
price lists; firm prices) and demo-tenant-b (one account price list plus public list prices; firm
and indicative prices). Offline and deterministic: a fixed clock, no network, no real LLM, and
running it twice prints identical output. All prices and merchants are fictional; this is not a
supplier quote and nothing is sent or ordered.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from aiplat.profile import load_profile  # noqa: E402
from components.job_kits import KitError, load_library  # noqa: E402
from components.matching.approvals import InMemoryApprovedMatchStore  # noqa: E402
from components.matching.catalogue import load_catalogue  # noqa: E402
from components.matching.classification import load_classification  # noqa: E402
from components.matching.engine import MatchingEngine  # noqa: E402
from components.matching.index import CatalogIndex  # noqa: E402
from components.matching.ontology import default_data_dir, load_ontology  # noqa: E402
from components.matching.policy import GatePolicy  # noqa: E402
from components.pricing import InMemoryOfferStore, PricingConfig  # noqa: E402
from components.quoting import (  # noqa: E402
    QuoteResult,
    QuotingContext,
    approve_match,
    build_quote,
    dumps,
    order_lines_from_kit,
    quote_draft_ui,
)
from components.quoting.loading import load_price_files, specs_from_manifest  # noqa: E402

DATA = ROOT / "profiles" / "data" / "quoting"
KITS = ROOT / "profiles" / "data" / "job_kits" / "uk"
AS_OF = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
BANNER = "SYNTHETIC / ILLUSTRATIVE DATA - fictional merchants and prices - not a supplier quote"
RULE = "-" * 100


class FixedClock:
    def now(self) -> datetime:
        return AS_OF


def money(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:,.2f}"


def clip(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "~"


def build_context() -> tuple[QuotingContext, list[str]]:
    resolved = load_profile("uk").profile.model_dump(mode="json")
    pricing = PricingConfig.from_mapping(resolved)
    policy = GatePolicy.from_mapping(resolved["matching"])
    data = default_data_dir()
    registry = load_classification(data / "classification.yaml")
    ontology = load_ontology(data / "ontology", registry)
    items = load_catalogue(data / "catalogue_seed.yaml", ontology, registry)
    clock = FixedClock()
    engine = MatchingEngine(CatalogIndex(items, ontology), InMemoryApprovedMatchStore(clock),
                            policy=policy)
    store = InMemoryOfferStore(pricing)
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    texts = {f["file"]: (DATA / f["file"]).read_text(encoding="utf-8") for f in manifest["files"]}
    reports = load_price_files(store, specs_from_manifest(manifest, texts), pricing)
    loaded = [f"  {r.origin:34} {r.visibility:15} {str(r.tenant_id or '-'):14} "
              f"{r.offers:4} offers, {len(r.quarantined)} quarantined" for r in reports]
    return QuotingContext(engine=engine, offers=store, pricing=pricing, clock=clock), loaded


def kit_for(scope: str, finish_level: str | None) -> Any:
    library = load_library(KITS)
    spec = library.scope(f"bathroom_{scope}" if not scope.startswith("bathroom_") else scope)
    answers = {"finish_level": finish_level} if finish_level else {}
    return library.resolve(spec.scope_id, answers, {m.id: m.sample for m in spec.measurements})


def print_firm(quote: QuoteResult) -> None:
    print("FIRM LINES (the only lines in the totals)")
    print(f"  {'line':26} {'qty':>10} {'merchant':14} {'packs':>5} {'unit price':>10} "
          f"{'goods':>9}  note")
    for x in sorted(quote.draft.lines, key=lambda x: [r.line_id for r in quote.results]
                    .index(x.line_id)):
        res = next(r for r in quote.results if r.line_id == x.line_id)
        note = "previously approved" if res.match and res.match.previously_approved else ""
        flags = ",".join(x.flags)
        print(f"  {x.line_id:26} {x.quantity:>7} {x.unit.value:>3} {x.merchant_id:14} "
              f"{x.packs:>5} {x.unit_price:>10} {money(x.goods_total):>9}  "
              f"{clip((note + ' ' + flags).strip(), 36)}")
    if not quote.draft.lines:
        print("  (none)")


def print_totals(quote: QuoteResult) -> None:
    t = quote.draft.totals
    print("\nDELIVERY PER MERCHANT")
    for d in quote.draft.deliveries:
        fee = "not stated" if d.fee is None else f"{money(d.fee)} {t.currency}"
        print(f"  {d.merchant_id:14} spend {money(d.spend):>10}  delivery {fee:>14}  "
              f"({len(d.line_ids)} lines)")
    print(f"\nFIRM TOTALS ({t.currency}, comparison basis {t.basis})")
    print(f"  goods {money(t.goods):>10}   delivery {money(t.delivery):>8}   "
          f"subtotal {money(t.subtotal):>10}")
    print(f"  VAT at {t.tax_rate * 100:.0f}% {money(t.tax):>10}   total ex VAT "
          f"{money(t.total_ex_tax):>10}   total inc VAT {money(t.total_inc_tax):>10}")
    opt = quote.draft.optimisation
    print(f"  basket: {opt.method}{'' if opt.exact else ' (not proven optimal)'}, saves {money(opt.savings_vs_line_by_line)} vs line-by-line"
          + ("" if opt.savings_vs_single_merchant is None
             else f", {money(opt.savings_vs_single_merchant)} vs one merchant"))
    if t.delivery_incomplete:
        print("  delivery terms missing for some merchant: delivery may be understated")


def print_queue(quote: QuoteResult, show: int) -> None:
    print(f"\nREVIEW QUEUE ({len(quote.review_queue)} lines need a person; nothing is priced)")
    for r in quote.review_queue[:show]:
        print(f"  {r.line_id:26} {clip(r.request.text, 60)}")
        if r.review is not None and r.review.question:
            print(f"      question: {clip(r.review.question, 88)}")
        elif r.review is not None and r.review.reasons:
            print(f"      why: {clip(r.review.reasons[0], 88)}")
        for c in (r.review.candidates if r.review else ()):
            print(f"      candidate {c.sku_id} {clip(c.title, 48)} ({c.score})")
    if len(quote.review_queue) > show:
        print(f"  ... and {len(quote.review_queue) - show} more (--review-lines to show more)")
    print(f"\nINDICATIVE ONLY ({len(quote.indicative_lines)} lines; not firm, never in a total)")
    for r in quote.indicative_lines:
        rng = r.indicative
        if rng is not None:
            span = money(rng.low) if rng.low == rng.high else f"{money(rng.low)} to {money(rng.high)}"
            print(f"  {r.line_id:26} {span} {rng.currency} per "
                  f"{rng.unit.value} (list price, {rng.count} source(s), indicative, not a quote)")
    print(f"\nNO USABLE OFFER ({len(quote.no_offer_lines)} lines)")
    for r in quote.no_offer_lines:
        print(f"  {r.line_id:26} {', '.join(r.excluded_codes) or r.reasons[-1].code}")
    print(f"\nUNMATCHED ({len(quote.unmatched)} lines: no catalogue product, or a service)")
    for r in quote.unmatched:
        print(f"  {r.line_id:26} {clip(r.reasons[0].code, 30):30} {clip(r.request.text, 40)}")
    if quote.skipped:
        print(f"\nSKIPPED ({len(quote.skipped)} kit lines the tenant does not need)")
        for s in quote.skipped:
            print(f"  {s.kit_line_id:26} {s.reason}")


def print_quote(title: str, quote: QuoteResult, scope: str, finish: str | None,
                show: int) -> None:
    d = quote.draft
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")
    print(f"tenant {quote.tenant_id}   scope {scope}   finish level {finish or 'default'}   "
          f"as of {d.created_at.isoformat()}   quote {d.quote_id}")
    print(BANNER)
    print("lines: " + ", ".join(f"{k} {v}" for k, v in quote.partition().items()))
    print(RULE)
    print_firm(quote)
    print_totals(quote)
    print_queue(quote, show)
    f = d.freshness
    print(f"\nFRESHNESS  offers used {f.offers_used}; oldest observation "
          f"{f.oldest_observed_at.isoformat() if f.oldest_observed_at else 'n/a'}; "
          f"oldest age {f.max_age_hours_observed} h")
    print(f"\n{d.notice}")


def apply_decisions(ctx: QuotingContext, tenant: str, quote: QuoteResult) -> int:
    decisions = json.loads((DATA / "demo_reviewer_decisions.json").read_text(encoding="utf-8"))
    queued = {r.line_id: r for r in quote.review_queue}
    done = 0
    for d in decisions["decisions"]:
        line = queued.get(d["kit_line_id"])
        if line is not None:
            approve_match(ctx, tenant, line.request, d["sku_id"], decisions["approver"])
            done += 1
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", default="demo-tenant-a",
                        choices=["demo-tenant-a", "demo-tenant-b"])
    parser.add_argument("--scope", default="full", help="full, wc_only, cloakroom or wet_room")
    parser.add_argument("--finish-level", default=None, choices=["budget", "most_used", "premium"])
    parser.add_argument("--no-review", action="store_true",
                        help="print only the first quote, without the demo reviewer's decisions")
    parser.add_argument("--review-lines", type=int, default=6,
                        help="how many review-queue lines to print in full")
    parser.add_argument("--export", type=Path, default=None, help="write quote-draft-ui/1 JSON")
    args = parser.parse_args(argv)
    try:
        kit = kit_for(args.scope, args.finish_level)
    except KitError as exc:
        print(f"cannot resolve the kit: {exc}", file=sys.stderr)
        return 2
    ctx, loaded = build_context()
    print(BANNER)
    print("price files (handed in as text; nothing is fetched):")
    print("\n".join(loaded))
    lines = order_lines_from_kit(kit)
    quote = build_quote(ctx, args.tenant, lines)
    print_quote("FIRST QUOTE (before any review)", quote, kit.scope_id, args.finish_level,
                args.review_lines)
    if not args.no_review:
        n = apply_decisions(ctx, args.tenant, quote)
        print(f"\n[the demo reviewer approves a product for {n} review lines "
              f"(synthetic decisions); the same quote is run again]")
        quote = build_quote(ctx, args.tenant, lines)
        print_quote("QUOTE AFTER REVIEW (approved lines resolve instantly)", quote,
                    kit.scope_id, args.finish_level, args.review_lines)
    if args.export is not None:
        args.export.write_text(dumps(quote_draft_ui(quote)), encoding="utf-8")
        print(f"\nwrote {args.export}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

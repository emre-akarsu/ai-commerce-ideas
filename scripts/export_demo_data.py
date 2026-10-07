"""Export the demo data for the web UI: price books and quotes for both demo tenants.

    python scripts/export_demo_data.py [--out apps/web/lib/quote-data] [--check]

For tenants demo-tenant-a and demo-tenant-b and the kit scopes full, wc_only, cloakroom and
wet_room (default kit answers, default finish level) this writes
`<out>/<tenant>/<scope>.json`, an object {meta, price_book, quote_first, quote_after_review,
reviewer_decisions}, and `<out>/index.json` listing every combination with its headline counts.

* `price_book` is `price-books-ui/1` (components.pricebook), built from the quote AFTER review
  (the state a person would be looking at), so coverage and gaps reflect the approvals.
* `quote_first` and `quote_after_review` are `quote-draft-ui/1` (components.quoting).
* `quote_options` is `quote-options-ui/1` (components.quoting `quote_options`), built from the
  quote AFTER review with the demo buyer inputs recorded in `options_inputs`: a SYNTHETIC
  preferred-supplier list (the tenant's own private price files, first two in manifest order) and,
  for ONE scope per tenant (`REFERENCE_SCOPE`), an invented budget, required-by date and delivery
  cap, so the balanced option can appear. The other scopes carry no references, so the export says
  why there is no balanced option. The options compare prices the customer holds; they are not a
  market-wide best price, and nothing is chosen, sent or ordered.
* `reviewer_decisions` lists the SYNTHETIC decisions applied to the review queue: those of the
  quoting demo (profiles/data/quoting/demo_reviewer_decisions.json) wherever their kit line is in
  the queue, plus the invented extras in profiles/data/pricebook/reviewer_decisions_extra.json.
  With none applied it is empty and `quote_after_review` equals `quote_first`.

Everything is SYNTHETIC/ILLUSTRATIVE: fictional merchants, invented prices and decisions, a fixed
clock, no network and no model. Output is byte-identical on every run (`--check` verifies the
files on disk against a fresh run). Nothing is sent or ordered; the request drafts are text.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from aiplat.profile import load_profile  # noqa: E402
from components.job_kits import JobKitLibrary, load_library  # noqa: E402
from components.matching.approvals import InMemoryApprovedMatchStore  # noqa: E402
from components.matching.catalogue import load_catalogue  # noqa: E402
from components.matching.classification import load_classification  # noqa: E402
from components.matching.engine import MatchingEngine  # noqa: E402
from components.matching.index import CatalogIndex  # noqa: E402
from components.matching.ontology import default_data_dir, load_ontology  # noqa: E402
from components.matching.policy import GatePolicy  # noqa: E402
from components.pricebook import (  # noqa: E402
    ImportSummary,
    MerchantInfo,
    RequestContext,
    RequestTemplate,
    RfqMode,
    RfqTemplate,
    build_price_book,
    draft_requests,
    draft_rfq_messages,
    price_books_ui,
    rfq_for_gaps,
    summaries_from_reports,
)
from components.pricing import InMemoryOfferStore, PricingConfig  # noqa: E402
from components.quoting import (  # noqa: E402
    OptionsConfig,
    QuoteResult,
    QuotingContext,
    approve_match,
    build_quote,
    order_lines_from_kit,
    quote_draft_ui,
    quote_options,
    quote_options_ui,
)
from components.quoting.export import dumps  # noqa: E402
from components.quoting.loading import load_price_files, specs_from_manifest  # noqa: E402

QUOTING = ROOT / "profiles" / "data" / "quoting"
PRICEBOOK = ROOT / "profiles" / "data" / "pricebook"
KITS = ROOT / "profiles" / "data" / "job_kits" / "uk"
DEFAULT_OUT = ROOT / "apps" / "web" / "lib" / "quote-data"
AS_OF = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
TENANTS = ("demo-tenant-a", "demo-tenant-b")
SCOPES = ("full", "wc_only", "cloakroom", "wet_room")
LABEL = ("SYNTHETIC/ILLUSTRATIVE DEMO DATA: fictional merchants, invented prices and invented "
         "reviewer decisions; not real prices, not a supplier quote; nothing is sent or ordered")
# SYNTHETIC buyer inputs for the quote options (invented; a real buyer would supply their own).
# Only the scope named here gets a budget, a required-by date and a delivery cap, so the balanced
# option appears for it; every other scope has no buyer reference and shows why there is none.
REFERENCE_SCOPE = {"demo-tenant-a": "cloakroom", "demo-tenant-b": "cloakroom"}
DEMO_REFERENCES = {  # tenant -> (budget_total on the ex-VAT basis, required_by, max_deliveries)
    "demo-tenant-a": (Decimal("490"), date(2026, 10, 10), 3),
    "demo-tenant-b": (Decimal("240"), date(2026, 10, 10), 1),
}
INPUTS_LABEL = ("SYNTHETIC demo buyer inputs: an invented preferred-supplier list and, for one "
                "scope per customer, an invented budget, required-by date and delivery cap")
BUYERS = {  # invented buyers for the request drafts
    "demo-tenant-a": ("Alex Example", "Example Bathrooms Ltd (fictional)"),
    "demo-tenant-b": ("Sam Sample", "Sample Fitters Ltd (fictional)"),
}


class FixedClock:
    def now(self) -> datetime:
        return AS_OF


@dataclass(frozen=True)
class World:
    """Everything that does not change between combinations."""

    pricing: PricingConfig
    policy: GatePolicy
    index: CatalogIndex
    library: JobKitLibrary
    manifest: dict[str, Any]
    texts: dict[str, str]
    merchants: tuple[MerchantInfo, ...]
    template: RequestTemplate
    rfq_template: RfqTemplate
    decisions: dict[str, Any]
    extras: dict[str, Any]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def build_world() -> World:
    resolved = load_profile("uk").profile.model_dump(mode="json")
    data = default_data_dir()
    registry = load_classification(data / "classification.yaml")
    ontology = load_ontology(data / "ontology", registry)
    items = load_catalogue(data / "catalogue_seed.yaml", ontology, registry)
    manifest = read_json(QUOTING / "manifest.json")
    template = yaml.safe_load((PRICEBOOK / "request_templates.yaml").read_text(encoding="utf-8"))
    return World(
        pricing=PricingConfig.from_mapping(resolved),
        policy=GatePolicy.from_mapping(resolved["matching"]),
        index=CatalogIndex(items, ontology), library=load_library(KITS), manifest=manifest,
        texts={f["file"]: (QUOTING / f["file"]).read_text(encoding="utf-8")
               for f in manifest["files"]},
        merchants=tuple(MerchantInfo(m["merchant_id"], m["name"]) for m in manifest["merchants"]),
        template=RequestTemplate.from_mapping(template),
        rfq_template=RfqTemplate.from_mapping(yaml.safe_load(
            (PRICEBOOK / "rfq_templates.yaml").read_text(encoding="utf-8"))),
        decisions=read_json(QUOTING / "demo_reviewer_decisions.json"),
        extras=read_json(PRICEBOOK / "reviewer_decisions_extra.json"))


def fresh_context(world: World) -> tuple[QuotingContext, tuple[ImportSummary, ...]]:
    """A new offer store with every price file loaded and a new, empty approvals store."""
    clock = FixedClock()
    store = InMemoryOfferStore(world.pricing)
    reports = load_price_files(store, specs_from_manifest(world.manifest, world.texts),
                               world.pricing)
    by_source = {f["source_id"]: f["merchant_id"] for f in world.manifest["files"]}
    engine = MatchingEngine(world.index, InMemoryApprovedMatchStore(clock), policy=world.policy)
    ctx = QuotingContext(engine=engine, offers=store, pricing=world.pricing, clock=clock)
    return ctx, summaries_from_reports(reports, by_source)


def apply_decisions(ctx: QuotingContext, world: World, tenant: str, scope: str,
                    quote: QuoteResult) -> list[dict[str, Any]]:
    """Approve the synthetic decisions whose kit line is in the review queue; return them."""
    queued = {r.line_id: r for r in quote.review_queue}
    candidates = [(d, "quoting demo", world.decisions["approver"])
                  for d in world.decisions["decisions"]]
    candidates += [(d, "pricebook demo", world.extras["approver"])
                   for d in world.extras["scopes"].get(scope, [])]
    applied: list[dict[str, Any]] = []
    for d, source, approver in candidates:
        line = queued.get(d["kit_line_id"])
        if line is None:
            continue
        approve_match(ctx, tenant, line.request, d["sku_id"], approver)
        applied.append({"kit_line_id": d["kit_line_id"], "line_id": line.line_id,
                        "sku_id": d["sku_id"], "note": d["note"], "approver": approver,
                        "source": source, "label": "synthetic, invented for the demo"})
    return applied


def request_context(world: World, tenant: str) -> RequestContext:
    name, company = BUYERS[tenant]
    letter = tenant[-1].upper()
    refs = {m.merchant_id: f"ACC-{letter}-{1001 + i}"
            for i, m in enumerate(sorted(world.merchants, key=lambda m: m.merchant_id))}
    return RequestContext(buyer_name=name, buyer_company=company, account_references=refs)


def demo_preferred(world: World, tenant: str) -> list[str]:
    """A SYNTHETIC preferred-supplier list: the tenant's first two private price files, in
    manifest order (the same rule as scripts/demo_quote.py)."""
    own = [f["merchant_id"] for f in world.manifest["files"] if f.get("tenant_id") == tenant]
    return list(dict.fromkeys(own))[:2]


def options_inputs(world: World, tenant: str, scope: str) -> dict[str, Any]:
    """The demo buyer inputs used for the options of one combination, as plain JSON."""
    out: dict[str, Any] = {
        "label": INPUTS_LABEL, "synthetic": True,
        "preferred_merchants": demo_preferred(world, tenant),
        "budget_total": None, "budget_vat_basis": None, "required_by": None,
        "max_deliveries": None, "has_references": False}
    if REFERENCE_SCOPE.get(tenant) == scope:
        budget, required_by, cap = DEMO_REFERENCES[tenant]
        out.update(budget_total=str(budget), budget_vat_basis=world.pricing.compare_basis,
                   required_by=required_by.isoformat(), max_deliveries=cap, has_references=True)
    return out


def options_config(inputs: dict[str, Any]) -> OptionsConfig:
    if not inputs["has_references"]:
        return OptionsConfig()
    return OptionsConfig(budget_total=Decimal(inputs["budget_total"]),
                         required_by=date.fromisoformat(inputs["required_by"]),
                         max_deliveries=inputs["max_deliveries"])


def export_combination(world: World, tenant: str, scope: str) -> dict[str, Any]:
    ctx, imports = fresh_context(world)
    spec = world.library.scope(f"bathroom_{scope}")
    kit = world.library.resolve(spec.scope_id, {}, {m.id: m.sample for m in spec.measurements})
    lines = order_lines_from_kit(kit)
    first = build_quote(ctx, tenant, lines)
    applied = apply_decisions(ctx, world, tenant, scope, first)
    after = build_quote(ctx, tenant, lines) if applied else first
    book = build_price_book(ctx.offers, tenant, world.merchants, world.pricing, ctx.clock,
                            quote=after, imports=imports)
    drafts = draft_requests(world.template, book.merchants, request_context(world, tenant))
    rctx = request_context(world, tenant)
    groups = rfq_for_gaps(book.gaps)
    names = {m.merchant_id: m.name for m in world.merchants}
    rfq = {k: draft_rfq_messages(world.rfq_template, groups, names, rctx, mode)
           for k, mode in (("per_supplier", RfqMode.PER_SUPPLIER), ("per_item", RfqMode.PER_ITEM))}
    first_doc = quote_draft_ui(first)
    inputs = options_inputs(world, tenant, scope)
    options = quote_options(after, ctx.pricing, ctx.clock, preferred=inputs["preferred_merchants"],
                            config=options_config(inputs))
    return {
        "meta": {
            "format": "quote-data-bundle/1", "label": LABEL, "synthetic": True,
            "tenant_id": tenant, "scope_id": kit.scope_id, "scope_label": spec.title,
            "finish_level": "default", "as_of": AS_OF.isoformat(),
            "price_book_basis": "quote_after_review",
            "formats": "price-books-ui/1, quote-draft-ui/1",
            "generated_by": "scripts/export_demo_data.py",
        },
        "price_book": price_books_ui(
            book, drafts, label=LABEL, rfq_per_supplier=rfq["per_supplier"],
            rfq_per_item=rfq["per_item"]),
        "quote_first": first_doc,
        "quote_after_review": quote_draft_ui(after) if applied else first_doc,
        "reviewer_decisions": applied,
        "quote_options": quote_options_ui(options),
        "options_inputs": inputs,
    }


def headline(doc: dict[str, Any]) -> dict[str, Any]:
    p, t = doc["partition"], doc["totals"]
    return {"lines_total": sum(p.values()), "priced": p["priced"], "review": p["review"],
            "unmatched": p["unmatched"], "indicative": p["indicative_only"],
            "no_offer": p["no_offer"], "skipped": p["skipped"],
            "firm_total_ex_vat": t["total_ex_tax"], "firm_total_inc_vat": t["total_inc_tax"],
            "currency": t["currency"]}


def options_headline(doc: dict[str, Any]) -> dict[str, Any]:
    opts = doc["options"]
    totals = [(Decimal(o["totals"]["total_ex_tax"]), o["totals"]["total_inc_tax"]) for o in opts]
    low = min(totals) if totals else None
    high = max(totals) if totals else None
    return {
        "options_shown": len(opts), "option_ids": [o["option_id"] for o in opts],
        "duplicates": len(doc["duplicates"]),
        "lowest_total_ex_vat": str(low[0]) if low else None,
        "lowest_total_inc_vat": low[1] if low else None,
        "highest_total_ex_vat": str(high[0]) if high else None,
        "balanced_shown": any(o["option_id"] == "balanced" for o in opts),
        "balanced_status": doc["config"]["balanced"]["status"],
        "exact": doc["optimiser"]["exact"],
        "search_incomplete": doc["optimiser"]["search_incomplete"],
        "excluded_lines": len(doc["excluded_lines"]),
        "indicative_lines": len(doc["indicative_block"]["lines"]),
    }


def index_entry(tenant: str, scope: str, bundle: dict[str, Any]) -> dict[str, Any]:
    book = bundle["price_book"]
    return {
        "tenant_id": tenant, "scope_id": bundle["meta"]["scope_id"],
        "scope_label": bundle["meta"]["scope_label"], "path": f"{tenant}/{scope}.json",
        "reviewer_decisions": len(bundle["reviewer_decisions"]),
        "first": headline(bundle["quote_first"]),
        "after_review": headline(bundle["quote_after_review"]),
        "options": options_headline(bundle["quote_options"])
        | {"has_buyer_references": bundle["options_inputs"]["has_references"]},
        "price_book": {k: book["freshness_summary"][k] for k in
                       ("current", "stale", "missing", "indicative_only")}
        | {"gaps": len(book["gaps"])},
    }


def generate() -> dict[str, str]:
    """Every output file as {relative path: text}; deterministic."""
    world = build_world()
    files: dict[str, str] = {}
    entries = []
    for tenant in TENANTS:
        for scope in SCOPES:
            bundle = export_combination(world, tenant, scope)
            files[f"{tenant}/{scope}.json"] = dumps(bundle)
            entries.append(index_entry(tenant, scope, bundle))
    files["index.json"] = dumps({
        "format": "quote-data-index/1", "label": LABEL, "synthetic": True,
        "as_of": AS_OF.isoformat(), "combinations": entries})
    return files


def table(files: dict[str, str]) -> str:
    rows = [f"{'tenant':14} {'scope':10} {'priced':>6} {'review':>6} {'unmatched':>9} "
            f"{'indic.':>6} {'no offer':>8} {'ex VAT':>10} {'inc VAT':>10} {'dec.':>4} "
            f"{'book c/s/m/i':<12} {'gaps':>4}",
            "-" * 118]
    for e in json.loads(files["index.json"])["combinations"]:
        a, b = e["after_review"], e["price_book"]
        rows.append(
            f"{e['tenant_id']:14} {e['path'].split('/')[1][:-5]:10} {a['priced']:>6} "
            f"{a['review']:>6} {a['unmatched']:>9} {a['indicative']:>6} {a['no_offer']:>8} "
            f"{a['firm_total_ex_vat']:>10} {a['firm_total_inc_vat']:>10} "
            f"{e['reviewer_decisions']:>4} "
            f"{b['current']}/{b['stale']}/{b['missing']}/{b['indicative_only']:<6} "
            f"{b['gaps']:>4}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true",
                        help="do not write; fail if the files on disk differ from a fresh run")
    args = parser.parse_args(argv)
    files = generate()
    print("SYNTHETIC / ILLUSTRATIVE DATA - fictional merchants and prices (after-review quote)")
    print(table(files))
    if args.check:
        stale = [name for name, text in sorted(files.items())
                 if not (args.out / name).is_file()
                 or (args.out / name).read_text(encoding="utf-8") != text]
        if stale:
            print(f"out of date: {stale}", file=sys.stderr)
            return 1
        print(f"{len(files)} files are up to date in {args.out}")
        return 0
    for name, text in files.items():
        path = args.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} files to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

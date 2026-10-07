"""Generate the SYNTHETIC/ILLUSTRATIVE price files for the quoting demo and tests.

Fictional merchants, fictional prices, no real data. Every value is a pure function of the
catalogue seed (profiles/data/matching/uk/catalogue_seed.yaml) and fixed constants below, derived
by hashing (sha256), never by a random generator or a clock, so running this twice gives the same
bytes (tests/quoting/test_synthetic_data.py compares the files on disk with `generate()`).

    python profiles/data/quoting/generate_prices.py            # rewrite the files
    python profiles/data/quoting/generate_prices.py --check    # exit 1 if a file is out of date

Files written next to this script:
  prices/*.csv   one CSV per price list (columns in COLUMNS)
  manifest.json  what each file is: merchant, who may see it, how it is declared

What the data deliberately contains, so the engine's gates have something to find: five merchants
with different pack sizes (single items, multi-packs, prices per m/m2/kg/litre, prices per 100 or
1000 pieces), ex-VAT and inc-VAT price columns, delivery fees with free-over thresholds, stale rows
(observed long ago), expired rows, rows that give no VAT basis, out-of-stock and low-stock rows,
minimum order quantities, a few price outliers, and about 9% of the catalogue that nobody lists.
These are NOT licensed cross-reference data and not market prices.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "packages"))

from components.matching.catalogue import load_catalogue  # noqa: E402
from components.matching.classification import load_classification  # noqa: E402
from components.matching.models import CatalogItem  # noqa: E402
from components.matching.ontology import default_data_dir, load_ontology  # noqa: E402
from components.pricing import Unit  # noqa: E402
from components.quoting.units import unit_basis_for_item  # noqa: E402

D = Decimal
LABEL = ("SYNTHETIC/ILLUSTRATIVE price data: fictional merchants and brands, invented prices, not "
         "real prices, not licensed data, not a market claim")
LABEL_COLUMN = "synthetic_label"  # not mapped by the loader; there so an opened CSV says what it is
LABEL_VALUE = "SYNTHETIC-ILLUSTRATIVE-NOT-REAL-PRICES"
AS_OF = "2026-10-05T08:00:00+00:00"
STALE_AT = "2026-09-18T08:00:00+00:00"  # older than the 168 h trade-feed limit on 2026-10-07
VALID_UNTIL = "2026-11-05T00:00:00+00:00"
EXPIRED_AT = "2026-10-06T07:00:00+00:00"  # after the default observation, before the demo clock
TENANT_A = "demo-tenant-a"
TENANT_B = "demo-tenant-b"
VAT = D("0.20")
COLUMNS = (
    "sku", "price_ex_vat", "price_inc_vat", "price", "vat_basis", "price_per", "uom", "pack_size",
    "pack_unit", "min_order_qty", "order_multiple", "stock", "lead_time_days", "delivery_fee",
    "free_delivery_over", "observed_at", "valid_until",
)

# type -> (group, price of one SKU as catalogued is rate * size, size attribute or None)
# Rates are invented, per unit named in the comment.
RATES: dict[str, tuple[str, str, str]] = {
    "plasterboard": ("boards", "3.9", "m2"), "cement_backer_board": ("boards", "12", "m2"),
    "timber_stud": ("boards", "2.4", "m"), "metal_stud": ("boards", "1.9", "m"),
    "tile": ("tiling", "18", "m2"), "tile_adhesive": ("tiling", "0.65", "kg"),
    "tile_grout": ("tiling", "2.2", "kg"), "trim": ("tiling", "2.8", "m"),
    "tanking_kit": ("tiling", "9.5", "m2"), "primer": ("finish", "7", "l"),
    "paint": ("finish", "6", "l"), "silicone_sealant": ("finish", "4.5", "each"),
    "ptfe_tape": ("plumbing", "1.2", "each"), "drywall_screw": ("fixings", "2.4", "per100"),
    "wood_screw": ("fixings", "3.1", "per100"), "wall_plug": ("fixings", "3.6", "per100"),
    "cavity_fixing": ("fixings", "0.45", "each"), "copper_pipe": ("plumbing", "7.5", "m"),
    "plastic_barrier_pipe": ("plumbing", "2.2", "m"), "waste_pipe": ("plumbing", "3", "m"),
    "pipe_fitting": ("plumbing", "2.2", "each"), "isolating_valve": ("plumbing", "4.8", "each"),
    "tap_connector": ("plumbing", "4.2", "each"), "trap": ("plumbing", "5.5", "each"),
    "basin_waste": ("sanitary", "8", "each"), "pan_connector": ("plumbing", "6", "each"),
    "wc": ("sanitary", "95", "each"), "basin": ("sanitary", "62", "each"),
    "bath": ("sanitary", "148", "each"), "shower_tray": ("sanitary", "130", "each"),
    "shower_enclosure": ("sanitary", "190", "each"), "shower_valve": ("sanitary", "85", "each"),
    "basin_tap": ("sanitary", "48", "each"), "towel_rail": ("sanitary", "72", "each"),
    "extractor_fan": ("electrical", "34", "each"), "duct": ("electrical", "6", "m"),
    "downlight": ("electrical", "6.5", "each"), "shaver_socket": ("electrical", "14", "each"),
    "mirror": ("sanitary", "85", "each"), "ufh_mat": ("electrical", "55", "m2"),
    "extractor_duct": ("electrical", "6", "m"),
}
MEASURE_STYLE_TYPES = {
    "plasterboard": Unit.M2, "cement_backer_board": Unit.M2, "tile": Unit.M2,
    "tile_adhesive": Unit.KG, "tile_grout": Unit.KG, "paint": Unit.LITRE, "primer": Unit.LITRE,
    "copper_pipe": Unit.M, "plastic_barrier_pipe": Unit.M, "waste_pipe": Unit.M,
    "timber_stud": Unit.M, "metal_stud": Unit.M, "duct": Unit.M, "trim": Unit.M,
}
MULTI_TYPES = {"pipe_fitting", "isolating_valve", "downlight", "cavity_fixing", "tap_connector",
               "ptfe_tape", "silicone_sealant", "trim", "trap"}
PER_UNIT_TYPES = {"drywall_screw", "wood_screw", "wall_plug"}


@dataclass(frozen=True)
class Merchant:
    merchant_id: str
    name: str
    fee: str  # delivery fee below the threshold, ex VAT
    free_over: str  # delivery is free strictly over this spend
    factor: D  # overall price level
    coverage: dict[str, D]  # chance of listing an SKU, by group
    per_unit_prices: bool  # quotes fixings per 100 or 1000


MERCHANTS = (
    Merchant("m-brindlecote", "Brindlecote Builders Merchants (fictional)", "18.00", "250.00",
             D("0.97"), {"boards": D("0.9"), "tiling": D("0.9"), "finish": D("0.9"),
                         "fixings": D("0.9"), "plumbing": D("0.3"), "sanitary": D("0.2"),
                         "electrical": D("0.3")}, True),
    Merchant("m-northgate", "Northgate Plumb Supply (fictional)", "12.50", "150.00",
             D("1.03"), {"boards": D("0.2"), "tiling": D("0.35"), "finish": D("0.35"),
                         "fixings": D("0.4"), "plumbing": D("0.95"), "sanitary": D("0.8"),
                         "electrical": D("0.5")}, False),
    Merchant("m-halden", "Halden Trade Counter (fictional)", "25.00", "400.00",
             D("0.94"), {g: D("0.6") for g in
                         ("boards", "tiling", "finish", "fixings", "plumbing", "sanitary",
                          "electrical")}, True),
    Merchant("m-pennywell", "Pennywell Bathroom Centre (fictional)", "9.95", "100.00",
             D("1.08"), {"boards": D("0.05"), "tiling": D("0.4"), "finish": D("0.2"),
                         "fixings": D("0.1"), "plumbing": D("0.5"), "sanitary": D("0.95"),
                         "electrical": D("0.5")}, False),
    Merchant("m-corvane", "Corvane DIY Warehouse (fictional)", "6.99", "75.00",
             D("1.01"), {"boards": D("0.4"), "tiling": D("0.85"), "finish": D("0.85"),
                         "fixings": D("0.8"), "plumbing": D("0.5"), "sanitary": D("0.4"),
                         "electrical": D("0.8")}, False),
)
SHARED_RETAIL = ("m-pennywell", "m-corvane")  # public price lists: indicative for everyone
RETAIL_UPLIFT = D("1.14")
ACCOUNT_DISCOUNT = D("0.88")


def frac(*parts: str) -> D:
    """A stable number in [0, 1) from the parts (sha256, so identical on every machine)."""
    digest = hashlib.sha256("|".join(parts).encode()).digest()
    return D(int.from_bytes(digest[:6], "big") % 10_000) / D(10_000)


def money(value: D) -> D:
    return max(value, D("0.01")).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def text(value: D) -> str:
    return format(value, "f")


def load_items() -> tuple[CatalogItem, ...]:
    data = default_data_dir()
    registry = load_classification(data / "classification.yaml")
    ontology = load_ontology(data / "ontology", registry)
    items = load_catalogue(data / "catalogue_seed.yaml", ontology, registry)
    return tuple(sorted(items, key=lambda i: i.sku_id))


def unit_price_ex(item: CatalogItem) -> D:
    """Price of one SKU as catalogued (one sale unit), ex VAT, before merchant factors."""
    _, rate, per = RATES[item.product_type]
    basis = unit_basis_for_item(item)
    size = D(1)
    if per in ("m2", "m", "kg", "l"):
        unit = {"m2": Unit.M2, "m": Unit.M, "kg": Unit.KG, "l": Unit.LITRE}[per]
        size = basis.content(unit) or D(1)
    elif per == "per100":
        size = (basis.content(Unit.EACH) or D(1)) / D(100)
    sku_factor = D("0.8") + D("0.6") * frac(item.sku_id, "level")
    return D(rate) * size * sku_factor


def listed(item: CatalogItem, merchant: Merchant) -> bool:
    if frac(item.sku_id, "unlisted") < D("0.07"):
        return False  # nobody lists these: exercises "no offer"
    group = RATES[item.product_type][0]
    return frac(item.sku_id, merchant.merchant_id, "list") < merchant.coverage[group]


def style_of(item: CatalogItem, merchant: Merchant) -> str:
    t = item.product_type
    if t in PER_UNIT_TYPES and merchant.per_unit_prices:
        return "per_unit"
    options = ["unit"]
    if t in MEASURE_STYLE_TYPES:
        options += ["measure", "measure"]
    if t in MULTI_TYPES:
        options += ["multi"]
    return options[int(frac(merchant.merchant_id, t, "style") * len(options))]


def vat_columns(row: dict[str, str], ex: D, key: str) -> None:
    """Fill the price columns: both, ex only, inc only, a bare price (no VAT basis) or a bare
    price with a stated basis. The mode is a stable function of `key`."""
    pick = frac(key, "vat")
    inc = money(ex * (1 + VAT))
    if pick < D("0.06"):
        row["price"] = text(ex)  # no VAT basis stated: the engine will not use it
    elif pick < D("0.10"):
        row["price"], row["vat_basis"] = text(ex), "ex vat"
    elif pick < D("0.25"):
        row["price_ex_vat"] = text(ex)
    elif pick < D("0.40"):
        row["price_inc_vat"] = text(inc)
    else:
        row["price_ex_vat"], row["price_inc_vat"] = text(ex), text(inc)


def pack_columns(row: dict[str, str], item: CatalogItem, merchant: Merchant, style: str,
                 base: D) -> D:
    """Set the pack and price-basis columns; return the amount that the price columns carry."""
    t, key = item.product_type, f"{item.sku_id}|{merchant.merchant_id}"
    basis = unit_basis_for_item(item)
    if style == "per_unit":
        pieces = basis.content(Unit.EACH) or D(1)
        divisor = D(1000) if item.uom.value == "per_1000" else D(100)
        row.update(price_per="each", uom=item.uom.value, pack_size="1")
        return money(base / pieces * divisor)
    if style == "measure":
        unit = MEASURE_STYLE_TYPES[t]
        content = basis.content(unit)
        assert content is not None
        copies = D(1) if unit is not Unit.M2 else D([1, 4, 6, 8][int(frac(key, "k") * 4)])
        row.update(price_per=unit.value, pack_size=text(content * copies), pack_unit=unit.value)
        return money(base / content)
    if style == "multi":
        k = D([5, 10][int(frac(key, "k") * 2)])
        row["pack_size"] = text(k)
        return money(base * k * (1 - D("0.04") - frac(key, "disc") * D("0.04")))
    row["pack_size"] = "1"
    return money(base)


def stock_columns(row: dict[str, str], key: str) -> None:
    pick = frac(key, "stock")
    if pick < D("0.04"):
        row["stock"], row["lead_time_days"] = "out of stock", "14"
    elif pick < D("0.12"):
        row["stock"], row["lead_time_days"] = "low stock", str(2 + int(frac(key, "lt") * 4))
    elif pick < D("0.92"):
        row["stock"], row["lead_time_days"] = "in stock", str(int(frac(key, "lt") * 3))
    if frac(key, "moq") < D("0.12"):
        row["min_order_qty"] = str(2 + int(frac(key, "moqn") * 3))
    if frac(key, "mult") < D("0.04"):
        row["order_multiple"] = "2"


def date_columns(row: dict[str, str], key: str, *, expires: bool) -> None:
    if expires and frac(key, "expired") < D("0.02"):
        row["valid_until"] = EXPIRED_AT  # observed (the file default) before it lapsed
    elif frac(key, "stale") < D("0.06"):
        row["observed_at"] = STALE_AT
    elif frac(key, "day") < D("0.3"):
        row["observed_at"] = "2026-10-06T08:00:00+00:00"


def row_for(item: CatalogItem, merchant: Merchant, *, factor: D, trade: bool) -> dict[str, str]:
    key = f"{item.sku_id}|{merchant.merchant_id}"
    row = dict.fromkeys(COLUMNS, "")
    row["sku"] = item.sku_id
    noise = D("0.97") + D("0.06") * frac(key, "noise")
    base = unit_price_ex(item) * merchant.factor * noise * factor
    if frac(key, "outlier") < D("0.012"):
        base *= 4  # a deliberate price outlier
    amount = pack_columns(row, item, merchant, style_of(item, merchant), base)
    vat_columns(row, amount, key)
    stock_columns(row, key)
    date_columns(row, key, expires=trade)
    if frac(key, "nodelivery") >= D("0.05"):
        row["delivery_fee"], row["free_delivery_over"] = merchant.fee, merchant.free_over
    return row


def csv_text(rows: list[dict[str, str]]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=(*COLUMNS, LABEL_COLUMN), lineterminator="\n")
    writer.writeheader()
    writer.writerows({**r, LABEL_COLUMN: LABEL_VALUE} for r in rows)
    return out.getvalue()


@dataclass(frozen=True)
class FileSpec:
    name: str
    merchant: Merchant
    rows: list[dict[str, str]]
    entry: dict[str, object]


def trade_file(merchant: Merchant, items: tuple[CatalogItem, ...]) -> FileSpec:
    rows = [row_for(i, merchant, factor=D(1), trade=True) for i in items if listed(i, merchant)]
    short = merchant.merchant_id.removeprefix("m-")
    return FileSpec(f"prices/{short}_trade.csv", merchant, rows, {
        "source_id": f"synth-{short}-trade", "merchant_id": merchant.merchant_id,
        "kind": "trade_feed", "visibility": "tenant_private", "tenant_id": TENANT_A,
        "price_type": "trade_list", "tenant_attested": True, "account_specific": False,
        "licence": "tenant-supplied-synthetic", "confidence": "0.90",
        "default_valid_until": VALID_UNTIL,
        "note": f"{merchant.name}: trade price list supplied and attested by {TENANT_A}"})


def retail_file(merchant: Merchant, items: tuple[CatalogItem, ...]) -> FileSpec:
    rows = [row_for(i, merchant, factor=RETAIL_UPLIFT, trade=False) for i in items
            if listed(i, merchant) and frac(i.sku_id, merchant.merchant_id, "public") < D("0.6")]
    short = merchant.merchant_id.removeprefix("m-")
    return FileSpec(f"prices/{short}_public_retail.csv", merchant, rows, {
        "source_id": f"synth-{short}-public", "merchant_id": merchant.merchant_id,
        "kind": "affiliate_feed", "visibility": "shared", "tenant_id": None,
        "price_type": "retail", "tenant_attested": False, "account_specific": False,
        "licence": "synthetic-illustrative", "confidence": "0.60",
        "default_valid_until": None,
        "note": f"{merchant.name}: public list prices, shared with every tenant, indicative only"})


def tenant_b_file(items: tuple[CatalogItem, ...]) -> FileSpec:
    halden = next(m for m in MERCHANTS if m.merchant_id == "m-halden")
    account = Merchant(halden.merchant_id, halden.name, "15.00", "200.00", halden.factor,
                       halden.coverage, True)
    rows = [row_for(i, account, factor=ACCOUNT_DISCOUNT, trade=True) for i in items
            if frac(i.sku_id, "tenant-b") < D("0.45") and frac(i.sku_id, "unlisted") >= D("0.07")]
    return FileSpec("prices/halden_account_tenant_b.csv", account, rows, {
        "source_id": "synth-halden-account-b", "merchant_id": halden.merchant_id,
        "kind": "trade_feed", "visibility": "tenant_private", "tenant_id": TENANT_B,
        "price_type": "account_specific", "tenant_attested": True, "account_specific": True,
        "licence": "tenant-supplied-synthetic", "confidence": "0.90",
        "default_valid_until": VALID_UNTIL,
        "note": f"{halden.name}: account prices of {TENANT_B}, private to that tenant"})


def file_specs() -> list[FileSpec]:
    items = load_items()
    specs = [trade_file(m, items) for m in MERCHANTS]
    specs += [retail_file(m, items) for m in MERCHANTS if m.merchant_id in SHARED_RETAIL]
    specs.append(tenant_b_file(items))
    return specs


def manifest(specs: list[FileSpec]) -> dict[str, object]:
    files = []
    for spec in specs:
        files.append({"file": spec.name, "observed_at": AS_OF, "default_currency": "GBP",
                      "default_vat_basis": "unknown", "method": "file_row", "synthetic": True,
                      "rows": len(spec.rows), **spec.entry})
    return {"id": "quoting-synthetic-prices-v1", "label": LABEL, "as_of": AS_OF,
            "tenants": [TENANT_A, TENANT_B],
            "merchants": [{"merchant_id": m.merchant_id, "name": m.name} for m in MERCHANTS],
            "columns": list(COLUMNS), "label_column": LABEL_COLUMN, "files": files}


def generate() -> dict[str, str]:
    """Every generated file as relative path -> text."""
    specs = file_specs()
    out = {s.name: csv_text(s.rows) for s in specs}
    out["manifest.json"] = json.dumps(manifest(specs), indent=2, sort_keys=True) + "\n"
    return out


def main(argv: list[str] | None = None) -> int:
    check = "--check" in (argv if argv is not None else sys.argv[1:])
    stale = []
    for name, body in generate().items():
        path = HERE / name
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("out of date:", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

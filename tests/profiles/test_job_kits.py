"""UK bathroom job-type kits (templates) are well-formed, cited and licence-clean.

The kits are synthetic/illustrative seed data (profiles/data/job_kits/README.md). These checks are
offline and deterministic: they parse the YAML, evaluate every quantity formula with Decimal through
a small AST whitelist (never eval), and enumerate every variant combination to prove the rules hold.
"""

from __future__ import annotations

import ast
import itertools
import re
from collections.abc import Callable, Iterator, Mapping
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KIT_DIR = ROOT / "profiles" / "data" / "job_kits" / "uk"
README = ROOT / "profiles" / "data" / "job_kits" / "README.md"
NOTES_DIR = ROOT / "research_notes" / "UK refurbishment job templates data"
TEMPLATES = ("bathroom_full", "bathroom_cloakroom", "wc_replacement", "wet_room")

LICENCES = {
    "OGL-3.0",                         # licence confirmed in the notes
    "OGL-3.0-unconfirmed",             # gov.uk document; OGL wording not confirmed in the notes
    "CC-BY-ND-4.0",                    # Uniclass 2015
    "ODC-BY-1.0",                      # ETIM
    "unknown-copyright-facts-only",    # council/HA/tender/forum/retailer text with no licence seen
    "all-rights-reserved-facts-only",  # terms seen and they reserve rights: cite facts, never copy
    "manufacturer-doc-facts-only",     # manufacturer instructions/datasheets: cite facts, never copy
}
EVIDENCE = {"manufacturer_doc", "standard", "public_spec", "retailer", "forum", "search_snippet",
            "derived"}
EXCLUDED_URL_PARTS = ("m3nhf", "m3h.co.uk", "sfg20", "bimobject", "eclass", "spons", "bcis",
                      # Sell2Wales attachments that are M3NHF SOR extracts (all rights reserved)
                      "id=357559", "id=334127", "id=357553")
BRANDS = ("geberit", "grohe", "mira", "triton", "mapei", "marmox", "vent-axia", "ventaxia",
          "ideal standard", "armitage", "twyford", "mcalpine", "bristan", "hardie", "wedi", "altro",
          "polyflor", "forbo", "knauf", "aquapanel", "dulux", "weber", "ardex", "british gypsum",
          "gyproc", "envirovent", "pegler", "akw", "kudos", "merlyn", "croydex", "myson", "dimplex",
          "scolmore", "greenwood", "manrose", "viega", "roca", "idealcast", "idealform", "bal ")
UNITS = {"nr", "m", "m2", "kg", "l", "cartridge", "pack", "kit", "roll", "item", "pair"}
COUNT_UNITS = {"nr", "cartridge", "pack", "kit", "roll", "item", "pair"}
REQUIRED_FULL_GROUPS = {"strip_out", "new_wall", "first_fix_plumbing", "electrics", "waterproofing",
                        "tiling", "sanitaryware", "shower", "ventilation", "consumables",
                        "decorating", "waste"}
ALLOWED_INT_LITERALS = set(range(11)) | {1000}   # structural counts and mm->m; never a factor
FUNCS: dict[str, Callable[..., Decimal]] = {
    "ceil": lambda x: x.to_integral_value(rounding=ROUND_CEILING),
    "floor": lambda x: x.to_integral_value(rounding=ROUND_FLOOR),
    "max": lambda *a: max(a),
    "min": lambda *a: min(a),
}


# --------------------------------------------------------------------------- helpers


def load(name: str) -> dict[str, Any]:
    data = yaml.safe_load((KIT_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict), name
    return data


def notes_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(NOTES_DIR.glob("*.md")))


def params() -> dict[str, Any]:
    return load("parameters")


def uniclass_verified(code: str, title: str, notes: str) -> bool:
    """Code and title as checked live in the notes: either in full ("Pr_40_20_93_94 WC pans") or
    as a sibling written after its parent ("Pr_40_20 ... _93_89 WC cisterns")."""
    if f"{code} {title}" in notes:
        return True
    parts = code.split("_")
    prefix, suffix = "_".join(parts[:3]), "_" + "_".join(parts[3:])
    return len(parts) > 3 and prefix in notes and f"{suffix} {title}" in notes


def lines(t: Mapping[str, Any]) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    for g in t["groups"]:
        for line in g["lines"]:
            yield g, line


def provenance_holders(name: str) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    if name == "parameters":
        p = params()
        for k, v in p["parameters"].items():
            yield f"parameters.{k}", v["provenance"]
        for k, v in p["lookups"].items():
            yield f"lookups.{k}", v["provenance"]
        return
    t = load(name)
    for _, line in lines(t):
        yield f"line {line['id']}", line["provenance"]
    for r in t["rules"]:
        yield f"rule {r['id']}", r["provenance"]


def check_formula(expr: str, names: set[str]) -> ast.Expression:
    """Parse a quantity formula; allow only arithmetic, declared names and whitelisted calls."""
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Expression | ast.Load | ast.operator | ast.unaryop):
            if isinstance(node, ast.operator) and not isinstance(
                    node, ast.Add | ast.Sub | ast.Mult | ast.Div):
                raise ValueError(f"operator {type(node).__name__} not allowed in {expr!r}")
            continue
        if isinstance(node, ast.BinOp | ast.UnaryOp):
            continue
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, int):
                raise ValueError(f"literal {node.value!r} in {expr!r}: use a named parameter")
            if node.value not in ALLOWED_INT_LITERALS:
                raise ValueError(f"literal {node.value} in {expr!r}: use a named parameter")
            continue
        if isinstance(node, ast.Call):
            if not (isinstance(node.func, ast.Name) and node.func.id in FUNCS) or node.keywords:
                raise ValueError(f"call not allowed in {expr!r}")
            continue
        if isinstance(node, ast.Name):
            if node.id not in names and node.id not in FUNCS:
                raise ValueError(f"undeclared name {node.id!r} in {expr!r}")
            continue
        raise ValueError(f"syntax {type(node).__name__} not allowed in {expr!r}")
    return tree


def evaluate(expr: str, env: Mapping[str, Decimal]) -> Decimal:
    tree = check_formula(expr, set(env))

    def ev(n: ast.AST) -> Decimal:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            return Decimal(str(n.value))
        if isinstance(n, ast.Name):
            return env[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd):
            return ev(n.operand)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            return a / b
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            return FUNCS[n.func.id](*(ev(a) for a in n.args))
        raise ValueError(type(n).__name__)

    return ev(tree)


def check_condition(expr: str, variants: Mapping[str, Any]) -> ast.Expression:
    """A `when` condition: declared variants, ==/!=/in against declared values, and/or/not."""
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            if not isinstance(node.left, ast.Name) or len(node.comparators) != 1:
                raise ValueError(f"comparison must be <variant> op <value> in {expr!r}")
            var = variants.get(node.left.id)
            if var is None or var["type"] != "enum":
                raise ValueError(f"{node.left.id!r} is not a declared enum variant in {expr!r}")
            right = node.comparators[0]
            vals = [right] if isinstance(right, ast.Constant) else getattr(right, "elts", None)
            if vals is None or not all(isinstance(v, ast.Constant) for v in vals):
                raise ValueError(f"right side must be literal value(s) in {expr!r}")
            for v in vals:
                assert isinstance(v, ast.Constant)
                if v.value not in var["values"]:
                    raise ValueError(f"{v.value!r} is not a value of {node.left.id} in {expr!r}")
        elif isinstance(node, ast.Name):
            if node.id not in variants:
                raise ValueError(f"undeclared variant {node.id!r} in {expr!r}")
        elif not isinstance(node, ast.Expression | ast.BoolOp | ast.And | ast.Or | ast.UnaryOp
                            | ast.Not | ast.Load | ast.Eq | ast.NotEq | ast.In | ast.NotIn
                            | ast.Constant | ast.Tuple | ast.List):
            raise ValueError(f"syntax {type(node).__name__} not allowed in {expr!r}")
    return tree


_CHECKED: dict[tuple[str, int], ast.Expression] = {}


def holds(expr: str | None, choice: Mapping[str, Any], variants: Mapping[str, Any]) -> bool:
    if expr is None:
        return True
    key = (expr, id(variants))
    if key not in _CHECKED:
        _CHECKED[key] = check_condition(expr, variants)
    tree = _CHECKED[key]

    def ev(n: ast.AST) -> Any:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]
            return all(vals) if isinstance(n.op, ast.And) else any(vals)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not ev(n.operand)
        if isinstance(n, ast.Name):
            return choice[n.id]
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Tuple | ast.List):
            return [ev(e) for e in n.elts]
        if isinstance(n, ast.Compare):
            left, right, op = ev(n.left), ev(n.comparators[0]), n.ops[0]
            if isinstance(op, ast.Eq):
                return left == right
            if isinstance(op, ast.NotEq):
                return left != right
            if isinstance(op, ast.In):
                return left in right
            if isinstance(op, ast.NotIn):
                return left not in right
        raise ValueError(type(n).__name__)

    return bool(ev(tree))


def condition_names(t: Mapping[str, Any]) -> set[str]:
    exprs = [g.get("when") for g in t["groups"]] + [line.get("when") for _, line in lines(t)]
    exprs += [r.get("when") for r in t["rules"]]
    return {n.id for e in exprs if e for n in ast.walk(ast.parse(e, mode="eval"))
            if isinstance(n, ast.Name)}


def combos(t: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    """Every combination of the variants that appear in a condition; the rest stay at default
    (they cannot change which lines are active, e.g. shower_kw only selects a lookup row)."""
    variants = t["variants"]
    used = condition_names(t)
    keys = [k for k in variants if k in used]
    fixed = {k: v["default"] for k, v in variants.items() if k not in used}
    domains = [[False, True] if variants[k]["type"] == "bool" else list(variants[k]["values"])
               for k in keys]
    for values in itertools.product(*domains):
        yield {**fixed, **dict(zip(keys, values, strict=True))}


def active_lines(t: Mapping[str, Any], choice: Mapping[str, Any]) -> set[str]:
    v = t["variants"]
    return {line["id"] for g, line in lines(t)
            if holds(g.get("when"), choice, v) and holds(line.get("when"), choice, v)}


def sample_env(t: Mapping[str, Any]) -> dict[str, Decimal]:
    env = {k: Decimal(p["value"]) for k, p in params()["parameters"].items()}
    env.update({k: Decimal(i["sample"]) for k, i in t["inputs"].items()})
    for k, d in (t.get("derived") or {}).items():
        env[k] = evaluate(d["formula"], env)
    return env


# --------------------------------------------------------------------------- the helpers themselves


@pytest.mark.parametrize("bad", ["__import__('os')", "x ** 2", "1.1 * x", "x * 300", "y + 1",
                                 "x.real", "[x][0]", "ceil(x, key=1)", "'a'"])
def test_the_formula_checker_rejects_unsafe_or_hard_coded_expressions(bad: str) -> None:
    with pytest.raises(ValueError):
        check_formula(bad, {"x"})


def test_the_evaluator_uses_decimal_and_ceil_rounds_up() -> None:
    env = {"a": Decimal("2.88"), "b": Decimal("10.1")}
    assert evaluate("ceil(b / a)", env) == Decimal(4)
    assert evaluate("b * (1 + a) - 1", env) == Decimal("10.1") * Decimal("3.88") - 1
    assert isinstance(evaluate("max(a, b)", env), Decimal)


def test_the_condition_checker_rejects_unknown_variants_and_values() -> None:
    v = {"wc_type": {"type": "enum", "values": ["close_coupled", "wall_hung"]},
         "layout_change": {"type": "bool"}}
    assert holds("wc_type == 'wall_hung' and not layout_change",
                 {"wc_type": "wall_hung", "layout_change": False}, v)
    for bad in ("wc_type == 'back_to_wall'", "wall_type == 'stud'", "layout_change == 1",
                "__import__('os')"):
        with pytest.raises(ValueError):
            check_condition(bad, v)


# --------------------------------------------------------------------------- files and labels


def test_all_kit_files_and_the_readme_exist() -> None:
    for name in (*TEMPLATES, "parameters"):
        assert (KIT_DIR / f"{name}.yaml").is_file(), name
    assert README.is_file()


@pytest.mark.parametrize("name", (*TEMPLATES, "parameters"))
def test_every_file_is_labelled_synthetic_and_needs_tradesperson_review(name: str) -> None:
    t = load(name)
    assert t["id"].startswith("uk.") and t["version"] and isinstance(t["version"], str)
    assert "synthetic" in t["label"] and "tradesperson review required" in t["label"]
    assert t["status"] == "needs_tradesperson_review"


def test_readme_states_licensing_policy_and_review_status() -> None:
    text = README.read_text(encoding="utf-8")
    for must in ("Uniclass 2015 © NBS, CC BY-ND 4.0", "ODC-By", "M3NHF", "SFG20", "BIMobject",
                 "ECLASS", "Spon", "BCIS", "needs_tradesperson_review", "verbatim"):
        assert must in text, must
    for name in TEMPLATES:
        assert f"{name}.yaml" in text, name


# --------------------------------------------------------------------------- provenance


@pytest.mark.parametrize("name", (*TEMPLATES, "parameters"))
def test_every_line_rule_and_parameter_cites_an_allowed_source_from_the_notes(name: str) -> None:
    notes = notes_text()
    holders = list(provenance_holders(name))
    assert holders
    for where, prov in holders:
        assert isinstance(prov, list) and prov, f"{where}: no provenance"
        for p in prov:
            assert p["source_title"].strip(), where
            url = p["url"]
            assert url.startswith("https://") or url.startswith("http://"), (where, url)
            assert url in notes, f"{where}: {url} is not a source in the research notes"
            assert p["licence"] in LICENCES, (where, p["licence"])
            assert p["evidence_quality"] in EVIDENCE, (where, p["evidence_quality"])
            if p["evidence_quality"] == "derived":
                assert p.get("derived_from", "").strip(), f"{where}: derived without derived_from"
            low = url.lower()
            assert not [x for x in EXCLUDED_URL_PARTS if x in low], (where, url)


@pytest.mark.parametrize("name", TEMPLATES)
def test_lines_are_generic_specs_without_brand_names(name: str) -> None:
    for _, line in lines(load(name)):
        text = f"{line['description']} {line['spec']}".lower()
        hits = [b for b in BRANDS if re.search(rf"\b{re.escape(b.strip())}\b", text)]
        assert not hits, (line["id"], hits)


@pytest.mark.parametrize("name", TEMPLATES)
def test_classification_codes_are_only_those_verified_in_the_notes(name: str) -> None:
    notes = notes_text()
    t = load(name)
    assert "Uniclass 2015 © NBS, CC BY-ND 4.0" in t["classification_attribution"]["uniclass"]
    assert "ODC-By" in t["classification_attribution"]["etim"]
    for _, line in lines(t):
        u = line.get("uniclass_pr")
        if u:
            assert re.fullmatch(r"Pr_\d\d(_\d\d){1,3}", u["code"]), line["id"]
            assert uniclass_verified(u["code"], u["title"], notes), (line["id"], u)
            assert u["version"].startswith("Pr v"), line["id"]
        e = line.get("etim_class")
        if e:
            assert re.search(rf"{e['code']} {re.escape(e['title'])}", notes), (line["id"], e)
            assert e["version"] == "ETIM 10.1", line["id"]


# --------------------------------------------------------------------------- structure and formulas


@pytest.mark.parametrize("name", TEMPLATES)
def test_structure_ids_units_and_groups(name: str) -> None:
    t = load(name)
    ids = [line["id"] for _, line in lines(t)]
    assert len(ids) == len(set(ids)), "duplicate line ids"
    group_ids = [g["id"] for g in t["groups"]]
    assert len(group_ids) == len(set(group_ids))
    for g, line in lines(t):
        assert line["unit"] in UNITS, (line["id"], line["unit"])
        assert isinstance(line["quantity"], str), line["id"]
        assert line["description"].strip() and line["spec"].strip(), line["id"]
        assert g["lines"], g["id"]
    if name == "bathroom_full":
        assert REQUIRED_FULL_GROUPS <= set(group_ids), REQUIRED_FULL_GROUPS - set(group_ids)
        new_wall = next(g for g in t["groups"] if g["id"] == "new_wall")
        assert new_wall["when"] == "layout_change"


def test_parameters_are_decimal_strings_with_units() -> None:
    p = params()
    for k, v in p["parameters"].items():
        assert isinstance(v["value"], str), k
        Decimal(v["value"])
        assert v["unit"].strip() and v["description"].strip(), k
    for needed in ("tile_waste_factor", "bathroom_extract_l_s", "sanitary_extract_l_s",
                   "adhesive_kg_per_m2_per_mm", "grout_formula_constant",
                   "plasterboard_screw_centres_mm"):
        assert needed in p["parameters"], needed


@pytest.mark.parametrize("name", TEMPLATES)
def test_formulas_reference_only_declared_inputs_and_parameters(name: str) -> None:
    t = load(name)
    env = sample_env(t)  # also evaluates every derived value in declaration order
    for k, i in t["inputs"].items():
        assert i["unit"].strip() and i["description"].strip(), k
        assert k not in params()["parameters"], f"input {k} shadows a parameter"
    for _, line in lines(t):
        q = evaluate(line["quantity"], env)
        assert q >= 0, (line["id"], q)
        if line["unit"] in COUNT_UNITS:
            assert q == q.to_integral_value(), f"{line['id']}: {q} {line['unit']} is not whole"


@pytest.mark.parametrize("name", TEMPLATES)
def test_spec_placeholders_and_lookups_resolve(name: str) -> None:
    t, p = load(name), params()
    for _, line in lines(t):
        for ref in re.findall(r"\{(\w+)\}", line["spec"]):
            assert ref in p["parameters"], (line["id"], ref)
        lk = line.get("spec_lookup")
        if lk:
            table = p["lookups"][lk["table"]]
            var = t["variants"][lk["key"]]
            assert table["key_variant"] == lk["key"]
            assert set(var["values"]) <= set(table["rows"]), (line["id"], var["values"])


def test_tile_quantity_uses_the_profile_waste_factor_not_a_literal() -> None:
    t = load("bathroom_full")
    tiles = next(line for _, line in lines(t) if line["id"] == "tl_wall_tiles")
    env = sample_env(t)
    waste = Decimal(params()["parameters"]["tile_waste_factor"]["value"])
    assert evaluate(tiles["quantity"], env) == Decimal(t["inputs"]["wall_tiled_m2"]["sample"]) * (
        1 + waste)


# --------------------------------------------------------------------------- variants and rules


@pytest.mark.parametrize("name", TEMPLATES)
def test_variants_and_conditions_are_declared(name: str) -> None:
    t = load(name)
    for k, v in t["variants"].items():
        assert v["question"].strip(), k
        assert v["type"] in {"bool", "enum"}, k
        if v["type"] == "enum":
            assert v["values"] and v["default"] in v["values"], k
        else:
            assert isinstance(v["default"], bool), k
    for g in t["groups"]:
        if g.get("when"):
            check_condition(g["when"], t["variants"])
        for line in g["lines"]:
            if line.get("when"):
                check_condition(line["when"], t["variants"])
    for r in t["rules"]:
        if r.get("when"):
            check_condition(r["when"], t["variants"])


@pytest.mark.parametrize("name", TEMPLATES)
def test_rules_reference_existing_lines_and_hold_for_every_variant_combination(name: str) -> None:
    t = load(name)
    ids = {line["id"] for _, line in lines(t)}
    for r in t["rules"]:
        refs = set(r.get("requires", [])) | set(r.get("excludes", []))
        assert refs, r["id"]
        assert refs <= ids, (r["id"], refs - ids)
        assert r["rationale"].strip(), r["id"]
    n = 0
    for choice in combos(t):
        n += 1
        active = active_lines(t, choice)
        for r in t["rules"]:
            if holds(r.get("when"), choice, t["variants"]):
                missing = set(r.get("requires", [])) - active
                clash = set(r.get("excludes", [])) & active
                assert not missing and not clash, (r["id"], choice, missing, clash)
    assert n >= 2


def test_wall_hung_wc_needs_frame_plate_and_pan_but_no_separate_110mm_connector() -> None:
    for name in ("bathroom_full", "bathroom_cloakroom", "wc_replacement"):
        t = load(name)
        rule = next(r for r in t["rules"] if r["id"] == "wall_hung_wc")
        assert rule["when"] == "wc_type == 'wall_hung'"
        assert {"sw_wc_frame", "sw_wc_flush_plate", "sw_wc_pan_wall_hung"} <= set(rule["requires"])
        assert "sw_wc_pan_connector" in rule["excludes"]


def test_electric_shower_rule_and_circuit_lookup() -> None:
    t, p = load("bathroom_full"), params()
    rule = next(r for r in t["rules"] if r["id"] == "electric_shower")
    assert {"el_shower_isolator", "el_shower_rcbo", "el_shower_cable"} <= set(rule["requires"])
    table = p["lookups"]["electric_shower_circuit"]
    capacity = p["lookups"]["twin_earth_current_capacity_a"]["rows"]
    manufacturer_min = Decimal(p["parameters"]["electric_shower_cable_min_mm2"]["value"])
    sizes = sorted(capacity, key=Decimal)
    for kw, row in table["rows"].items():
        mcb = max(Decimal(a) for a in row["mcb_a_options"])
        for method, chosen in row["cable_mm2_by_method"].items():
            expect = next(s for s in sizes if Decimal(s) >= manufacturer_min
                          and Decimal(capacity[s][method]) >= mcb)
            assert chosen == expect, (kw, method, chosen, expect)


def test_extractor_rule_requires_isolator_duct_and_condensation_trap() -> None:
    for name in TEMPLATES:
        t = load(name)
        rule = next((r for r in t["rules"] if r["id"] == "extractor_fan"), None)
        if rule is None:
            assert name == "wc_replacement"
            continue
        assert {"vn_fan", "el_fan_isolator", "vn_duct", "vn_condensation_trap"} <= set(
            rule["requires"])

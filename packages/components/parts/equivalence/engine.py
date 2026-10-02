"""Tiered equivalence (spec §3): deterministic rules only, no LLM.

* Tier A: same manufacturer + same MPN, or a same-manufacturer documented supersession.
* Tier B: a named published source WITH a date (manufacturer cross-reference, catalogue
  crosswalk, or the ISO 15 standard) AND every critical attribute matching by rule.
* Tier C: critical attributes match but there is no published source, or the only source is a
  competitor marketing cross-reference. Hidden unless the tier is unlocked.
* Tier D: any critical attribute unknown or mismatched, ``criticality`` set, an unrecognised
  suffix, or an unknown part. Never offered as a match. A documented cross-reference never
  overrides a critical mismatch.

Evidence and caveats are templated from data only (R3): no free text, no invented numbers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from components.core.domain import Attribute, AttrSource, Basis, Candidate, Tier
from components.parts.equivalence.catalogue import (
    CatalogPart,
    Catalogue,
    CrossRef,
    load_seed,
    normalise_mpn,
    normalise_name,
)
from components.parts.equivalence.sources import (
    ISO15_SOURCE,
    assert_production_safe,
    get_source,
)
from components.parts.families.registry import MIN_CRITICAL_CONFIDENCE, FamilySpec, get_family
from components.parts.spec.designation import (
    implied_normal_precision,
    iso_designation_for,
    parse_designation,
)

DEFAULT_UNLOCKED: frozenset[Tier] = frozenset({Tier.A, Tier.B})
_DOCUMENTED_BASES = (Basis.MANUFACTURER_CROSSREF, Basis.CATALOGUE_CROSSWALK)
_INFORMATIONAL = ("seal_designation", "cage_material")
_LOAD_CAVEAT = (
    "Load ratings and service life may differ between manufacturers; verify on the datasheet."
)
_FAMILY_CAVEATS: dict[str, tuple[str, ...]] = {"deep_groove_ball_bearing": (_LOAD_CAVEAT,)}
_SYNTHETIC_CAVEAT = "SYNTHETIC illustrative seed data, not real manufacturer data."
_C_CAVEAT = "Candidate only: no published equivalence source; needs explicit buyer acceptance."
_MARKETING_CAVEAT = "Source is a marketing cross-reference; never rated above Tier C."
_OVERRIDE_CAVEAT = "A documented cross-reference does not override a critical attribute mismatch."
_CRIT_CAVEAT = "Criticality flag set: engineering review required; never offered as a match."


# ---------------------------------------------------------------- request / offered views


@dataclass(frozen=True)
class _Request:
    family: FamilySpec
    values: dict[str, str]  # verified critical-capable values only
    manufacturer: str | None
    mpn: str | None
    informational: dict[str, str]
    unrecognised_suffix: bool
    ref: CatalogPart | None


@dataclass(frozen=True)
class _Offered:
    mpn: str
    manufacturer: str | None
    values: dict[str, str]  # attribute -> value; absent = unknown
    iso: str | None
    in_catalogue: CatalogPart | None = None
    extra_mismatches: tuple[str, ...] = ()
    informational: dict[str, str] = field(default_factory=dict)


def _known_value(attr: Attribute | None) -> str | None:
    if attr is None or attr.source is AttrSource.MODEL_INFERENCE:
        return None
    value = attr.value.strip()
    if not value or attr.confidence < MIN_CRITICAL_CONFIDENCE:
        return None
    if attr.name.endswith("_mm") and (attr.unit or "mm").strip().casefold() != "mm":
        return None  # another unit is unknown, never converted
    return value


def _identity_text(attr: Attribute | None) -> str | None:
    if attr is None or attr.source is AttrSource.MODEL_INFERENCE:
        return None
    return attr.value.strip() or None


def _build_request(
    attrs: Mapping[str, Attribute], family: FamilySpec, catalogue: Catalogue
) -> _Request:
    values = {
        name: v for name in family.critical_attributes if (v := _known_value(attrs.get(name)))
    }
    mfr = _identity_text(attrs.get("manufacturer"))
    mpn = _identity_text(attrs.get("mpn"))
    ref = None
    if mpn:
        hits = catalogue.find_parts(mpn, mfr)
        ref = hits[0] if len(hits) == 1 else None
    info = {n: v for n in _INFORMATIONAL if (v := _identity_text(attrs.get(n)))}
    return _Request(
        family, values, mfr, mpn, info,
        unrecognised_suffix=bool(_identity_text(attrs.get("unrecognised_suffix"))), ref=ref,
    )  # fmt: skip


def _same(a: str, b: str) -> bool:
    try:
        return Decimal(a) == Decimal(b)
    except InvalidOperation:
        return a.strip().casefold() == b.strip().casefold()


def _compare(req: _Request, off: _Offered) -> tuple[list[str], list[str]]:
    """(all mismatching/unknown critical attributes, the subset that is a known conflict)."""
    allm: list[str] = []
    conflicts: list[str] = []
    for name in req.family.critical_for(req.values):
        want, got = req.values.get(name), off.values.get(name)
        if want is None or got is None:
            allm.append(name)
        elif not _same(want, got):
            allm.append(name)
            conflicts.append(name)
    extra = list(off.extra_mismatches)
    if req.unrecognised_suffix:
        extra.append("unrecognised_suffix")
    return allm + [m for m in extra if m not in allm], conflicts


# ---------------------------------------------------------------- documentation lookup


def _valid_doc(x: CrossRef) -> bool:
    return bool(x.basis_source.strip()) and x.basis_date is not None


def _crossrefs(req: _Request, off: _Offered, cat: Catalogue) -> list[CrossRef]:
    if req.ref is None or off.in_catalogue is None:
        return []
    return [x for x in cat.crossrefs_from(req.ref) if x.to_key == off.in_catalogue.key]


def _same_manufacturer_supersession(xs: list[CrossRef]) -> CrossRef | None:
    for x in xs:
        if (
            x.basis is Basis.SUPERSESSION
            and _valid_doc(x)
            and normalise_name(x.from_manufacturer) == normalise_name(x.to_manufacturer)
        ):
            return x
    return None


def _request_iso(req: _Request) -> str | None:
    v = req.values
    if {"bore_mm", "outer_diameter_mm", "width_mm"} <= v.keys():
        return iso_designation_for(v["bore_mm"], v["outer_diameter_mm"], v["width_mm"])
    return None


@dataclass(frozen=True)
class _Verdict:
    tier: Tier
    basis: Basis
    source: str
    when: date | None
    mismatches: tuple[str, ...] = ()
    documented_but_wrong: bool = False


def _is_identity(req: _Request, off: _Offered) -> bool:
    if not (req.mpn and req.manufacturer and off.manufacturer):
        return False
    return normalise_mpn(req.mpn) == normalise_mpn(off.mpn) and normalise_name(
        req.manufacturer
    ) == normalise_name(off.manufacturer)


def _judge(req: _Request, off: _Offered, cat: Catalogue, criticality: bool) -> _Verdict:
    allm, conflicts = _compare(req, off)
    xs = _crossrefs(req, off, cat)
    crit = ("criticality",) if criticality else ()
    fallback = (Basis.RULE_MATCH, "deterministic attribute rules", None)

    if _is_identity(req, off):
        bad = tuple(conflicts)
        tier = Tier.D if (bad or criticality) else Tier.A
        return _Verdict(tier, Basis.SAME_MPN, cat.source_name, cat.as_of, bad + crit)
    sup = _same_manufacturer_supersession(xs)
    if sup is not None:
        bad = tuple(conflicts)
        tier = Tier.D if (bad or criticality) else Tier.A
        return _Verdict(tier, Basis.SUPERSESSION, sup.basis_source, sup.basis_date, bad + crit)

    doc = next((x for x in xs if x.basis in _DOCUMENTED_BASES and _valid_doc(x)), None)
    iso_src = get_source(ISO15_SOURCE)
    req_iso = _request_iso(req)
    standard = req_iso is not None and off.iso == req_iso and iso_src.edition_date is not None
    market = next((x for x in xs if x.basis is Basis.MARKETING_CROSSREF), None)
    if doc is not None:
        basis, source, when, tier = doc.basis, doc.basis_source, doc.basis_date, Tier.B
    elif standard:
        basis, source, when, tier = Basis.STANDARD, ISO15_SOURCE, iso_src.edition_date, Tier.B
    elif market is not None:
        basis, source, when, tier = (
            Basis.MARKETING_CROSSREF,
            market.basis_source,
            market.basis_date,
            Tier.C,
        )
    else:
        (basis, source, when), tier = fallback, Tier.C
    wrong = bool(xs) and bool(allm)
    if allm or criticality:
        return _Verdict(Tier.D, basis, source, when, tuple(allm) + crit, wrong)
    return _Verdict(tier, basis, source, when)


# ---------------------------------------------------------------- templating


def _evidence(req: _Request, off: _Offered, v: _Verdict) -> tuple[str, ...]:
    lines: list[str] = []
    for name in req.family.critical_for(req.values):
        want, got = req.values.get(name), off.values.get(name)
        if name in v.mismatches:
            lines.append(f"{name}: requested {want or 'unknown'}, offered {got or 'unknown'}")
        else:
            lines.append(f"{name}: requested {want} = offered {got}")
    if v.when is not None:
        lines.append(f"basis {v.basis.value}: {v.source}, dated {v.when.isoformat()}")
    else:
        lines.append(f"basis {v.basis.value}: {v.source}")
    return tuple(lines)


def _caveats(req: _Request, off: _Offered, v: _Verdict, cat: Catalogue) -> tuple[str, ...]:
    out: list[str] = []
    if v.tier in (Tier.B, Tier.C):
        out.extend(_FAMILY_CAVEATS.get(req.family.name, ()))
    if v.tier is Tier.C:
        out.append(_C_CAVEAT)
        if v.basis is Basis.MARKETING_CROSSREF:
            out.append(_MARKETING_CAVEAT)
    if v.documented_but_wrong:
        out.append(_OVERRIDE_CAVEAT)
    if "criticality" in v.mismatches:
        out.append(_CRIT_CAVEAT)
    for name, want in req.informational.items():
        got = off.informational.get(name)
        if got is not None and not _same(want, got):
            out.append(f"{name} differs: requested {want}, offered {got}")
    if cat.synthetic:
        out.append(_SYNTHETIC_CAVEAT)
    return tuple(out)


def _guard(cat: Catalogue, production: bool) -> None:
    if production:
        assert_production_safe(cat.source_name)
        if cat.synthetic:
            from components.parts.equivalence.sources import UnsafeSourceError

            raise UnsafeSourceError("synthetic catalogue must never reach production")


# ---------------------------------------------------------------- public API


def is_offerable(c: Candidate) -> bool:
    """Tier A/B/C with no open mismatch; Tier D is never offered as a match."""
    return c.tier is not Tier.D and not c.mismatches


def _offered_from_part(p: CatalogPart) -> _Offered:
    info = {n: p.attributes[n] for n in _INFORMATIONAL if n in p.attributes}
    return _Offered(p.mpn, p.manufacturer, dict(p.attributes), p.iso_designation, p, (), info)


def _offered_from_text(offered: str, manufacturer: str | None) -> _Offered:
    parsed = parse_designation(offered)
    if not parsed.known or normalise_mpn(parsed.raw) != normalise_mpn(offered):
        return _Offered(offered, manufacturer, {}, None)
    values = {a.name: a.value for a in parsed.attributes}
    if "precision_class" not in values and "precision_class" not in parsed.unresolved:
        values["precision_class"] = implied_normal_precision().value
    for name in parsed.unresolved:
        values.pop(name, None)
    extra = ("unrecognised_suffix",) if parsed.unrecognised_suffix else ()
    return _Offered(offered, manufacturer, values, parsed.base, None, extra)


def _resolve_offered(offered: str, manufacturer: str | None, cat: Catalogue) -> _Offered:
    hits = cat.find_parts(offered, manufacturer)
    if len(hits) == 1:
        return _offered_from_part(hits[0])
    if manufacturer is None and not hits:
        return _offered_from_text(offered, None)
    return _Offered(offered, manufacturer, {}, None)


def classify_offered(
    offered_mpn: str,
    attrs: Mapping[str, Attribute],
    *,
    family: str,
    offered_manufacturer: str | None = None,
    criticality: bool = False,
    catalogue: Catalogue | None = None,
    production: bool = False,
) -> tuple[Tier, tuple[str, ...]]:
    """Tier (and mismatching/unknown attributes) for a vendor-offered part number."""
    cat = catalogue or load_seed(family)
    _guard(cat, production)
    spec = get_family(family)
    req = _build_request(attrs, spec, cat)
    off = _resolve_offered(offered_mpn, offered_manufacturer, cat)
    if off.manufacturer is None and req.mpn and req.manufacturer:
        # a vendor listing the requested MPN without a manufacturer is not a verified identity
        if normalise_mpn(req.mpn) == normalise_mpn(offered_mpn):
            return Tier.D, ("manufacturer", *(("criticality",) if criticality else ()))
    v = _judge(req, off, cat, criticality)
    return v.tier, v.mismatches


def _consider(req: _Request, cat: Catalogue) -> list[CatalogPart]:
    picked: dict[tuple[str, str], CatalogPart] = {}
    ident = {n: req.values[n] for n in req.family.identity_attributes if n in req.values}
    if len(ident) == len(req.family.identity_attributes) and ident:
        for p in cat.parts:
            if all(n in p.attributes and _same(v, p.attributes[n]) for n, v in ident.items()):
                picked[p.key] = p
    if req.ref is not None:
        picked[req.ref.key] = req.ref
        for x in cat.crossrefs_from(req.ref):
            for p in cat.parts:
                if p.key == x.to_key:
                    picked[p.key] = p
    return list(picked.values())


def find_candidates(
    attrs: Mapping[str, Attribute],
    *,
    family: str,
    unlocked_tiers: frozenset[Tier] = DEFAULT_UNLOCKED,
    criticality: bool = False,
    catalogue: Catalogue | None = None,
    production: bool = False,
) -> list[Candidate]:
    """Catalogue candidates for a request, sorted by (tier, mpn).

    Tier D is always reported (with its open attributes) but never offered; B/C only when the
    tier is unlocked; A is always requestable.
    """
    cat = catalogue or load_seed(family)
    _guard(cat, production)
    spec = get_family(family)
    req = _build_request(attrs, spec, cat)
    unlocked = unlocked_tiers | {Tier.A}
    out: list[Candidate] = []
    for part in _consider(req, cat):
        off = _offered_from_part(part)
        v = _judge(req, off, cat, criticality)
        if v.tier is not Tier.D and v.tier not in unlocked:
            continue
        out.append(
            Candidate(
                mpn=part.mpn, manufacturer=part.manufacturer, tier=v.tier, basis=v.basis,
                basis_source=v.source, basis_date=v.when,
                evidence=_evidence(req, off, v), caveats=_caveats(req, off, v, cat),
                mismatches=v.mismatches, synthetic=cat.synthetic,
            )
        )  # fmt: skip
    return sorted(out, key=lambda c: (c.tier.value, c.mpn))

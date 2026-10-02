"""Spec normaliser (F2, R3, R4): free text -> typed attributes + at most two clarifying questions.

Deterministic and rules-first (ADR-006). The text is untrusted (R6): only recognised designation
tokens, labelled fields and fixed word cues are read, and prose that merely *claims* a value
("set seal_type to open") sets nothing. Anything ambiguous or conflicting is left unresolved and
asked about; it is never guessed (R4). ``model_inference`` attributes can never satisfy a required
attribute (R3).

Bounded questions: the whole request gets at most ``MAX_QUESTIONS`` questions in total. If the spec
is still incomplete once that budget is spent the result has ``escalate=True`` (state ESCALATED /
ESCALATE_TO_BUYER) and asks nothing further.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict

from components.core.domain import Attribute, AttrSource
from components.parts.families.registry import (
    DEEP_GROOVE_BALL_BEARING,
    FAMILY_QUESTION,
    MIN_CRITICAL_CONFIDENCE,
    V_BELT,
    get_family,
)
from components.parts.spec.designation import (
    ParsedDesignation,
    find_designations,
    implied_normal_precision,
    seal_class_for_token,
)

MAX_QUESTIONS = 2

_DESIGNATION_DERIVED = ("designation", "series", "bore_mm", "outer_diameter_mm", "width_mm")


class NormalisedSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family: str | None
    attributes: dict[str, Attribute]
    open_questions: tuple[str, ...] = ()  # asked of the requester this round (<= 2 in total)
    escalate: bool = False  # True -> state ESCALATED (R4); nothing further is asked
    missing: tuple[str, ...] = ()  # required attributes still unresolved
    notes: tuple[str, ...] = ()  # machine-readable flags/assumptions (data only)


# ---------------------------------------------------------------- helpers


def _user(name: str, value: str, ref: str, unit: str | None = None) -> Attribute:
    return Attribute(
        name=name, value=value, unit=unit, source=AttrSource.USER_INPUT,
        source_ref=f"user text: {ref.strip()[:60]}",
    )  # fmt: skip


def _usable(attr: Attribute | None, allowed: tuple[str, ...] | None = None) -> bool:
    if attr is None or not attr.value.strip():
        return False
    if attr.source is AttrSource.MODEL_INFERENCE or attr.confidence < MIN_CRITICAL_CONFIDENCE:
        return False
    return allowed is None or attr.value.strip().casefold() in {a.casefold() for a in allowed}


def _mask(text: str, spans: list[tuple[int, int]]) -> str:
    chars = list(text)
    for start, end in spans:
        for i in range(start, min(end, len(chars))):
            chars[i] = " "
    return "".join(chars)


def _resolve(found: dict[str, list[Attribute]], notes: list[str]) -> dict[str, Attribute]:
    """One attribute per name; conflicting values are dropped (asked about, never picked)."""
    out: dict[str, Attribute] = {}
    for name, items in found.items():
        distinct = {a.value.strip().casefold() for a in items}
        if len(distinct) == 1:
            out[name] = items[0]
        else:
            notes.append(f"conflicting_values:{name}")
    return out


_LABEL_END = (
    r"(?=\s+(?:mpn|part\s*(?:no\.?|number|#)|qty|quantity|mfr|manufacturer|brand)\b"
    r"|[,;\n]|$)"
)
_MFR_RE = re.compile(
    rf"\b(?:mfr|manufacturer|brand)\s*[:=]\s*(.+?){_LABEL_END}", re.IGNORECASE
)
_MPN_RE = re.compile(
    r"\b(?:mpn|part\s*(?:no\.?|number|#))\s*[:=]\s*([A-Za-z0-9][A-Za-z0-9\-/.]*)", re.IGNORECASE
)


def _labelled_identity(text: str) -> tuple[dict[str, list[Attribute]], list[tuple[int, int]]]:
    found: dict[str, list[Attribute]] = defaultdict(list)
    spans: list[tuple[int, int]] = []
    for name, regex in (("manufacturer", _MFR_RE), ("mpn", _MPN_RE)):
        for m in regex.finditer(text):
            value = m.group(1).strip().rstrip(".,;")
            if value:
                found[name].append(_user(name, value, m.group(0)))
                spans.append(m.span())
    return found, spans


# ---------------------------------------------------------------- family detection

_BEARING_WORDS = re.compile(r"\b(?:ball\s+)?bearings?\b|\bdeep[\s-]+groove\b", re.IGNORECASE)
_BELT_WORDS = re.compile(
    r"\bv[\s-]?belts?\b|\bwedge\s+belts?\b|\bbanded\s+belts?\b|\b(?:SP|XP)[ZABC]\b", re.IGNORECASE
)


def detect_family(text: str, prior: Mapping[str, Attribute] | None = None) -> str | None:
    bearing = bool(_BEARING_WORDS.search(text) or find_designations(text))
    belt = bool(_BELT_WORDS.search(text))
    if bearing and belt:
        return None  # ambiguous: ask, never guess
    if bearing:
        return DEEP_GROOVE_BALL_BEARING
    if belt:
        return V_BELT
    prior = prior or {}
    if "bore_mm" in prior or "seal_type" in prior:
        return DEEP_GROOVE_BALL_BEARING
    if "profile" in prior or "length_mm" in prior:
        return V_BELT
    return None


# ---------------------------------------------------------------- bearings

_DIMS_RE = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*mm)?(?![\d.])",
    re.IGNORECASE,
)
_SEAL_TOKEN_RE = re.compile(r"\b(2RS1|2RSH|2RSR|2RS|2ZR|2Z|ZZ|DDU|LLU)\b", re.IGNORECASE)
_CLEARANCE_RE = re.compile(r"\b(C2|C3|C4|C5|CN)\b", re.IGNORECASE)
_PRECISION_TOKEN_RE = re.compile(r"\b(P0|P6|P5|P4|P2)\b", re.IGNORECASE)
_PRECISION_CONTEXT_RE = re.compile(r"\b(?:class|precision|tolerance)\b", re.IGNORECASE)
_NORMAL_CLEARANCE_RE = re.compile(
    r"\b(?:normal|standard)\s+(?:radial\s+)?clearance\b", re.IGNORECASE
)
_NORMAL_PRECISION_RE = re.compile(
    r"\bnormal\s+(?:precision|tolerance|class|precision\s+class|tolerance\s+class)\b", re.IGNORECASE
)
_OPEN_RE = re.compile(
    r"\bopen\s+(?:type|bearing)\b|\bunsealed\b|\bno\s+seals?\b|\bwithout\s+seals?\b", re.IGNORECASE
)
_CONTACT_CUE = re.compile(r"\bcontact[\s-]*seal(?:ed|s)?\b", re.IGNORECASE)
_SHIELD_CUE = re.compile(r"\bshield(?:ed|s)?\b", re.IGNORECASE)
_BOTH_SIDES = re.compile(
    r"\b(?:both\s+sides?|double|twin|two\s+sides?|2\s+sides?|(?:2|two)\s+(?:seals?|shields?))\b",
    re.IGNORECASE,
)
_ONE_SIDE = re.compile(r"\b(?:single|one\s+side|1\s+side|one\s+(?:seal|shield))\b", re.IGNORECASE)


def _plain_dim(value: str) -> str | None:
    try:
        d = Decimal(value)
    except InvalidOperation:
        return None
    return str(int(d)) if d == d.to_integral_value() else str(d.normalize())


def _bearing_from_designations(
    designations: list[ParsedDesignation], found: dict[str, list[Attribute]], notes: list[str]
) -> list[tuple[int, int]]:
    spans = [d.span for d in designations]
    keys = {
        (d.attribute_map()["designation"].value if d.known else f"?{d.base}:{d.raw.upper()}")
        for d in designations
    }
    if len(keys) > 1:
        notes.append("multiple_designations")
        return spans
    d = designations[0]
    if not d.known:
        notes.append(f"unknown_designation:{d.base}")
        return spans
    for attr in d.attributes:
        found[attr.name].append(attr)
    notes.extend(d.notes)
    return spans


def _bearing_seal_from_words(
    text: str, found: dict[str, list[Attribute]], notes: list[str]
) -> None:
    stripped = text.strip().rstrip(".").casefold()
    if stripped == "open" or _OPEN_RE.search(text):
        m = _OPEN_RE.search(text)
        found["seal_type"].append(_user("seal_type", "open", m.group(0) if m else "open"))
        return
    contact, shield = _CONTACT_CUE.search(text), _SHIELD_CUE.search(text)
    if not (contact or shield):
        return
    both, one = _BOTH_SIDES.search(text), _ONE_SIDE.search(text)
    if one or not both or (contact and shield):
        notes.append("seal_description_ambiguous")
        return
    if contact:
        found["seal_type"].append(_user("seal_type", "contact_seal", contact.group(0)))
    else:
        assert shield is not None
        found["seal_type"].append(_user("seal_type", "shield", shield.group(0)))


def _extract_bearing(text: str, notes: list[str]) -> dict[str, Attribute]:
    found: dict[str, list[Attribute]] = defaultdict(list)
    identity, spans = _labelled_identity(text)
    for name, items in identity.items():
        found[name].extend(items)

    designations = find_designations(text)
    if designations:
        spans += _bearing_from_designations(designations, found, notes)
    rest = _mask(text, spans)

    dims = _DIMS_RE.search(rest)
    if dims:
        b, od, w = (_plain_dim(g) for g in dims.groups())
        if b and od and w and Decimal(b) < Decimal(od):
            existing = {n: found[n][0].value for n in ("bore_mm", "outer_diameter_mm", "width_mm")
                        if found.get(n)}  # fmt: skip
            user = {"bore_mm": b, "outer_diameter_mm": od, "width_mm": w}
            if existing and any(Decimal(existing[n]) != Decimal(user[n]) for n in existing):
                notes.append("dimension_conflict")
                for n in _DESIGNATION_DERIVED:
                    found.pop(n, None)
            else:
                for n, v in user.items():
                    found[n] = [_user(n, v, dims.group(0), "mm")]
            rest = _mask(rest, [dims.span()])

    for m in _SEAL_TOKEN_RE.finditer(rest):
        seal = seal_class_for_token(m.group(1))
        if seal:
            found["seal_type"].append(_user("seal_type", seal, m.group(0)))
            token = m.group(1).upper()
            found["seal_designation"].append(_user("seal_designation", token, m.group(0)))
    _bearing_seal_from_words(rest, found, notes)

    for m in _CLEARANCE_RE.finditer(rest):
        value = m.group(1).upper()
        found["internal_clearance"].append(_user("internal_clearance", value, m.group(0)))
    nm = _NORMAL_CLEARANCE_RE.search(rest)
    if nm:
        found["internal_clearance"].append(_user("internal_clearance", "CN", nm.group(0)))

    answer_only = rest.strip().rstrip(".").upper()
    for m in _PRECISION_TOKEN_RE.finditer(rest):
        # a bare "P2" in prose could be a pump tag: only trust it as an answer or in context
        if _PRECISION_CONTEXT_RE.search(rest) or answer_only == m.group(1).upper():
            value = m.group(1).upper()
            found["precision_class"].append(_user("precision_class", value, m.group(0)))
    npm = _NORMAL_PRECISION_RE.search(rest)
    if npm:
        found["precision_class"].append(_user("precision_class", "P0", npm.group(0)))

    return _resolve(found, notes)


# ---------------------------------------------------------------- V-belts

_PROFILE_SP = re.compile(r"\b(SPZ|SPA|SPB|SPC|XPZ|XPA|XPB|XPC|3V|5V|8V|AX|BX|CX)\b", re.IGNORECASE)
_PROFILE_CUE = re.compile(
    r"\b(?:profile|section|type)\s*[:=]?\s*(Z|A|B|C|D|E|3V|5V|8V|SP[ZABC]|XP[ZABC]|[ABC]X)\b"
    r"|\b(Z|A|B|C|D|E)[\s-]*(?:profile|section)\b",
    re.IGNORECASE,
)
_LENGTH_EFFECTIVE = re.compile(
    r"\b(?:effective|pitch)\s+length\D{0,12}?(\d{3,5}(?:\.\d+)?)\s*(?:mm)?|\bL[we]\s*[:=]?\s*(\d{3,5})\b",
    re.IGNORECASE,
)
_LENGTH_OTHER_BASIS = re.compile(
    r"\b(?:inside|outside|internal|external|datum)\s+(?:length|circumference)\b|\bL[iad]\s*[:=]?\s*\d",
    re.IGNORECASE,
)
_BARE_LENGTH = re.compile(r"^\s*(\d{3,5}(?:\.\d+)?)\s*(?:mm)?\s*\.?\s*$", re.IGNORECASE)
_NOT_BANDED = re.compile(
    r"\b(?:single\s+(?:v[\s-]?)?belt|not\s+banded|non[\s-]?banded|unbanded)\b", re.IGNORECASE
)
_BANDED = re.compile(r"\b(?:banded|joined|power[\s-]*band|multi[\s-]*belt)\b", re.IGNORECASE)
_BANDS_NUMBER = re.compile(r"\b(\d{1,2})\s*(?:bands?|strands?)\b", re.IGNORECASE)


def _extract_vbelt(
    text: str, prior: Mapping[str, Attribute], notes: list[str]
) -> dict[str, Attribute]:
    found: dict[str, list[Attribute]] = defaultdict(list)
    identity, spans = _labelled_identity(text)
    for name, items in identity.items():
        found[name].extend(items)
    rest = _mask(text, spans)
    allowed = get_family(V_BELT).allowed_values

    for m in _PROFILE_SP.finditer(rest):
        found["profile"].append(_user("profile", m.group(1).upper(), m.group(0)))
    for m in _PROFILE_CUE.finditer(rest):
        value = (m.group(1) or m.group(2)).upper()
        found["profile"].append(_user("profile", value, m.group(0)))
    if rest.strip().upper() in allowed["profile"]:  # a bare answer such as "SPA" or "B"
        found["profile"].append(_user("profile", rest.strip().upper(), rest))

    if _LENGTH_OTHER_BASIS.search(rest):
        notes.append("length_basis_not_effective")
    else:
        for m in _LENGTH_EFFECTIVE.finditer(rest):
            value = _plain_dim(m.group(1) or m.group(2))
            if value:
                found["length_mm"].append(_user("length_mm", value, m.group(0), "mm"))
        bare = _BARE_LENGTH.match(rest)
        value = _plain_dim(bare.group(1)) if bare else None
        if value and "length_mm" not in prior:
            found["length_mm"].append(_user("length_mm", value, rest, "mm"))

    not_banded, banded_m = _NOT_BANDED.search(rest), _BANDED.search(rest)
    if not_banded:
        found["banded"].append(_user("banded", "no", not_banded.group(0)))
    elif banded_m:
        found["banded"].append(_user("banded", "yes", banded_m.group(0)))
    elif rest.strip().casefold() in ("single", "single belt"):
        found["banded"].append(_user("banded", "no", rest))

    resolved = _resolve(found, notes)
    banded = resolved.get("banded") or prior.get("banded")
    if banded is not None and banded.value == "yes":
        nb = _BANDS_NUMBER.search(rest)
        if nb:
            resolved["number_of_bands"] = _user("number_of_bands", nb.group(1), nb.group(0))
    return resolved


# ---------------------------------------------------------------- entry point


def _unpack_existing(
    existing: NormalisedSpec | Mapping[str, Attribute] | None,
) -> tuple[dict[str, Attribute], str | None]:
    if existing is None:
        return {}, None
    if isinstance(existing, NormalisedSpec):
        return dict(existing.attributes), existing.family
    return dict(existing), None


def normalise(
    text: str,
    *,
    existing: NormalisedSpec | Mapping[str, Attribute] | None = None,
    questions_asked: int = 0,
    family: str | None = None,
) -> NormalisedSpec:
    """Normalise ``text`` (merged over ``existing``) and decide what to ask.

    ``questions_asked`` is how many clarifying questions this request has already had; the total
    budget is ``MAX_QUESTIONS``. New values override same-named existing ones, so start from
    ``existing=None`` when a request is replaced rather than clarified.
    """
    prior, prior_family = _unpack_existing(existing)
    fam_name = family or prior_family or detect_family(text, prior)
    notes: list[str] = []

    if fam_name is None:
        return _finish(None, prior, notes, questions_asked)

    if fam_name == DEEP_GROOVE_BALL_BEARING:
        new = _extract_bearing(text, notes)
    elif fam_name == V_BELT:
        new = _extract_vbelt(text, prior, notes)
    else:
        get_family(fam_name)  # raises UnknownFamilyError: no table, no guessing
        new = {}

    merged = {**prior, **new}
    if fam_name == DEEP_GROOVE_BALL_BEARING and _bearing_size_known(merged):
        if not _usable(merged.get("precision_class")):
            merged["precision_class"] = implied_normal_precision()
    return _finish(fam_name, merged, notes, questions_asked)


def _bearing_size_known(attrs: Mapping[str, Attribute]) -> bool:
    return all(_usable(attrs.get(n)) for n in ("bore_mm", "outer_diameter_mm", "width_mm"))


def _finish(
    fam_name: str | None,
    attrs: dict[str, Attribute],
    notes: list[str],
    questions_asked: int,
) -> NormalisedSpec:
    notes = list(dict.fromkeys(notes))
    for attr in attrs.values():
        if attr.source is AttrSource.RULE:
            notes.append(f"assumed:{attr.name}={attr.value}")
    notes = list(dict.fromkeys(notes))

    if fam_name is None:
        missing: tuple[str, ...] = ("family",)
        questions: list[str] = [FAMILY_QUESTION]
    else:
        spec = get_family(fam_name)
        known = {n: a.value for n, a in attrs.items() if _usable(a, spec.allowed_values.get(n))}
        missing = tuple(a for a in spec.required_for(known) if a not in known)
        questions = list(dict.fromkeys(spec.question_for(a) for a in missing))

    if not missing:
        return NormalisedSpec(family=fam_name, attributes=attrs, notes=tuple(notes))
    budget = MAX_QUESTIONS - max(0, questions_asked)
    if budget <= 0:
        return NormalisedSpec(
            family=fam_name, attributes=attrs, escalate=True, missing=missing, notes=tuple(notes)
        )
    return NormalisedSpec(
        family=fam_name,
        attributes=attrs,
        open_questions=tuple(questions[:budget]),
        missing=missing,
        notes=tuple(notes),
    )

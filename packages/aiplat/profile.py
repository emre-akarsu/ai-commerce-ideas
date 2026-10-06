"""Deployment profiles: configuration that varies per jurisdiction / market / vertical / tenant.

Layering (later wins): platform defaults -> `extends` chain (e.g. base -> uk) -> tenant overrides.
Config can TIGHTEN or LOCALISE behaviour; it can never loosen the hard rules. Safety invariants
(R1-R12) have no config keys at all, and the validators below reject values that would weaken them
(e.g. an empty AI-disclosure footer, enabling cold marketing email, auto-enabled follow-ups).

Usage:  profile = load_profile("uk")   # ResolvedProfile (immutable, hashed, with provenance)
        python -m aiplat.profile validate uk | show uk | diff us uk
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, get_args

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROFILES_DIR = Path(__file__).resolve().parents[2] / "profiles"
MAX_EXTENDS_DEPTH = 5


class _P(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Locale(_P):
    region: str = Field(min_length=2, max_length=8)  # e.g. "US", "GB"
    language: str = "en-US"  # BCP-47, drives UI copy and number/date formatting
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d"
    working_week: tuple[int, ...] = (0, 1, 2, 3, 4)  # Monday=0
    holidays: tuple[date, ...] = ()  # public/bank holidays; empty = weekends only (see docs)


class MoneyPolicy(_P):
    base_currency: str = Field(pattern=r"^[A-Z]{3}$")
    accepted_currencies: tuple[str, ...]
    symbol_map: dict[str, str] = Field(default_factory=dict)  # unambiguous symbols -> ISO code
    bare_dollar_currency: str | None = None  # what a bare "$" means here; None = ambiguous
    assumed_currency: Literal["flag_require_approval", "assume_base_flag", "reject"] = (
        "flag_require_approval"
    )

    @model_validator(mode="after")
    def _consistent(self) -> MoneyPolicy:
        if self.base_currency not in self.accepted_currencies:
            raise ValueError("base_currency must be in accepted_currencies")
        for sym, iso in self.symbol_map.items():
            if iso not in self.accepted_currencies:
                raise ValueError(f"symbol {sym!r} maps to non-accepted currency {iso}")
        if self.bare_dollar_currency and self.bare_dollar_currency not in self.accepted_currencies:
            raise ValueError("bare_dollar_currency must be an accepted currency")
        return self


class TaxPolicy(_P):
    name: str = "Sales tax"
    standard_rate: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("0.5"))
    quote_basis_default: Literal["ex_tax", "inc_tax", "unknown"] = "unknown"
    # What to do when a quote does not state whether tax is included.
    unknown_basis: Literal["flag_require_approval", "assume_default_flag"] = "flag_require_approval"
    # Ask the supplier, in the RFQ, to say whether its price includes the tax (fewer silent quotes).
    ask_basis_in_rfq: bool = False


class LeadTimePolicy(_P):
    default_unit: Literal["calendar_days", "working_days"] = "calendar_days"


REQUIRED_FOOTER_CLAUSES = ("AI assistant", "cannot accept terms", "{buyer}")

# Business identity ("company particulars"): company details some jurisdictions require on business
# letters and order forms, including in electronic form. A profile may REQUIRE the block and choose
# its labels; the VALUES are per-tenant deployment facts and never live in a profile. The setting
# only ADDS a requirement: it has no key that can remove, move or reword the R8 footer.
IdentityField = Literal["legal_name", "registration_number", "registered_office", "registered_in"]
IDENTITY_FIELDS: tuple[str, ...] = get_args(IdentityField)
# Generic English defaults; a profile overrides them via `labels`. The send-service carries a mirror
# of these constants (components never import aiplat); tests/profiles keeps the two copies equal.
DEFAULT_IDENTITY_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "legal_name": "Company name",
        "registration_number": "Company number",
        "registered_office": "Registered office",
        "registered_in": "Registered in",
    }
)
MAX_IDENTITY_LABEL_CHARS = 40
# Lines the outbound message format already owns; a label equal to one of them would be ambiguous.
RESERVED_LINE_LABELS = ("Phone", "Reply to", "RFQ reference")
_LABEL_COLONS = ":\uff1a"  # ASCII and fullwidth colon: the rendered line is "<label>: <value>"


def _label_key(label: str) -> str:
    return " ".join(label.lower().split())


def _draws_nothing(c: str) -> bool:
    """Letters and marks that render as nothing although they are not in a control or format
    category: the Hangul fillers, the braille blank and the variation-selector supplement. The
    send-service refuses the same characters as hidden text (and the rest of its hidden set is in
    category C, which the label check already rejects); tests/profiles keeps the two in step."""
    return c in "\u115f\u1160\u2800\u3164\uffa0" or "\U000e0100" <= c <= "\U000e01ef"


def _check_identity_label(field: str, label: str) -> None:
    where = f"business_identity label for {field!r}"
    if not 1 <= len(label) <= MAX_IDENTITY_LABEL_CHARS or label != label.strip():
        raise ValueError(
            f"{where} must be 1-{MAX_IDENTITY_LABEL_CHARS} characters without surrounding spaces"
        )
    if any(c in _LABEL_COLONS for c in label):
        raise ValueError(f"{where} must not contain a colon")
    if any(
        unicodedata.category(c)[0] == "C" or (c.isspace() and c != " ") or _draws_nothing(c)
        for c in label
    ):
        raise ValueError(f"{where} must be plain text (no control, hidden or bidi characters)")
    if _label_key(label) in {_label_key(r) for r in RESERVED_LINE_LABELS}:
        raise ValueError(f"{where} collides with a line the outbound message already uses")


class BusinessIdentityPolicy(_P):
    required: bool = False
    # Which company details go on the message, in this order. Listed without `required`, the lines
    # are included when the tenant has values for them (optional block).
    fields: tuple[IdentityField, ...] = ()
    # Optional wording overrides per listed field; anything not listed uses DEFAULT_IDENTITY_LABELS.
    labels: Mapping[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _consistent(self) -> BusinessIdentityPolicy:
        if self.required and not self.fields:
            raise ValueError("business_identity.required needs at least one field")
        if len(set(self.fields)) != len(self.fields):
            raise ValueError("business_identity.fields must be unique")
        unlisted = sorted(set(self.labels) - set(self.fields))
        if unlisted:
            raise ValueError(f"business_identity.labels keys must be listed in fields: {unlisted}")
        for field_name, label in self.labels.items():
            _check_identity_label(field_name, label)
        effective = [_label_key(label) for label in self.effective_labels().values()]
        if len(set(effective)) != len(effective):
            raise ValueError("business_identity labels must be distinct (ignoring case)")
        return self

    def effective_labels(self) -> dict[str, str]:
        """Label per listed field, in field order: the profile's override, else the default."""
        return {f: self.labels.get(f, DEFAULT_IDENTITY_LABELS[f]) for f in self.fields}


class LegalPolicy(_P):
    jurisdiction: str
    contact_data_regime: str  # e.g. "UK_GDPR", "GDPR", "CCPA", "none"
    # Appended by the send-service to every outbound message (R8). Must keep the required clauses.
    disclosure_footer: str
    marketing_email_allowed: Literal[False] = False  # invariant: the product sends no marketing
    notices: tuple[str, ...] = ()  # extra jurisdiction notices shown in the UI / DPA checklist
    # Company-particulars block on outbound messages; default "not required". Not tenant-overridable
    # (and so not in TENANT_OVERRIDABLE).
    business_identity: BusinessIdentityPolicy = Field(default_factory=BusinessIdentityPolicy)

    @field_validator("disclosure_footer")
    @classmethod
    def _footer_keeps_invariants(cls, v: str) -> str:
        low = v.lower()
        for clause in REQUIRED_FOOTER_CLAUSES:
            if clause.lower() not in low:
                raise ValueError(f"disclosure_footer must contain {clause!r} (R8)")
        return v


class RetentionPolicy(_P):
    raw_email_days: int = Field(default=90, ge=1, le=365)
    po_records_years: int = Field(default=7, ge=1, le=15)
    audit_years: int = Field(default=7, ge=1, le=15)


class ApprovalPolicy(_P):
    threshold: Decimal = Field(default=Decimal("500"), gt=0)  # in base currency
    daily_aggregate_threshold: Decimal | None = Field(default=None, gt=0)
    send_approval_ttl_minutes: int = Field(default=30, ge=1, le=1440)
    substitution_ttl_hours: int = Field(default=24, ge=1, le=72)


class CapsPolicy(_P):
    per_order_max: Decimal | None = Field(default=None, gt=0)
    daily_aggregate_max: Decimal | None = Field(default=None, gt=0)


class CommsPolicy(_P):
    max_vendors: int = Field(default=4, ge=1, le=8)
    down_now_max_vendors: int = Field(default=2, ge=1, le=4)
    followups_default_enabled: Literal[False] = False  # invariant: follow-ups never default on
    reply_token_ttl_days: int = Field(default=90, ge=1, le=180)
    alias_domain_required: Literal[True] = True  # invariant: no mailbox OAuth at R0/R1


class TierPolicy(_P):
    enabled: tuple[Literal["A", "B"], ...] = ("A", "B")  # C is unlock-only; D is never a match
    unlock_c_after_confirmed: int = Field(default=50, ge=50)
    safety_critical_forces_d: Literal[True] = True

    @model_validator(mode="after")
    def _a_always(self) -> TierPolicy:
        if "A" not in self.enabled:
            raise ValueError("tier A must be enabled")
        return self


class PartsPolicy(_P):
    enabled_families: tuple[str, ...] = ("deep_groove_ball_bearing", "v_belt")
    standards: tuple[str, ...] = ("ISO 15",)  # informational; drives source labels
    allowed_source_ids: tuple[str, ...] = ()  # empty = all registered, subject to licence guard
    require_licensed_sources_in_production: Literal[True] = True


MATCHING_SOURCE_KINDS = (
    "trade_feed",
    "merchant_api",
    "affiliate_feed",
    "search_snapshot",
    "manual_quote",
)


class MatchingPolicy(_P):
    """Product matching gate (docs/product/07-product-matching-engine-spec-v2.md).

    v1 prototype defaults: re-tune them on real order lines. The deterministic attribute checks and
    the review rule for quantity-versus-size ambiguity have no off switch: the judge can rank
    candidates, never approve alone."""

    auto_accept_min_score: Decimal = Field(default=Decimal("0.75"), ge=Decimal("0.5"), le=1)
    auto_accept_min_lead: Decimal = Field(default=Decimal("0.05"), ge=0, le=Decimal("0.5"))
    reject_below_score: Decimal = Field(default=Decimal("0.35"), ge=0, le=Decimal("0.7"))
    retrieve_top_k: int = Field(default=50, ge=5, le=200)
    judge_top_k: int = Field(default=5, ge=2, le=10)
    judge_examples: int = Field(default=3, ge=0, le=10)
    review_show_top: int = Field(default=3, ge=1, le=10)
    llm_cost_ceiling_per_1000_lines: Decimal = Field(default=Decimal("1.50"), gt=0)  # base currency
    require_zero_failed_checks: Literal[True] = True
    quantity_size_ambiguity_forces_review: Literal[True] = True

    @model_validator(mode="after")
    def _ordered(self) -> MatchingPolicy:
        if self.reject_below_score >= self.auto_accept_min_score:
            raise ValueError("reject_below_score must be below auto_accept_min_score")
        if self.judge_top_k > self.retrieve_top_k:
            raise ValueError("judge_top_k cannot exceed retrieve_top_k")
        return self


def _default_offer_ages() -> dict[str, int]:
    return {
        "trade_feed": 168,
        "merchant_api": 24,
        "affiliate_feed": 48,
        "search_snapshot": 24,
        "manual_quote": 720,
    }


class PricingPolicy(_P):
    """Offer freshness and best-price comparison.

    Offers from a source kind older than its limit never count as a best price. Search snapshots
    (third-party search results) are indicative only: they can seed a price range but never a quote
    line, and the kind stays off unless the deployment enables it."""

    max_offer_age_hours: dict[str, int] = Field(default_factory=_default_offer_ages)
    stale_offers: Literal["exclude_from_best", "flag_only"] = "exclude_from_best"
    compare_basis: Literal["ex_tax", "inc_tax"] = "ex_tax"
    include_delivery_in_comparison: bool = True
    price_outlier_ratio: Decimal = Field(default=Decimal("3"), ge=Decimal("1.5"), le=10)
    allow_search_snapshot_sources: bool = False

    @field_validator("max_offer_age_hours")
    @classmethod
    def _known_kinds(cls, v: dict[str, int]) -> dict[str, int]:
        for kind, hours in v.items():
            if kind not in MATCHING_SOURCE_KINDS:
                raise ValueError(f"unknown offer source kind {kind!r}")
            if not 1 <= hours <= 24 * 365:
                raise ValueError(f"max_offer_age_hours[{kind}] must be 1..8760")
        return v


class BillingPolicy(_P):
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    price_per_completed_request: Decimal | None = Field(default=None, ge=0)
    free_requests: int = Field(default=10, ge=0)
    prices_include_tax: bool = False


class UiPolicy(_P):
    language: str = "en-US"
    copy_overrides: dict[str, str] = Field(default_factory=dict)


class DeploymentProfile(_P):
    profile_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,40}$")
    extends: str | None = None
    description: str = ""
    locale: Locale
    money: MoneyPolicy
    tax: TaxPolicy = TaxPolicy()
    lead_time: LeadTimePolicy = LeadTimePolicy()
    legal: LegalPolicy
    retention: RetentionPolicy = RetentionPolicy()
    approvals: ApprovalPolicy = ApprovalPolicy()
    caps: CapsPolicy = CapsPolicy()
    comms: CommsPolicy = CommsPolicy()
    tiers: TierPolicy = TierPolicy()
    parts: PartsPolicy = PartsPolicy()
    matching: MatchingPolicy = MatchingPolicy()
    pricing: PricingPolicy = PricingPolicy()
    billing: BillingPolicy = BillingPolicy()
    ui: UiPolicy = UiPolicy()
    features: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _currency_alignment(self) -> DeploymentProfile:
        if self.billing.currency not in self.money.accepted_currencies:
            raise ValueError("billing.currency must be an accepted currency")
        return self


# Keys a tenant may override (dotted paths), always re-validated against the bounds above.
TENANT_OVERRIDABLE = frozenset(
    {
        "approvals.threshold",
        "approvals.daily_aggregate_threshold",
        "caps.per_order_max",
        "caps.daily_aggregate_max",
        "comms.max_vendors",
        "comms.down_now_max_vendors",
        "retention.raw_email_days",
        "ui.copy_overrides",
        "features",
    }
)


class ResolvedProfile(_P):
    profile: DeploymentProfile
    layers: tuple[str, ...]  # e.g. ("base", "uk", "tenant:acme")
    provenance: dict[str, str]  # dotted key -> layer that set it
    digest: str  # sha256 of the canonical resolved profile; recorded in audit events

    def short(self) -> str:
        return f"{self.profile.id}@{self.digest[:12]}"


class ProfileError(ValueError):
    pass


def _deep_merge(base: dict[str, Any], over: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, Mapping) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _flatten(d: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, Mapping) and v and prefix.count(".") < 2:
            flat.update(_flatten(v, key + "."))
        else:
            flat[key] = v
    return flat


def _read(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProfileError(f"{path}: top level must be a mapping")
    return data


def _chain(profile_id: str, root: Path) -> list[tuple[str, dict[str, Any]]]:
    chain: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    current: str | None = profile_id
    while current:
        if current in seen:
            raise ProfileError(f"extends cycle at {current!r}")
        if len(seen) >= MAX_EXTENDS_DEPTH:
            raise ProfileError("extends chain too deep")
        seen.add(current)
        path = root / f"{current}.yaml"
        if not path.is_file():
            raise ProfileError(f"profile {current!r} not found at {path}")
        data = _read(path)
        chain.append((current, data))
        current = data.get("extends")
    chain.reverse()  # base first
    return chain


def _canonical(profile: DeploymentProfile) -> str:
    return json.dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def resolve(
    chain: list[tuple[str, dict[str, Any]]],
    tenant_overrides: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
) -> ResolvedProfile:
    merged: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    layers: list[str] = []
    for name, data in chain:
        layers.append(name)
        merged = _deep_merge(merged, data)
        for key in _flatten(data):
            provenance[key] = name
    if tenant_overrides:
        flat = _flatten(tenant_overrides)
        for key in flat:
            if not any(key == ok or key.startswith(ok + ".") for ok in TENANT_OVERRIDABLE):
                raise ProfileError(f"tenant may not override {key!r}")
        merged = _deep_merge(merged, tenant_overrides)
        layer = f"tenant:{tenant_id or 'unknown'}"
        layers.append(layer)
        for key in flat:
            provenance[key] = layer
    merged["id"] = chain[-1][0]
    try:
        profile = DeploymentProfile.model_validate(merged)
    except Exception as exc:
        raise ProfileError(str(exc)) from exc
    digest = hashlib.sha256(_canonical(profile).encode()).hexdigest()
    return ResolvedProfile(
        profile=profile, layers=tuple(layers), provenance=provenance, digest=digest
    )


def load_profile(
    profile_id: str,
    *,
    root: Path | None = None,
    tenant_overrides: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
) -> ResolvedProfile:
    return resolve(_chain(profile_id, root or PROFILES_DIR), tenant_overrides, tenant_id)


def diff(a: ResolvedProfile, b: ResolvedProfile) -> dict[str, tuple[Any, Any]]:
    fa = _flatten(a.profile.model_dump(mode="json"))
    fb = _flatten(b.profile.model_dump(mode="json"))
    keys = sorted(set(fa) | set(fb))
    return {k: (fa.get(k), fb.get(k)) for k in keys if fa.get(k) != fb.get(k) and k != "id"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in {"validate", "show", "diff"}:
        print("usage: python -m aiplat.profile validate <id> | show <id> | diff <id> <id>")
        return 2
    try:
        if args[0] == "validate":
            r = load_profile(args[1])
            print(f"OK {r.short()} layers={'>'.join(r.layers)}")
        elif args[0] == "show":
            r = load_profile(args[1])
            print(json.dumps(r.profile.model_dump(mode="json"), indent=2, sort_keys=True))
        else:
            for key, (x, y) in diff(load_profile(args[1]), load_profile(args[2])).items():
                print(f"{key}: {x!r} -> {y!r}")
    except ProfileError as exc:
        print(f"INVALID: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

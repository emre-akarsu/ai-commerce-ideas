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
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

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


class LeadTimePolicy(_P):
    default_unit: Literal["calendar_days", "working_days"] = "calendar_days"


REQUIRED_FOOTER_CLAUSES = ("AI assistant", "cannot accept terms", "{buyer}")


class LegalPolicy(_P):
    jurisdiction: str
    contact_data_regime: str  # e.g. "UK_GDPR", "GDPR", "CCPA", "none"
    # Appended by the send-service to every outbound message (R8). Must keep the required clauses.
    disclosure_footer: str
    marketing_email_allowed: Literal[False] = False  # invariant: the product sends no marketing
    notices: tuple[str, ...] = ()  # extra jurisdiction notices shown in the UI / DPA checklist

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

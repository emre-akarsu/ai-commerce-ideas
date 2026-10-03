"""`legal.business_identity`: the company-particulars block a profile may require on outbound mail.

The setting only ADDS a requirement. It is not tenant-overridable, has no key that could remove,
move or reword the R8 footer, and holds labels only (the values are per-tenant deployment facts).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from aiplat.profile import (
    DEFAULT_IDENTITY_LABELS,
    IDENTITY_FIELDS,
    MAX_IDENTITY_LABEL_CHARS,
    PROFILES_DIR,
    RESERVED_LINE_LABELS,
    TENANT_OVERRIDABLE,
    BusinessIdentityPolicy,
    LegalPolicy,
    ProfileError,
    diff,
    load_profile,
    main,
)
from components.send_service import message as send_message
from components.send_service.errors import MalformedMessage

FOUR = ("legal_name", "registration_number", "registered_office", "registered_in")
UK_LABELS = {
    "legal_name": "Company name",
    "registration_number": "Company number",
    "registered_office": "Registered office",
    "registered_in": "Registered in",
}
FOOTER = (
    "Prepared with an AI assistant. It cannot accept terms or place orders; "
    "only a purchase order from {buyer} binds."
)
BAD_LABELS = [
    pytest.param("", id="empty"),
    pytest.param("   ", id="blank"),
    pytest.param(" Company name", id="leading-space"),
    pytest.param("Company name ", id="trailing-space"),
    pytest.param("A" * (MAX_IDENTITY_LABEL_CHARS + 1), id="41-chars"),
    pytest.param("Company: name", id="colon-inside"),
    pytest.param("Company name:", id="colon-at-end"),
    pytest.param(":", id="colon-only"),
    pytest.param("Company：name", id="fullwidth-colon"),
    pytest.param("Company\nname", id="newline"),
    pytest.param("Company\rname", id="carriage-return"),
    pytest.param("Company\tname", id="tab"),
    pytest.param("Company\x00name", id="nul"),
    pytest.param("Company\x7fname", id="del"),
    pytest.param("Company\x85name", id="c1-next-line"),
    pytest.param("Company name", id="line-separator"),
    pytest.param("Company​name", id="zero-width-space"),
    pytest.param("Company‍name", id="zero-width-joiner"),
    pytest.param("Company‮name", id="bidi-override"),
    pytest.param("Company⁦name", id="bidi-isolate"),
    pytest.param("Company؜name", id="arabic-letter-mark"),
    pytest.param("Company﻿name", id="bom"),
    pytest.param("Phone", id="reserved-phone"),
    pytest.param("reply  TO", id="reserved-reply-to"),
    pytest.param("RFQ reference", id="reserved-rfq-reference"),
]


def uk_tree(tmp_path: Path) -> Path:
    root = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR, root)
    return root


def patch_uk_identity(root: Path, **changes: Any) -> None:
    """Rewrite uk.yaml with `legal.business_identity` keys replaced (None deletes the key)."""
    path = root / "uk.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    identity = dict(data["legal"].get("business_identity", {}))
    for key, value in changes.items():
        if value is None:
            identity.pop(key, None)
        else:
            identity[key] = value
    data["legal"]["business_identity"] = identity
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


# ---------------------------------------------------------------- schema


def test_default_is_not_required_and_empty() -> None:
    p = BusinessIdentityPolicy()
    assert p.required is False and p.fields == () and dict(p.labels) == {}
    legal = LegalPolicy(jurisdiction="x", contact_data_regime="none", disclosure_footer=FOOTER)
    assert legal.business_identity == p


def test_required_without_fields_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at least one field"):
        BusinessIdentityPolicy(required=True)
    with pytest.raises(ValidationError, match="at least one field"):
        BusinessIdentityPolicy(required=True, fields=())


def test_not_required_may_still_list_fields_as_an_optional_block() -> None:
    p = BusinessIdentityPolicy(required=False, fields=["legal_name"])
    assert p.fields == ("legal_name",) and p.required is False


def test_unknown_or_duplicate_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BusinessIdentityPolicy(fields=["legal_name", "vat_number"])
    with pytest.raises(ValidationError, match="unique"):
        BusinessIdentityPolicy(required=True, fields=["legal_name", "legal_name"])


def test_unknown_keys_are_rejected_so_a_typo_never_disables_the_requirement() -> None:
    with pytest.raises(ValidationError):
        BusinessIdentityPolicy(requried=True, fields=["legal_name"])  # type: ignore[call-arg]
    with pytest.raises(ValidationError):  # values never live in a profile
        BusinessIdentityPolicy(required=True, fields=["legal_name"], values={"legal_name": "X"})  # type: ignore[call-arg]


def test_label_keys_must_be_listed_in_fields() -> None:
    with pytest.raises(ValidationError, match="listed in fields"):
        BusinessIdentityPolicy(required=True, fields=["legal_name"], labels={"registered_in": "Where"})
    with pytest.raises(ValidationError, match="listed in fields"):
        BusinessIdentityPolicy(fields=["legal_name"], labels={"nonsense": "Where"})


@pytest.mark.parametrize("label", BAD_LABELS)
def test_bad_labels_are_rejected(label: str) -> None:
    with pytest.raises(ValidationError, match="label"):
        BusinessIdentityPolicy(required=True, fields=["legal_name"], labels={"legal_name": label})


@pytest.mark.parametrize(
    "label",
    ["Company name", "x", "A" * MAX_IDENTITY_LABEL_CHARS, "Sitz der Gesellschaft", "公司名称", "Reg. no.",
     "Registered in (nation)", "Handelsregisternummer"],
)
def test_plain_labels_up_to_the_limit_are_accepted(label: str) -> None:
    p = BusinessIdentityPolicy(required=True, fields=["legal_name"], labels={"legal_name": label})
    assert p.labels["legal_name"] == label


def test_effective_labels_must_be_distinct_ignoring_case() -> None:
    with pytest.raises(ValidationError, match="distinct"):
        BusinessIdentityPolicy(
            fields=["legal_name", "registration_number"],
            labels={"legal_name": "Name", "registration_number": "NAME"},
        )
    with pytest.raises(ValidationError, match="distinct"):  # collides with another field's default
        BusinessIdentityPolicy(
            fields=["legal_name", "registration_number"], labels={"legal_name": "company  NUMBER"}
        )


def test_non_string_label_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BusinessIdentityPolicy(fields=["legal_name"], labels={"legal_name": 12})


def test_effective_labels_apply_defaults_overrides_and_field_order() -> None:
    p = BusinessIdentityPolicy(
        required=True, fields=["registered_in", "legal_name"], labels={"legal_name": "Name"}
    )
    assert p.effective_labels() == {"registered_in": "Registered in", "legal_name": "Name"}
    assert list(p.effective_labels()) == ["registered_in", "legal_name"]
    assert BusinessIdentityPolicy().effective_labels() == {}


def test_policy_is_immutable_and_has_exactly_three_keys() -> None:
    p = BusinessIdentityPolicy(required=True, fields=["legal_name"])
    with pytest.raises(ValidationError):
        p.required = False  # type: ignore[misc]
    # nothing here can remove, move or reword the R8 footer
    assert set(BusinessIdentityPolicy.model_fields) == {"required", "fields", "labels"}


def test_identity_cannot_relax_the_footer_invariant() -> None:
    with pytest.raises(ValidationError, match="disclosure_footer"):
        LegalPolicy(
            jurisdiction="x", contact_data_regime="none", disclosure_footer="Hello",
            business_identity={"required": True, "fields": ["legal_name"]},
        )


def test_constants_mirror_the_send_service_module() -> None:
    """The message layer has no run-time dependency on aiplat, so the two modules carry copies that
    must stay equal. (Dropping the message-layer copy of the default labels would also mean editing
    the package exports and removing tests of the exported constant, so it was left as is.)"""
    assert dict(DEFAULT_IDENTITY_LABELS) == dict(send_message.DEFAULT_IDENTITY_LABELS)
    assert tuple(IDENTITY_FIELDS) == tuple(send_message.DEFAULT_IDENTITY_LABELS)
    assert tuple(IDENTITY_FIELDS) == FOUR
    assert MAX_IDENTITY_LABEL_CHARS == send_message.MAX_IDENTITY_LABEL_CHARS
    assert {x.lower() for x in RESERVED_LINE_LABELS} == {
        x.lower() for x in send_message.RESERVED_LINE_LABELS
    }


# The two validators (the profile's, and the one the message layer applies to the labels it renders) are
# separate code because components never import aiplat. They must give the same verdict on any label.
def _cp(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


LABEL_PROBES = [
    # plain labels both must accept
    "Company name", "x", "A" * MAX_IDENTITY_LABEL_CHARS, "Sitz der Gesellschaft", "Reg. no.",
    "Registered in (nation)", "Handelsregisternummer", "Soci" + _cp(0xE9) + "t" + _cp(0xE9),
    _cp(0x516C, 0x53F8, 0x540D, 0x79F0),
    # shape rules
    "", " ", "  ", " Company name", "Company name ", "A" * (MAX_IDENTITY_LABEL_CHARS + 1),
    "Company: name", "Company name:", ":", "Company" + _cp(0xFF1A) + "name",
    # reserved line labels, any case or spacing
    "Phone", "phone", "PHONE", "Reply to", "reply  TO", "RFQ reference", "rfq   REFERENCE",
    # control, line-breaking, hidden and bidirectional characters
    "Company\nname", "Company\rname", "Company\tname", "Company\x00name", "Company\x7fname",
    "Company\x0bname", "Company\x0cname", "Company\x1cname",
    *[f"Comp{chr(c)}any" for c in range(0x80, 0xA0)],  # all of C1, NEL included
    "Comp" + _cp(0x2028) + "any", "Comp" + _cp(0x2029) + "any", "Comp" + _cp(0x61C) + "any",
    "Comp" + _cp(0x200B) + "any", "Comp" + _cp(0x200D) + "any", "Comp" + _cp(0x202E) + "any",
    "Comp" + _cp(0x2066) + "any", "Comp" + _cp(0xFEFF) + "any", "Comp" + _cp(0x2060) + "any",
    # format, private-use and unassigned characters, and spaces other than the ASCII one
    "Comp" + _cp(0xAD) + "any", "Comp" + _cp(0x180E) + "any", "Comp" + _cp(0xE000) + "any",
    "Comp" + _cp(0x378) + "any", "Comp" + _cp(0xFFFE) + "any", "Comp" + _cp(0xE0020) + "any",
    "Company" + _cp(0xA0) + "name", "Company" + _cp(0x3000) + "name", "Company" + _cp(0x2003) + "name",
    "Company" + _cp(0x202F) + "name", "Company" + _cp(0x1680) + "name",
]


def _profile_accepts(label: str) -> bool:
    try:
        BusinessIdentityPolicy(required=True, fields=["legal_name"], labels={"legal_name": label})
    except ValidationError:
        return False
    return True


def _message_accepts(label: str) -> bool:
    try:
        send_message.validate_identity_pairs([(label, "Acme Plant Ltd")])
    except MalformedMessage:
        return False
    return True


def _required_label_accepts(label: str) -> bool:
    try:
        send_message.validate_identity_labels((label,))
    except ValueError:
        return False
    return True


@pytest.mark.parametrize("label", LABEL_PROBES, ids=lambda label: ascii(label)[:48])
def test_profile_and_message_label_validation_agree(label: str) -> None:
    verdicts = (_profile_accepts(label), _message_accepts(label), _required_label_accepts(label))
    assert len(set(verdicts)) == 1, (ascii(label), verdicts)


def test_the_label_probe_set_has_both_accepted_and_rejected_labels() -> None:
    verdicts = [_profile_accepts(label) for label in LABEL_PROBES]
    assert sum(verdicts) >= 8 and sum(not v for v in verdicts) >= 50


_SAFE_LABEL = st.text(alphabet="abcXYZ09 .()'-", min_size=1, max_size=20).map(str.strip).filter(bool)
_ODD = [chr(c) for c in (0x0B, 0x1C, 0x85, 0x9F, 0xA0, 0xAD, 0x2003, 0x2028, 0x2029, 0x61C, 0x200B, 0x202E,
                         0x3164, 0x2800, 0xE000, 0x378, 0xFF1A)] + [":", "\n", "\t", " ", "Phone"]


@settings(max_examples=400, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(base=_SAFE_LABEL, odd=st.lists(st.sampled_from(_ODD), max_size=2), at=st.integers(0, 20))
def test_label_validators_agree_on_generated_labels(base: str, odd: list[str], at: int) -> None:
    label = base[:at] + "".join(odd) + base[at:]
    verdicts = (_profile_accepts(label), _message_accepts(label), _required_label_accepts(label))
    assert len(set(verdicts)) == 1, (ascii(label), verdicts)


# ---------------------------------------------------------------- shipped profiles


def test_base_and_us_do_not_require_the_block() -> None:
    us = load_profile("us").profile.legal.business_identity
    assert us.required is False and us.fields == () and dict(us.labels) == {}
    base = yaml.safe_load((PROFILES_DIR / "base.yaml").read_text(encoding="utf-8"))
    assert base["legal"]["business_identity"]["required"] is False
    assert not base["legal"]["business_identity"].get("fields")


def test_uk_requires_the_four_fields_with_default_labels() -> None:
    bi = load_profile("uk").profile.legal.business_identity
    assert bi.required is True
    assert bi.fields == FOUR
    assert dict(bi.labels) == UK_LABELS
    assert bi.effective_labels() == UK_LABELS
    assert dict(DEFAULT_IDENTITY_LABELS) == UK_LABELS  # the generic English defaults


@pytest.mark.parametrize("pid", ["uk-scotland", "uk-ni"])
def test_regional_uk_profiles_inherit_the_requirement_and_do_not_duplicate_it(pid: str) -> None:
    r = load_profile(pid)
    assert r.profile.legal.business_identity == load_profile("uk").profile.legal.business_identity
    assert r.provenance["legal.business_identity.required"] == "uk"
    assert "business_identity" not in (PROFILES_DIR / f"{pid}.yaml").read_text(encoding="utf-8")


def test_no_shipped_profile_carries_identity_values() -> None:
    for path in PROFILES_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        bi = (data.get("legal") or {}).get("business_identity") or {}
        assert set(bi) <= {"required", "fields", "labels"}, path.name


def test_template_documents_the_key_as_a_comment_only() -> None:
    lines = (PROFILES_DIR / "_template.yaml").read_text(encoding="utf-8").splitlines()
    hits = [ln for ln in lines if "business_identity" in ln]
    assert hits
    assert all(ln.lstrip().startswith("#") for ln in hits)  # a template must not switch it on


def test_template_example_is_valid_when_uncommented() -> None:
    lines = (PROFILES_DIR / "_template.yaml").read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.lstrip().startswith("# business_identity:"))
    block = [lines[start]]
    for ln in lines[start + 1 :]:
        if not ln.lstrip().startswith("#   "):
            break
        block.append(ln)
    data = yaml.safe_load("\n".join(ln.replace("# ", "", 1) for ln in block))
    policy = BusinessIdentityPolicy.model_validate(data["business_identity"])
    assert policy.required and policy.fields


def test_cli_validates_shows_and_diffs_the_setting(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", "uk"]) == 0
    assert main(["show", "uk"]) == 0
    assert '"business_identity"' in capsys.readouterr().out
    changed = diff(load_profile("us"), load_profile("uk"))
    assert changed["legal.business_identity.required"] == (False, True)
    assert changed["legal.business_identity.fields"] == ([], list(FOUR))


# ---------------------------------------------------------------- loading and layering


def test_loader_wraps_schema_errors_for_a_profile_file(tmp_path: Path) -> None:
    root = uk_tree(tmp_path)
    patch_uk_identity(root, fields=[])
    with pytest.raises(ProfileError, match="at least one field"):
        load_profile("uk", root=root)
    patch_uk_identity(root, fields=list(FOUR), labels={"legal_name": "Company: name"})
    with pytest.raises(ProfileError, match="label"):
        load_profile("uk", root=root)
    patch_uk_identity(root, labels={"legal_name": "A" * 41})
    with pytest.raises(ProfileError, match="label"):
        load_profile("uk", root=root)


def test_regional_profile_inherits_a_changed_parent(tmp_path: Path) -> None:
    root = uk_tree(tmp_path)
    patch_uk_identity(root, fields=["legal_name", "registered_in"], labels={"legal_name": "Name"})
    child = load_profile("uk-scotland", root=root).profile.legal.business_identity
    assert child.fields == ("legal_name", "registered_in") and child.required is True
    assert child.effective_labels() == {"legal_name": "Name", "registered_in": "Registered in"}


@pytest.mark.parametrize(
    "override",
    [
        {"legal": {"business_identity": {"required": False}}},
        {"legal": {"business_identity": {"fields": []}}},
        {"legal": {"business_identity": {"fields": ["legal_name"]}}},
        {"legal": {"business_identity": {"labels": {"legal_name": "Name"}}}},
        {"legal": {"business_identity": {}}},
        {"legal": {"business_identity": None}},
    ],
)
def test_tenant_cannot_override_the_setting(override: dict[str, Any]) -> None:
    with pytest.raises(ProfileError, match="may not override"):
        load_profile("uk", tenant_overrides=override, tenant_id="acme")
    with pytest.raises(ProfileError, match="may not override"):
        load_profile("us", tenant_overrides=override, tenant_id="acme")


def test_setting_is_not_in_the_tenant_whitelist() -> None:
    assert not [k for k in TENANT_OVERRIDABLE if "business_identity" in k or k.startswith("legal")]


def test_digest_changes_when_any_part_of_the_setting_changes(tmp_path: Path) -> None:
    base = load_profile("uk").digest
    seen = {base}
    variants: list[dict[str, Any]] = [
        {"required": False},
        {"fields": ["legal_name", "registration_number", "registered_in", "registered_office"]},
        {
            "fields": ["legal_name", "registration_number", "registered_office"],
            "labels": {k: v for k, v in UK_LABELS.items() if k != "registered_in"},
        },
        {"labels": {**UK_LABELS, "registration_number": "Registered number"}},
        {"labels": {k: v for k, v in UK_LABELS.items() if k != "registered_in"}},
    ]
    for i, change in enumerate(variants):
        root = uk_tree(tmp_path / str(i))
        patch_uk_identity(root, **change)
        digest = load_profile("uk", root=root).digest
        assert digest not in seen, change
        seen.add(digest)
    # and the digest is stable for an unchanged setting
    assert load_profile("uk").digest == base

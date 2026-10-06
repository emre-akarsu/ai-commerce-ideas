"""The UI export of each scope matches its JSON schema and is byte-identical on regeneration."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from components.job_kits import JobKitLibrary

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "profiles" / "data" / "job_kits" / "export.schema.json"
EXPORT_DIR = ROOT / "profiles" / "data" / "job_kits" / "uk" / "export"
SCRIPT = ROOT / "scripts" / "export_job_kits.py"
SCOPES = ("bathroom_full", "bathroom_cloakroom", "bathroom_wc_only", "bathroom_wet_room")
TYPES: dict[str, Any] = {"object": dict, "array": list, "string": str, "boolean": bool,
                         "null": type(None), "integer": int, "number": (int, float)}


def validate(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> None:
    """A small JSON Schema subset: $ref, type, enum, const, required, properties,
    additionalProperties: false, items, minItems, maxItems, minimum, pattern-free."""
    if "$ref" in schema:
        name = schema["$ref"].removeprefix("#/$defs/")
        return validate(value, root["$defs"][name], root, path)
    types = schema.get("type")
    if types is not None:
        allowed = [types] if isinstance(types, str) else types
        ok = any(isinstance(value, TYPES[t]) and not (t in {"integer", "number"}
                                                      and isinstance(value, bool))
                 for t in allowed)
        assert ok, f"{path}: {value!r} is not {allowed}"
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: {value!r} not in {schema['enum']}"
    if "const" in schema:
        assert value == schema["const"], f"{path}: {value!r} != {schema['const']!r}"
    if "minimum" in schema:
        assert value >= schema["minimum"], f"{path}: {value} < {schema['minimum']}"
    if isinstance(value, dict):
        for key in schema.get("required", []):
            assert key in value, f"{path}: missing {key}"
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            assert not extra, f"{path}: unexpected {sorted(extra)}"
        for key, sub in props.items():
            if key in value:
                validate(value[key], sub, root, f"{path}.{key}")
    if isinstance(value, list):
        assert len(value) >= schema.get("minItems", 0), f"{path}: too few items"
        assert len(value) <= schema.get("maxItems", len(value)), f"{path}: too many items"
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], root, f"{path}[{i}]")
    return None


def load_script() -> Any:
    spec = importlib.util.spec_from_file_location("export_job_kits", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_validator_rejects_bad_documents() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    with pytest.raises(AssertionError):
        validate({"format": "nope"}, schema, schema)


@pytest.mark.parametrize("scope_id", SCOPES)
def test_export_matches_the_schema(library: JobKitLibrary, scope_id: str) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data = json.loads(library.export_ui_json(scope_id))
    validate(data, schema, schema)
    assert data["scope"]["scope_id"] == scope_id
    assert "synthetic" in data["label"]
    assert len(data["upfront_questions"]) <= data["max_upfront_questions"] == 3
    by_id = {q["id"]: q for q in data["questions"]}
    assert set(data["upfront_questions"]) == {q for q, v in by_id.items() if v["ask"] == "upfront"}
    for q in data["questions"]:
        assert q["default"] in [o["value"] for o in q["options"]], q["id"]
        assert all(o["label"].strip() for o in q["options"]), q["id"]
    review_questions = {r["key"] for r in data["review_defaults"] if r["kind"] == "question"}
    assert review_questions == {q for q, v in by_id.items() if v["ask"] == "on_review"}
    for module in data["modules"]:
        for line in module["lines"]:
            if line["options"]:
                assert sum(o["default"] for o in line["options"]) == 1, line["id"]
                assert line["default_option"] in [o["id"] for o in line["options"]]


@pytest.mark.parametrize("scope_id", SCOPES)
def test_export_is_deterministic_and_the_committed_file_is_current(
        library: JobKitLibrary, scope_id: str) -> None:
    first = library.export_ui_json(scope_id)
    assert first == library.export_ui_json(scope_id)
    assert first.endswith("\n")
    committed = EXPORT_DIR / f"{scope_id}.json"
    assert committed.read_bytes() == first.encode("utf-8"), (
        f"{committed.name} is stale: run scripts/export_job_kits.py")


def test_the_export_script_regenerates_byte_identical_files(tmp_path: Path) -> None:
    script = load_script()
    for run in ("a", "b"):
        assert script.main(["--out", str(tmp_path / run)]) == 0
    for scope_id in SCOPES:
        a = (tmp_path / "a" / f"{scope_id}.json").read_bytes()
        assert a == (tmp_path / "b" / f"{scope_id}.json").read_bytes()
        assert a == (EXPORT_DIR / f"{scope_id}.json").read_bytes()
    assert sorted(p.name for p in (tmp_path / "a").iterdir()) == sorted(
        f"{s}.json" for s in SCOPES)

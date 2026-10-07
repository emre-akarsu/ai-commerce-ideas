"""A small JSON Schema subset validator (no dependency): $ref, type, enum, const, pattern,
required, properties, additionalProperties: false, items, anyOf. Raises AssertionError."""

from __future__ import annotations

import re
from typing import Any

TYPES: dict[str, Any] = {"object": dict, "array": list, "string": str, "boolean": bool,
                         "null": type(None), "integer": int, "number": (int, float)}


def _type_ok(value: Any, t: str) -> bool:
    if t in ("integer", "number") and isinstance(value, bool):
        return False
    if t == "number" and isinstance(value, float):
        return True
    return isinstance(value, TYPES[t])


def validate(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> None:
    if "$ref" in schema:
        return validate(value, root["$defs"][schema["$ref"].removeprefix("#/$defs/")], root, path)
    if "anyOf" in schema:
        errors = []
        for sub in schema["anyOf"]:
            try:
                return validate(value, sub, root, path)
            except AssertionError as exc:
                errors.append(str(exc))
        raise AssertionError(f"{path}: no alternative matched: {errors}")
    types = schema.get("type")
    if types is not None:
        allowed = [types] if isinstance(types, str) else types
        assert any(_type_ok(value, t) for t in allowed), f"{path}: {value!r} is not {allowed}"
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: {value!r} not in {schema['enum']}"
    if "const" in schema:
        assert value == schema["const"], f"{path}: {value!r} != {schema['const']!r}"
    if "pattern" in schema and isinstance(value, str):
        assert re.search(schema["pattern"], value), f"{path}: {value!r} !~ {schema['pattern']}"
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
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            validate(item, schema["items"], root, f"{path}[{i}]")
    return None

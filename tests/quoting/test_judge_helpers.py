"""A scripted judge for the tests: always names the same product first, whatever the order."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

_BLOCK = re.compile(r"name=candidates\n(.*?)\n[^\n]*UNTRUSTED_DATA", re.S)


def agree_on(sku_id: str) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    def respond(system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        block = _BLOCK.search(user)
        assert block, "the judge prompt lists the candidates in a fenced block"
        ids = [c["sku_id"] for c in json.loads(block.group(1))]
        ordered = sorted(ids, key=lambda s: (s != sku_id, s))
        return {"ranked": [{"sku_id": i} for i in ordered]}

    return respond

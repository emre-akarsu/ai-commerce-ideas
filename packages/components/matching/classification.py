"""Registry of the classification codes this component may store (verified codes only).

Only codes read live from the Uniclass taxon pages or the bSDD API and recorded in
`research_notes/UK refurbishment job templates data/classification_standards.md` are listed.
Titles are stored verbatim. Uniclass 2015 is CC BY-ND 4.0, so codes and titles are never
edited, merged or extended; our own product types are a separate namespace that merely
references a Uniclass code. ETIM is ODC-By 1.0 (attribution kept in the registry file). A code
that is not in the registry is rejected by the ontology loader and by the ontology writer, so
an LLM proposal can never introduce an invented classification (R3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SYSTEMS = ("uniclass_pr", "etim")


class ClassificationError(ValueError):
    """A classification code is unknown, mistitled, or the registry file is malformed."""


@dataclass(frozen=True)
class VerifiedCodes:
    uniclass_pr: Mapping[str, str]
    etim: Mapping[str, str]
    attribution: Mapping[str, str]
    uniclass_version: str
    etim_version: str
    source_note: str
    verified_on: str

    def check(self, system: str, code: str, title: str | None = None) -> None:
        """Raise unless `code` (and, when given, its verbatim `title`) is in the registry."""
        table = {"uniclass_pr": self.uniclass_pr, "etim": self.etim}.get(system)
        if table is None:
            raise ClassificationError(f"unknown classification system {system!r}")
        if code not in table:
            raise ClassificationError(f"{system} code {code!r} is not verified")
        if title is not None and table[code] != title:
            raise ClassificationError(
                f"{system} code {code!r} is verified with title {table[code]!r}, not {title!r}"
            )


def _table(raw: Any, name: str) -> dict[str, str]:
    if not isinstance(raw, dict) or not raw:
        raise ClassificationError(f"classification file: {name} must be a non-empty mapping")
    return {str(k): str(v) for k, v in raw.items()}


def load_classification(path: Path) -> VerifiedCodes:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ClassificationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ClassificationError(f"{path}: expected a mapping")
    attribution = _table(data.get("attribution"), "attribution")
    for key, needle in (("uniclass", "Uniclass 2015 © NBS, CC BY-ND 4.0"), ("etim", "ODC-By")):
        if needle not in attribution.get(key, ""):
            raise ClassificationError(f"classification attribution.{key} must contain {needle!r}")
    return VerifiedCodes(
        uniclass_pr=_table(data.get("uniclass_pr"), "uniclass_pr"),
        etim=_table(data.get("etim"), "etim"),
        attribution=attribution,
        uniclass_version=str(data.get("uniclass_version", "")),
        etim_version=str(data.get("etim_version", "")),
        source_note=str(data.get("source_note", "")),
        verified_on=str(data.get("verified_on", "")),
    )

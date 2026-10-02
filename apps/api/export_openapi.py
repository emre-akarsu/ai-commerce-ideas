"""Write apps/api/openapi.json from the app schema: `python -m apps.api.export_openapi`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .auth import AuthError
from .main import create_app

OUT = Path(__file__).with_name("openapi.json")


class _Unused:
    def __getattr__(self, name: str) -> Any:
        raise NotImplementedError(name)

    def authenticate(self, token: str) -> Any:
        raise AuthError("schema export only")


def build_schema() -> dict[str, Any]:
    return create_app(_Unused(), _Unused()).openapi()  # type: ignore[arg-type]


def main() -> None:
    OUT.write_text(json.dumps(build_schema(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

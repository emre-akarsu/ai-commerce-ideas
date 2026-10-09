"""``python -m aiplat.compose validate|show <deployment.yaml>...``"""

from __future__ import annotations

import sys

from .models import CompositionError
from .resolve import load_deployment


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) < 2 or args[0] not in ("validate", "show"):
        print("usage: python -m aiplat.compose validate|show <deployment.yaml>...", file=sys.stderr)
        return 2
    code = 0
    for path in args[1:]:
        try:
            comp = load_deployment(path)
        except CompositionError as exc:
            print(f"FAIL {path}\n{exc}", file=sys.stderr)
            code = 1
            continue
        print(f"ok   {path}  {comp.short()}  profile={comp.profile.short()}")
        if args[0] == "show":
            for s in comp.template.steps:
                mod = comp.bound.get(s.id)
                print(f"     {s.id:<12} {s.uses:<22} {mod.ref if mod else 'kernel'}")
            for key, layer in sorted(comp.provenance.items()):
                print(f"     {key} <- {layer}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

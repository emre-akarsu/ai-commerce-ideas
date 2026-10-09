import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]   # the repository root (this file is docs/_work/tools/ed.py)
def edit(path, pairs):
    """All-or-nothing string replacement: each `old` must occur exactly once in the file (path relative to the repo root)."""
    p = ROOT / path
    s = p.read_text()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f"{path}: expected exactly 1 match, found {n}: {old[:90]!r}"
        s = s.replace(old, new, 1)
    p.write_text(s)
    print("edited", path, len(pairs))

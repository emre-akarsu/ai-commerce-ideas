import re, sys, pathlib, subprocess, urllib.parse

ROOT = pathlib.Path(".").resolve()

def slug(h):
    h = re.sub(r"`", "", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = h.strip().lower()
    out = []
    for ch in h:
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        elif ch == " ":
            out.append("-")
        # other punctuation dropped
    return "".join(out)

anchor_cache = {}
def anchors(path):
    if path in anchor_cache:
        return anchor_cache[path]
    txt = path.read_text(errors="replace")
    a = set()
    seen = {}
    in_code = False
    for line in txt.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slug(m.group(2))
            n = seen.get(s, 0)
            seen[s] = n + 1
            a.add(s if n == 0 else f"{s}-{n}")
        for m2 in re.finditer(r'<a\s+id="([^"]+)"', line):
            a.add(m2.group(1))
    anchor_cache[path] = a
    return a

def check(files):
    bad = []
    for f in files:
        txt = f.read_text(errors="replace")
        # strip fenced code
        body = re.sub(r"```.*?```", "", txt, flags=re.S)
        body = re.sub(r"`[^`\n]*`", lambda m: "`" + "x" * (len(m.group(0)) - 2) + "`", body)
        for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", body):
            tgt = m.group(1)
            if re.match(r"^(https?:|mailto:|tel:)", tgt):
                continue
            tgt = urllib.parse.unquote(tgt)
            path, _, frag = tgt.partition("#")
            if path == "":
                dest = f
            else:
                dest = (f.parent / path).resolve()
            if not dest.exists():
                bad.append((f.relative_to(ROOT).as_posix(), tgt, "missing file"))
                continue
            if frag and dest.suffix == ".md":
                if frag.lower() not in anchors(dest) and frag not in anchors(dest):
                    bad.append((f.relative_to(ROOT).as_posix(), tgt, "missing anchor"))
    return bad

if __name__ == "__main__":
    files = [pathlib.Path(a).resolve() for a in sys.argv[1:]]
    bad = check(files)
    for b in bad:
        print(*b, sep=" | ")
    print("files", len(files), "broken", len(bad))

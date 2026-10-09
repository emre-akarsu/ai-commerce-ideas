import json, re, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from registry import REGISTRY
REPO = pathlib.Path("/home/user/ai-commerce-ideas")
out = []
for did, _sec, _label, path in REGISTRY:
    txt = (REPO / path).read_text()
    for i, m in enumerate(re.finditer(r"```mermaid\n(.*?)```", txt, re.S)):
        out.append({"id": f"{path}#{i+1}", "key": f"{did}_{i+1}", "body": m.group(1)})
pathlib.Path(__file__).parent.joinpath("blocks.json").write_text(json.dumps(out))
print(len(out), "diagrams")

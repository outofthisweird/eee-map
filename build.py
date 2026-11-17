#!/usr/bin/env python3
"""Build index.html: a single self-contained file.

- src/map.html          the prototype (HTML + CSS + JS)
- data/stations.json    pasted in at __DATA__
- vendor/nycta/         NYCTA design system (public output of nycta-gsm, refreshed by tools/sync_nycta.sh):
                        sections 0–1 of nycta.css (typeface + tokens) pasted in at /*__NYCTA__*/,
                        with every woff2 it references (Albert Sans NYCTA, NYCTA Hangul) embedded as a data URI.

Usage: python3 build.py   (writes ./index.html)"""
import base64, re
from pathlib import Path

root = Path(__file__).parent
src = (root / "src/map.html").read_text(encoding="utf-8")
data = (root / "data/stations.json").read_text(encoding="utf-8")
nycta = (root / "vendor/nycta/nycta.css").read_text(encoding="utf-8")

# nycta.css is split into numbered sections ("/* ---…\n   N. Title"). Keep 0 (typeface) and 1 (tokens) only:
# its base styles, components and OS-driven dark mode would fight the map's own UI (dark mode here is the ◐ button).
starts = [m.start() for m in re.finditer(r"/\* -{20,}\n   \d+\. ", nycta)]
heads = {int(re.search(r"\n   (\d+)\. ", nycta[s:s + 200]).group(1)): s for s in starts}
assert 0 in heads and 1 in heads and 2 in heads, "nycta.css section layout changed: check build.py"
tokens = nycta[heads[0]:heads[2]].rstrip()
fonts = re.findall(r'url\("\.\./fonts/([\w.-]+\.woff2)"\)', tokens)
assert "albert-sans-nycta-wght.woff2" in fonts and "nycta-hangul.woff2" in fonts, "nycta.css font urls changed: check build.py"
for name in set(fonts):
    b64 = base64.b64encode((root / "vendor/nycta" / name).read_bytes()).decode()
    tokens = tokens.replace(f'url("../fonts/{name}")', f'url("data:font/woff2;base64,{b64}")')
tokens = "/* NYCTA design system — vendor/nycta/nycta.css §0–1 (" + \
    (root / "vendor/nycta/SOURCE.txt").read_text(encoding="utf-8").splitlines()[-1].strip() + ") */\n" + tokens

for key in ("__DATA__", "/*__NYCTA__*/"):
    assert src.count(key) == 1, f"src/map.html must contain {key} exactly once"
out = src.replace("/*__NYCTA__*/", tokens).replace("__DATA__", data)
(root / "index.html").write_text(out, encoding="utf-8")
print(f"index.html built ({len(out) // 1024} KB)")

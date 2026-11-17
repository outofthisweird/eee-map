#!/usr/bin/env python3
"""Build index.html: a single self-contained file.

- src/map.html          the prototype (HTML + CSS + JS)
- data/stations.json    pasted in at __DATA__
- vendor/nycta/         NYCTA design system (public output of nycta-gsm, refreshed by tools/sync_nycta.sh):
                        sections 0–1 of nycta.css (typeface + tokens) pasted in at /*__NYCTA__*/,
                        with the Albert Sans NYCTA woff2 embedded as a data URI.

Usage: python3 build.py   (writes ./index.html)"""
import base64, re
from pathlib import Path

root = Path(__file__).parent
src = (root / "src/map.html").read_text(encoding="utf-8")
data = (root / "data/stations.json").read_text(encoding="utf-8")
nycta = (root / "vendor/nycta/nycta.css").read_text(encoding="utf-8")
font = (root / "vendor/nycta/albert-sans-nycta-wght.woff2").read_bytes()

# nycta.css is split into numbered sections ("/* ---…\n   N. Title"). Keep 0 (typeface) and 1 (tokens) only:
# its base styles, components and OS-driven dark mode would fight the map's own UI (dark mode here is the ◐ button).
starts = [m.start() for m in re.finditer(r"/\* -{20,}\n   \d+\. ", nycta)]
heads = {int(re.search(r"\n   (\d+)\. ", nycta[s:s + 200]).group(1)): s for s in starts}
assert 0 in heads and 1 in heads and 2 in heads, "nycta.css section layout changed: check build.py"
tokens = nycta[heads[0]:heads[2]].rstrip()
url = 'url("../fonts/albert-sans-nycta-wght.woff2")'
assert tokens.count(url) == 1, "nycta.css font url changed: check build.py"
tokens = tokens.replace(url, 'url("data:font/woff2;base64,' + base64.b64encode(font).decode() + '")')
tokens = "/* NYCTA design system — vendor/nycta/nycta.css §0–1 (" + \
    (root / "vendor/nycta/SOURCE.txt").read_text(encoding="utf-8").splitlines()[-1].strip() + ") */\n" + tokens

for key in ("__DATA__", "/*__NYCTA__*/"):
    assert src.count(key) == 1, f"src/map.html must contain {key} exactly once"
out = src.replace("/*__NYCTA__*/", tokens).replace("__DATA__", data)
(root / "index.html").write_text(out, encoding="utf-8")
print(f"index.html built ({len(out) // 1024} KB)")

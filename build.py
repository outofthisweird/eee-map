#!/usr/bin/env python3
"""Build index.html: a single self-contained file.

- src/map.html          the prototype (HTML + CSS + JS)
- data/stations.json    pasted in at __DATA__
- data/en.json          English version (series names, station names and titles by id), pasted in at __DATA_EN__
- vendor/nycta/         NYCTA design system (public output of nycta-gsm, refreshed by tools/sync_nycta.sh):
                        sections 0–1 of nycta.css (typeface + tokens) pasted in at /*__NYCTA__*/,
                        followed by its generated disc glyph-mask block (DEC-035; rules live in src/map.html),
                        with every woff2 it references (Albert Sans NYCTA, NYCTA Hangul) embedded as a data URI;
                        and nycta-map.js (route map geometry, NYCTAMap.geometry) inlined at /*__NYCTA_MAP__*/,
                        ahead of the map script that calls it.

Usage: python3 build.py   (writes ./index.html)"""
import base64, json, re
from pathlib import Path

root = Path(__file__).parent
src = (root / "src/map.html").read_text(encoding="utf-8")
data = (root / "data/stations.json").read_text(encoding="utf-8")
data_en = (root / "data/en.json").read_text(encoding="utf-8")
missing = [s["id"] for day in json.loads(data).values() for s in day if s["id"] not in json.loads(data_en)["stations"]]
if missing:   # they show their Korean text in the English version
    print(f"data/en.json: no English for {len(missing)} station(s): {', '.join(missing)}")
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
# Disc glyphs (nycta DEC-035): the generated block of baked outlines, one --disc-mask per label. Only custom properties;
# the .disc / ::after rules that use them are in src/map.html.
MB, ME = "/* disc glyph masks — generated", "/* end of disc glyph masks */"
assert nycta.count(MB) == 1 and nycta.count(ME) == 1, "nycta.css disc glyph-mask block not found: check build.py"
tokens += "\n\n" + nycta[nycta.index(MB):nycta.index(ME) + len(ME)]
tokens = "/* NYCTA design system — vendor/nycta/nycta.css §0–1 + disc glyph masks (" + \
    (root / "vendor/nycta/SOURCE.txt").read_text(encoding="utf-8").splitlines()[-1].strip() + ") */\n" + tokens

# Route map geometry (nycta DEC-036): the same NYCTAMap.geometry the nycta map draws with. Never edited here; rules
# change in nycta, then tools/sync_nycta.sh. Its auto-draw only touches .map elements holding a JSON <script> (none here).
mapjs = (root / "vendor/nycta/nycta-map.js").read_text(encoding="utf-8")
assert "geometry:" in mapjs and "window.NYCTAMap" in mapjs, "nycta-map.js no longer exports NYCTAMap.geometry: check build.py"
mapjs = re.sub(r"</(script)", r"<\\/\1", mapjs, flags=re.I)   # inline: a '</script' (even in a comment) would end the tag

for key in ("__DATA__", "__DATA_EN__", "/*__NYCTA__*/", "/*__NYCTA_MAP__*/"):
    assert src.count(key) == 1, f"src/map.html must contain {key} exactly once"
out = src.replace("/*__NYCTA__*/", tokens).replace("__DATA_EN__", data_en).replace("__DATA__", data).replace("/*__NYCTA_MAP__*/", mapjs)
(root / "index.html").write_text(out, encoding="utf-8")
print(f"index.html built ({len(out) // 1024} KB)")

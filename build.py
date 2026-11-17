#!/usr/bin/env python3
"""Build index.html: src/map.html with data/stations.json pasted in at __DATA__.
Usage: python3 build.py   (writes ./index.html — a single self-contained file)"""
from pathlib import Path
root = Path(__file__).parent
src = (root / "src/map.html").read_text(encoding="utf-8")
data = (root / "data/stations.json").read_text(encoding="utf-8")
assert src.count("__DATA__") == 1, "src/map.html must contain __DATA__ exactly once"
(root / "index.html").write_text(src.replace("__DATA__", data), encoding="utf-8")
print("index.html built")

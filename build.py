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
                        ahead of the map script that calls it;
                        and the print simulation layer (DEC-038): nycta.css §14 after the tokens, and the NYCTAPrint
                        block of nycta.js (ink-edge filter + <button data-print-toggle> switch) at /*__NYCTA_PRINT__*/.
- posts/*.md            웹 연재(G 노선) 글. 맨 위 머리말(title, station, date, summary, draft) + 마크다운 본문.
                        글마다 posts/<이름>.html(src/post.html 틀)을 만들고, 노선도에는 DATA['글']로 역을 넣는다.
                        posts/post.css = nycta 토큰(서체는 ../vendor/nycta/ 파일을 가리킴) + src/post.css.
                        이름이 _로 시작하는 파일(_template.md)은 건너뛴다.

Usage: python3 build.py   (writes ./index.html)"""
import base64, html, json, re
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
# Print simulation layer (nycta DEC-038): §14, opt-in with <html data-print>, switched by a <button data-print-toggle>.
assert 14 in heads, "nycta.css §14 (print layer) not found: check build.py"
nxt = min([s for s in heads.values() if s > heads[14]] + [len(nycta)])
tokens += "\n\n" + nycta[heads[14]:nxt].rstrip()
# 글 페이지(posts/post.css)는 nycta.css를 통째로 쓴다(2026-11-21 사용자 요청: 원래 있는 모듈을 최대한 이용).
# 판·칸(.plate .m), 표지(.sign-train .sign-direction), 원판, 화살표, 안내 막대(.guide), 문서 규모 h1–h3·p, 다크 모드가 그대로 온다.
post_tokens = nycta
for name in set(fonts):   # posts/post.css sits in posts/: the font files are served from vendor/nycta/
    post_tokens = post_tokens.replace(f'url("../fonts/{name}")', f'url("../vendor/nycta/{name}")')
tokens = "/* NYCTA design system — vendor/nycta/nycta.css §0–1 + disc glyph masks + §14 print layer (" + \
    (root / "vendor/nycta/SOURCE.txt").read_text(encoding="utf-8").splitlines()[-1].strip() + ") */\n" + tokens

# Route map geometry (nycta DEC-036): the same NYCTAMap.geometry the nycta map draws with. Never edited here; rules
# change in nycta, then tools/sync_nycta.sh. Its auto-draw only touches .map elements holding a JSON <script> (none here).
mapjs = (root / "vendor/nycta/nycta-map.js").read_text(encoding="utf-8")
assert "geometry:" in mapjs and "window.NYCTAMap" in mapjs, "nycta-map.js no longer exports NYCTAMap.geometry: check build.py"
mapjs = re.sub(r"</(script)", r"<\\/\1", mapjs, flags=re.I)   # inline: a '</script' (even in a comment) would end the tag

njs = (root / "vendor/nycta/nycta.js").read_text(encoding="utf-8")
PB = "/* Print simulation layer (DEC-038)"
assert njs.count(PB) == 1 and "data-print-toggle" in njs, "nycta.js print block not found: check build.py"
printjs = njs[njs.index(PB):].rstrip()
assert printjs.endswith("})();"), "nycta.js print block is no longer the last block: check build.py"
printjs = re.sub(r"</(script)", r"<\\/\1", printjs, flags=re.I)

# ---------- 웹 연재(G): posts/*.md → 글 페이지 + 노선도의 역 ----------
POSTS = root / "posts"
POST_MARK = "<!-- built from posts/{} by build.py: edit the .md, not this file -->"
m = re.search(r"\bG: \{ token:'(--c-[a-z]+)' \}", src)
assert m, "DESIGN.lines.G token not found in src/map.html: check build.py"
G_TOKEN = m.group(1)   # 노선 색은 src/map.html DESIGN.lines.G 한 곳에서만 정한다
G_SERIES = re.search(r"\{key:'G'[^}]*series:\[\['G','([^']+)'\]\]", src).group(1)

# 글 속 원판 {G}, {G:orange} (2026-11-21 사용자 요청: 본문 중간에 원판을 바로 부르기). 모양은 nycta 줄 안 원판(.disc--inline, DEC-034).
# 색: 이름을 적으면 그 색, 아니면 노선도 노선(DESIGN.lines/groups, src/map.html 한 곳)의 색, 그것도 아니면 nycta.css의
# 1970 매뉴얼 노선 색(data-line 규칙, 예: {A} 파랑), 그마저 없으면 검정. 글자는 노랑에만 검정, 나머지는 흰색(DEC-004).
LINE_TOKENS = dict(re.findall(r"\b(\w+): \{ token:'(--c-[a-z]+)' \}", src[src.index("lines: {"):src.index("groups: {")]))
GROUP_TOKENS = dict(re.findall(r"\b(\w+): \{ token:'(--c-[a-z]+)', lines:", src[src.index("groups: {"):]))
for k, g in re.findall(r"\b(\w+): \{ group:'(\w+)' \}", src[src.index("lines: {"):src.index("groups: {")]):
    LINE_TOKENS[k] = GROUP_TOKENS[g]
assert LINE_TOKENS.get("G") == G_TOKEN, "DESIGN.lines parse failed: check build.py"
DISC_COLORS = ("yellow", "orange", "red", "magenta", "green", "lightblue", "blue", "black")   # nycta 팔레트(COLOR-005) + 검정
for c in DISC_COLORS:
    assert f"--c-{c}:" in nycta, f"nycta.css has no --c-{c}: check build.py"
DISC_RE = re.compile(r"(\\?)\{([0-9A-Z]{1,2})(?::([a-z]+))?\}")

def disc_html(label, token=None, hidden=False):
    style = f' style="--line:var({token});color:var(--c-{"black" if token == "--c-yellow" else "white"})"' if token else ""
    color = f' data-color="{token[4:]}"' if token else ""
    return (f'<span class="disc disc--inline" data-line="{label}"{color}{style}' + (' aria-hidden="true"' if hidden else "") +
            f'><span>{label}</span></span>')

CURRENT = ["posts"]   # 오류 메시지에 쓸 지금 만드는 글

def md_discs(t):
    def one(m):
        if m.group(1): return m.group(0)[1:]          # \{G} → 글자 그대로 {G}
        label, name = m.group(2), m.group(3)
        if name and name not in DISC_COLORS:
            raise SystemExit(f"{CURRENT[0]}: 원판 {m.group(0)}에 쓴 색 이름을 찾지 못했습니다. 쓸 수 있는 색은 {', '.join(DISC_COLORS)}입니다.")
        return disc_html(label, f"--c-{name}" if name else LINE_TOKENS.get(label))
    # <code> 안은 건드리지 않는다
    return "".join(seg if seg.startswith("<code>") else DISC_RE.sub(one, seg) for seg in re.split(r"(<code>.*?</code>)", t))

def rich(t):
    """머리말 글(제목·요약)을 글 페이지에 넣을 때: 원판 표기를 원판으로(본문과 같은 규칙)."""
    return md_discs(html.escape(t))

def plain(t):
    """원판을 그릴 수 없는 곳(브라우저 탭 이름, 검색 설명, 노선도 역 이름·팝업 요약)에는 원판 표기를 빼고 글자만 남긴다."""
    md_discs(html.escape(t))   # 색 이름 확인만
    return re.sub(r"\s{2,}", " ", DISC_RE.sub(lambda m: m.group(0)[1:] if m.group(1) else "", t)).strip()

def md_inline(t):
    t = html.escape(t)
    def link(m):
        ext = re.match(r"https?://", m.group(2))
        return f'<a href="{m.group(2)}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{m.group(1)}</a>"
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return md_discs(t)

def md_blocks(text):
    """작은 마크다운: 문단, ## 소제목, > 인용, - · 1. 목록, --- 구분선, 이미지 한 줄(설명이 있으면 캡션), <로 시작하는 HTML은 그대로.
    한 줄 바꿈은 띄어쓰기로 이어지고, 줄 끝에 공백 두 칸이나 역슬래시를 두면 그 자리에서 줄을 바꾼다."""
    out, buf, kind = [], [], None
    def para(lines):
        return "<br>".join(md_inline(l.rstrip("\\").strip()) if l.endswith(("  ", "\\")) else md_inline(l.strip()) for l in lines) \
            if any(l.endswith(("  ", "\\")) for l in lines) else md_inline(" ".join(l.strip() for l in lines))
    def flush():
        nonlocal buf, kind
        if not buf: return
        if kind == "p":
            img = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", " ".join(l.strip() for l in buf))
            if img and img.group(1):
                out.append(f'<figure><img src="{html.escape(img.group(2))}" alt="{html.escape(img.group(1))}" loading="lazy">'
                           f"<figcaption>{md_inline(img.group(1))}</figcaption></figure>")
            else:
                out.append(f"<p>{para(buf)}</p>")
        elif kind == "quote":
            out.append("<blockquote>" + "".join(f"<p>{para(b.splitlines())}</p>" for b in "\n".join(buf).split("\n\n") if b.strip()) + "</blockquote>")
        elif kind in ("ul", "ol"):
            out.append(f"<{kind}>" + "".join(f"<li>{md_inline(i)}</li>" for i in buf) + f"</{kind}>")
        elif kind == "html":
            out.append("\n".join(buf))
        buf, kind = [], None
    for line in text.splitlines():
        st = line.strip()
        if kind == "html" and st:
            buf.append(line); continue
        if not st:
            if kind == "quote": buf.append(""); continue
            flush(); continue
        h = re.match(r"(#{1,4})\s+(.*)", st)
        li = re.match(r"[-*]\s+(.*)", st); ol = re.match(r"\d+[.)]\s+(.*)", st)
        if h:
            flush(); lv = min(3, max(2, len(h.group(1)))); out.append(f"<h{lv}>{md_inline(h.group(2))}</h{lv}>")
        elif re.fullmatch(r"(-{3,}|\*{3,})", st):
            flush(); out.append("<hr>")
        elif st.startswith("<"):
            flush(); kind = "html"; buf.append(line)
        elif st.startswith(">"):
            if kind != "quote": flush(); kind = "quote"
            buf.append(st[1:].lstrip())
        elif li or ol:
            k = "ul" if li else "ol"
            if kind != k: flush(); kind = k
            buf.append((li or ol).group(1))
        elif kind in ("ul", "ol") and line[:1] in " \t":
            buf[-1] += " " + st   # 목록 항목이 다음 줄로 이어짐
        else:
            if kind != "p": flush(); kind = "p"
            buf.append(line)
    flush()
    return "\n".join("      " + b for b in out)

def front_matter(text, name):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n?(.*)", text, re.S)
    assert m, f"posts/{name}: 맨 위에 --- 로 감싼 머리말(title, date …)이 있어야 합니다"
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1); meta[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("title", "date"):
        assert meta.get(k), f"posts/{name}: 머리말에 {k}가 없습니다"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["date"]), f"posts/{name}: date는 2026-11-21 형식으로 씁니다"
    meta["draft"] = meta.get("draft", "").lower() in ("true", "yes", "1", "예")
    return meta, m.group(2)

# [eee] 끝 줄(2026-11-21 사용자 요청, 그린 대로): [← (G) 이전 글 제목] [(G) 다음 글 제목 →] [돌아가기 ↙].
# 화살표는 가리키는 쪽 끝에 붙는다(사용자 지정, COPY-005의 '화살표 먼저'와 다름). 제목 앞 원판은 그 글의 노선(G),
# 제목이 원판으로 시작하면 그 원판을 쓴다. 줄은 글처럼 흘러 넘치면 다음 줄로 이어진다(사용자 취향, CLAUDE.md).
# 화살표·원판이 홀로 줄 끝·줄 머리에 남지 않게 붙어 있는 첫(끝) 낱말과 묶는다(.nw).
# 글 페이지(posts/*.html, 화살표 #arrow)와 노선도 읽기 판(index.html, 화살표 #nyarrow)이 같이 쓴다.
def seq_body(d, title, label, after, arrow_id="arrow"):
    a = f'<svg class="arrow" data-dir="{d}" aria-hidden="true"><use href="#{arrow_id}"/></svg>'
    if title:
        t = rich(title).strip(); m = re.match(r'(<span class="disc[^>]*><span>[^<]*</span></span>)\s*', t)
        lead, t = (m.group(1), t[m.end():]) if m else (disc_html("G", G_TOKEN, hidden=True), t)
    else:
        lead, t = "", label
    if after:   # [원판 첫 낱말] … [끝 낱말 화살표]
        f = re.match(r'([^\s<]+)\s+(.*)$', t)
        if lead and f: t = f'<span class="nw">{lead}{f.group(1)}</span> {f.group(2)}'; lead = ""
        l = re.match(r'^(.*\S)\s+([^\s<>]+)$', t)
        return f'{lead}{l.group(1)} <span class="nw">{l.group(2)}{a}</span>' if l else f'<span class="nw">{lead}{t}{a}</span>'
    f = re.match(r'([^\s<]+)\s+(.*)$', t)   # [화살표 원판 첫 낱말] …
    return f'<span class="nw">{a}{lead}{f.group(1)}</span> {f.group(2)}' if f else f'<span class="nw">{a}{lead}{t}</span>'

def seq_aria(label, title):
    return f' aria-label="{html.escape(label + ": " + plain(title))}"' if title else ' aria-label="노선도로 돌아가기"'

def map_body(body_html):
    """[eee] 노선도 읽기 판에 넣는 본문: 글 페이지(posts/) 기준 상대 주소를 index.html 기준으로 바꾼다(그림·글 사이 링크)."""
    return re.sub(r'\b(src|href)="(?![a-z][\w+.-]*:|/|#)([^"]+)"', r'\1="posts/\2"', body_html)

def build_posts(data_text, post_tokens):
    if not POSTS.is_dir():
        return data_text
    tpl = (root / "src/post.html").read_text(encoding="utf-8").replace("/*__NYCTA_PRINT__*/", printjs)   # ⁘ 인쇄 질감(잉크 번짐 필터 주입)
    (POSTS / "post.css").write_text("/* posts/post.css — build.py가 만든다: vendor/nycta/nycta.css 전체 + src/post.css. src/post.css를 고친다. */\n" + post_tokens + "\n\n" +
        (root / "src/post.css").read_text(encoding="utf-8"), encoding="utf-8")
    posts = []
    for f in sorted(POSTS.glob("*.md")):
        if f.name.startswith("_"): continue
        meta, body = front_matter(f.read_text(encoding="utf-8"), f.name)
        posts.append(dict(meta, file=f, slug=f.stem, body=body))
    posts.sort(key=lambda p: (p["date"], p["slug"]))   # 역 번호는 게시일 순서(G-01부터)
    for i, p in enumerate(posts): p["id"] = f"G-{i + 1:02d}"
    public = [p for p in posts if not p["draft"]]
    disc = disc_html("G", G_TOKEN, hidden=True)
    for p in posts:
        CURRENT[0] = f"posts/{p['file'].name}"; plain(p.get("station", ""))   # 오류 메시지용, 역 이름의 색 이름도 확인
        seq_list = posts if p["draft"] else public   # 공개 글의 이전·다음에는 초안이 끼지 않는다
        k = seq_list.index(p); prev = seq_list[k - 1] if k else None; nxt = seq_list[k + 1] if k + 1 < len(seq_list) else None
        def item(cls, href, label, d, title=None, after=False):
            return f'<li><a class="{cls}" href="{href}"{seq_aria(label, title)}>{seq_body(d, title, label, after)}</a></li>'
        seq = "".join(filter(None, (item("prev", f'{prev["slug"]}.html', "이전 글", "left", prev["title"]) if prev else "",
                                     item("next", f'{nxt["slug"]}.html', "다음 글", "right", nxt["title"], after=True) if nxt else "",
                                     item("back", f'../index.html#{p["id"]}', "돌아가기", "down-left", after=True))))   # 항목 사이에 빈칸 없음(2026-11-21 사용자 요청: 제목 안 띄어쓰기만)
        y, mo, d = map(int, p["date"].split("-"))
        page = tpl
        # 글 머리(2026-11-21 사용자 요청, 매뉴얼 SIGN-016 열차 표지처럼): 흰 칸에 원판, 그 옆에 제목. 제목이 원판으로 시작하면 그 원판, 아니면 G
        th = rich(p["title"]); lead = re.match(r'(<span class="disc[^>]*><span>[^<]*</span></span>)\s*', th)
        head_disc, head_title = (lead.group(1), th[lead.end():]) if lead else (disc, th)
        head_disc = head_disc.replace("disc disc--inline", "disc", 1)   # 칸 안의 큰 원판: 줄 안 원판 규칙(DEC-034)이 아니라 지름에서 글자 크기를 잡는다
        for key, val in (("__TITLE_TEXT__", html.escape(plain(p["title"]))), ("__TITLE__", head_title), ("__HEADDISC__", head_disc),
                         ("__SUMMARY__", html.escape(plain(p.get("summary", "")))), ("__ID__", p["id"]),
                         ("__DISC__", disc), ("__SERIES__", html.escape(G_SERIES)), ("__DATE_TEXT__", f"{y}년 {mo}월 {d}일"),
                         ("__DATE__", p["date"]), ("__SEQ__", seq), ("__BODY__", md_blocks(p["body"]))):
            page = page.replace(key, val)
        page = page.replace("<head>", "<head>\n" + POST_MARK.format(p["file"].name), 1)
        (POSTS / f'{p["slug"]}.html').write_text(page, encoding="utf-8")
        # [eee] 노선도 읽기 판(2026-11-21 사용자 요청: 요약을 누르면 팝업이 읽기 판으로 커진다). file://에서도 열리게 fetch 없이
        # 본문을 데이터에 넣는다. 이전·다음은 보이는 글(배포 사이트는 초안 제외)에 따라 노선도가 고르므로, 이 글이 '이전 글'일 때와
        # '다음 글'일 때의 끝 줄 조각을 둘 다 넣어 둔다
        p["reader"] = {"slug": p["slug"], "th": rich(p["title"]).strip(), "tt": plain(p["title"]), "body": map_body(md_blocks(p["body"])),
                       "np": seq_body("left", p["title"], "이전 글", False, "nyarrow"), "nn": seq_body("right", p["title"], "다음 글", True, "nyarrow")}
    # .md가 없어진 글 페이지(build.py가 만든 것만)는 지운다
    for h in POSTS.glob("*.html"):
        if not (POSTS / f"{h.stem}.md").exists() and "by build.py: edit the .md" in h.read_text(encoding="utf-8")[:400]:
            h.unlink(); print(f"posts/{h.name}: removed (no .md)")
    d = json.loads(data_text)
    d["글"] = [{"id": p["id"], "b": "G", "s": plain(p.get("station") or p["title"]), "t": plain(p.get("station") or p["title"]), "d": p["date"],
               "u": f'posts/{p["slug"]}.html', "ser": G_SERIES, "m": plain(p.get("summary", "")), "post": 1, **p["reader"],
               **({"draft": 1} if p["draft"] else {})}
              for p in posts]
    if posts:
        print(f"posts: {len(public)} published, {len(posts) - len(public)} draft(s) (drafts show on file:// / localhost only)")
    # 본문 HTML이 <script> 안에 들어가므로 '</'를 끊어 둔다(JSON 문자열 안에서 '<\/'는 '</'와 같다)
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")

data = build_posts(data, post_tokens)
for key in ("__DATA__", "__DATA_EN__", "/*__NYCTA__*/", "/*__NYCTA_MAP__*/", "/*__NYCTA_PRINT__*/"):
    assert src.count(key) == 1, f"src/map.html must contain {key} exactly once"
out = src.replace("/*__NYCTA__*/", tokens).replace("__DATA_EN__", data_en).replace("__DATA__", data).replace("/*__NYCTA_MAP__*/", mapjs).replace("/*__NYCTA_PRINT__*/", printjs)
(root / "index.html").write_text(out, encoding="utf-8")
print(f"index.html built ({len(out) // 1024} KB)")

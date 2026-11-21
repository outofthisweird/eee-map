"""웹 연재(G) 읽기 판 테스트(2026-11-21): 팝업 → 읽기 판 → 다음 글 → 닫기, 브라우저 뒤로 가기, 주소로 바로 열기.
   python3 build.py && python3 tests/reader_test.py
   (Playwright: ../nycta-gsm-src/.venv/bin/python tests/reader_test.py)"""
import asyncio, os
from pathlib import Path
from playwright.async_api import async_playwright
URL = (Path(__file__).resolve().parents[1] / "index.html").as_uri()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        ok = True
        def check(name, cond, info=""):
            nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, info)
        for w, h in ((1400, 900), (390, 844)):
            pg = await b.new_page(viewport={"width": w, "height": h})
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(URL); await pg.evaluate("localStorage.clear()")
            await pg.goto(URL); await pg.wait_for_timeout(2500)
            tag = f"[{w}px]"
            G = await pg.evaluate("byLine.G.st.map(s=>({id:s.id,slug:s.slug,tt:s.tt}))")
            k = 1 if len(G) > 2 else 0
            # 1. 역을 누르면 팝업, 요약을 누르면 같은 페이지에서 읽기 판
            pt = await pg.evaluate(f"(()=>{{const s=byLine.G.st[{k}];centerOn(s,0,true);const r=s.g.querySelector('.dot').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}})()")
            await pg.mouse.click(*pt); await pg.wait_for_timeout(700)
            href = await pg.evaluate("location.href")
            await pg.click("#psum"); await pg.wait_for_timeout(900)
            r = await pg.evaluate("""(()=>{const p=panel.getBoundingClientRect();return {hash:location.hash,reading:reading&&reading.id,
              cls:panel.classList.contains('reading'),title:rtitle.textContent,body:rbody.textContent.length,
              path:location.pathname,cover:p.width*p.height/(innerWidth*innerHeight),
              st:(()=>{const d=reading.g.querySelector('.dot').getBoundingClientRect();return {x:d.x+d.width/2,y:d.y+d.height/2}})(),
              left:p.left,top:p.top,bodyFs:parseFloat(getComputedStyle(rbody).fontSize),chrome:getComputedStyle(logo).visibility}})()""")
            check(f"{tag} summary opens the reading plate, no page change", r["cls"] and r["reading"] == G[k]["id"] and r["hash"] == "#read=" + G[k]["slug"]
                  and G[k]["tt"] in r["title"] and r["body"] > 200 and r["path"].endswith("index.html"), r)
            check(f"{tag} the plate covers most of the screen, the station shows beside it", r["cover"] > (.85 if w < 641 else .4)
                  and 0 <= r["st"]["x"] <= w and 0 <= r["st"]["y"] <= h and (r["st"]["x"] < r["left"] if w > 640 else r["st"]["y"] < r["top"])
                  and r["chrome"] == "hidden", r)
            # 2. 다음 글: 카메라가 그 역으로 가고 판 내용이 바뀐다
            nxt = await pg.query_selector("#rnav a.next")
            check(f"{tag} end line has next / back", nxt is not None and await pg.query_selector("#rnav a.back") is not None)
            await nxt.click(); await pg.wait_for_timeout(900)
            r2 = await pg.evaluate("""(()=>{const p=panel.getBoundingClientRect(),d=reading.g.querySelector('.dot').getBoundingClientRect();
              return {hash:location.hash,reading:reading.id,title:rtitle.textContent,top:reader.scrollTop,
              st:{x:d.x+d.width/2,y:d.y+d.height/2},anchor:readerAnchor(reading),current:current.id}})()""")
            check(f"{tag} next moves to the next station and swaps the article", r2["reading"] == G[k + 1]["id"] == r2["current"]
                  and r2["hash"] == "#read=" + G[k + 1]["slug"] and G[k + 1]["tt"] in r2["title"] and r2["top"] == 0
                  and abs(r2["st"]["x"] - r2["anchor"][0]) < 3 and abs(r2["st"]["y"] - r2["anchor"][1]) < 3, r2)
            # 3. 돌아가기: 판이 닫히고 그 역 팝업이 노선도에 남는다. 뒤로 가기 한 번이면 노선도를 떠나지 않는다
            await pg.click("#rnav a.back"); await pg.wait_for_timeout(900)
            r3 = await pg.evaluate("({reading:!!reading,open:panel.classList.contains('open'),cls:panel.classList.contains('reading'),hash:location.hash,current:current&&current.id,chrome:getComputedStyle(logo).visibility})")
            check(f"{tag} 돌아가기 closes the plate back to the popup", not r3["reading"] and not r3["cls"] and r3["open"]
                  and r3["current"] == G[k + 1]["id"] and r3["hash"] == "#" + G[k + 1]["id"] and r3["chrome"] == "visible", r3)
            # 4. Esc, 브라우저 뒤로 가기
            await pg.click("#psum"); await pg.wait_for_timeout(700)
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(700)
            r4 = await pg.evaluate("({reading:!!reading,open:panel.classList.contains('open'),hash:location.hash})")
            await pg.click("#psum"); await pg.wait_for_timeout(700)
            await pg.go_back(); await pg.wait_for_timeout(900)
            r5 = await pg.evaluate("({reading:!!reading,open:panel.classList.contains('open'),hash:location.hash,url:location.href})")
            check(f"{tag} Esc closes the plate", not r4["reading"] and r4["open"] and r4["hash"].startswith("#G-"), r4)
            # 4b. 판 바깥(노선도)을 누르면 돌아가기와 같다. 닫힐 때는 빈 판이 팝업 자리로 줄어든다
            await pg.click("#psum"); await pg.wait_for_timeout(700)
            await pg.mouse.click(30 if w > 640 else 195, h - 30 if w > 640 else 30); await pg.wait_for_timeout(120)
            ghost = await pg.evaluate("!!document.querySelector('.rghost')&&panel.classList.contains('hold')")
            await pg.wait_for_timeout(900)
            r7 = await pg.evaluate("({reading:!!reading,open:panel.classList.contains('open'),hold:panel.classList.contains('hold'),ghost:!!document.querySelector('.rghost'),hash:location.hash})")
            check(f"{tag} a click outside the plate goes back, with a closing animation", ghost and not r7["reading"] and r7["open"]
                  and not r7["hold"] and not r7["ghost"] and r7["hash"].startswith("#G-"), {"ghostSeen": ghost, **r7})
            # 4c. 끝 줄: 제목 안 띄어쓰기 말고는 빈칸·간격이 없다
            await pg.click("#psum"); await pg.wait_for_timeout(700)
            r8 = await pg.evaluate("""(()=>{const n=rnav,a=[...n.querySelectorAll('a')];
              const gaps=[...n.querySelectorAll('a,.disc,.arrow')].map(x=>{const c=getComputedStyle(x);return parseFloat(c.marginLeft)+parseFloat(c.marginRight)});
              return {between:[...n.childNodes].filter(x=>x.nodeType===3).length,gaps:Math.max(...gaps),
                spaces:a.map(x=>x.textContent.split(' ').length-1),titles:a.map(x=>x.classList.contains('back')?0:(x.getAttribute('aria-label').split(': ')[1].split(' ').length-1))}})()""")
            check(f"{tag} end line has no spaces but the titles' own", r8["between"] == 0 and r8["gaps"] == 0 and r8["spaces"] == r8["titles"], r8)
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(900)
            check(f"{tag} browser back closes the plate and stays on the map", not r5["reading"] and r5["open"]
                  and r5["url"].split("#")[0] == href.split("#")[0] and r5["hash"].startswith("#G-"), r5)
            # 5. 주소로 바로 들어오면 그 역에서 판이 열린 채로 시작
            await pg.goto(URL + "#read=" + G[0]["slug"]); await pg.wait_for_timeout(600)
            r6 = await pg.evaluate("({reading:reading&&reading.id,cls:panel.classList.contains('reading'),st:(()=>{const d=byLine.G.st[0].g.querySelector('.dot').getBoundingClientRect();return [d.x,d.y]})()})")
            check(f"{tag} #read=<post> opens with the plate", r6["reading"] == G[0]["id"] and r6["cls"]
                  and 0 <= r6["st"][0] <= w and 0 <= r6["st"][1] <= h, r6)
            # 6. 새로고침은 처음부터: 읽던 중에 새로고침해도 노선이 자라나는 애니메이션이 나오고, 그 뒤 판이 다시 열린다
            await pg.reload(); await pg.wait_for_timeout(150)
            a = await pg.evaluate("({anims:document.getAnimations().length,reading:!!reading})")
            await pg.wait_for_timeout(2300)
            z = await pg.evaluate("({reading:reading&&reading.id,hash:location.hash})")
            check(f"{tag} reload while reading replays the intro, then reopens the plate", a["anims"] > 50 and not a["reading"]
                  and z["reading"] == G[0]["id"] and z["hash"] == "#read=" + G[0]["slug"], {"first": a, "later": z})
            check(f"{tag} no JS errors", not errs, errs[:3])
            await pg.close()
        await b.close()
        raise SystemExit(0 if ok else 1)
asyncio.run(main())

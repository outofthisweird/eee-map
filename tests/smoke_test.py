"""Headless smoke test.  pip install playwright && playwright install chromium
   python3 build.py && python3 tests/smoke_test.py"""
import asyncio, random
from pathlib import Path
from playwright.async_api import async_playwright
URL = (Path(__file__).resolve().parents[1] / "index.html").as_uri()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()")
        await pg.goto(URL); await pg.wait_for_timeout(3500)
        ok = True
        def check(name, cond, info=""):
            nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, info)

        # 1. clicking a station opens the popup with the Instagram link
        pt = await pg.evaluate("(()=>{const s=byLine.E.st[5];const r=s.g.querySelector('.dot').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
        await pg.mouse.click(*pt); await pg.wait_for_timeout(900)
        check("popup opens on click", await pg.evaluate("!!current && document.querySelector('#panel').classList.contains('open')"))
        await pg.keyboard.press("Escape")

        # 2. random layouts (↻): on the grid, no terminal transfers, no self-crossing
        bad = {"offgrid": 0, "termXfer": 0, "selfCross": 0}
        for _ in range(20):
            await pg.evaluate("document.querySelector('#replay').click()"); await pg.wait_for_timeout(120)
            r = await pg.evaluate("""(()=>({offgrid:all.filter(offGrid).length,
              termXfer:all.filter(s=>s.xfer&&(s.i===0||s.i===s.line.st.length-1)).length,
              selfCross:LINES.reduce((n,L)=>n+tangles(L,L.st.map(s=>[s.x,s.y])).cross.length,0)}))()""")
            for k in bad: bad[k] += r[k]
        check("20 random layouts clean", not any(bad.values()), bad)
        await pg.wait_for_timeout(3000)

        # 3. dragging stations: stays on grid, dragged station mostly stays put
        random.seed(1); moved = []
        for _ in range(12):
            sid = await pg.evaluate(f"(()=>{{const c=all.filter(s=>!s.xfer&&s.i>0);return c[{random.randrange(99)}%c.length].id}})()")
            await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');view={{k:.8,x:720-s.x*.8,y:450-s.y*.8}};apply()}})()"); await pg.wait_for_timeout(80)
            a = await pg.evaluate(f"(()=>{{const r=all.find(x=>x.id==='{sid}').g.querySelector('.dot').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}})()")
            dx, dy = random.uniform(-160, 160), random.uniform(-160, 160)
            await pg.mouse.move(*a); await pg.mouse.down()
            for i in range(1, 13): await pg.mouse.move(a[0]+dx*i/12, a[1]+dy*i/12); await pg.wait_for_timeout(16)
            drop = await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');return [s.x,s.y]}})()")
            await pg.mouse.up(); await pg.wait_for_timeout(1800)
            aft = await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');return [s.x,s.y]}})()")
            moved.append(((drop[0]-aft[0])**2 + (drop[1]-aft[1])**2) ** .5)
        check("all stations on grid after drags", await pg.evaluate("all.filter(offGrid).length") == 0)
        check("dragged station stays put (>=75%)", sum(m < 1 for m in moved) >= .75*len(moved), [round(m) for m in moved])
        check("no JS errors", not errs, errs[:3])
        await b.close()
        raise SystemExit(0 if ok else 1)
asyncio.run(main())

"""환승역 근처 드래그 스트레스 테스트.
   python3 build.py && python3 tests/drag_stress.py [드래그 횟수]
환승역 바로 옆 역과 환승역 자체를 크게 끌어 본 뒤 꼬임(자기 교차·접힘)과
늘어난 구간이 얼마나 남는지 센다."""
import asyncio, random, sys, os
from pathlib import Path
from playwright.async_api import async_playwright
URL = (Path(__file__).resolve().parents[1] / "index.html").as_uri()
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30

STATS = """(()=>{let cross=0,folds=0,long=0;LINES.forEach(L=>{const q=L.st.map(s=>[s.x,s.y]);const t=tangles(L,q);
  cross+=t.cross.length;folds+=t.folds.length;
  for(let i=1;i<q.length;i++)if(Math.hypot(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1])>PULL.maxGap*1.6)long++});
  const split=all.filter(s=>(s.i===0||s.i===s.line.st.length-1)&&s.xfer).length;
  return {cross,folds,long,offgrid:all.filter(offGrid).length,termXfer:split,
    corner:TRACK.reduce((n,L)=>n+L.route.bad,0),curved:curvedNow.length,nameClash:nameClashes}})()"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()")
        await pg.goto(URL); await pg.wait_for_timeout(3000)
        random.seed(7)
        tot = {"cross": 0, "folds": 0, "long": 0, "offgrid": 0, "termXfer": 0, "corner": 0, "curved": 0, "nameClash": 0}; moved = []; worst = []
        for n in range(N):
            if n % 10 == 0:   # 10번마다 새 랜덤 배치
                await pg.evaluate(f"(()=>{{sdrag=null;settle=null;tween=null;generate(rng({1000+n}));savePos();build()}})()")
                await pg.wait_for_timeout(200)
            before = await pg.evaluate(STATS)
            kind = "xfer" if n % 3 == 2 else "nb"
            sid = await pg.evaluate(f"""(()=>{{const X=all.filter(s=>s.xfer&&!s.owner);
              const nb=all.filter(s=>!s.xfer&&s.i>0&&[s.line.st[s.i-1],s.line.st[s.i+1]].some(o=>o&&o.xfer));
              const c={'"xfer"' if kind == "xfer" else 'nb'}==="xfer"?X:nb;return c.length?c[{random.randrange(999)}%c.length].id:null}})()""".replace('"xfer"===', '"xfer"==='))
            if not sid: continue
            await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');view={{k:.6,x:720-s.x*.6,y:450-s.y*.6}};apply()}})()")
            await pg.wait_for_timeout(60)
            a = await pg.evaluate(f"(()=>{{const r=all.find(x=>x.id==='{sid}').g.querySelector('.dot').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}})()")
            ang = random.uniform(0, 6.283); dist = random.uniform(150, 280)
            import math
            dx, dy = math.cos(ang) * dist, math.sin(ang) * dist
            await pg.mouse.move(*a); await pg.mouse.down()
            for i in range(1, 16): await pg.mouse.move(a[0]+dx*i/15, a[1]+dy*i/15); await pg.wait_for_timeout(16)
            drop = await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');return [s.x,s.y]}})()")
            await pg.mouse.up(); await pg.wait_for_timeout(3000)
            aft = await pg.evaluate(f"(()=>{{const s=all.find(x=>x.id==='{sid}');return [s.x,s.y]}})()")
            st = await pg.evaluate(STATS)
            delta = {k: max(0, st[k] - before[k]) for k in tot}
            for k in tot: tot[k] += delta[k]
            moved.append(round(((drop[0]-aft[0])**2 + (drop[1]-aft[1])**2) ** .5))
            if any(delta.values()): worst.append((n, kind, sid, delta))
        print("새로 생긴 문제 합계:", tot)
        print("드래그한 역이 놓은 뒤 밀려난 거리(px):", moved)
        for w in worst[:12]: print("  ", w)
        print("JS 오류:", errs[:3])
        await b.close()
asyncio.run(main())

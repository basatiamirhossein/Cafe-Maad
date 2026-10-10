"""Full-page screenshots of chosen routes. Usage: python3 shots.py lang width route [route...]"""
import asyncio
import pathlib
import sys

from playwright.async_api import async_playwright

H = pathlib.Path(__file__).parent
URL = (H.parent.parent / "index.html").as_uri()
FIX = "body{position:relative}.backdrop{position:absolute!important;inset:0!important;height:auto!important;background-size:auto 1300px!important;background-repeat:repeat-y!important}"


async def main(lang: str, width: int, routes: list[str]) -> None:
    out = H / "shots"; out.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = await b.new_page(viewport={"width": width, "height": 900 if width > 800 else 844})
        await pg.goto(URL + "#" + lang); await pg.wait_for_timeout(500)
        await pg.add_style_tag(content=FIX)
        for r in routes:
            await pg.evaluate(f"location.hash = '{r}'"); await pg.wait_for_timeout(400)
            name = f"{lang}-{width}-{r.strip('#/').replace('/', '_') or 'home'}.png"
            await pg.screenshot(path=str(out / name), full_page=True, timeout=240000)
            print(name)
        await b.close()

asyncio.run(main(sys.argv[1], int(sys.argv[2]), sys.argv[3:]))

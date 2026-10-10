"""Layout sweep: every route x 4 languages x 5 viewports. Reports JS errors, horizontal overflow and empty i18n slots."""
import asyncio
import json
import pathlib
import sys

from playwright.async_api import async_playwright

H = pathlib.Path(__file__).parent
URL = (H.parent.parent / "index.html").as_uri()
ROUTES = ["#/", "#/products", "#/products/gear", "#/products/mugs", "#/products/more", "#/order", "#/wholesale", "#/blog", "#/blog/01", "#/blog/07", "#/blog/17", "#/about", "#/contact"]
LANGS = ["fa", "en", "ar", "tr"]
VIEWS = [(360, 740), (390, 844), (768, 1024), (1280, 800), (1440, 900)]
if len(sys.argv) > 1 and sys.argv[1] == "quick":
    VIEWS = [(390, 844), (1440, 900)]

CHECK = """() => {
  const vw = document.documentElement.clientWidth;
  const over = [];
  for (const n of document.querySelectorAll('body *')) {
    if (n.closest('[hidden], .table-wrap, figure.info, .drawer, svg, .toast, .skip, .receipt')) continue;
    const r = n.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.right > vw + 1 || r.left < -1) { over.push((n.className && n.className.baseVal === undefined ? n.className : n.tagName) + ' ' + Math.round(r.left) + '..' + Math.round(r.right)); if (over.length > 4) break; }
  }
  const empty = [...document.querySelectorAll('[data-i18n],[data-i18n-html]')].filter(n => !n.closest('[hidden]') && !n.textContent.trim() && n.dataset.i18n !== 'faOnly').map(n => n.dataset.i18n || n.dataset.i18nHtml);
  return { sw: document.documentElement.scrollWidth, vw, over, empty, title: document.title };
}"""


async def main() -> None:
    problems = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        for w, h in VIEWS:
            ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg = await ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            await pg.goto(URL + "#/")
            await pg.wait_for_timeout(400)
            for lang in LANGS:
                await pg.click(f'[data-lang="{lang}"]') if w > 0 else None
                for r in ROUTES:
                    await pg.evaluate(f"location.hash = '{r}'")
                    await pg.wait_for_timeout(120)
                    res = await pg.evaluate(CHECK)
                    if res["sw"] > res["vw"] + 1 or res["over"] or res["empty"]:
                        problems.append({"view": w, "lang": lang, "route": r, **res})
            if errs:
                problems.append({"view": w, "errors": errs[:5]})
            await ctx.close()
        await b.close()
    print(json.dumps(problems, ensure_ascii=False, indent=1)[:6000])
    print("problem count", len(problems))


asyncio.run(main())

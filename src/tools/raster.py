"""Rasterize svg/*.svg with Chromium (transparent background) and save WebP files in img/."""
import asyncio, base64, json, pathlib, sys
from PIL import Image
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
FONTS = HERE.parent / "fonts"
TARGET = {"bg": (1920, None), "cup-big": (900, None), "grounds": (900, None), "twobeans": (640, None)}
DEFAULT_PRODUCT = 480

def font_css() -> str:
    b = base64.b64encode((FONTS / "tektur.woff2").read_bytes()).decode()
    return f'@font-face{{font-family:"Tektur";src:url(data:font/woff2;base64,{b}) format("woff2");font-weight:400 900;font-stretch:75% 100%}}'

async def main(names: list[str]) -> None:
    css = font_css()
    files = sorted((HERE / "svg").glob("*.svg"))
    if names:
        files = [p for p in files if p.stem in names]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        for svg in files:
            text = svg.read_text(encoding="utf-8")
            w = int(text.split('width="')[1].split('"')[0]); h = int(text.split('height="')[1].split('"')[0])
            pg = await b.new_page(viewport={"width": w, "height": h})
            await pg.set_content(f"<html><head><style>{css}html,body{{margin:0;background:transparent}}svg{{display:block}}</style></head><body>{text}</body></html>")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(150)
            png = HERE / "img" / f"{svg.stem}.png"
            await pg.screenshot(path=str(png), omit_background=svg.stem != "bg", timeout=180000)
            await pg.close()
            im = Image.open(png)
            if svg.stem == "bg":
                im = im.convert("RGB")
            tw = TARGET.get(svg.stem, (DEFAULT_PRODUCT if not svg.stem.startswith(("cup", "bean")) else (720 if svg.stem.startswith("cup") else 160), None))[0]
            if im.width > tw:
                im = im.resize((tw, round(im.height * tw / im.width)), Image.LANCZOS)
            q = 78 if svg.stem == "bg" else 84
            out = HERE / "img" / f"{svg.stem}.webp"
            im.save(out, "WEBP", quality=q, method=6)
            print(svg.stem, im.size, out.stat().st_size)
        await b.close()

asyncio.run(main(sys.argv[1:]))

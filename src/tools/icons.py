"""Cafe Maad logo: writes the header symbol into icons.svg and the app icons into /icons.

Usage: python3 src/tools/icons.py        (needs Playwright + Chromium; run again after changing the mark)
"""
import asyncio
import base64
import io
import json
import pathlib
import re

from PIL import Image
from playwright.async_api import async_playwright

SRC = pathlib.Path(__file__).resolve().parent.parent
ROOT = SRC.parent
OUT = ROOT / "icons"

NAVY, CREAM, CORAL, SAND, PAGE = "#172b5e", "#fbf6ee", "#ce685f", "#e8d4a1", "#efe1bd"
BOX = 1254
CENTRE = (628, 442)  # centre of the mark's bounding box inside BOX
# The "ماد" letters with the cup bowl (body) and the two steam lines, traced from Amir's logo.
BODY = [(43, "M285 399H360L402 466L360 540H285"),
        (46, "M462 404V504Q462 528 483 539L645 624Q655 629 665 624L833 540Q847 533 847 516V399H925L969 466L925 540H847")]
STEAM = [(32, "M570 246C598 268 600 300 584 322C562 352 562 385 600 413"),
         (32, "M651 246C679 268 681 300 665 322C643 352 643 385 681 413")]


def mark(scale: float, cx: float, cy: float) -> str:
    body = "".join(f'<path stroke="{CREAM}" stroke-width="{w}" d="{d}"/>' for w, d in BODY)
    steam = "".join(f'<path stroke="{CORAL}" stroke-width="{w}" stroke-linecap="butt" d="{d}"/>' for w, d in STEAM)
    return (f'<g transform="translate({cx} {cy}) scale({scale}) translate({-CENTRE[0]} {-CENTRE[1]})" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round">{body}{steam}</g>')


def badge(r: float = BOX / 2) -> str:
    """Navy disc with the mark only; used for the header, footer and favicon."""
    c = BOX / 2
    return f'<circle cx="{c}" cy="{c}" r="{r}" fill="{NAVY}"/>' + mark(1.28 * r / c, c, c + 13 * r / c)


def app_icon(r: float, font_css: str) -> str:
    """Navy disc with dotted ring, mark and the MAAD wordmark; used for home-screen icons."""
    c, k = BOX / 2, r / (BOX / 2)
    return (f'<style>{font_css}</style><circle cx="{c}" cy="{c}" r="{r}" fill="{NAVY}"/>'
            f'<circle cx="{c}" cy="{c}" r="{560 * k}" fill="none" stroke="{SAND}" stroke-width="{10 * k}" '
            f'stroke-dasharray="{22 * k} {26 * k}" opacity=".7"/>'
            + mark(0.92 * k, c, c - 107 * k)
            + f'<text x="{c}" y="{c + 278 * k}" text-anchor="middle" font-family="Tektur" font-weight="800" '
              f'font-size="{190 * k}" letter-spacing="{14 * k}" fill="{SAND}">MAAD</text>')


def svg(inner: str, bg: str | None = None) -> str:
    rect = f'<rect width="{BOX}" height="{BOX}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BOX} {BOX}" width="{BOX}" height="{BOX}">{rect}{inner}</svg>'


def write_symbol() -> None:
    icons = SRC / "icons.svg"
    sym = f'<symbol id="logo" viewBox="0 0 {BOX} {BOX}">{badge()}</symbol>'
    text, n = re.subn(r'<symbol id="logo".*?</symbol>', lambda _: sym, icons.read_text(encoding="utf-8"), count=1, flags=re.S)
    if n != 1:
        raise SystemExit("icons.svg: logo symbol not found")
    icons.write_text(text, encoding="utf-8")


async def render(pages: dict[str, tuple[str, int]]) -> dict[str, Image.Image]:
    out: dict[str, Image.Image] = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        try:
            for name, (doc, size) in pages.items():
                pg = await b.new_page(viewport={"width": size, "height": size})
                doc = doc.replace("<svg ", f'<svg style="display:block;width:{size}px;height:{size}px" ', 1)
                await pg.set_content(f'<html><body style="margin:0">{doc}</body></html>')
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(150)
                out[name] = Image.open(io.BytesIO(await pg.screenshot(omit_background=True)))
                await pg.close()
        finally:
            await b.close()
    return out


def manifest() -> str:
    icons = [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
             {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
             {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]
    return json.dumps({"name": "کافه ماد | Cafe Maad", "short_name": "کافه ماد", "lang": "fa", "dir": "rtl",
                       "start_url": "/", "scope": "/", "display": "standalone",
                       "background_color": PAGE, "theme_color": NAVY, "icons": icons}, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    font = base64.b64encode((SRC / "assets" / "fonts" / "tektur.woff2").read_bytes()).decode()
    font_css = f'@font-face{{font-family:"Tektur";src:url(data:font/woff2;base64,{font}) format("woff2");font-weight:400 900}}'
    half = BOX / 2
    pages = {
        "icon-512": (svg(app_icon(half, font_css)), 512),
        "icon-192": (svg(app_icon(half, font_css)), 192),
        # Android crops maskable icons to its own shape (usually a circle) inside the inner 80%.
        "icon-maskable-512": (svg(app_icon(half * 0.84, font_css), NAVY), 512),
        # iOS rounds the square itself, so the disc sits on the site's cream to keep the round look.
        "apple-touch-icon": (svg(app_icon(half * 0.9, font_css), PAGE), 180),
        "favicon-32": (svg(badge()), 32),
    }
    OUT.mkdir(exist_ok=True)
    for name, im in asyncio.run(render(pages)).items():
        im.save(OUT / f"{name}.png", optimize=True)
    (OUT / "favicon.svg").write_text(svg(badge()), encoding="utf-8")
    (ROOT / "manifest.webmanifest").write_text(manifest(), encoding="utf-8")
    write_symbol()
    print("icons:", ", ".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()

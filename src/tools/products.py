"""Product photos for the catalogue (src/catalog.json) -> src/assets/products/<id>.webp (480 x 520).

Coffee products reuse the Cafe Maad pouch photos: the old line of label text is painted out and the product's
own name is printed in its place. Powders get a code-drawn brand scene (pouch or jar, bowl of powder, accents).
Usage: python3 src/tools/products.py [id ...]     (needs Pillow, numpy and Playwright with Chromium)
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

SRC = Path(__file__).resolve().parent.parent
PHOTO = SRC / "assets" / "photo"
FONTS = SRC / "assets" / "fonts"
OUT = SRC / "assets" / "products"
W, H = 480, 520
NAVY, CORAL, SAND, MINT, OLIVE, CREAM = "#172B5E", "#CE685F", "#E8D4A1", "#ECF5DB", "#908364", "#EFE1BD"
FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# base photo, crop (x0, y0, width) in photo pixels, rectangles to paint out, label layout
BASES = {
    "robusta": {"photo": "beans-r100.jpg", "crop": (0, 300, 736), "erase": [], "label": "oval"},
    "arabica": {"photo": "beans-a100.jpg", "crop": (78, 0, 604), "erase": [(296, 194, 430, 227, "dark")], "label": "pouch"},
    "mixR": {"photo": "beans-r70.jpg", "crop": (83, 0, 604), "erase": [(252, 515, 424, 571, "dark"), (500, 345, 548, 425, "dark")], "label": "box"},
    "mixA": {"photo": "beans-a70.jpg", "crop": (13, 0, 604), "erase": [(244, 290, 416, 309, "dark")], "label": "kraft"},
    "crema": {"photo": "pouch.jpg", "crop": (0, 21, 242), "erase": [(58, 108, 190, 177, "light")], "label": "olive"},
}


def blur(a: np.ndarray, r: int) -> np.ndarray:
    """Three box-blur passes along both axes (close to a Gaussian), edges clamped."""
    for axis in (0, 1):
        for _ in range(3):
            pad = [(0, 0)] * a.ndim
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
            a = (np.take(c, range(2 * r + 1, c.shape[axis]), axis=axis) - np.take(c, range(0, c.shape[axis] - 2 * r - 1), axis=axis)) / (2 * r + 1)
    return a


def inpaint(im: Image.Image, rects: list[tuple[int, int, int, int, str]]) -> Image.Image:
    """Remove printed text inside each rectangle: pixels much darker (or lighter, for "light" ink) than the paper
    are masked and refilled from the surrounding paper, so the paper's own gradient and grain stay intact."""
    a = np.asarray(im, dtype=np.float32)
    lum = a @ np.array([.299, .587, .114], dtype=np.float32)
    mask = np.zeros(lum.shape, dtype=bool)
    for x0, y0, x1, y1, ink in rects:
        box = lum[y0:y1, x0:x1]
        paper = float(np.median(box))
        mask[y0:y1, x0:x1] = (box > paper + 22) if ink == "light" else (box < paper - 22)
    for _ in range(2):  # grow the mask so anti-aliased edges go too
        m = mask.copy()
        m[1:] |= mask[:-1]; m[:-1] |= mask[1:]; m[:, 1:] |= mask[:, :-1]; m[:, :-1] |= mask[:, 1:]
        mask = m
    valid = (~mask).astype(np.float32)
    out = a.copy()
    for radius in (3, 6, 12):
        num = blur(out * valid[..., None], radius)
        den = blur(valid, radius)[..., None]
        fill = num / np.maximum(den, 1e-4)
        ok = (den[..., 0] > .15) & mask
        out[ok] = fill[ok]
        valid = np.maximum(valid, ok.astype(np.float32))
        mask &= ~ok
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def data_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def font_css() -> str:
    faces = [("Digi Ghaf", "digighaf.woff2", "700"), ("Shabnam", "shabnam-b.woff2", "700"), ("Tektur", "tektur.woff2", "400 900")]
    return "".join(f'@font-face{{font-family:"{n}";src:url(data:font/woff2;base64,{base64.b64encode((FONTS / f).read_bytes()).decode()}) format("woff2");font-weight:{w}}}' for n, f, w in faces)


def base_key(p: dict) -> str:
    if p["cat"] == "mix":
        return "mixR" if p["id"] in ("mixR100", "mixR80", "mixR70") else "mixA"
    return p["cat"]


def subline(p: dict) -> str:
    en = p["name"]["en"].upper()
    return {"robusta": f"ROBUSTA · {en}", "arabica": f"ARABICA · {en}"}.get(p["cat"], en)


def coffee_html(p: dict, clean: dict[str, str]) -> str:
    key = base_key(p)
    b = BASES[key]
    x0, y0, cw = b["crop"]
    s = W / cw
    fa, en = p["name"]["fa"], subline(p)
    if key == "crema":
        fa = fa.replace("سوپرکرما ", "")
        en = p["name"]["en"].replace("Super Crema ", "").upper()
    labels = {
        "oval": f'''<div class="ov"><i></i><em>SINGLE ORIGIN</em><b>CAFE<br>MAAD</b><span class="fa">{fa}</span><small>{en}</small></div>''',
        "pouch": f'''<div class="ln" style="left:296px;top:192px;width:134px"><span class="fa" style="color:#b9675d;font-size:21px;margin-top:4px">{fa}</span><small style="color:#6f625b;font-size:7.6px">{en}</small></div>''',
        "box": f'''<div class="ln" style="left:250px;top:509px;width:176px"><span class="fa" style="color:#7b5148;font-size:23px">{fa}</span><small style="color:#7b5148;font-size:8.4px">{en} · ROASTED IN TEHRAN</small></div>''',
        "kraft": f'''<div class="ln" style="left:240px;top:293px;width:180px;flex-direction:row;gap:7px;justify-content:center"><span class="fa" style="color:#5b4a42;font-size:19px">{fa}</span></div>''',
        "olive": f'''<div class="ln cr" style="left:56px;top:104px;width:136px"><b>Super Crema</b><span class="fa">{fa}</span><small>{en}</small></div>''',
    }
    return f'''<div class="stage"><div class="photo" style="transform:scale({s:.5f}) translate({-x0}px,{-y0}px)">
<img src="{clean[key]}">{labels[b["label"]]}</div></div>'''


COFFEE_CSS = """
.stage{position:relative;width:480px;height:520px;overflow:hidden}
.photo{position:absolute;left:0;top:0;transform-origin:0 0}
.photo img{display:block}
.fa{font-family:"Digi Ghaf";direction:rtl;line-height:1.05;white-space:nowrap}
.ln{position:absolute;display:flex;flex-direction:column;align-items:center;gap:2px;text-align:center;mix-blend-mode:multiply;filter:blur(.15px)}
.ln small{font-family:Tektur;font-weight:600;letter-spacing:.14em;white-space:nowrap}
.ov{position:absolute;left:359px;top:563px;width:216px;height:254px;border-radius:50%;background:radial-gradient(ellipse at 40% 35%,#1d3168,#162a5a 60%,#122452);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;color:#e9dcb8;box-shadow:0 1px 2px rgba(0,0,0,.25);filter:blur(.2px)}
.ov i{position:absolute;inset:9px;border:2px solid #d9c9a2;border-radius:50%}
.ov em{font:600 10.5px Tektur;letter-spacing:.16em;color:#d9786e;font-style:normal}
.ov b{font:900 31px/0.98 Tektur;letter-spacing:.04em;text-align:center}
.ov .fa{font-size:30px;color:#f2e6c4;margin-top:3px}
.ov small{font:600 8.6px Tektur;letter-spacing:.14em;color:#e9dcb8;opacity:.9}
.cr{mix-blend-mode:normal;color:#ece4c8;gap:3px}
.cr b{font:400 21px/1 Georgia,"DejaVu Serif",serif;letter-spacing:.01em}
.cr .fa{font-size:15px;color:#f3ead0}
.cr small{color:#e2dabb;font-size:6.6px}
"""

# powders: (container, body colour, label ink, powder colour, accent)
POWDER_LOOK = {
    "masala": ("pouch", CORAL, NAVY, "#d8b183", "spice"), "masalaNoSugar": ("pouch", OLIVE, NAVY, "#d1ad86", "spice"),
    "cappuccino": ("pouch", SAND, NAVY, "#c9a07a", "beans"), "whiteChoc": ("pouch", MINT, NAVY, "#f4ecda", "whitechoc"),
    "hotChoc": ("pouch", NAVY, CORAL, "#6b4434", "choc"), "cocoa": ("pouch", OLIVE, NAVY, "#5a3426", "choc"),
    "goldIndia": ("jar", CORAL, NAVY, "#a8682c", "beans"), "goldBrazil": ("jar", OLIVE, NAVY, "#9c5e27", "beans"),
    "classic": ("jar", NAVY, CORAL, "#5b3522", "beans"), "instantEspresso": ("jar", CORAL, NAVY, "#3f2418", "beans"),
    "coffeeMate": ("pouch", CREAM, NAVY, "#f7f1e4", "beans"), "turkish": ("pouch", NAVY, CORAL, "#4a2b1e", "beans"),
    "karakPistachio": ("pouch", MINT, NAVY, "#e3cfa8", "pistachio"), "karakSaffron": ("pouch", SAND, NAVY, "#e5c48f", "saffron"),
}


def shade(hex_color: str, k: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    f = (lambda c: c + (255 - c) * k) if k > 0 else (lambda c: c * (1 + k))
    return "#" + "".join(f"{max(0, min(255, round(f(c)))):02x}" for c in (r, g, b))


def bean(x: float, y: float, rot: float, s: float = 1) -> str:
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})"><ellipse rx="13" ry="9" fill="#4a2a1c"/>'
            f'<ellipse rx="13" ry="9" fill="url(#beanHi)"/><path d="M-11 1 C-4 -3 4 4 11 -1" stroke="#24130c" stroke-width="2" fill="none"/></g>')


def accents(kind: str) -> str:
    if kind == "beans":
        return bean(352, 452, 20) + bean(380, 470, -30, .9) + bean(330, 476, 70, .85) 
    if kind == "spice":
        stick = lambda x, y, r: (f'<g transform="translate({x} {y}) rotate({r})"><rect x="-46" y="-6" width="92" height="12" rx="6" fill="#8a4a2c"/>'
                                 f'<rect x="-46" y="-6" width="92" height="5" rx="3" fill="#a9603a"/><path d="M-46 0h92" stroke="#6d3820" stroke-width="1"/></g>')
        star = "".join(f'<ellipse cx="0" cy="-10" rx="5" ry="11" fill="#7a3f24" transform="rotate({a})"/>' for a in range(0, 360, 45))
        return stick(360, 458, -12) + stick(372, 474, 4) + f'<g transform="translate(410 446)">{star}<circle r="4" fill="#4d2615"/></g>'
    if kind == "choc":
        chunk = lambda x, y, r: f'<g transform="translate({x} {y}) rotate({r})"><rect x="-17" y="-12" width="34" height="24" rx="3" fill="#3b2117"/><rect x="-14" y="-9" width="13" height="8" rx="2" fill="#4e2d20"/><rect x="2" y="-9" width="13" height="8" rx="2" fill="#4e2d20"/></g>'
        return chunk(360, 458, 14) + chunk(394, 478, -20)
    if kind == "whitechoc":
        chunk = lambda x, y, r: f'<g transform="translate({x} {y}) rotate({r})"><rect x="-17" y="-12" width="34" height="24" rx="3" fill="#f6eedb" stroke="#e1d3b1"/><rect x="-14" y="-9" width="13" height="8" rx="2" fill="#efe3c6"/></g>'
        return chunk(360, 458, 14) + chunk(394, 478, -20)
    if kind == "pistachio":
        nut = lambda x, y, r: f'<g transform="translate({x} {y}) rotate({r})"><ellipse rx="12" ry="8" fill="#d9c49a"/><ellipse rx="8" ry="5.5" cx="1" fill="#8fae4f"/></g>'
        return nut(352, 456, 20) + nut(378, 472, -25) + nut(334, 478, 60)
    if kind == "saffron":
        th = "".join(f'<path d="M{x} {y} q6 -10 14 -16" stroke="#c0391b" stroke-width="2.4" fill="none" stroke-linecap="round" transform="rotate({r} {x} {y})"/>'
                     for x, y, r in [(345, 466, 0), (360, 470, 30), (372, 462, -20), (352, 478, 60), (386, 474, 10)])
        return f'<ellipse cx="366" cy="472" rx="34" ry="10" fill="#f3e9d2" opacity=".9"/>{th}'
    return ""


def powder_html(p: dict) -> str:
    kind, body, ink, powder, acc = POWDER_LOOK[p["id"]]
    fa, en = p["name"]["fa"], p["name"]["en"].upper()
    lt, dk = shade(body, .22), shade(body, -.22)
    on_dark = body in (NAVY, OLIVE, CORAL)
    if kind == "pouch":
        vessel = f'''
<path d="M136 96 Q136 82 150 82 H330 Q344 82 344 96 V400 Q344 416 328 418 Q240 427 152 418 Q136 416 136 400 Z" fill="url(#body)"/>
<rect x="136" y="82" width="208" height="28" rx="12" fill="{dk}" opacity=".35"/>
<path d="M144 112 H336" stroke="{dk}" stroke-width="2" opacity=".5"/><path d="M144 117 H336" stroke="#fff" stroke-width="1" opacity=".25"/>
<rect x="150" y="90" width="11" height="318" rx="5.5" fill="#fff" opacity=".18"/>
<rect x="160" y="164" width="160" height="176" rx="16" fill="{CREAM if on_dark else '#fbf6ea'}" opacity=".96"/>'''
        lab_y = 176
    else:
        vessel = f'''
<rect x="166" y="118" width="148" height="30" rx="8" fill="url(#lid)"/>
<path d="M174 150 H306 Q322 152 324 170 V392 Q322 412 302 414 H178 Q158 412 156 392 V170 Q158 152 174 150 Z" fill="url(#glass)"/>
<path d="M170 176 H310 V398 Q306 406 296 406 H184 Q174 406 170 398 Z" fill="{powder}"/><path d="M170 176 H310 V398 Q306 406 296 406 H184 Q174 406 170 398 Z" fill="{shade(powder, -.4)}" filter="url(#granF)"/>
<rect x="164" y="160" width="9" height="236" rx="4.5" fill="#fff" opacity=".35"/>
<rect x="160" y="214" width="160" height="128" fill="{CREAM}"/><rect x="160" y="214" width="160" height="8" fill="{body}"/><rect x="160" y="334" width="160" height="8" fill="{body}"/>'''
        lab_y = 224
    badge = '<g transform="translate(300 150) rotate(12)"><circle r="27" fill="#fbf6ea" stroke="#CE685F" stroke-width="2"/><text y="5" text-anchor="middle" font-family="Digi Ghaf" font-size="12" fill="#CE685F" direction="rtl">بدون شکر</text></g>' if p["id"] == "masalaNoSugar" else ""
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<radialGradient id="bg" cx=".5" cy=".38" r=".75"><stop offset="0" stop-color="#f7f0e2"/><stop offset=".6" stop-color="#ecdfc4"/><stop offset="1" stop-color="#dcc8a4"/></radialGradient>
<linearGradient id="table" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3d1ad"/><stop offset="1" stop-color="#cdb48a"/></linearGradient>
<linearGradient id="body" x1="0" x2="1"><stop offset="0" stop-color="{lt}"/><stop offset=".45" stop-color="{body}"/><stop offset="1" stop-color="{dk}"/></linearGradient>
<linearGradient id="lid" x1="0" x2="1"><stop offset="0" stop-color="{shade(ink, .25)}"/><stop offset=".5" stop-color="{ink}"/><stop offset="1" stop-color="{shade(ink, -.3)}"/></linearGradient>
<linearGradient id="glass" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".5" stop-color="#fff" stop-opacity=".25"/><stop offset="1" stop-color="#fff" stop-opacity=".45"/></linearGradient>
<filter id="granF" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="9"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.25"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="drop" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="6" dy="10" stdDeviation="9" flood-color="#4a3418" flood-opacity=".28"/></filter>
<radialGradient id="beanHi" cx=".35" cy=".3" r=".7"><stop offset="0" stop-color="#9a6040" stop-opacity=".9"/><stop offset="1" stop-color="#4a2a1c" stop-opacity="0"/></radialGradient>
<radialGradient id="heap" cx=".45" cy=".3" r=".8"><stop offset="0" stop-color="{shade(powder, .18)}"/><stop offset="1" stop-color="{shade(powder, -.18)}"/></radialGradient>
<linearGradient id="bowl" x1="0" x2="1"><stop offset="0" stop-color="#2a4386"/><stop offset=".5" stop-color="#172B5E"/><stop offset="1" stop-color="#0f1d42"/></linearGradient>
<filter id="soft"><feGaussianBlur stdDeviation="10"/></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .2  0 0 0 0 .1  0 0 0 .45 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect y="408" width="{W}" height="{H - 408}" fill="url(#table)"/>
<rect y="404" width="{W}" height="10" fill="#f3e6c6" opacity=".6" filter="url(#soft)"/>
<ellipse cx="242" cy="424" rx="112" ry="16" fill="#5b4126" opacity=".28" filter="url(#soft)"/>
<g filter="url(#drop)">{vessel}</g>
<g text-anchor="middle">
<text x="240" y="{lab_y + 18}" font-family="Tektur" font-weight="800" font-size="12" letter-spacing="2.2" fill="{ink}">CAFE MAAD</text>
<path d="M214 {lab_y + 28} H266" stroke="{CORAL}" stroke-width="2"/>
<text x="240" y="{lab_y + 66}" font-family="Digi Ghaf" font-size="{32 if len(fa) < 9 else 25 if len(fa) < 13 else 21}" fill="{ink}" direction="rtl">{fa}</text>
<text x="240" y="{lab_y + 92}" font-family="Tektur" font-weight="600" font-size="{9.5 if len(en) < 18 else 8}" letter-spacing="1.6" fill="{OLIVE}">{en}</text>
<text x="240" y="{lab_y + 140}" font-family="Tektur" font-weight="600" font-size="8" letter-spacing="2" fill="{ink}" opacity=".7">TEHRAN · SATTARKHAN</text>
</g>
{badge}
<ellipse cx="110" cy="482" rx="70" ry="13" fill="#3b2a16" opacity=".32" filter="url(#soft)"/>
<path d="M46 444 Q50 492 110 494 Q170 492 174 444 Z" fill="url(#bowl)"/>
<ellipse cx="110" cy="444" rx="64" ry="11" fill="#22397a"/>
<path d="M54 444 Q74 404 110 402 Q148 404 166 444 Z" fill="url(#heap)"/><path d="M54 444 Q74 404 110 402 Q148 404 166 444 Z" fill="{shade(powder, -.45)}" filter="url(#granF)" opacity=".55"/>
<ellipse cx="110" cy="444" rx="56" ry="7" fill="url(#heap)"/>
{accents(acc)}
</svg>'''


async def main(only: list[str]) -> None:
    OUT.mkdir(exist_ok=True)
    cat = json.loads((SRC / "catalog.json").read_text(encoding="utf-8"))["products"]
    if only:
        cat = [p for p in cat if p["id"] in only]
    clean = {}
    for key, b in BASES.items():
        im = Image.open(PHOTO / b["photo"]).convert("RGB")
        clean[key] = data_uri(inpaint(im, b["erase"]) if b["erase"] else im)
    css = font_css()
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = await br.new_page(viewport={"width": W, "height": H})
        for p in cat:
            if p["cat"] == "powder":
                body, style = powder_html(p), ""
            else:
                body, style = coffee_html(p, clean), COFFEE_CSS
            await pg.set_content(f"<html><head><style>{css}html,body{{margin:0}}{style}</style></head><body>{body}</body></html>")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(80)
            png = await pg.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H})
            im = Image.open(io.BytesIO(png)).convert("RGB")
            out = OUT / f"{p['id']}.webp"
            im.save(out, "WEBP", quality=80, method=6)
            print(p["id"], out.stat().st_size)
        await br.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

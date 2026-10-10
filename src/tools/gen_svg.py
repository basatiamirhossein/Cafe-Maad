"""Generate photo-style top-down (flat-lay) SVG scenes for the Cafe Maad site.

Every scene is lit from the top-left, so highlights sit top-left and shadows fall bottom-right.
Run: python3 gen_svg.py  -> writes svg/<name>.svg and svg/manifest.json
"""
from __future__ import annotations

import json
import math
import pathlib
import random

OUT = pathlib.Path(__file__).parent / "svg"
OUT.mkdir(exist_ok=True)

LIGHT = (-0.55, -0.8)  # unit-ish direction toward the light


class Ids:
    def __init__(self, prefix: str) -> None:
        self.prefix, self.n = prefix, 0

    def __call__(self, name: str) -> str:
        self.n += 1
        return f"{self.prefix}{name}{self.n}"


def f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def svg_doc(w: int, h: int, defs: list[str], body: list[str]) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg>')


def blur_filter(fid: str, sd: float, pad: float = 0.5) -> str:
    return (f'<filter id="{fid}" x="-{pad}" y="-{pad}" width="{1 + 2 * pad}" height="{1 + 2 * pad}">'
            f'<feGaussianBlur stdDeviation="{f(sd)}"/></filter>')


def grain_filter(fid: str, freq: float = 0.9, alpha: float = 0.35, seed: int = 3) -> str:
    return (f'<filter id="{fid}" x="0" y="0" width="1" height="1">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" seed="{seed}"/>'
            f'<feColorMatrix type="saturate" values="0"/>'
            f'<feComponentTransfer><feFuncA type="table" tableValues="0 {alpha}"/></feComponentTransfer>'
            f'<feComposite in2="SourceGraphic" operator="in"/></filter>')


def radial(gid: str, stops: list[tuple[float, str, float]], cx=0.5, cy=0.5, r=0.5, fx=None, fy=None,
           units: str = "objectBoundingBox") -> str:
    fxy = f' fx="{f(fx)}" fy="{f(fy)}"' if fx is not None else ""
    s = "".join(f'<stop offset="{f(o)}" stop-color="{c}" stop-opacity="{f(a)}"/>' for o, c, a in stops)
    return f'<radialGradient id="{gid}" gradientUnits="{units}" cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"{fxy}>{s}</radialGradient>'


def linear(gid: str, stops: list[tuple[float, str, float]], x1=0, y1=0, x2=1, y2=1,
           units: str = "objectBoundingBox") -> str:
    s = "".join(f'<stop offset="{f(o)}" stop-color="{c}" stop-opacity="{f(a)}"/>' for o, c, a in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="{units}" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}">'
            f'{s}</linearGradient>')


def shade(hex_color: str, k: float) -> str:
    """k>0 lightens toward white, k<0 darkens toward black."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if k >= 0:
        r, g, b = (round(c + (255 - c) * k) for c in (r, g, b))
    else:
        r, g, b = (round(c * (1 + k)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------- coffee bean
def bean(ids: Ids, defs: list[str], x: float, y: float, L: float, ang: float, face_up: bool,
         roast: float = 0.0, shadow: bool = True, shadow_list: list[str] | None = None) -> str:
    """One roasted bean, length L, centred at x,y and rotated ang degrees. Returns the bean markup."""
    a = math.radians(-ang)
    lx, ly = LIGHT
    hx = (lx * math.cos(a) - ly * math.sin(a)) * 0.22 * L
    hy = (lx * math.sin(a) + ly * math.cos(a)) * 0.26 * L
    base = shade("#6b3d20", roast)
    gid = ids("bg")
    defs.append(radial(gid, [(0, shade(base, 0.38), 1), (0.42, base, 1), (0.85, shade(base, -0.55), 1), (1, shade(base, -0.72), 1)],
                       cx=hx, cy=hy, r=0.78 * L, units="userSpaceOnUse"))
    p = (f"M0,{f(-0.5 * L)} C{f(0.3 * L)},{f(-0.5 * L)} {f(0.38 * L)},{f(-0.16 * L)} {f(0.36 * L)},{f(0.08 * L)} "
         f"C{f(0.34 * L)},{f(0.38 * L)} {f(0.18 * L)},{f(0.5 * L)} 0,{f(0.5 * L)} "
         f"C{f(-0.2 * L)},{f(0.5 * L)} {f(-0.37 * L)},{f(0.34 * L)} {f(-0.36 * L)},{f(0.04 * L)} "
         f"C{f(-0.35 * L)},{f(-0.3 * L)} {f(-0.25 * L)},{f(-0.5 * L)} 0,{f(-0.5 * L)}Z")
    parts = [f'<path d="{p}" fill="url(#{gid})"/>']
    if face_up:
        c = (f"M{f(0.01 * L)},{f(-0.42 * L)} C{f(0.13 * L)},{f(-0.2 * L)} {f(-0.13 * L)},{f(0.02 * L)} {f(0.0)},{f(0.2 * L)} "
             f"S{f(-0.02 * L)},{f(0.38 * L)} 0,{f(0.44 * L)}")
        parts.append(f'<path d="{c}" fill="none" stroke="#1a0c05" stroke-width="{f(0.075 * L)}" stroke-linecap="round"/>')
        parts.append(f'<path d="{c}" transform="translate({f(-0.045 * L)} 0)" fill="none" stroke="#e9b98c" stroke-opacity=".22" '
                     f'stroke-width="{f(0.025 * L)}" stroke-linecap="round"/>')
    else:
        parts.append(f'<ellipse cx="0" cy="0" rx="{f(0.05 * L)}" ry="{f(0.3 * L)}" fill="#2a1408" opacity=".18"/>')
    parts.append(f'<ellipse cx="{f(hx * 0.9)}" cy="{f(hy * 0.9)}" rx="{f(0.09 * L)}" ry="{f(0.15 * L)}" fill="url(#spec)"/>')
    if shadow and shadow_list is not None:
        shadow_list.append(f'<ellipse cx="{f(x + 0.07 * L)}" cy="{f(y + 0.11 * L)}" rx="{f(0.37 * L)}" ry="{f(0.5 * L)}" '
                           f'transform="rotate({f(ang)} {f(x + 0.07 * L)} {f(y + 0.11 * L)})" fill="#1d0e04" opacity=".55"/>')
    return f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})">{"".join(parts)}</g>'


def spec_def() -> str:
    return radial("spec", [(0, "#ffffff", 0.42), (1, "#ffffff", 0)])


# ---------------------------------------------------------------- latte art
def art_heart(u: float, foam: str, line: str) -> str:
    p = (f"M0,{f(0.56 * u)} C{f(-0.16 * u)},{f(0.38 * u)} {f(-0.64 * u)},{f(0.12 * u)} {f(-0.6 * u)},{f(-0.2 * u)} "
         f"C{f(-0.56 * u)},{f(-0.5 * u)} {f(-0.2 * u)},{f(-0.56 * u)} 0,{f(-0.3 * u)} "
         f"C{f(0.2 * u)},{f(-0.56 * u)} {f(0.56 * u)},{f(-0.5 * u)} {f(0.6 * u)},{f(-0.2 * u)} "
         f"C{f(0.64 * u)},{f(0.12 * u)} {f(0.16 * u)},{f(0.38 * u)} 0,{f(0.56 * u)}Z")
    rings = "".join(
        f'<path d="M{f(-k * u)},{f(-0.12 * u)} C{f(-k * u)},{f(0.12 * u)} {f(-0.12 * u)},{f((0.1 + k * 0.4) * u)} 0,{f((0.12 + k * 0.5) * u)} '
        f'C{f(0.12 * u)},{f((0.1 + k * 0.4) * u)} {f(k * u)},{f(0.12 * u)} {f(k * u)},{f(-0.12 * u)}" fill="none" stroke="{line}" '
        f'stroke-opacity=".28" stroke-width="{f(0.03 * u)}"/>' for k in (0.42, 0.28))
    tail = f'<path d="M0,{f(-0.34 * u)} L0,{f(0.7 * u)}" stroke="{line}" stroke-opacity=".55" stroke-width="{f(0.025 * u)}" stroke-linecap="round"/>'
    return f'<path d="{p}" fill="{foam}"/>{rings}{tail}'


def art_rosetta(u: float, foam: str, line: str, n: int = 9) -> str:
    out = []
    for i in range(n):
        t = i / (n - 1)
        w = (0.62 - 0.42 * t) * u
        y = (0.5 - 0.95 * t) * u
        h = (0.17 - 0.06 * t) * u
        out.append(f'<path d="M{f(-w)},{f(y - h * 0.6)} C{f(-w)},{f(y + h)} {f(w)},{f(y + h)} {f(w)},{f(y - h * 0.6)} '
                   f'C{f(w * 0.72)},{f(y + h * 0.35)} {f(-w * 0.72)},{f(y + h * 0.35)} {f(-w)},{f(y - h * 0.6)}Z" fill="{foam}"/>')
    out.append(f'<ellipse cx="0" cy="{f(-0.56 * u)}" rx="{f(0.13 * u)}" ry="{f(0.1 * u)}" fill="{foam}"/>')
    out.append(f'<path d="M0,{f(-0.62 * u)} L0,{f(0.7 * u)}" stroke="{line}" stroke-opacity=".7" stroke-width="{f(0.03 * u)}" stroke-linecap="round"/>')
    return "".join(out)


def art_tulip(u: float, foam: str, line: str) -> str:
    out = []
    for y, w, h in ((0.36, 0.56, 0.36), (0.02, 0.44, 0.3), (-0.3, 0.32, 0.24)):
        out.append(f'<path d="M{f(-w * u)},{f((y - h * 0.4) * u)} C{f(-w * u)},{f((y + h) * u)} {f(w * u)},{f((y + h) * u)} {f(w * u)},{f((y - h * 0.4) * u)} '
                   f'C{f(w * 0.55 * u)},{f((y - h * 0.05) * u)} {f(-w * 0.55 * u)},{f((y - h * 0.05) * u)} {f(-w * u)},{f((y - h * 0.4) * u)}Z" fill="{foam}"/>')
    out.append(f'<ellipse cx="0" cy="{f(-0.5 * u)}" rx="{f(0.16 * u)}" ry="{f(0.13 * u)}" fill="{foam}"/>')
    out.append(f'<path d="M0,{f(-0.6 * u)} L0,{f(0.72 * u)}" stroke="{line}" stroke-opacity=".6" stroke-width="{f(0.028 * u)}" stroke-linecap="round"/>')
    return "".join(out)


def art_crema(u: float, foam: str, line: str) -> str:
    """Espresso: no milk, just tiger-striped crema swirls."""
    out = []
    rnd = random.Random(11)
    for _ in range(9):
        r = rnd.uniform(0.15, 0.85) * u
        a0 = rnd.uniform(0, 360)
        a1 = a0 + rnd.uniform(40, 120)
        x0, y0 = r * math.cos(math.radians(a0)), r * math.sin(math.radians(a0))
        x1, y1 = r * math.cos(math.radians(a1)), r * math.sin(math.radians(a1))
        out.append(f'<path d="M{f(x0)},{f(y0)} A{f(r)},{f(r)} 0 0 1 {f(x1)},{f(y1)}" fill="none" stroke="{foam}" '
                   f'stroke-opacity="{f(rnd.uniform(0.18, 0.4))}" stroke-width="{f(rnd.uniform(0.03, 0.08) * u)}" stroke-linecap="round"/>')
    return "".join(out)


ARTS = {"heart": art_heart, "rosetta": art_rosetta, "tulip": art_tulip, "crema": art_crema}

CREMAS = {
    # centre, mid, edge
    "light": ("#d2a06c", "#a86a3c", "#5e3219"),
    "mid": ("#c48b55", "#93582d", "#4f2914"),
    "dark": ("#a8703f", "#7a4422", "#3d1d0c"),
    "espresso": ("#c98b4f", "#8d4f25", "#36190a"),
    "black": ("#3a2214", "#24140a", "#120a05"),
}

GLAZES = {
    "white": ("#ffffff", "#f6f2ec", "#ddd5c9", "#fbf9f5", "#cfc5b6"),
    "coral": ("#e48f86", "#ce685f", "#9c4038", "#f3c9c2", "#b8564d"),
    "navy": ("#3d5694", "#1d3570", "#0d1c45", "#e9e2d4", "#c9bea9"),
}


def cup(ids: Ids, defs: list[str], cx: float, cy: float, R: float, art: str = "heart", crema: str = "mid",
        glaze: str = "white", saucer: bool = True, spoon: bool = False, handle_deg: float = 28,
        art_rot: float = 0) -> str:
    g_hi, g_mid, g_lo, wall_hi, wall_lo = GLAZES[glaze]
    out: list[str] = []
    blur_big, blur_mid, blur_small, blur_tiny = ids("f"), ids("f"), ids("f"), ids("f")
    defs += [blur_filter(blur_big, R * 0.12), blur_filter(blur_mid, R * 0.06), blur_filter(blur_small, R * 0.025),
             blur_filter(blur_tiny, R * 0.012, 0.2)]
    sx, sy = 0.07 * R, 0.1 * R
    if saucer:
        SR = 1.5 * R
        sg = ids("sg")
        defs.append(radial(sg, [(0, "#ffffff", 1), (0.58, "#f7f4ef", 1), (0.8, "#e9e3d9", 1), (0.86, "#efebe4", 1),
                                (0.93, "#fbfaf6", 1), (0.985, "#f4f0ea", 1), (1, "#d8d0c3", 1)], cx=0.47, cy=0.45, r=0.53))
        out.append(f'<ellipse cx="{f(cx + sx * 1.3)}" cy="{f(cy + sy * 1.3)}" rx="{f(SR)}" ry="{f(SR)}" fill="#2b1a0e" opacity=".32" filter="url(#{blur_big})"/>')
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(SR)}" fill="url(#{sg})"/>')
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(1.13 * R)}" fill="none" stroke="#8a7560" stroke-opacity=".13" '
                   f'stroke-width="{f(0.035 * R)}" filter="url(#{blur_small})"/>')
        out.append(f'<path d="M{f(cx - SR * 0.93)},{f(cy - SR * 0.2)} A{f(SR * 0.95)},{f(SR * 0.95)} 0 0 1 {f(cx - SR * 0.2)},{f(cy - SR * 0.93)}" '
                   f'fill="none" stroke="#ffffff" stroke-opacity=".9" stroke-width="{f(0.03 * R)}" stroke-linecap="round" filter="url(#{blur_tiny})"/>')
    if spoon:
        out.append(teaspoon(ids, defs, cx - 0.62 * R, cy + 0.98 * R, 1.25 * R, -58))
    # cast shadow of the cup and handle
    hr = math.radians(handle_deg)
    hx, hy = cx + math.cos(hr) * 1.22 * R, cy + math.sin(hr) * 1.22 * R
    out.append(f'<circle cx="{f(cx + sx)}" cy="{f(cy + sy)}" r="{f(1.02 * R)}" fill="#24140a" opacity=".36" filter="url(#{blur_mid})"/>')
    out.append(f'<rect x="{f(hx - 0.36 * R + sx)}" y="{f(hy - 0.17 * R + sy)}" width="{f(0.72 * R)}" height="{f(0.34 * R)}" rx="{f(0.17 * R)}" '
               f'transform="rotate({f(handle_deg)} {f(hx + sx)} {f(hy + sy)})" fill="#24140a" opacity=".3" filter="url(#{blur_small})"/>')
    # handle
    hg = ids("hg")
    defs.append(linear(hg, [(0, g_hi, 1), (0.55, g_mid, 1), (1, g_lo, 1)], 0, 0, 0, 1))
    out.append(f'<g transform="rotate({f(handle_deg)} {f(cx)} {f(cy)})">'
               f'<rect x="{f(cx + 0.86 * R)}" y="{f(cy - 0.17 * R)}" width="{f(0.66 * R)}" height="{f(0.34 * R)}" rx="{f(0.17 * R)}" fill="url(#{hg})"/>'
               f'<rect x="{f(cx + 1.08 * R)}" y="{f(cy - 0.065 * R)}" width="{f(0.3 * R)}" height="{f(0.13 * R)}" rx="{f(0.065 * R)}" '
               f'fill="{"#e6e0d6" if saucer else "#cdbfa8"}"/>'
               f'<rect x="{f(cx + 1.08 * R)}" y="{f(cy - 0.065 * R)}" width="{f(0.3 * R)}" height="{f(0.05 * R)}" rx="{f(0.025 * R)}" fill="#000" opacity=".12"/>'
               f'</g>')
    # body
    bg = ids("cg")
    defs.append(radial(bg, [(0, g_hi, 1), (0.62, g_mid, 1), (1, g_lo, 1)], cx=0.36, cy=0.32, r=0.75))
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="url(#{bg})"/>')
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.985 * R)}" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="{f(0.02 * R)}"/>')
    # inner wall: dark where it faces away from the light (top-left), bright bottom-right
    wg = ids("wg")
    defs.append(linear(wg, [(0, wall_lo, 1), (0.55, shade(wall_hi, -0.03), 1), (1, wall_hi, 1)], 0.15, 0.1, 0.85, 0.9))
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.9 * R)}" fill="url(#{wg})"/>')
    # liquid
    c0, c1, c2 = CREMAS[crema]
    lg = ids("lg")
    defs.append(radial(lg, [(0, c0, 1), (0.62, c1, 1), (0.93, c2, 1), (1, shade(c2, -0.35), 1)], cx=0.5, cy=0.5, r=0.5))
    clip = ids("clip")
    defs.append(f'<clipPath id="{clip}"><circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.8 * R)}"/></clipPath>')
    grain = ids("gr")
    defs.append(grain_filter(grain, 1.4, 0.5, seed=int(cx) % 50))
    u = 0.8 * R * 0.78
    foam_g = ids("fg")
    defs.append(radial(foam_g, [(0, "#fbf5ea", 1), (0.7, "#f3e6cf", 1), (1, "#e3cba6", 1)], cx=0.45, cy=0.4, r=0.6))
    art_svg = ARTS[art](u, f"url(#{foam_g})" if art != "crema" else "#e8b77e", c2)
    out.append(f'<g clip-path="url(#{clip})">'
               f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.8 * R)}" fill="url(#{lg})"/>'
               f'<g transform="translate({f(cx)} {f(cy + 0.04 * R)}) rotate({f(art_rot)})" filter="url(#{blur_tiny})">{art_svg}</g>'
               f'<rect x="{f(cx - R)}" y="{f(cy - R)}" width="{f(2 * R)}" height="{f(2 * R)}" fill="#6b4a33" filter="url(#{grain})" '
               f'style="mix-blend-mode:multiply" opacity=".35"/>'
               f'<circle cx="{f(cx + 0.05 * R)}" cy="{f(cy + 0.07 * R)}" r="{f(0.82 * R)}" fill="none" stroke="#1a0b03" stroke-opacity=".55" '
               f'stroke-width="{f(0.1 * R)}" filter="url(#{blur_small})"/>'
               f'<ellipse cx="{f(cx - 0.3 * R)}" cy="{f(cy - 0.34 * R)}" rx="{f(0.24 * R)}" ry="{f(0.1 * R)}" transform="rotate(-38 {f(cx - 0.3 * R)} {f(cy - 0.34 * R)})" '
               f'fill="#fff" opacity=".13" filter="url(#{blur_small})"/>'
               f'</g>')
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(0.8 * R)}" fill="none" stroke="#000" stroke-opacity=".1" stroke-width="{f(0.012 * R)}"/>')
    # rim highlight arc
    out.append(f'<path d="M{f(cx - 0.93 * R)},{f(cy + 0.05 * R)} A{f(0.95 * R)},{f(0.95 * R)} 0 0 1 {f(cx + 0.1 * R)},{f(cy - 0.94 * R)}" fill="none" '
               f'stroke="#fff" stroke-opacity=".95" stroke-width="{f(0.03 * R)}" stroke-linecap="round" filter="url(#{blur_tiny})"/>')
    return "".join(out)


def teaspoon(ids: Ids, defs: list[str], x: float, y: float, L: float, ang: float) -> str:
    mg = ids("mg")
    defs.append(linear(mg, [(0, "#8e9399", 1), (0.3, "#f4f6f8", 1), (0.5, "#b9bec4", 1), (0.72, "#ffffff", 1), (1, "#7d838a", 1)], 0, 0, 0, 1))
    sb = ids("f")
    defs.append(blur_filter(sb, L * 0.025))
    bowl_rx, bowl_ry = 0.2 * L, 0.13 * L
    handle = (f"M{f(0.18 * L)},{f(-0.035 * L)} L{f(0.95 * L)},{f(-0.05 * L)} Q{f(1.02 * L)},0 {f(0.95 * L)},{f(0.05 * L)} "
              f"L{f(0.18 * L)},{f(0.035 * L)}Z")
    shadow = (f'<g transform="translate({f(0.04 * L)} {f(0.06 * L)})" fill="#1d1208" opacity=".38" filter="url(#{sb})">'
              f'<ellipse cx="0" cy="0" rx="{f(bowl_rx)}" ry="{f(bowl_ry)}"/><path d="{handle}"/></g>')
    metal = (f'<ellipse cx="0" cy="0" rx="{f(bowl_rx)}" ry="{f(bowl_ry)}" fill="url(#{mg})"/>'
             f'<ellipse cx="{f(-0.02 * L)}" cy="{f(0.01 * L)}" rx="{f(bowl_rx * 0.75)}" ry="{f(bowl_ry * 0.62)}" fill="#6f757c" opacity=".35"/>'
             f'<path d="{handle}" fill="url(#{mg})"/>'
             f'<path d="M{f(0.25 * L)},{f(-0.012 * L)} L{f(0.92 * L)},{f(-0.02 * L)}" stroke="#fff" stroke-opacity=".8" stroke-width="{f(0.008 * L)}"/>')
    return f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})">{shadow}{metal}</g>'


# ---------------------------------------------------------------- scenes
def scene_cup(name: str, art: str, crema: str, size: int = 900, **kw) -> tuple[str, str]:
    ids = Ids(name[:2])
    defs = [spec_def()]
    body = [cup(ids, defs, size * 0.47, size * 0.47, size * 0.29, art=art, crema=crema, **kw)]
    return name, svg_doc(size, size, defs, body)


def scene_mug(name: str, glaze: str, art: str, crema: str, size: int = 700) -> tuple[str, str]:
    ids = Ids(name[:2])
    defs = [spec_def()]
    body = [cup(ids, defs, size * 0.44, size * 0.47, size * 0.33, art=art, crema=crema, glaze=glaze, saucer=False, handle_deg=20)]
    return name, svg_doc(size, size, defs, body)


def scene_beans(name: str, size: int = 260, face_up: bool = True, ang: float = 20) -> tuple[str, str]:
    ids = Ids("bn")
    defs = [spec_def()]
    shadows: list[str] = []
    b = bean(ids, defs, size / 2 - 6, size / 2 - 8, size * 0.62, ang, face_up, 0, True, shadows)
    sb = ids("f")
    defs.append(blur_filter(sb, size * 0.03))
    return name, svg_doc(size, size, defs, [f'<g filter="url(#{sb})">{"".join(shadows)}</g>', b])


def scene_background(name: str = "bg", W: int = 1920, H: int = 1280) -> tuple[str, str]:
    rnd = random.Random(42)
    ids = Ids("b")
    defs = [spec_def(), grain_filter("linen", 0.75, 0.5, 9), blur_filter("vig", 120, 0.2)]
    defs.append(linear("table", [(0, "#efe5d7", 1), (0.5, "#e7dbc9", 1), (1, "#d9c9b2", 1)], 0, 0, 1, 1))
    body = [f'<rect width="{W}" height="{H}" fill="url(#table)"/>',
            f'<rect width="{W}" height="{H}" fill="#8b7258" filter="url(#linen)" style="mix-blend-mode:multiply" opacity=".55"/>']
    placed: list[tuple[float, float, float]] = []

    def free(x: float, y: float, L: float, overlap: float) -> bool:
        return all((x - px) ** 2 + (y - py) ** 2 > (overlap * (L + pl) / 2) ** 2 for px, py, pl in placed)

    layers: list[list[tuple]] = [[] for _ in range(4)]
    piles = [(260, 1120, 560, 560), (1720, 110, 420, 300), (1830, 1180, 300, 120)]
    for px, py, pr, n in piles:
        tries = 0
        count = 0
        while count < n and tries < n * 40:
            tries += 1
            r = pr * math.sqrt(rnd.random())
            t = rnd.uniform(0, 2 * math.pi)
            x, y = px + r * math.cos(t), py + r * math.sin(t)
            if not (-60 < x < W + 60 and -60 < y < H + 60):
                continue
            L = rnd.uniform(44, 58)
            depth = 1 - r / pr
            layer = min(3, int(depth * 4 + rnd.random() * 0.8))
            if free(x, y, L, 0.62 if layer == 0 else 0.5):
                placed.append((x, y, L))
                layers[layer].append((x, y, L))
                count += 1
    for _ in range(70):
        x, y, L = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(44, 56)
        if free(x, y, L, 1.4):
            placed.append((x, y, L))
            layers[0].append((x, y, L))
    for li, layer in enumerate(layers):
        shadows: list[str] = []
        beans = [bean(ids, defs, x, y, L, rnd.uniform(0, 360), rnd.random() < 0.6, rnd.uniform(-0.12, 0.1), True, shadows)
                 for x, y, L in layer]
        sid = ids("f")
        defs.append(blur_filter(sid, 4 + li, 0.1))
        body.append(f'<g filter="url(#{sid})">{"".join(shadows)}</g>')
        body.extend(beans)
    body.insert(2, cup(ids, defs, 1560, 820, 150, art="heart", crema="mid", handle_deg=-20))
    body.insert(3, cup(ids, defs, 720, 150, 95, art="crema", crema="espresso", handle_deg=150))
    body.append(f'<rect x="-200" y="-200" width="{W + 400}" height="{H + 400}" fill="none" stroke="#3b2414" stroke-opacity=".35" '
                f'stroke-width="380" filter="url(#vig)"/>')
    return name, svg_doc(W, H, defs, body)


# ---------------------------------------------------------------- products
def drop(ids: Ids, defs: list[str], inner: str, dx: float, dy: float, sd: float, op: float = 0.32) -> str:
    fid = ids("f")
    defs.append(blur_filter(fid, sd))
    return f'<g transform="translate({f(dx)} {f(dy)})" filter="url(#{fid})" opacity="{f(op)}">{inner}</g>'


def scene_v60(name: str = "v60", S: int = 600) -> tuple[str, str]:
    ids = Ids("v6")
    defs = [spec_def()]
    cx, cy, R = S * 0.46, S * 0.48, S * 0.34
    silhouette = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="#1b0f07"/>'
                  f'<rect x="{f(cx + R * 0.8)}" y="{f(cy - R * 0.2)}" width="{f(R * 0.52)}" height="{f(R * 0.4)}" rx="{f(R * 0.2)}" fill="#1b0f07"/>')
    body = [drop(ids, defs, silhouette, R * 0.08, R * 0.12, R * 0.08)]
    cg = ids("g")
    defs.append(radial(cg, [(0, "#eaa098", 1), (0.6, "#ce685f", 1), (1, "#a24a41", 1)], cx=0.35, cy=0.3, r=0.75))
    body.append(f'<rect x="{f(cx + R * 0.8)}" y="{f(cy - R * 0.2)}" width="{f(R * 0.52)}" height="{f(R * 0.4)}" rx="{f(R * 0.2)}" fill="url(#{cg})"/>')
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="url(#{cg})"/>')
    ig = ids("g")
    defs.append(radial(ig, [(0, "#7e3a33", 1), (0.5, "#b4554c", 1), (0.92, "#d97e75", 1), (1, "#c0645b", 1)], cx=0.55, cy=0.58, r=0.55))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.88)}" fill="url(#{ig})"/>')
    for k in range(16):  # spiral ribs
        a = k * 22.5
        pts = []
        for j in range(8):
            rr = R * (0.28 + j * 0.08)
            aa = math.radians(a + j * 5)
            pts.append(f"{f(cx + rr * math.cos(aa))},{f(cy + rr * math.sin(aa))}")
        body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#f0a59c" stroke-opacity=".55" stroke-width="{f(R * 0.025)}" stroke-linecap="round"/>')
    pg = ids("g")
    defs.append(radial(pg, [(0, "#d9cfbf", 1), (0.55, "#f2ece2", 1), (1, "#fbf8f2", 1)], cx=0.55, cy=0.55, r=0.55))
    folds = "".join(f'<path d="M{f(cx)},{f(cy)} L{f(cx + R * 0.74 * math.cos(math.radians(a)))},{f(cy + R * 0.74 * math.sin(math.radians(a)))}" '
                    f'stroke="#c9bda9" stroke-opacity=".5" stroke-width="{f(R * 0.012)}"/>' for a in range(0, 360, 30))
    body.append(f'<circle cx="{f(cx + R * 0.04)}" cy="{f(cy)}" r="{f(R * 0.74)}" fill="url(#{pg})"/>{folds}')
    gg = ids("g")
    defs.append(radial(gg, [(0, "#2a160b", 1), (0.7, "#4a2a16", 1), (1, "#6e4527", 1)], cx=0.5, cy=0.5, r=0.5))
    grain = ids("gr")
    defs.append(grain_filter(grain, 2.2, 0.85, 4))
    body.append(f'<circle cx="{f(cx + R * 0.03)}" cy="{f(cy + R * 0.02)}" r="{f(R * 0.42)}" fill="url(#{gg})"/>')
    body.append(f'<circle cx="{f(cx + R * 0.03)}" cy="{f(cy + R * 0.02)}" r="{f(R * 0.42)}" fill="#c08a5a" filter="url(#{grain})" style="mix-blend-mode:screen" opacity=".55"/>')
    rnd = random.Random(5)
    for _ in range(26):
        rr, aa = R * 0.3 * math.sqrt(rnd.random()), rnd.uniform(0, 6.28)
        body.append(f'<circle cx="{f(cx + R * 0.03 + rr * math.cos(aa))}" cy="{f(cy + R * 0.02 + rr * math.sin(aa))}" r="{f(rnd.uniform(1.5, 4))}" '
                    f'fill="none" stroke="#d9a873" stroke-opacity=".6" stroke-width="1.2"/>')
    body.append(f'<path d="M{f(cx - R * 0.95)},{f(cy - R * 0.05)} A{f(R * 0.96)},{f(R * 0.96)} 0 0 1 {f(cx - R * 0.05)},{f(cy - R * 0.95)}" fill="none" '
                f'stroke="#fff" stroke-opacity=".7" stroke-width="{f(R * 0.03)}" stroke-linecap="round"/>')
    return name, svg_doc(S, S, defs, body)


def scene_moka(name: str = "moka", S: int = 600) -> tuple[str, str]:
    ids = Ids("mk")
    defs = [spec_def()]
    cx, cy = S * 0.44, S * 0.5
    def octo(r: float, rot: float = 22.5) -> list[tuple[float, float]]:
        return [(cx + r * math.cos(math.radians(rot + 45 * i)), cy + r * math.sin(math.radians(rot + 45 * i))) for i in range(8)]
    R = S * 0.3
    outer = octo(R * 1.08)
    sil = (f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in outer)}" fill="#111"/>'
           f'<rect x="{f(cx + R * 0.9)}" y="{f(cy - R * 0.16)}" width="{f(R * 0.95)}" height="{f(R * 0.32)}" rx="{f(R * 0.14)}" fill="#111"/>'
           f'<polygon points="{f(cx - R * 1.0)},{f(cy - R * 0.22)} {f(cx - R * 1.38)},{f(cy)} {f(cx - R * 1.0)},{f(cy + R * 0.22)}" fill="#111"/>')
    body = [drop(ids, defs, sil, R * 0.1, R * 0.14, R * 0.08, 0.35)]
    hg = ids("g")
    defs.append(linear(hg, [(0, "#4a4a4a", 1), (0.4, "#1d1d1d", 1), (1, "#050505", 1)], 0, 0, 0, 1))
    body.append(f'<rect x="{f(cx + R * 0.85)}" y="{f(cy - R * 0.16)}" width="{f(R * 1.0)}" height="{f(R * 0.32)}" rx="{f(R * 0.14)}" fill="url(#{hg})"/>')
    body.append(f'<path d="M{f(cx + R * 1.0)},{f(cy - R * 0.1)} L{f(cx + R * 1.75)},{f(cy - R * 0.1)}" stroke="#fff" stroke-opacity=".25" stroke-width="{f(R * 0.03)}" stroke-linecap="round"/>')
    spout = f'{f(cx - R * 0.95)},{f(cy - R * 0.24)} {f(cx - R * 1.36)},{f(cy)} {f(cx - R * 0.95)},{f(cy + R * 0.24)}'
    sg = ids("g")
    defs.append(linear(sg, [(0, "#f4f5f6", 1), (0.5, "#a7abb0", 1), (1, "#6c7176", 1)], 0, 0, 0, 1))
    body.append(f'<polygon points="{spout}" fill="url(#{sg})"/>')
    for ring, k in ((octo(R * 1.08), 1.0), (octo(R * 0.92), 0.92)):
        for i in range(8):
            (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % 8]
            mid = math.atan2((y0 + y1) / 2 - cy, (x0 + x1) / 2 - cx)
            lit = 0.5 + 0.5 * (-math.cos(mid) * 0.55 - math.sin(mid) * 0.8)
            v = int(105 + 140 * lit * k)
            body.append(f'<polygon points="{f(cx)},{f(cy)} {f(x0)},{f(y0)} {f(x1)},{f(y1)}" fill="rgb({v},{v + 3},{v + 6})"/>')
    body.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in octo(R * 0.92))}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>')
    lg = ids("g")
    defs.append(radial(lg, [(0, "#e9ebee", 1), (0.7, "#b8bcc1", 1), (1, "#8e9398", 1)], cx=0.38, cy=0.34, r=0.7))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.62)}" fill="url(#{lg})"/>')
    for i in range(36):
        a = math.radians(i * 10)
        body.append(f'<line x1="{f(cx + R * 0.2 * math.cos(a))}" y1="{f(cy + R * 0.2 * math.sin(a))}" x2="{f(cx + R * 0.6 * math.cos(a))}" '
                    f'y2="{f(cy + R * 0.6 * math.sin(a))}" stroke="#fff" stroke-opacity=".12" stroke-width="1"/>')
    kg = ids("g")
    defs.append(radial(kg, [(0, "#5a5a5a", 1), (0.5, "#1e1e1e", 1), (1, "#000", 1)], cx=0.35, cy=0.3, r=0.7))
    body.append(drop(ids, defs, f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.2)}" fill="#000"/>', R * 0.05, R * 0.07, R * 0.04, 0.45))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.2)}" fill="url(#{kg})"/>')
    body.append(f'<ellipse cx="{f(cx - R * 0.06)}" cy="{f(cy - R * 0.07)}" rx="{f(R * 0.06)}" ry="{f(R * 0.035)}" fill="#fff" opacity=".45"/>')
    return name, svg_doc(S, S, defs, body)


def scene_press(name: str = "press", S: int = 600) -> tuple[str, str]:
    ids = Ids("fp")
    defs = [spec_def()]
    cx, cy, R = S * 0.45, S * 0.5, S * 0.3
    sil = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 1.06)}" fill="#111"/>'
           f'<path d="M{f(cx + R * 0.9)},{f(cy - R * 0.45)} C{f(cx + R * 1.75)},{f(cy - R * 0.5)} {f(cx + R * 1.75)},{f(cy + R * 0.5)} {f(cx + R * 0.9)},{f(cy + R * 0.45)}" '
           f'stroke="#111" stroke-width="{f(R * 0.2)}" fill="none"/>')
    body = [drop(ids, defs, sil, R * 0.1, R * 0.14, R * 0.09, 0.33)]
    hg = ids("g")
    defs.append(linear(hg, [(0, "#3b3b3b", 1), (1, "#0a0a0a", 1)], 0, 0, 1, 1))
    body.append(f'<path d="M{f(cx + R * 0.9)},{f(cy - R * 0.45)} C{f(cx + R * 1.75)},{f(cy - R * 0.5)} {f(cx + R * 1.75)},{f(cy + R * 0.5)} {f(cx + R * 0.9)},{f(cy + R * 0.45)}" '
                f'stroke="url(#{hg})" stroke-width="{f(R * 0.2)}" fill="none" stroke-linecap="round"/>')
    cg = ids("g")
    defs.append(radial(cg, [(0, "#2a160b", 1), (0.8, "#1a0c05", 1), (1, "#5a3a22", 1)], cx=0.5, cy=0.5, r=0.5))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 1.06)}" fill="url(#{cg})"/>')
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 1.04)}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="{f(R * 0.03)}"/>')
    mg = ids("g")
    defs.append(linear(mg, [(0, "#ffffff", 1), (0.35, "#c3c7cc", 1), (0.6, "#8f949a", 1), (1, "#dfe2e5", 1)], 0, 0, 1, 1))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 1.08)}" fill="none" stroke="url(#{mg})" stroke-width="{f(R * 0.07)}"/>')
    lg = ids("g")
    defs.append(radial(lg, [(0, "#f2f3f5", 1), (0.75, "#b3b8be", 1), (1, "#7f858b", 1)], cx=0.38, cy=0.34, r=0.72))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.86)}" fill="url(#{lg})"/>')
    for i in range(48):
        a = math.radians(i * 7.5)
        body.append(f'<line x1="{f(cx + R * 0.3 * math.cos(a))}" y1="{f(cy + R * 0.3 * math.sin(a))}" x2="{f(cx + R * 0.84 * math.cos(a))}" '
                    f'y2="{f(cy + R * 0.84 * math.sin(a))}" stroke="#fff" stroke-opacity=".1" stroke-width="1"/>')
    body.append(f'<path d="M{f(cx - R * 1.14)},{f(cy - R * 0.14)} L{f(cx - R * 1.32)},{f(cy)} L{f(cx - R * 1.14)},{f(cy + R * 0.14)}Z" fill="url(#{mg})"/>')
    kg = ids("g")
    defs.append(radial(kg, [(0, "#6a6a6a", 1), (0.45, "#1c1c1c", 1), (1, "#000", 1)], cx=0.35, cy=0.3, r=0.7))
    body.append(drop(ids, defs, f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.24)}" fill="#000"/>', R * 0.07, R * 0.1, R * 0.05, 0.5))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.24)}" fill="url(#{kg})"/>')
    body.append(f'<ellipse cx="{f(cx - R * 0.08)}" cy="{f(cy - R * 0.09)}" rx="{f(R * 0.07)}" ry="{f(R * 0.04)}" fill="#fff" opacity=".5"/>')
    return name, svg_doc(S, S, defs, body)


def scene_grinder(name: str = "grinder", S: int = 600) -> tuple[str, str]:
    ids = Ids("gd")
    defs = [spec_def()]
    cx, cy, R = S * 0.42, S * 0.55, S * 0.2
    arm_end = (cx + R * 2.0, cy - R * 1.25)
    sil = (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="#111"/>'
           f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(arm_end[0])}" y2="{f(arm_end[1])}" stroke="#111" stroke-width="{f(R * 0.22)}" stroke-linecap="round"/>'
           f'<circle cx="{f(arm_end[0])}" cy="{f(arm_end[1])}" r="{f(R * 0.36)}" fill="#111"/>')
    body = [drop(ids, defs, sil, R * 0.16, R * 0.22, R * 0.12, 0.35)]
    bg = ids("g")
    defs.append(radial(bg, [(0, "#f5f6f7", 1), (0.65, "#a9aeb4", 1), (1, "#6a7076", 1)], cx=0.38, cy=0.34, r=0.72))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="url(#{bg})"/>')
    for i in range(40):
        a = math.radians(i * 9)
        body.append(f'<line x1="{f(cx + R * 0.94 * math.cos(a))}" y1="{f(cy + R * 0.94 * math.sin(a))}" x2="{f(cx + R * math.cos(a))}" '
                    f'y2="{f(cy + R * math.sin(a))}" stroke="#555" stroke-opacity=".35" stroke-width="2"/>')
    ag = ids("g")
    defs.append(linear(ag, [(0, "#ffffff", 1), (0.5, "#9da2a8", 1), (1, "#5c6267", 1)], 0, 0, 0, 1))
    body.append(f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(arm_end[0])}" y2="{f(arm_end[1])}" stroke="url(#{ag})" stroke-width="{f(R * 0.2)}" stroke-linecap="round"/>')
    wg = ids("g")
    defs.append(radial(wg, [(0, "#c99567", 1), (0.6, "#8c5a32", 1), (1, "#5a351b", 1)], cx=0.36, cy=0.32, r=0.72))
    body.append(f'<circle cx="{f(arm_end[0])}" cy="{f(arm_end[1])}" r="{f(R * 0.36)}" fill="url(#{wg})"/>')
    nut = ids("g")
    defs.append(radial(nut, [(0, "#ffffff", 1), (1, "#7b8187", 1)], cx=0.35, cy=0.3, r=0.75))
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R * 0.24)}" fill="url(#{nut})" stroke="#666" stroke-opacity=".4"/>')
    return name, svg_doc(S, S, defs, body)


def scene_lying(name: str, kind: str, S: int = 600) -> tuple[str, str]:
    """Objects lying on their side, seen from above: flask, tumbler, syrup bottle."""
    ids = Ids(kind[:2])
    defs = [spec_def()]
    cx, cy = S * 0.5, S * 0.5
    body: list[str] = []
    if kind == "flask":
        x0, x1, h = S * 0.16, S * 0.84, S * 0.2
        sil = f'<rect x="{f(x0)}" y="{f(cy - h / 2)}" width="{f(x1 - x0)}" height="{f(h)}" rx="{f(h * 0.3)}" fill="#111"/>'
        body.append(drop(ids, defs, sil, 10, 18, 14, 0.38))
        g = ids("g")
        defs.append(linear(g, [(0, "#5a74b3", 1), (0.25, "#2a4486", 1), (0.7, "#172b5e", 1), (1, "#0a1636", 1)], 0, 0, 0, 1))
        body.append(f'<rect x="{f(x0 + S * 0.14)}" y="{f(cy - h / 2)}" width="{f(x1 - x0 - S * 0.14)}" height="{f(h)}" rx="{f(h * 0.3)}" fill="url(#{g})"/>')
        m = ids("g")
        defs.append(linear(m, [(0, "#ffffff", 1), (0.3, "#c9cdd2", 1), (0.7, "#7c8288", 1), (1, "#4c5156", 1)], 0, 0, 0, 1))
        body.append(f'<rect x="{f(x0)}" y="{f(cy - h * 0.46)}" width="{f(S * 0.17)}" height="{f(h * 0.92)}" rx="{f(h * 0.2)}" fill="url(#{m})"/>')
        for i in range(9):
            x = x0 + S * 0.02 + i * S * 0.014
            body.append(f'<line x1="{f(x)}" y1="{f(cy - h * 0.42)}" x2="{f(x)}" y2="{f(cy + h * 0.42)}" stroke="#000" stroke-opacity=".18" stroke-width="2"/>')
        body.append(f'<text x="{f(S * 0.56)}" y="{f(cy + h * 0.12)}" text-anchor="middle" font-family="Tektur, Arial" font-weight="800" '
                    f'font-size="{f(h * 0.3)}" fill="#e8d4a1" letter-spacing="3">CAFE MAAD</text>')
        body.append(f'<rect x="{f(x0 + S * 0.18)}" y="{f(cy - h * 0.36)}" width="{f(x1 - x0 - S * 0.24)}" height="{f(h * 0.08)}" rx="{f(h * 0.04)}" fill="#fff" opacity=".35"/>')
    elif kind == "tumbler":
        h0, h1 = S * 0.22, S * 0.17
        x0, x1 = S * 0.18, S * 0.82
        pts = f"{f(x0)},{f(cy - h0 / 2)} {f(x1)},{f(cy - h1 / 2)} {f(x1)},{f(cy + h1 / 2)} {f(x0)},{f(cy + h0 / 2)}"
        body.append(drop(ids, defs, f'<polygon points="{pts}" fill="#111"/>', 10, 18, 14, 0.36))
        g = ids("g")
        defs.append(linear(g, [(0, "#fbf3df", 1), (0.3, "#efe1bd", 1), (0.75, "#d9c294", 1), (1, "#a8916a", 1)], 0, 0, 0, 1))
        body.append(f'<polygon points="{pts}" fill="url(#{g})"/>')
        band = ids("g")
        defs.append(linear(band, [(0, "#e6a99f", 1), (0.5, "#ce685f", 1), (1, "#8f3b33", 1)], 0, 0, 0, 1))
        body.append(f'<rect x="{f(S * 0.46)}" y="{f(cy - h0 * 0.47)}" width="{f(S * 0.12)}" height="{f(h0 * 0.94)}" fill="url(#{band})"/>')
        lid = ids("g")
        defs.append(linear(lid, [(0, "#3c568f", 1), (0.5, "#172b5e", 1), (1, "#0b1838", 1)], 0, 0, 0, 1))
        body.append(f'<rect x="{f(x0 - S * 0.06)}" y="{f(cy - h0 * 0.55)}" width="{f(S * 0.08)}" height="{f(h0 * 1.1)}" rx="{f(S * 0.02)}" fill="url(#{lid})"/>')
        body.append(f'<text x="{f(S * 0.7)}" y="{f(cy + h1 * 0.14)}" text-anchor="middle" font-family="Tektur, Arial" font-weight="800" '
                    f'font-size="{f(h1 * 0.3)}" fill="#172b5e" letter-spacing="2">MAAD</text>')
        body.append(f'<path d="M{f(x0 + 6)},{f(cy - h0 * 0.36)} L{f(x1 - 6)},{f(cy - h1 * 0.33)}" stroke="#fff" stroke-opacity=".7" stroke-width="5" stroke-linecap="round"/>')
    elif kind == "syrup":
        h = S * 0.2
        x0, x1 = S * 0.12, S * 0.88
        shape = (f"M{f(x0 + S * 0.2)},{f(cy - h / 2)} L{f(x1 - S * 0.05)},{f(cy - h / 2)} Q{f(x1)},{f(cy - h / 2)} {f(x1)},{f(cy - h * 0.35)} "
                 f"L{f(x1)},{f(cy + h * 0.35)} Q{f(x1)},{f(cy + h / 2)} {f(x1 - S * 0.05)},{f(cy + h / 2)} L{f(x0 + S * 0.2)},{f(cy + h / 2)} "
                 f"C{f(x0 + S * 0.12)},{f(cy + h / 2)} {f(x0 + S * 0.12)},{f(cy + h * 0.16)} {f(x0 + S * 0.06)},{f(cy + h * 0.16)} "
                 f"L{f(x0 + S * 0.06)},{f(cy - h * 0.16)} C{f(x0 + S * 0.12)},{f(cy - h * 0.16)} {f(x0 + S * 0.12)},{f(cy - h / 2)} {f(x0 + S * 0.2)},{f(cy - h / 2)}Z")
        body.append(drop(ids, defs, f'<path d="{shape}" fill="#111"/>', 10, 18, 14, 0.34))
        g = ids("g")
        defs.append(linear(g, [(0, "#e7a35e", 1), (0.35, "#b5641f", 1), (0.8, "#7a3a0c", 1), (1, "#4e2207", 1)], 0, 0, 0, 1))
        body.append(f'<path d="{shape}" fill="url(#{g})"/>')
        capg = ids("g")
        defs.append(linear(capg, [(0, "#3a3a3a", 1), (0.5, "#111", 1), (1, "#000", 1)], 0, 0, 0, 1))
        body.append(f'<rect x="{f(x0)}" y="{f(cy - h * 0.2)}" width="{f(S * 0.08)}" height="{f(h * 0.4)}" rx="4" fill="url(#{capg})"/>')
        body.append(f'<rect x="{f(S * 0.42)}" y="{f(cy - h / 2)}" width="{f(S * 0.3)}" height="{f(h)}" fill="#efe1bd"/>')
        body.append(f'<rect x="{f(S * 0.42)}" y="{f(cy - h / 2)}" width="{f(S * 0.3)}" height="{f(h * 0.14)}" fill="#ce685f"/>')
        body.append(f'<text x="{f(S * 0.57)}" y="{f(cy + h * 0.08)}" text-anchor="middle" font-family="Tektur, Arial" font-weight="800" '
                    f'font-size="{f(h * 0.2)}" fill="#172b5e" letter-spacing="2">VANILLA</text>')
        body.append(f'<text x="{f(S * 0.57)}" y="{f(cy + h * 0.3)}" text-anchor="middle" font-family="Tektur, Arial" font-weight="600" '
                    f'font-size="{f(h * 0.11)}" fill="#6b6146" letter-spacing="2">CAFE MAAD SYRUP</text>')
        body.append(f'<path d="M{f(x0 + S * 0.22)},{f(cy - h * 0.33)} L{f(x1 - S * 0.05)},{f(cy - h * 0.33)}" stroke="#fff" stroke-opacity=".55" stroke-width="5" stroke-linecap="round"/>')
    return name, svg_doc(S, S, defs, body)


def scene_giftbox(name: str = "giftbox", S: int = 600) -> tuple[str, str]:
    ids = Ids("gb")
    defs = [spec_def()]
    x0, y0, w = S * 0.18, S * 0.17, S * 0.62
    body = [drop(ids, defs, f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(w)}" rx="10" fill="#111"/>', 14, 22, 16, 0.36)]
    g = ids("g")
    defs.append(linear(g, [(0, "#dcb98a", 1), (0.6, "#c79c69", 1), (1, "#a97c4a", 1)], 0, 0, 1, 1))
    gr = ids("gr")
    defs.append(grain_filter(gr, 0.8, 0.45, 2))
    body.append(f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(w)}" rx="10" fill="url(#{g})"/>')
    body.append(f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(w)}" rx="10" fill="#5a3a1c" filter="url(#{gr})" style="mix-blend-mode:multiply" opacity=".5"/>')
    rg = ids("g")
    defs.append(linear(rg, [(0, "#e48f86", 1), (0.5, "#ce685f", 1), (1, "#a8443b", 1)], 0, 0, 1, 0))
    rgv = ids("g")
    defs.append(linear(rgv, [(0, "#e48f86", 1), (0.5, "#ce685f", 1), (1, "#a8443b", 1)], 0, 0, 0, 1))
    cx, cy = x0 + w / 2, y0 + w / 2
    body.append(f'<rect x="{f(cx - S * 0.035)}" y="{f(y0)}" width="{f(S * 0.07)}" height="{f(w)}" fill="url(#{rg})"/>')
    body.append(f'<rect x="{f(x0)}" y="{f(cy - S * 0.035)}" width="{f(w)}" height="{f(S * 0.07)}" fill="url(#{rgv})"/>')
    loop = ids("g")
    defs.append(radial(loop, [(0, "#efb1a9", 1), (0.6, "#ce685f", 1), (1, "#9c4038", 1)], cx=0.4, cy=0.35, r=0.7))
    bow = "".join(f'<ellipse cx="{f(cx + dx)}" cy="{f(cy + dy)}" rx="{f(S * 0.09)}" ry="{f(S * 0.05)}" transform="rotate({a} {f(cx + dx)} {f(cy + dy)})" fill="url(#{loop})"/>'
                  for dx, dy, a in ((-S * 0.07, -S * 0.05, 35), (S * 0.07, -S * 0.05, -35), (-S * 0.06, S * 0.06, -30), (S * 0.06, S * 0.06, 30)))
    body.append(drop(ids, defs, bow, 6, 9, 6, 0.4))
    body.append(bow)
    body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(S * 0.035)}" fill="#a8443b"/>')
    body.append(f'<circle cx="{f(x0 + w * 0.2)}" cy="{f(y0 + w * 0.8)}" r="{f(S * 0.07)}" fill="#172b5e"/>'
                f'<circle cx="{f(x0 + w * 0.2)}" cy="{f(y0 + w * 0.8)}" r="{f(S * 0.06)}" fill="none" stroke="#e8d4a1" stroke-width="1.5" stroke-dasharray="3 3"/>'
                f'<text x="{f(x0 + w * 0.2)}" y="{f(y0 + w * 0.8 + S * 0.012)}" text-anchor="middle" font-family="Tektur, Arial" font-weight="800" font-size="{f(S * 0.03)}" fill="#e8d4a1">MAAD</text>')
    return name, svg_doc(S, S, defs, body)


def scene_filters(name: str = "filters", S: int = 600) -> tuple[str, str]:
    ids = Ids("pf")
    defs = [spec_def()]
    body = []
    for k in range(3):
        ox, oy = S * (0.12 + k * 0.05), S * (0.2 + k * 0.05)
        shape = (f"M{f(ox)},{f(oy)} L{f(ox + S * 0.6)},{f(oy)} L{f(ox + S * 0.42)},{f(oy + S * 0.4)} "
                 f"Q{f(ox + S * 0.3)},{f(oy + S * 0.47)} {f(ox + S * 0.18)},{f(oy + S * 0.4)}Z")
        body.append(drop(ids, defs, f'<path d="{shape}" fill="#111"/>', 4, 7, 6, 0.22))
        g = ids("g")
        defs.append(linear(g, [(0, "#fffdf8", 1), (1, "#e9dfcc", 1)], 0, 0, 1, 1))
        body.append(f'<path d="{shape}" fill="url(#{g})"/>')
        crimp = "".join(f'<line x1="{f(ox + S * (0.6 - j * 0.0125))}" y1="{f(oy + j * S * 0.024)}" x2="{f(ox + S * (0.6 - j * 0.0125) - 8)}" '
                        f'y2="{f(oy + j * S * 0.024 + 4)}" stroke="#cbbda4" stroke-width="2"/>' for j in range(16))
        body.append(crimp)
    return name, svg_doc(S, S, defs, body)


def scene_choco(name: str = "choco", S: int = 600) -> tuple[str, str]:
    ids = Ids("ch")
    defs = [spec_def()]
    x0, y0, w, h = S * 0.12, S * 0.24, S * 0.74, S * 0.48
    body = [drop(ids, defs, f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" rx="8" fill="#111"/>', 12, 18, 14, 0.36)]
    body.append(f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" rx="8" fill="#2b1409"/>')
    cols, rows = 4, 3
    cw, ch = (w * 0.62) / cols, h / rows
    for i in range(cols):
        for j in range(rows):
            x, y = x0 + i * cw, y0 + j * ch
            g = ids("g")
            defs.append(linear(g, [(0, "#7a4527", 1), (0.5, "#4a2412", 1), (1, "#2a1208", 1)], 0, 0, 1, 1))
            body.append(f'<rect x="{f(x + 5)}" y="{f(y + 5)}" width="{f(cw - 10)}" height="{f(ch - 10)}" rx="4" fill="url(#{g})"/>')
            body.append(f'<rect x="{f(x + 13)}" y="{f(y + 13)}" width="{f(cw - 26)}" height="{f(ch - 26)}" rx="3" fill="#3d1d0d"/>')
    fx = x0 + w * 0.62
    foil = ids("g")
    defs.append(linear(foil, [(0, "#fff7d6", 1), (0.3, "#d9b860", 1), (0.6, "#f4e3a1", 1), (1, "#a7852f", 1)], 0, 0, 1, 1))
    body.append(f'<path d="M{f(fx - 10)},{f(y0)} L{f(fx + 14)},{f(y0 + h * 0.2)} L{f(fx - 6)},{f(y0 + h * 0.45)} L{f(fx + 16)},{f(y0 + h * 0.7)} L{f(fx - 8)},{f(y0 + h)} L{f(fx + 30)},{f(y0 + h)} L{f(fx + 30)},{f(y0)}Z" fill="url(#{foil})"/>')
    wrap = ids("g")
    defs.append(linear(wrap, [(0, "#e48f86", 1), (0.5, "#ce685f", 1), (1, "#a8443b", 1)], 0, 0, 0, 1))
    body.append(f'<rect x="{f(fx + 24)}" y="{f(y0 - 6)}" width="{f(x0 + w - fx - 18)}" height="{f(h + 12)}" rx="6" fill="url(#{wrap})"/>')
    body.append(f'<text x="{f(fx + 24 + (x0 + w - fx - 18) / 2)}" y="{f(y0 + h / 2 + 10)}" text-anchor="middle" font-family="Tektur, Arial" '
                f'font-weight="800" font-size="{f(S * 0.045)}" fill="#efe1bd" transform="rotate(-90 {f(fx + 24 + (x0 + w - fx - 18) / 2)} {f(y0 + h / 2)})" letter-spacing="3">MAAD 70%</text>')
    return name, svg_doc(S, S, defs, body)


def scene_grounds(name: str = "grounds", W: int = 1000, H: int = 420) -> tuple[str, str]:
    ids = Ids("gs")
    defs = [spec_def()]
    rnd = random.Random(3)
    body = []
    for k in range(5):
        cx, cy = W * (0.12 + k * 0.19), H * 0.5
        R = 72
        size = 0.9 + k * 1.3
        sid = ids("f")
        defs.append(blur_filter(sid, 9))
        body.append(f'<ellipse cx="{f(cx + 8)}" cy="{f(cy + 12)}" rx="{f(R)}" ry="{f(R * 0.95)}" fill="#2b1608" opacity=".35" filter="url(#{sid})"/>')
        g = ids("g")
        defs.append(radial(g, [(0, "#4a2814", 1), (0.7, "#5c3519", 1), (1, "#7a4b28", 1)], cx=0.45, cy=0.42, r=0.55))
        body.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(R)}" fill="url(#{g})"/>')
        n = int(1800 / (size ** 1.5))
        for _ in range(n):
            r = R * math.sqrt(rnd.random()) * 1.02
            a = rnd.uniform(0, 6.283)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            s = size * rnd.uniform(0.6, 1.4)
            light = 0.5 + 0.5 * (-(x - cx) / R * 0.5 - (y - cy) / R * 0.7)
            v = rnd.uniform(-0.25, 0.25) + light * 0.3
            col = shade("#6b3d20", max(-0.6, min(0.5, v)))
            body.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(s)}" height="{f(s * rnd.uniform(0.6, 1))}" transform="rotate({rnd.randint(0, 90)} {f(x)} {f(y)})" fill="{col}"/>')
    return name, svg_doc(W, H, defs, body)


def scene_two_beans(name: str = "twobeans", W: int = 800, H: int = 520) -> tuple[str, str]:
    ids = Ids("tb")
    defs = [spec_def()]
    shadows: list[str] = []
    b1 = bean(ids, defs, W * 0.32, H * 0.5, H * 0.62, -18, True, 0.06, True, shadows)
    b2 = bean(ids, defs, W * 0.7, H * 0.5, H * 0.52, 22, True, -0.1, True, shadows)
    sid = ids("f")
    defs.append(blur_filter(sid, 12))
    return name, svg_doc(W, H, defs, [f'<g filter="url(#{sid})">{"".join(shadows)}</g>', b1, b2])


def main() -> None:
    scenes = [
        scene_background(),
        scene_cup("cup-hero", "heart", "mid", spoon=True),
        scene_cup("cup-a70", "heart", "light"),
        scene_cup("cup-r70", "tulip", "dark", art_rot=-12),
        scene_cup("cup-a100", "rosetta", "light", art_rot=8),
        scene_cup("cup-r100", "crema", "espresso"),
        scene_cup("cup-big", "rosetta", "mid", size=1000),
        scene_beans("bean-a", face_up=True, ang=24),
        scene_beans("bean-b", face_up=False, ang=-30),
        scene_beans("bean-c", face_up=True, ang=-70),
        scene_v60(), scene_moka(), scene_press(), scene_grinder(),
        scene_mug("mug-coral", "coral", "crema", "black"),
        scene_mug("mug-navy", "navy", "heart", "mid"),
        scene_lying("flask", "flask"), scene_lying("tumbler", "tumbler"),
        scene_giftbox(), scene_lying("syrup", "syrup"), scene_filters(), scene_choco(),
        scene_grounds(), scene_two_beans(),
    ]
    manifest = {}
    for name, svg in scenes:
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        manifest[name] = len(svg)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()

"""Brand cover art for Maad blog articles (inline SVG, fixed brand palette)."""

ICONS: dict[str, str] = {
    "cup": '<path d="M-70 -30h120v40a60 60 0 0 1-60 60h0a60 60 0 0 1-60-60z"/><path d="M50 -10h18a22 22 0 0 1 0 44h-24"/><path d="M-100 82h180"/>'
           '<path d="M-40 -60c-10-16 10-24 0-40M-10 -60c-10-16 10-24 0-40M20 -60c-10-16 10-24 0-40"/>',
    "machine": '<rect x="-90" y="-90" width="180" height="60" rx="10"/><rect x="-90" y="-30" width="180" height="120" rx="6"/>'
               '<path d="M-40 -30v20h80v-20"/><path d="M-50 -10h100"/><path d="M-20 -10v14h40v-14"/>'
               '<rect x="-24" y="40" width="48" height="36" rx="4"/><path d="M-6 6v24M6 6v24"/><circle cx="60" cy="-60" r="14"/><path d="M60 -60l7-7"/>',
    "drop": '<path d="M0 -100C30 -55 60 -20 60 20a60 60 0 0 1-120 0c0-40 30-75 60-120z"/><path d="M-30 30a32 32 0 0 0 30 28"/>'
            '<path d="M-110 90h220" stroke-dasharray="6 10"/>',
    "pitcher": '<path d="M-55 -70h100l-12 140h-76z"/><path d="M45 -70l35-18"/><path d="M-55 -40c-40 0-40 70 0 70"/>'
               '<path d="M-20 0c10 20 30 20 40 0M-25 25c15 22 35 22 50 0"/>',
    "cherry": '<circle cx="-30" cy="30" r="44"/><circle cx="45" cy="45" r="38"/><path d="M-30 -14C-20 -60 10 -90 40 -100M45 7C40 -40 40 -80 40 -100"/>'
              '<path d="M40 -100c30 0 55 15 60 40-30 5-55-10-60-40z"/>',
    "grinder": '<path d="M-50 -90h100l-20 60h-60z"/><rect x="-55" y="-30" width="110" height="90" rx="8"/><rect x="-40" y="60" width="80" height="34" rx="4"/>'
               '<circle cx="0" cy="15" r="22"/><path d="M0 -7v44M-22 15h44"/>',
    "gauge": '<path d="M-90 40a90 90 0 0 1 180 0"/><path d="M-70 40a70 70 0 0 1 140 0" stroke-dasharray="3 12"/><path d="M0 40l46-56"/><circle cx="0" cy="40" r="10"/>'
             '<path d="M-110 80h220"/>',
    "leaf": '<path d="M-80 80C-80 -20 0 -90 90 -90c0 100-70 170-170 170z"/><path d="M-80 80L60 -60"/><path d="M-30 30l-10-40M10 -10l-6-40M10 -10l40 6M-30 30l40 4"/>',
    "ice": '<path d="M-60 -90h120l-14 180h-92z"/><rect x="-35" y="-30" width="34" height="34" rx="6" transform="rotate(-12 -18 -13)"/>'
           '<rect x="5" y="0" width="30" height="30" rx="6" transform="rotate(14 20 15)"/><path d="M30 -90l20-40"/><path d="M-58 -60h116"/>',
    "heart": '<path d="M0 70C-80 20-100 -20-80 -55c20-30 60-30 80 5 20-35 60-35 80-5 20 35 0 75-80 125z"/><path d="M-90 10h50l15-30 25 60 15-30h75"/>',
    "kettle": '<path d="M-70 -20h110l10 100h-130z"/><path d="M-30 -20c0-30 40-30 40 0"/><path d="M40 0c40 0 50-30 80-80"/><path d="M-70 10c-30 0-30 40 0 40"/>'
              '<path d="M118 -78c4 30 0 60-6 90" stroke-dasharray="4 9"/>',
    "wrench": '<path d="M-80 80L20 -20"/><path d="M20 -20a40 40 0 1 0 30-60l-20 22 4 22 22 4 22-20a40 40 0 0 1-58 32z"/><circle cx="-60" cy="60" r="6"/>',
    "bean": '<ellipse cx="0" cy="0" rx="70" ry="95" transform="rotate(-25)"/><path d="M-15 -85C25 -40-35 30 15 85" transform="rotate(-25)"/>',
    "chart": '<path d="M-100 80h200M-100 80v-170"/><path d="M-90 50l45-30 35 15 40-70 45 -25" /><circle cx="75" cy="-60" r="7"/><path d="M-60 80v-10M-20 80v-10M20 80v-10M60 80v-10"/>',
    "spoon": '<ellipse cx="0" cy="-50" rx="34" ry="46"/><path d="M0 -4v110"/><path d="M-80 -110c30 10 50 10 80 0s50-10 80 0" stroke-dasharray="5 9"/>',
    "trophy": '<path d="M-50 -90h100v40a50 50 0 0 1-100 0z"/><path d="M-50 -75h-30c0 40 20 50 34 50M50 -75h30c0 40-20 50-34 50"/><path d="M0 0v40M-36 40h72v26h-72z"/><path d="M-50 90h100"/>',
    "spark": '<path d="M0 -100l18 70 70 18-70 18-18 70-18-70-70-18 70-18z"/><path d="M70 -80l6 20 20 6-20 6-6 20-6-20-20-6 20-6z"/><circle cx="-70" cy="60" r="8"/>',
}

# (background from, background to, icon ink, accent, numeral)
PALETTES = {
    "trends": ("#f2b8a8", "#ce685f", "#172b5e", "#fbf6ee", "#fbf6ee"),
    "home":   ("#24407f", "#172b5e", "#e8d4a1", "#ce685f", "#fbf6ee"),
    "craft":  ("#f3e6c4", "#e8d4a1", "#172b5e", "#ce685f", "#ce685f"),
    "origin": ("#ecf5db", "#cfe0b4", "#172b5e", "#908364", "#908364"),
    "pro":    ("#1d3570", "#0f1f4a", "#ce685f", "#e8d4a1", "#e8d4a1"),
    "gear":   ("#fbf1dc", "#efe1bd", "#ce685f", "#172b5e", "#172b5e"),
    "life":   ("#f8ddd3", "#eaa79c", "#172b5e", "#fbf6ee", "#fbf6ee"),
}

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def cover_svg(art_id: str, cat: str, icon: str, size: str = "wide", uid: str = "") -> str:
    c0, c1, ink, accent, numeral = PALETTES.get(cat, PALETTES["craft"])
    w, h = (1200, 560) if size == "wide" else (600, 420)
    gid = f"g{art_id}{size}{uid}"
    num = str(int(art_id)).translate(FA_DIGITS)
    icon_svg = ICONS.get(icon, ICONS["cup"])
    scale = 1.5 if size == "wide" else 1.1
    cx, cy = (w * 0.30, h * 0.53)
    disc = h * 0.36
    dots = "".join(
        f'<circle cx="{w*0.74 - 77 + k*22:.0f}" cy="{h*0.74:.0f}" r="{3 + k*0.9:.1f}" fill="{ink}" fill-opacity=".55"/>'
        for k in range(8)
    )
    return (
        f'<svg class="cover-art" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient></defs>'
        f'<rect width="{w}" height="{h}" fill="url(#{gid})"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{disc:.0f}" fill="{accent}" fill-opacity=".22"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{disc*1.32:.0f}" fill="none" stroke="{accent}" stroke-opacity=".35" stroke-width="2" stroke-dasharray="2 10"/>'
        f'<text x="{w*0.74:.0f}" y="{h*0.50:.0f}" text-anchor="middle" font-family="Digi Ghaf, Shabnam, Tahoma, sans-serif" font-weight="700" font-size="{h*0.30:.0f}" fill="{numeral}">{num}</text>'
        f'<text x="{w*0.74:.0f}" y="{h*0.62:.0f}" text-anchor="middle" font-family="Tektur, sans-serif" font-size="{h*0.045:.0f}" letter-spacing="4" fill="{ink}" fill-opacity=".7">CAFE MAAD · JOURNAL</text>'
        f'{dots}'
        f'<g transform="translate({cx:.0f} {cy:.0f}) scale({scale})" fill="none" stroke="{ink}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">{icon_svg}</g>'
        f'</svg>'
    )


def bean_field() -> str:
    """Scattered coffee beans behind the page, echoing the homepage background."""
    import random
    rnd = random.Random(7)
    beans = []
    for _ in range(22):
        x, y = rnd.choice([rnd.uniform(0, 7), rnd.uniform(93, 100)]), rnd.uniform(2, 98)
        r, s = rnd.uniform(0, 360), rnd.uniform(0.7, 1.3)
        beans.append(f'<use href="#mb" transform="translate({x*14.4:.0f} {y*9:.0f}) rotate({r:.0f}) scale({s:.2f})"/>')
    return (
        '<svg class="beans" viewBox="0 0 1440 900" preserveAspectRatio="none" aria-hidden="true"><defs>'
        '<radialGradient id="mbg" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#9a6440"/><stop offset=".6" stop-color="#5e3a24"/><stop offset="1" stop-color="#3a2416"/></radialGradient>'
        '<g id="mb"><ellipse rx="8" ry="11.5" fill="url(#mbg)"/><path d="M-1 -10c3 4-3 6 0 10s-2 6 1 10" stroke="#2a180e" stroke-width="1.4" fill="none"/></g></defs>'
        + "".join(beans) + "</svg>"
    )

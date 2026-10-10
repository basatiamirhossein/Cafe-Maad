"""Assemble the Cafe Maad multi-page site (v5) into one self-contained HTML file.

Usage: python3 src/build.py  ->  index.html (full document, works offline and on GitHub Pages)
       and src/site.html (body-only variant used for the claude.ai preview).
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

H = Path(__file__).parent
ASSETS = H / "assets"
FONTS = ASSETS / "fonts"
BLOG = H / "content" / "blog"
OUT = H.parent / "index.html"
sys.dont_write_bytecode = True
sys.path.insert(0, str(BLOG))
from covers import cover_svg  # noqa: E402  (the journal's cover art)

FACES = [("Shabnam", "shabnam-l.woff2", "300", ""), ("Shabnam", "shabnam.woff2", "400", ""), ("Shabnam", "shabnam-b.woff2", "700", ""),
         ("Digi Ghaf", "digighaf.woff2", "700", ""), ("Molsaq", "molsaq-l.woff2", "300", ""), ("Molsaq", "molsaq-xb.woff2", "800", ""),
         ("Tektur", "tektur.woff2", "400 900", "font-stretch:75% 100%;")]
PHOTO_ALIASES = {"giftbox-photo": "giftbox"}

# Two images per article, placed between sections: (image, caption)
CAP = {
    "portafilter": "پرتافیلتر و اسپرسو؛ قلب هر کافه", "cup-a70": "اسپرسو با کرمای طلایی", "cup-r70": "کرمای غلیظ یک شات قوی",
    "cup-a100": "فنجان عربیکا؛ معطر و روشن", "cup-r100": "اسپرسوی پرکافئین با بدنه‌ی سنگین", "cup-big": "لاته‌آرت روی فوم ابریشمی شیر",
    "cup-hero": "کاپوچینو با نقش قلب", "v60": "دریپر V60، محبوب دم‌آوری دستی", "moka": "موکاپات؛ قهوه‌ی غلیظ خانگی",
    "press": "فرنچ‌پرس و دم‌آوری غوطه‌وری", "grinder": "آسیاب دستی با تیغه‌ی سرامیکی", "grounds": "از آسیاب خیلی ریز تا خیلی درشت",
    "twobeans": "دانه‌ی عربیکا و روبوستا کنار هم", "beans-r100": "دانه‌های تازه‌برشت کافه ماد", "beans-a100": "عربیکای صددرصد کافه ماد",
    "beans-r70": "ترکیب روبوستای کافه ماد", "pouch": "ترکیب امضای کافه ماد", "jar": "قهوه‌ی فوری، دوباره در صدر", "iced": "قهوه‌ی سرد، همه‌ی فصل‌ها",
    "housebox": "قهوه‌ی بیرون‌بر کافه ماد", "tumbler": "تراول‌ماگ برای قهوه در راه", "mug-coral": "یک ماگ گرم، یک مکث کوتاه", "filters": "فیلتر کاغذی و دم‌آوری تمیز",
}
ART_IMGS = {
    "01": ["iced", "jar"], "02": ["portafilter", "cup-a70"], "03": ["portafilter", "cup-r70"], "04": ["cup-big", "cup-hero"],
    "05": ["twobeans", "beans-r100"], "06": ["portafilter", "cup-r100"], "07": ["grinder", "grounds"], "08": ["portafilter", "cup-a100"],
    "09": ["cup-big", "cup-hero"], "10": ["twobeans", "beans-a100"], "11": ["iced", "tumbler"], "12": ["cup-a100", "mug-coral"],
    "13": ["v60", "press"], "14": ["v60", "moka"], "15": ["portafilter", "grinder"], "16": ["beans-r70", "twobeans"],
    "17": ["beans-r100", "pouch"], "18": ["cup-a70", "grounds"], "19": ["cup-hero", "portafilter"], "20": ["housebox", "cup-big"],
}
JS_IMGS = ["beans-a70", "beans-r70", "beans-a100", "beans-r100", "beans-ground", "v60", "moka", "press", "grinder", "mug-coral", "mug-navy", "flask",
           "tumbler", "giftbox-photo", "housebox", "jar", "syrup", "pouch", "filters", "choco", "bean-a", "bean-b", "bean-c", "portafilter"]

_cache: dict[str, str] = {}


def is_render(name: str) -> bool:
    return (ASSETS / "img" / f"{name}.webp").exists() and name not in PHOTO_ALIASES


def uri(name: str) -> str:
    if name in _cache:
        return _cache[name]
    webp = ASSETS / "img" / f"{name}.webp"
    if name not in PHOTO_ALIASES and webp.exists():
        data = webp.read_bytes()
    else:
        src = ASSETS / "photo" / f"{PHOTO_ALIASES.get(name, name)}.jpg"
        im = Image.open(src).convert("RGB")
        if im.width > 640:
            im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=80, method=6)
        data = buf.getvalue()
    _cache[name] = "data:image/webp;base64," + base64.b64encode(data).decode()
    return _cache[name]


def figure(name: str) -> str:
    kind = "frame-img frame-img--render" if is_render(name) else "frame-img"
    return (f'<figure class="shot"><div class="{kind}"><img data-img="{name}" alt="{CAP[name]}" width="900" height="506" loading="lazy" decoding="async">'
            f'<span class="badge-brand">CAFE MAAD</span></div><figcaption>{CAP[name]}</figcaption></figure>')


def with_images(aid: str, body: str) -> str:
    starts = [m.start() for m in re.finditer(r"<h2\b", body)]
    picks = ART_IMGS.get(aid, [])
    if len(starts) < 3 or len(picks) < 2:
        return body
    spots = [starts[2], starts[min(len(starts) - 2, 5)]]
    if spots[1] <= spots[0]:
        spots = spots[:1]
    for pos, name in sorted(zip(spots, picks), reverse=True):
        body = body[:pos] + figure(name) + body[pos:]
    return body


def articles() -> list[dict]:
    topics = json.loads((BLOG / "topics.json").read_text(encoding="utf-8"))
    out = []
    for tp in topics:
        mp, bp = BLOG / "articles" / f"{tp['id']}.json", BLOG / "articles" / f"{tp['id']}.html"
        if not (mp.exists() and bp.exists()):
            continue
        meta = json.loads(mp.read_text(encoding="utf-8"))
        body = bp.read_text(encoding="utf-8").replace("نکته‌ی باریستای ماد", "نکته‌ی باریستای کافه ماد")
        out.append({
            "id": tp["id"], "cat": tp["cat"], "title": meta["title"], "dek": meta.get("dek", ""), "kicker": meta.get("kicker", ""),
            "readMinutes": meta.get("readMinutes", 10), "takeaways": meta.get("keyTakeaways", []), "sources": meta.get("sources", []),
            "body": with_images(tp["id"], body),
            "cover": cover_svg(tp["id"], tp["cat"], tp["icon"], "card", "c"), "coverWide": cover_svg(tp["id"], tp["cat"], tp["icon"], "wide", "w"),
        })
    return out


def build() -> None:
    faces = "\n".join(
        f'@font-face{{font-family:"{a}";src:url(data:font/woff2;base64,{base64.b64encode((FONTS / f).read_bytes()).decode()}) format("woff2");font-weight:{w};{x}font-display:swap}}'
        for a, f, w, x in FACES)
    arts = articles()
    used = sorted(set(JS_IMGS) | {n for v in ART_IMGS.values() for n in v})
    art_json = json.dumps(arts, ensure_ascii=False).replace("</", "<\\/")
    app = (H / "app.js").read_text(encoding="utf-8")
    app = app.replace("/*I18N*/", (H / "i18n.js").read_text(encoding="utf-8"), 1)
    app = app.replace("/*ARTICLES*/[]", art_json, 1)
    app = app.replace("/*IMGMAP*/", ",".join(f'"{n}":"{uri(n)}"' for n in used), 1)
    body = re.sub(r"\{\{IMG:([\w-]+)\}\}", lambda m: uri(m.group(1)), (H / "body.html").read_text(encoding="utf-8"))
    css = (H / "base.css").read_text(encoding="utf-8").replace("{{IMG:bg}}", uri("bg")) + "\n" + (H / "pages.css").read_text(encoding="utf-8")
    css += "\n.btn--disabled { opacity: .5; pointer-events: none; }\n"
    page = (f"<title>کافه ماد | Cafe Maad</title>\n<style>\n{faces}\n{css}</style>\n"
            f"{(H / 'icons.svg').read_text(encoding='utf-8')}\n{body}\n<script>\n{app}\n</script>\n")
    (H / "site.html").write_text(page, encoding="utf-8")
    t_end = page.index("</style>") + len("</style>")
    head = ('<!doctype html>\n<html lang="fa" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="description" content="Cafe Maad: fresh roasted coffee on Sattarkhan, Tehran.">\n<meta name="theme-color" content="#172b5e">\n')
    OUT.write_text(head + page[:t_end] + "\n</head>\n<body>\n" + page[t_end:] + "</body>\n</html>\n", encoding="utf-8")
    print(f"site.html {len(page) / 1e6:.2f} MB, {len(arts)} articles, {len(used)} images")


if __name__ == "__main__":
    build()

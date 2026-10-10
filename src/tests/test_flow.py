"""Functional checks of the site logic (the 'backend' of a static site): builder pricing, cart, persistence,
checkout / wholesale / contact validation and the WhatsApp messages they produce, routing, language switching."""
import asyncio
import pathlib
import urllib.parse

from playwright.async_api import async_playwright

H = pathlib.Path(__file__).parent
URL = (H.parent.parent / "index.html").as_uri()
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))


async def main() -> None:
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        pg = await ctx.new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.add_init_script("window.__opened = []; window.open = (u) => { window.__opened.push(u); return {}; };")
        await pg.goto(URL + "#fa"); await pg.wait_for_timeout(400)
        await pg.evaluate("localStorage.clear()")
        await pg.goto(URL + "#/"); await pg.wait_for_timeout(400)

        # legacy language hash + routing
        await pg.goto(URL + "#en"); await pg.wait_for_timeout(300)
        check(await pg.evaluate("document.documentElement.lang") == "en" and await pg.evaluate("location.hash") == "#/", "legacy #en sets English and routes home")
        for lang, d in [("fa", "rtl"), ("ar", "rtl"), ("tr", "ltr"), ("en", "ltr")]:
            await pg.click(f'[data-lang="{lang}"]')
            check(await pg.evaluate("document.documentElement.dir") == d, f"{lang} sets dir={d}")
        await pg.click('[data-lang="fa"]')
        await pg.evaluate("location.hash='#/nope'"); await pg.wait_for_timeout(150)
        check(await pg.evaluate("!document.querySelector('[data-page=home]').hidden"), "unknown route falls back to home")
        await pg.evaluate("location.hash='#/blog/99'"); await pg.wait_for_timeout(250)
        check(await pg.evaluate("location.hash") == "#/blog", "missing article redirects to blog list")
        for r, page in [("#/products/gear", "products"), ("#/order", "order"), ("#/wholesale", "wholesale"), ("#/blog/05", "article"), ("#/about", "about"), ("#/contact", "contact")]:
            await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(150)
            vis = await pg.evaluate("[...document.querySelectorAll('.page')].filter(p=>!p.hidden).map(p=>p.dataset.page)")
            check(vis == [page], f"route {r} shows only {page}")
        check(await pg.evaluate("document.querySelector('.nav-links [aria-current=page]')?.dataset.navPage") == "contact", "active nav link marked")

        # home blend card -> products builder with that blend
        await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(200)
        await pg.locator('[data-page=home] [data-blend-cards] .card').nth(2).locator(".pick").click(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("location.hash") == "#/products/beans", "blend card opens products/beans")
        sel = await pg.evaluate("document.querySelector('[data-builder=products] [data-g=blend] [aria-checked=true]').textContent")
        check("۱۰۰٪ عربیکا" in sel, f"picked blend preselected ({sel})")

        # builder pricing: 100% arabica 520000 x 1.9 (500 g) = 988000, qty 2
        bld = pg.locator("[data-builder=products]")
        await bld.locator("[data-g=size] .chip").nth(1).click()
        await bld.locator("[data-g=form] .chip").nth(1).click()
        await bld.locator("[data-g=grind] .chip").nth(5).click()
        await bld.locator(".stepper button").nth(1).click()
        price = await bld.locator("[data-g=price]").text_content()
        check(price == "۱٬۹۷۶٬۰۰۰", f"builder price 2 x 500 g arabica = 1,976,000 ({price})")
        check("دمی V60" in await bld.locator("[data-g=grind-v]").text_content(), "summary shows chosen grind")
        await bld.locator("[data-g=form] .chip").nth(0).click()
        check(await bld.locator("[data-g=grind] .chip").first.is_disabled(), "grind chips disabled for whole bean")
        await bld.locator("[data-g=form] .chip").nth(1).click()
        await bld.locator("[data-g=add]").click()
        check(await pg.text_content("#cart-count") == "۲", "cart badge shows 2 after adding qty 2")
        # same config again merges
        await bld.locator("[data-g=add]").click()
        cart = await pg.evaluate("JSON.parse(localStorage.getItem('maad-cart-v1'))")
        check(len(cart) == 1 and cart[0]["qty"] == 3, f"same config merges into one line ({cart})")
        # keyboard: arrow keys move radio selection
        await bld.locator("[data-g=blend] [aria-checked=true]").focus()
        await pg.keyboard.press("ArrowLeft"); await pg.wait_for_timeout(120)
        k = await pg.evaluate("document.activeElement.getAttribute('aria-checked')")
        check(k == "true", "arrow key moves and focuses selected chip")

        # item from another category
        await pg.evaluate("location.hash='#/products/mugs'"); await pg.wait_for_timeout(200)
        await pg.locator("#items-cards .card").first.locator(".acts .mini").first.click()
        check(await pg.text_content("#cart-count") == "۴", "item add increments badge")
        # favourite persists
        await pg.locator("#items-cards .card").first.locator(".acts .mini").nth(1).click()
        check(await pg.evaluate("JSON.parse(localStorage.getItem('maad-favs-v1')).includes('i:mugCoral')"), "favourite saved")

        # drawer
        await pg.click("#cart-btn")
        check(await pg.evaluate("!document.getElementById('drawer').hidden"), "drawer opens")
        check(await pg.evaluate("document.activeElement.id") == "drawer-close", "focus moves into drawer")
        await pg.keyboard.press("Escape")
        check(await pg.evaluate("document.getElementById('drawer').hidden"), "Esc closes drawer")

        # persistence across reload
        await pg.reload(); await pg.wait_for_timeout(400)
        check(await pg.text_content("#cart-count") == "۴", "cart survives reload")
        # corrupted storage is ignored
        await pg.evaluate("localStorage.setItem('maad-cart-v1', JSON.stringify([{type:'item',id:'hack',qty:5},{type:'bean',blend:'a70',size:'250',form:'ground',grind:'x',qty:1}, ...JSON.parse(localStorage.getItem('maad-cart-v1'))]))")
        await pg.reload(); await pg.wait_for_timeout(400)
        check(await pg.text_content("#cart-count") == "۴", "invalid stored lines dropped")
        await pg.evaluate("localStorage.setItem('maad-cart-v1','{bad json')"); await pg.reload(); await pg.wait_for_timeout(300)
        check(await pg.text_content("#cart-count") == "۰", "broken storage does not crash")

        # rebuild a cart, then checkout
        await pg.evaluate("location.hash='#/order'"); await pg.wait_for_timeout(300)
        await pg.click("#checkout button[type=submit]")
        errs_shown = await pg.evaluate("[...document.querySelectorAll('#checkout .err')].filter(e=>e.textContent).map(e=>e.dataset.err)")
        check(set(errs_shown) == {"name", "phone", "address", "cart"}, f"empty checkout flags name/phone/address/cart ({errs_shown})")
        o = pg.locator("[data-builder=order]")
        await o.locator("[data-g=add]").click()
        await pg.locator("#quick-list .quick").first.locator("button").click()
        await pg.locator("[data-page=order] [data-cart-list] .stepper button").nth(1).click()
        sub = await pg.evaluate("document.querySelector('[data-page=order] [data-totals] .grand b').textContent")
        check(sub.startswith("۱٬۵۳۰٬۰۰۰"), f"total = 2 x 420,000 + 690,000 = 1,530,000 ({sub})")
        await pg.fill("#co-name", "امیر"); await pg.fill("#co-phone", "۰۹۱۲ ۳۴۵ ۶۷۸۹")
        await pg.click("label:has(input[value=pickup])")
        check(await pg.evaluate("document.getElementById('addr-field').hidden"), "pickup hides address")
        await pg.fill("#co-note", "بدون شکر")
        await pg.click("#checkout button[type=submit]"); await pg.wait_for_timeout(300)
        opened = await pg.evaluate("window.__opened")
        check(len(opened) == 1 and opened[0].startswith("https://wa.me/989336058471?text="), "checkout opens WhatsApp to the cafe number")
        text = urllib.parse.unquote(opened[0].split("text=")[1]) if opened else ""
        check("09123456789" in text and "تحویل در کافه" in text and "دریپر سرامیکی V60" in text and "× ۲" in text and "بدون شکر" in text, "order message has phone, method, items, qty, note")
        check(await pg.evaluate("!document.getElementById('order-done').hidden") and (await pg.text_content("#done-id")).startswith("MAAD-"), "confirmation with order id shown")
        check(await pg.text_content("#cart-count") == "۰", "cart cleared after order")
        await pg.click("#done-new")
        check(await pg.evaluate("!document.getElementById('order-main').hidden"), "new order resets view")

        # phone validation
        for raw, ok in [("09123456789", True), ("+989123456789", True), ("9123456789", True), ("0912345", False), ("+905321234567", True), ("abc", False)]:
            await pg.fill("#co-phone", raw); await pg.click("#checkout button[type=submit]")
            has = await pg.evaluate("Boolean(document.querySelector('#checkout [data-err=phone]').textContent)")
            check(has != ok, f"phone '{raw}' valid={ok}")

        # wholesale
        await pg.evaluate("location.hash='#/wholesale'"); await pg.wait_for_timeout(200)
        await pg.fill("#ws-kg", "3"); await pg.click("#wsform button[type=submit]")
        werr = await pg.evaluate("[...document.querySelectorAll('#wsform .err')].filter(e=>e.textContent).map(e=>e.dataset.err)")
        check(set(werr) == {"biz", "name", "phone", "kg", "blends"}, f"wholesale validation ({werr})")
        await pg.fill("#ws-kg", "25")
        check("کافه" in await pg.text_content("#ws-tier-hint") and "۱۵٪" in await pg.text_content("#ws-tier-hint"), "25 kg shows Café tier 15%")
        await pg.fill("#ws-biz", "کافه نمونه"); await pg.fill("#ws-name", "علی"); await pg.fill("#ws-phone", "09121112233")
        await pg.click("[data-ws-blends] label >> nth=0"); await pg.click("[data-ws-blends] label >> nth=3")
        await pg.click("#wsform button[type=submit]"); await pg.wait_for_timeout(200)
        opened = await pg.evaluate("window.__opened")
        wtext = urllib.parse.unquote(opened[-1].split("text=")[1])
        check("کافه نمونه" in wtext and "۲۵" in wtext and "فول کافئین" in wtext, "wholesale message content")
        check(await pg.evaluate("!document.getElementById('ws-ok').hidden"), "wholesale success note shown")

        # contact
        await pg.evaluate("location.hash='#/contact'"); await pg.wait_for_timeout(200)
        await pg.click("#ctform button[type=submit]")
        cerr = await pg.evaluate("[...document.querySelectorAll('#ctform .err')].filter(e=>e.textContent).map(e=>e.dataset.err)")
        check(set(cerr) == {"name", "phone", "message"}, f"contact validation ({cerr})")
        await pg.fill("#ct-name", "Sara"); await pg.fill("#ct-phone", "09350000000"); await pg.fill("#ct-msg", "Hello")
        await pg.click("#ctform button[type=submit]")
        check(len(await pg.evaluate("window.__opened")) == 3, "contact opens WhatsApp")
        check(await pg.evaluate("document.querySelectorAll('[data-faq] details').length") == 5, "FAQ rendered")

        # language switch keeps page and translates forms
        await pg.click('[data-lang="tr"]')
        check(await pg.text_content("#ctf-h") == "Mesaj gönder" and await pg.evaluate("!document.querySelector('[data-page=contact]').hidden"), "switching to Turkish keeps page, translates")
        check(await pg.evaluate("document.querySelector('#ct-subj option').textContent") == "Ürün hakkında soru", "select options translated")
        await pg.evaluate("location.hash='#/blog'"); await pg.wait_for_timeout(200)
        check(await pg.evaluate("document.querySelectorAll('#blog-grid .post').length") == 19, "blog lists 20 articles (1 featured + 19)")
        await pg.locator("#blog-chips .tab").nth(3).click()
        n = await pg.evaluate("document.querySelectorAll('#blog-grid .post').length + document.querySelectorAll('#blog-featured .feat').length")
        check(0 < n < 20, f"category filter narrows list ({n})")
        await pg.evaluate("location.hash='#/blog/13'"); await pg.wait_for_timeout(300)
        check(await pg.evaluate("document.querySelectorAll('#article .prose figure.shot img[src^=data]').length") == 2, "article has 2 brand images")
        check(await pg.evaluate("document.querySelectorAll('#article .toc button').length") >= 6, "article TOC built")
        check("Cafe Maad" in (await pg.evaluate("document.title")), "article title set")
        await ctx.close(); await b.close()
        check(not errs, f"no console errors ({errs[:3]})")

    for ok, label in results:
        print("PASS" if ok else "FAIL", label)
    print(f"{sum(ok for ok, _ in results)}/{len(results)} passed")


asyncio.run(main())

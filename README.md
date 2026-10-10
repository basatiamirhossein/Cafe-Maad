# Cafe Maad · کافه ماد

وب‌سایت فروشگاهی کافه ماد (قهوه ماد، ستارخان، تهران) در چهار زبان: فارسی، English، العربية و Türkçe.

The Cafe Maad coffee store site: fresh-roasted beans with a blend / size / grind builder, brewing gear, mugs and flasks, online and wholesale ordering through WhatsApp, a 20-article Persian coffee journal, and about and contact pages.

## Run it

Open `index.html` in any browser. It is one self-contained file (fonts and images are embedded), so it works offline and on any static host.

To publish it with GitHub Pages, go to **Settings → Pages**, choose **Deploy from a branch**, then pick `main` and `/ (root)`.

## Pages

| Route | Page |
|---|---|
| `#/` | Home |
| `#/products/beans` · `gear` · `mugs` · `more` | Products in four categories, with the bean builder (4 blends × 250 g / 500 g / 1 kg × whole bean or 10 grind levels) |
| `#/order` | Online order: builder, cart and checkout. The order is sent as a WhatsApp message |
| `#/wholesale` | Wholesale tiers and a quote request form |
| `#/blog`, `#/blog/01`–`20` | Coffee journal (articles are in Persian) |
| `#/about`, `#/contact` | About, and contact with FAQ |

The site has no server. The cart is kept in the visitor's browser (`localStorage`). The checkout, wholesale and contact forms open WhatsApp with the message filled in, addressed to 0933 605 8471.

## Edit and rebuild

Sources live in `src/`:

- `body.html`: page markup.
- `base.css` and `pages.css`: styles.
- `i18n.js`: all texts in fa / en / ar / tr.
- `app.js`: catalogue, prices, cart, builder, forms and router.
- `content/blog/`: articles and their cover art.
- `assets/`: images and fonts.

Rebuild `index.html` after any change:

```bash
pip install pillow
python3 src/build.py
```

Prices are samples and live in `app.js` (`BLENDS`, `CATALOG`). Wholesale discount rates live in `i18n.js` (`tiers`).

## Tests

```bash
pip install playwright
python3 src/tests/test_flow.py     # 59 checks: pricing, cart, storage, checkout, wholesale, contact, routing, languages
python3 src/tests/test_layout.py   # 13 pages × 4 languages × 5 screen sizes: overflow, empty texts, JS errors
```

## Before going public

- Prices and wholesale discounts are placeholders.
- Some product photos are rebranded versions of reference images from other brands. Replace them with your own photos.
- Check that the Digi Ghaf font licence allows web embedding. Shabnam and Tektur are open-source (OFL).

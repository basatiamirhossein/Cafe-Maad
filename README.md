# Cafe Maad · کافه ماد

وب‌سایت فروشگاهی کافه ماد (قهوه ماد، ستارخان، تهران) در چهار زبان: فارسی، English، العربية و Türkçe.

The Cafe Maad coffee store site: 38 products in five categories (single-origin Robusta, single-origin Arabica, blends, Super Crema special blends, powders) with a size / grind builder, a custom-blend builder (up to five coffees with percentage shares), online and wholesale ordering through WhatsApp, a 20-article Persian coffee journal, and about and contact pages.

## Run it

Open `index.html` in any browser. It is one self-contained file (fonts and images are embedded), so it works offline and on any static host.

To publish it with GitHub Pages, go to **Settings → Pages**, choose **Deploy from a branch**, then pick `main` and `/ (root)`.

The live site at <https://cafemaad.ir> runs on nginx behind ArvanCloud; see [deploy/README.md](deploy/README.md).

## Pages

| Route | Page |
|---|---|
| `#/` | Home |
| `#/products/robusta` · `arabica` · `mix` · `crema` · `powder` | Products by category, with the builder (250 g / 500 g / 1 kg / wholesale from 5 kg × whole bean or 10 grind levels; powders have no grind) |
| `#/products/custom` | Custom blend: two to five coffees, shares in percent adding up to 100, priced as the weighted average per kg |
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
- `catalog.json`: every product with its price per kg (in thousand toman) and its names and notes in four languages.
- `app.js`: pricing, cart, builders, forms and router.
- `assets/products/`: one photo per product, made by `tools/products.py` (coffee pouches with the product name on the label, drawn brand scenes for powders).
- `content/blog/`: articles and their cover art.
- `assets/`: images and fonts.
- `tools/icons.py`: the logo (header symbol in `icons.svg`), favicon, home-screen icons in `/icons` and `/manifest.webmanifest`. Run it after changing the logo (needs Playwright).

Rebuild `index.html` after any change:

```bash
pip install pillow
python3 src/build.py
```

## Updating prices

The source of truth is Amir's price list (project file `maad-inventory/price-list.md`): prices in thousand toman for 1 kg. Edit `kg` in `src/catalog.json` and rebuild. 250 g and 500 g are priced in proportion to 1 kg, rounded up to the next 1,000 toman; wholesale is charged per kg at the list price, from 5 kg. For a new product, add it to `catalog.json`, run `python3 src/tools/products.py <id>` (needs Pillow, numpy and Playwright) and rebuild. Wholesale discount rates live in `i18n.js` (`tiers`).

## Tests

```bash
pip install playwright
python3 src/tests/test_flow.py     # 76 checks: pricing, custom blend, cart, storage, checkout, wholesale, contact, routing, languages
python3 src/tests/test_layout.py   # 16 pages × 4 languages × 5 screen sizes: overflow, empty texts, JS errors
```

## Before going public

- Wholesale discount rates are placeholders.
- Some product photos are rebranded versions of reference images from other brands. Replace them with your own photos.
- Check that the Digi Ghaf font licence allows web embedding. Shabnam and Tektur are open-source (OFL).

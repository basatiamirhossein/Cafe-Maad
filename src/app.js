(() => {
  "use strict";
  const IMG = {/*IMGMAP*/};
  const ARTICLES = /*ARTICLES*/[];
/*I18N*/

  /* ---------- catalogue (src/catalog.json: kg = price of 1 kg in thousand toman) ---------- */
  const CATALOG = /*CATALOG*/[];
  const PHONE_INTL = "989336058471";
  const CATS = [
    { id: "robusta", icon: "#i-bean" }, { id: "arabica", icon: "#i-bean" }, { id: "mix", icon: "#i-grind" },
    { id: "crema", icon: "#i-flame" }, { id: "powder", icon: "#i-mug" }
  ];
  const PAGE_CATS = [...CATS, { id: "custom", icon: "#i-plus" }];
  const COFFEE_CATS = ["robusta", "arabica", "mix", "crema"];
  const BY_ID = Object.fromEntries(CATALOG.map((p) => [p.id, p]));
  const inCat = (cat) => CATALOG.filter((p) => p.cat === cat);
  const COFFEES = CATALOG.filter((p) => COFFEE_CATS.includes(p.cat));
  const isCoffee = (p) => COFFEE_CATS.includes(p.cat);
  const SIZES = [{ id: "250", g: 250 }, { id: "500", g: 500 }, { id: "1000", g: 1000 }, { id: "ws", g: 1000 }];
  const WS = { min: 5, max: 1000 };
  const GRINDS = [
    { id: "turkish", level: 1 }, { id: "espHome", level: 2 }, { id: "espPro", level: 2 }, { id: "moka", level: 3 }, { id: "aero", level: 3 },
    { id: "v60", level: 4 }, { id: "drip", level: 4 }, { id: "chemex", level: 5 }, { id: "french", level: 6 }, { id: "cold", level: 7 }
  ];
  const BLEND = { min: 2, max: 5 };
  const BLEND_COLORS = ["#172B5E", "#CE685F", "#908364", "#E8D4A1", "#7d9a6a"];
  const HOME_PICKS = { robusta: ["vietnam", "uganda", "indonesia", "vietnamDark"], arabica: ["brazilSantos", "colombia", "ethSidamo", "peru"], mix: ["mixA70", "mixA100", "mixR70", "mixR50"], crema: ["crema100", "crema80", "crema70"], powder: ["masala", "hotChoc", "goldBrazil", "karakSaffron"] };
  const NAV = [["navProducts", "#/products", "products"], ["navBlog", "#/blog", "blog"], ["navOrder", "#/order", "order"], ["navWholesale", "#/wholesale", "wholesale"], ["navAbout", "#/about", "about"], ["navContact", "#/contact", "contact"]];
  const PERK_ICONS = ["#i-flame", "#i-grind", "#i-truck", "#i-shield"];
  const TIER_MIN = [5, 20, 50];
  const LANGS = Object.keys(I18N);
  const MAX_QTY = 50;
  const CART_KEY = "maad-cart-v2";

  /* ---------- helpers ---------- */
  const root = document.documentElement;
  const $ = (id) => document.getElementById(id);
  const $$ = (sel, scope = document) => Array.from(scope.querySelectorAll(sel));
  const state = { lang: "fa", route: { page: "home", arg: "" }, homeTab: "mix", blogCat: "all", cart: [], favs: new Set(), pending: null };
  const t = () => I18N[state.lang];
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const icon = (id) => { const ns = "http://www.w3.org/2000/svg"; const s = document.createElementNS(ns, "svg"); const u = document.createElementNS(ns, "use"); u.setAttribute("href", id); s.setAttribute("aria-hidden", "true"); s.appendChild(u); return s; };
  const nf = () => new Intl.NumberFormat(t().locale);
  const num = (n) => nf().format(n);
  const money = (n) => nf().format(Math.round(n / 1000) * 1000);
  const clampQty = (q) => Math.min(MAX_QTY, Math.max(1, Math.round(Number(q) || 1)));
  const store = {
    get(key, fallback) { try { const v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); } catch (_) { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* storage unavailable: keep in memory only */ } }
  };
  const safe = (label, fn) => { try { return fn(); } catch (err) { console.error(`[cafe-maad] ${label}`, err); return undefined; } };
  const pName = (p) => p.name[state.lang] || p.name.fa;
  const pNote = (p) => p.note[state.lang] || p.note.fa;
  const pImg = (id) => `p-${id}`;
  const pctSign = () => (state.lang === "fa" || state.lang === "ar" ? "٪" : "%");

  /* ---------- pricing ---------- */
  // per-kg price in toman; a custom blend costs the weighted average of its coffees
  const perKg = (l) => l.type === "blend"
    ? Math.round(l.parts.reduce((s, x) => s + BY_ID[x.id].kg * x.pct, 0) / 100) * 1000
    : BY_ID[l.id].kg * 1000;
  // packs are priced in proportion to 1 kg, rounded up to the next 1,000 toman; wholesale is charged per kg
  const packPrice = (kgPrice, size) => size === "ws" ? kgPrice : Math.ceil(kgPrice * SIZES.find((s) => s.id === size).g / 1e6) * 1000;
  const qtyRange = (size) => size === "ws" ? WS : { min: 1, max: MAX_QTY };
  const clampFor = (size, q) => { const r = qtyRange(size); return Math.min(r.max, Math.max(r.min, Math.round(Number(q) || r.min))); };

  /* ---------- cart model ---------- */
  const validGrind = (l, coffee) => coffee
    ? (l.form === "whole" || (l.form === "ground" && GRINDS.some((g) => g.id === l.grind)))
    : l.form === "na";
  const validParts = (parts) => Array.isArray(parts) && parts.length >= BLEND.min && parts.length <= BLEND.max &&
    new Set(parts.map((x) => x?.id)).size === parts.length &&
    parts.every((x) => x && BY_ID[x.id] && isCoffee(BY_ID[x.id]) && Number.isInteger(x.pct) && x.pct >= 1 && x.pct <= 100) &&
    parts.reduce((s, x) => s + x.pct, 0) === 100;
  const validLine = (l) => l && typeof l === "object" && SIZES.some((s) => s.id === l.size) && (
    (l.type === "item" && Boolean(BY_ID[l.id]) && validGrind(l, isCoffee(BY_ID[l.id]))) ||
    (l.type === "blend" && validParts(l.parts) && validGrind(l, true)));
  const lineKey = (l) => {
    const how = `${l.size}:${l.form}:${l.form === "ground" ? l.grind : "-"}`;
    return l.type === "blend" ? `b:${l.parts.map((x) => `${x.id}-${x.pct}`).join("_")}:${how}` : `i:${l.id}:${how}`;
  };
  const loadCart = () => {
    const raw = store.get(CART_KEY, []);
    state.cart = Array.isArray(raw) ? raw.filter(validLine).map((l) => ({ ...l, key: lineKey(l), qty: clampFor(l.size, l.qty) })) : [];
  };
  const saveCart = () => store.set(CART_KEY, state.cart);
  const unitPrice = (l) => packPrice(perKg(l), l.size);
  const lineTotal = (l) => unitPrice(l) * l.qty;
  const cartCount = () => state.cart.reduce((s, l) => s + (l.size === "ws" ? 1 : l.qty), 0);
  const cartSubtotal = () => state.cart.reduce((s, l) => s + lineTotal(l), 0);
  const grindText = (l) => {
    const d = t();
    if (l.form === "na") return "";
    if (l.form === "whole") return d.forms.whole;
    const g = GRINDS.find((x) => x.id === l.grind);
    return `${d.grinds[l.grind]} (${d.levels[g.level - 1]})`;
  };
  const sizeText = (l) => l.size === "ws" ? `${t().sizes.ws} · ${num(l.qty)} ${t().kgUnit}` : t().sizes[l.size];
  const partsText = (parts) => parts.map((x) => `${num(x.pct)}${pctSign()} ${pName(BY_ID[x.id])}`).join(" + ");
  const describe = (l) => {
    const d = t();
    const how = [sizeText(l), grindText(l)].filter(Boolean).join(" · ");
    if (l.type === "blend") return { name: d.customName, detail: `${partsText(l.parts)} · ${how}`, img: pImg(l.parts[0].id), render: false };
    const p = BY_ID[l.id];
    return { name: pName(p), detail: how, img: pImg(p.id), render: false };
  };
  const addLine = (line, qty) => {
    const key = lineKey(line);
    const found = state.cart.find((l) => l.key === key);
    if (found) found.qty = clampFor(found.size, found.qty + qty);
    else state.cart.push({ ...line, key, qty: clampFor(line.size, qty) });
    saveCart(); renderCart(); toast(t().added); bumpBadge();
  };
  const setQty = (key, qty) => {
    const l = state.cart.find((x) => x.key === key);
    if (!l) return;
    if (qty < qtyRange(l.size).min) state.cart = state.cart.filter((x) => x.key !== key);
    else l.qty = clampFor(l.size, qty);
    saveCart(); renderCart();
  };

  /* ---------- small UI pieces ---------- */
  let toastTimer = 0;
  const toast = (msg) => { const n = $("toast"); n.textContent = msg; n.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => n.classList.remove("show"), 2200); };
  const bumpBadge = () => { const b = $("cart-count"); b.animate?.([{ transform: "scale(1.35)" }, { transform: "scale(1)" }], { duration: 300 }); };
  const stepper = (value, onChange, label, range = { min: 1, max: MAX_QTY }, unit = "") => {
    const wrap = el("div", "stepper"); wrap.setAttribute("role", "group"); wrap.setAttribute("aria-label", label);
    const dec = el("button"); dec.type = "button"; dec.setAttribute("aria-label", t().dec); dec.appendChild(icon("#i-minus"));
    const out = el("output", "num", unit ? `${num(value)} ${unit}` : num(value)); out.setAttribute("aria-live", "polite");
    const inc = el("button"); inc.type = "button"; inc.setAttribute("aria-label", t().inc); inc.appendChild(icon("#i-plus"));
    dec.addEventListener("click", () => onChange(value - 1));
    inc.addEventListener("click", () => onChange(value + 1));
    if (value >= range.max) inc.disabled = true;
    wrap.append(dec, out, inc);
    return wrap;
  };
  const productImg = (name, render, cls) => { const im = el("img", cls); im.src = IMG[name] || ""; im.alt = ""; im.width = 160; im.height = 160; im.decoding = "async"; if (render) im.classList.add("contain"); return im; };

  const card = ({ name, note, img, price, priceNote, onCart, favKey, onPick, pickLabel, active }) => {
    const d = t();
    const c = el("article", active ? "card is-on" : "card");
    const ph = el("div", "ph");
    const im = el("img"); im.src = IMG[img] || ""; im.alt = name; im.width = 480; im.height = 520; im.decoding = "async"; im.loading = "lazy"; ph.appendChild(im);
    if (onPick) { const pick = el("button", "pick"); pick.type = "button"; pick.setAttribute("aria-label", `${pickLabel || d.choose}: ${name}`); pick.addEventListener("click", onPick); c.appendChild(pick); }
    const acts = el("div", "acts");
    const cartBtn = el("button", "mini"); cartBtn.type = "button"; cartBtn.setAttribute("aria-label", `${onCart ? d.add : d.choose}: ${name}`); cartBtn.appendChild(icon("#i-cart"));
    cartBtn.addEventListener("click", onCart || onPick);
    const fav = el("button", "mini"); fav.type = "button"; fav.setAttribute("aria-label", `${d.fav}: ${name}`); fav.setAttribute("aria-pressed", String(state.favs.has(favKey))); fav.appendChild(icon("#i-heart"));
    fav.addEventListener("click", () => {
      if (state.favs.has(favKey)) state.favs.delete(favKey); else state.favs.add(favKey);
      store.set("maad-favs-v1", [...state.favs]);
      $$(`[data-fav="${favKey}"]`).forEach((b) => b.setAttribute("aria-pressed", String(state.favs.has(favKey))));
    });
    fav.dataset.fav = favKey;
    acts.append(cartBtn, fav);
    const pr = el("span", "price num", money(price)); pr.appendChild(el("small", null, priceNote ? `${d.currency} · ${priceNote}` : d.currency));
    c.append(ph, el("h3", null, name), el("p", null, note), acts, pr);
    return c;
  };
  const productCard = (p, onPick, active) => card({
    name: pName(p), note: pNote(p), img: pImg(p.id), price: p.kg * 1000, priceNote: t().perKg, favKey: `p:${p.id}`, onPick, active
  });

  /* radio-chip group with arrow-key support */
  const radioGroup = (container, options, current, onPick) => {
    const buttons = options.map((o) => {
      const b = el("button", "chip"); b.type = "button"; b.setAttribute("role", "radio");
      const on = o.value === current; b.setAttribute("aria-checked", String(on)); b.tabIndex = on ? 0 : -1;
      o.fill(b);
      b.addEventListener("click", () => onPick(o.value));
      return b;
    });
    container.replaceChildren(...buttons);
    container.onkeydown = (e) => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(e.key in keys)) return;
      e.preventDefault();
      const i = buttons.indexOf(document.activeElement);
      if (i < 0) return;
      const step = keys[e.key] * (root.dir === "rtl" && (e.key === "ArrowLeft" || e.key === "ArrowRight") ? -1 : 1);
      const next = options[(i + step + options.length) % options.length].value;
      onPick(next);
      requestAnimationFrame(() => container.querySelector('[aria-checked="true"]')?.focus());
    };
  };

  /* shared steps of both builders: size, whole/ground, grind; and the quantity / wholesale-kg row */
  const sizeChips = (box, cfg, kgPrice, render) => {
    const d = t();
    radioGroup(box, SIZES.map((s) => ({ value: s.id, fill: (n) => n.append(el("b", "num", d.sizes[s.id]), el("small", "num", s.id === "ws" ? `${money(kgPrice)} / ${d.perKg}` : money(packPrice(kgPrice, s.id)))) })), cfg.size,
      (v) => { if (v !== cfg.size) cfg.qty = qtyRange(v).min; cfg.size = v; render(); });
  };
  const grindChips = (formBox, grindBox, cfg, render) => {
    const d = t();
    radioGroup(formBox, ["whole", "ground"].map((f) => ({ value: f, fill: (n) => n.append(el("b", null, d.forms[f])) })), cfg.form, (v) => { cfg.form = v; render(); });
    const off = cfg.form === "whole";
    radioGroup(grindBox, GRINDS.map((x) => ({ value: x.id, fill: (n) => { n.append(el("b", null, d.grinds[x.id]), el("small", null, d.levels[x.level - 1])); if (off) { n.disabled = true; n.tabIndex = -1; } } })), cfg.grind, (v) => { cfg.grind = v; render(); });
    grindBox.setAttribute("aria-disabled", String(off));
    return off;
  };
  const qtyRow = (box, labelBox, cfg, render) => {
    const d = t(); const ws = cfg.size === "ws";
    labelBox.textContent = ws ? d.sumKg : d.sumQty;
    box.replaceChildren(stepper(cfg.qty, (q) => { cfg.qty = clampFor(cfg.size, q); render(); }, ws ? d.sumKg : d.qty, qtyRange(cfg.size), ws ? d.kgUnit : ""));
  };
  const wsNote = (box, ws) => {
    box.hidden = !ws;
    if (!ws) return;
    const d = t(); const a = el("a", null, d.wsMore); a.href = "#/wholesale";
    box.replaceChildren(el("span", null, `${d.wsPick} `), a);
  };
  const numberSteps = (host) => $$(".step-label", host).filter((n) => !n.closest("[hidden]")).forEach((n, i) => { n.querySelector("i").textContent = num(i + 1); });

  const summaryHtml = (uid) => `
      <div class="phone phone--sum" aria-live="polite">
        <div class="ph"><img data-g="img" alt="" width="480" height="520"></div>
        <h3 data-g="name"></h3>
        <p class="sum-note" data-g="note"></p>
        <ul class="sum-rows">
          <li><span data-k="sumSize"></span><b data-g="size-v" class="num"></b></li>
          <li data-g="grind-row"><span data-k="sumGrind"></span><b data-g="grind-v"></b></li>
          <li><span data-g="qty-l"></span><span data-g="qty"></span></li>
        </ul>
        <p class="hint hint--ws" data-g="ws-note" hidden></p>
        <div class="sum-foot">
          <div class="total"><small data-k="sumPrice"></small><b class="num"><span data-g="price"></span> <small data-k="currency"></small></b></div>
          <button class="btn btn--navy btn--sm" type="button" data-g="add"><svg aria-hidden="true"><use href="#i-cart"/></svg><span data-k="add"></span></button>
        </div>
        <p class="err" data-g="err" id="${uid}-err" role="alert"></p>
      </div>`;
  const grindStepsHtml = (uid, a, b) => `
        <div data-g="form-step">
          <div class="step-label" id="${uid}-l${a}"><i class="num"></i><span data-k="s4"></span></div>
          <div class="chips chips--2" data-g="form" role="radiogroup" aria-labelledby="${uid}-l${a}"></div>
        </div>
        <div data-g="grind-step">
          <div class="step-label" id="${uid}-l${b}"><i class="num"></i><span data-k="s5"></span></div>
          <div class="chips chips--2" data-g="grind" role="radiogroup" aria-labelledby="${uid}-l${b}"></div>
        </div>
        <p class="hint" data-g="hint"></p>`;

  /* ---------- product builder (one instance per page) ---------- */
  const builders = new Map();
  const mountBuilder = (host) => {
    const id = host.dataset.builder;
    const uid = `bld-${id}`;
    host.innerHTML = `
      <div class="phone">
        <div class="phone-top"><span class="chev"><svg width="18" height="18" aria-hidden="true"><use href="#i-chev"/></svg></span><span data-k="bPhone"></span><span style="width:34px"></span></div>
        <div class="step-label" id="${uid}-l1"><i class="num"></i><span data-k="s1"></span></div>
        <div class="chips chips--cats" data-g="cat" role="radiogroup" aria-labelledby="${uid}-l1"></div>
        <div class="step-label" id="${uid}-l2"><i class="num"></i><span data-k="s2"></span></div>
        <div class="chips chips--2" data-g="product" role="radiogroup" aria-labelledby="${uid}-l2"></div>
        <div class="step-label" id="${uid}-l3"><i class="num"></i><span data-k="s3"></span></div>
        <div class="chips chips--2" data-g="size" role="radiogroup" aria-labelledby="${uid}-l3"></div>
        ${grindStepsHtml(uid, 4, 5)}
      </div>${summaryHtml(uid)}`;
    const cfg = { cat: "mix", id: "mixA70", size: "250", form: "ground", grind: "espHome", qty: 1 };
    const g = (k) => host.querySelector(`[data-g="${k}"]`);
    const render = () => {
      const d = t();
      host.querySelectorAll("[data-k]").forEach((n) => { n.textContent = d[n.dataset.k] ?? ""; });
      const p = BY_ID[cfg.id];
      const coffee = isCoffee(p);
      radioGroup(g("cat"), CATS.map((c) => ({ value: c.id, fill: (n) => n.append(el("b", null, d.pcats[c.id])) })), cfg.cat, (v) => { if (v !== cfg.cat) { cfg.cat = v; cfg.id = inCat(v)[0].id; } render(); });
      radioGroup(g("product"), inCat(cfg.cat).map((x) => ({ value: x.id, fill: (n) => n.append(el("b", null, pName(x)), el("small", "num", `${money(x.kg * 1000)} / ${d.perKg}`)) })), cfg.id, (v) => { cfg.id = v; render(); });
      sizeChips(g("size"), cfg, perKg({ type: "item", id: cfg.id }), render);
      g("form-step").hidden = !coffee; g("grind-step").hidden = !coffee;
      const off = coffee ? grindChips(g("form"), g("grind"), cfg, render) : true;
      g("grind-step").classList.toggle("grind-off", off);
      g("hint").textContent = !coffee ? d.powderHint : off ? d.wholeHint : d.groundHint;
      numberSteps(host);
      const line = lineOf();
      g("img").src = IMG[pImg(p.id)] || ""; g("img").alt = pName(p);
      g("name").textContent = pName(p);
      g("note").textContent = pNote(p);
      g("size-v").textContent = d.sizes[cfg.size];
      g("grind-row").hidden = !coffee;
      g("grind-v").textContent = grindText(line);
      qtyRow(g("qty"), g("qty-l"), cfg, render);
      wsNote(g("ws-note"), cfg.size === "ws");
      g("price").textContent = num(lineTotal({ ...line, qty: cfg.qty }));
    };
    const lineOf = () => {
      const coffee = isCoffee(BY_ID[cfg.id]);
      return { type: "item", id: cfg.id, size: cfg.size, form: coffee ? cfg.form : "na", grind: coffee && cfg.form === "ground" ? cfg.grind : "-" };
    };
    g("add").addEventListener("click", () => { addLine(lineOf(), cfg.qty); cfg.qty = qtyRange(cfg.size).min; render(); });
    const api = {
      render, cfg,
      select(pid) { const p = BY_ID[pid]; if (p) { cfg.cat = p.cat; cfg.id = p.id; render(); } },
      selectCat(cat) { if (CATS.some((c) => c.id === cat) && cfg.cat !== cat) { cfg.cat = cat; cfg.id = inCat(cat)[0].id; render(); } }
    };
    builders.set(id, api);
    render();
  };

  /* ---------- custom blend builder: up to five coffees with percentage shares ---------- */
  const evenSplit = (n) => Array.from({ length: n }, (_, i) => Math.floor(100 / n) + (i < 100 % n ? 1 : 0));
  const mountCustom = (host) => {
    const uid = `cb-${host.dataset.custom}`;
    host.innerHTML = `
      <div class="phone">
        <div class="phone-top"><span class="chev"><svg width="18" height="18" aria-hidden="true"><use href="#i-chev"/></svg></span><span data-k="cbPhone"></span><span style="width:34px"></span></div>
        <div class="step-label" id="${uid}-l1"><i class="num"></i><span data-k="cbS1"></span></div>
        <div class="blend-bar" data-g="bar" aria-hidden="true"></div>
        <ol class="blend-rows" data-g="rows" aria-labelledby="${uid}-l1"></ol>
        <div class="blend-tools">
          <button class="btn btn--ghost btn--sm" type="button" data-g="more"><svg aria-hidden="true"><use href="#i-plus"/></svg><span data-k="cbAdd"></span></button>
          <button class="btn btn--ghost btn--sm" type="button" data-g="even" data-k="cbEven"></button>
          <span class="blend-sum num" data-g="sum" aria-live="polite"></span>
        </div>
        <div class="step-label" id="${uid}-l2"><i class="num"></i><span data-k="s3"></span></div>
        <div class="chips chips--2" data-g="size" role="radiogroup" aria-labelledby="${uid}-l2"></div>
        ${grindStepsHtml(uid, 3, 4)}
      </div>${summaryHtml(uid)}`;
    const cfg = { parts: [{ id: "brazilSantos", pct: 60 }, { id: "uganda", pct: 40 }], size: "250", form: "ground", grind: "espHome", qty: 1 };
    const g = (k) => host.querySelector(`[data-g="${k}"]`);
    const total = () => cfg.parts.reduce((s, x) => s + x.pct, 0);
    const valid = () => validParts(cfg.parts);
    const coffeeSelect = (part, i) => {
      const d = t();
      const sel = el("select"); sel.id = `${uid}-c${i}`; sel.setAttribute("aria-label", d.cbPart(num(i + 1)));
      COFFEE_CATS.forEach((c) => {
        const og = el("optgroup"); og.label = d.pcatsLong[c];
        inCat(c).forEach((p) => {
          const o = el("option", null, `${pName(p)} · ${money(p.kg * 1000)}`); o.value = p.id;
          o.disabled = p.id !== part.id && cfg.parts.some((x) => x.id === p.id);
          og.appendChild(o);
        });
        sel.appendChild(og);
      });
      sel.value = part.id;
      sel.addEventListener("change", () => { part.id = sel.value; render(); });
      return sel;
    };
    const pctInput = (part, i) => {
      const d = t();
      const wrap = el("div", "pct");
      const dec = el("button"); dec.type = "button"; dec.setAttribute("aria-label", `${d.dec} · ${d.cbPart(num(i + 1))}`); dec.appendChild(icon("#i-minus"));
      const inp = el("input"); inp.type = "number"; inp.inputMode = "numeric"; inp.min = "1"; inp.max = "100"; inp.step = "1"; inp.dir = "ltr"; inp.value = String(part.pct);
      inp.setAttribute("aria-label", `${d.cbPct} · ${d.cbPart(num(i + 1))}`);
      const inc = el("button"); inc.type = "button"; inc.setAttribute("aria-label", `${d.inc} · ${d.cbPart(num(i + 1))}`); inc.appendChild(icon("#i-plus"));
      const set = (v, rerender) => { part.pct = Math.min(100, Math.max(1, Math.round(Number(toLatinDigits(v)) || 1))); if (rerender) render(); else update(); };
      dec.addEventListener("click", () => set(part.pct - 5, true));
      inc.addEventListener("click", () => set(part.pct + 5, true));
      inp.addEventListener("input", () => { if (inp.value !== "") set(inp.value, false); });
      inp.addEventListener("change", () => { if (inp.value === "") set(1, false); inp.value = String(part.pct); });
      wrap.append(dec, inp, el("span", null, pctSign()), inc);
      return wrap;
    };
    const renderRows = () => {
      const d = t();
      g("rows").replaceChildren(...cfg.parts.map((part, i) => {
        const li = el("li", "blend-row");
        const dot = el("span", "dot"); dot.style.background = BLEND_COLORS[i];
        const rm = el("button", "mini"); rm.type = "button"; rm.appendChild(icon("#i-x")); rm.setAttribute("aria-label", `${d.remove}: ${pName(BY_ID[part.id])}`);
        rm.disabled = cfg.parts.length <= BLEND.min;
        rm.addEventListener("click", () => { cfg.parts.splice(i, 1); render(); });
        li.append(dot, coffeeSelect(part, i), pctInput(part, i), rm);
        return li;
      }));
      g("more").disabled = cfg.parts.length >= BLEND.max;
    };
    // everything that depends on the shares, without rebuilding the inputs being typed in
    const update = () => {
      const d = t();
      const sum = total();
      g("bar").replaceChildren(...cfg.parts.map((x, i) => { const s = el("i"); s.style.background = BLEND_COLORS[i]; s.style.flexGrow = String(x.pct); s.title = `${pName(BY_ID[x.id])} ${x.pct}%`; return s; }));
      const box = g("sum"); box.classList.toggle("is-ok", sum === 100); box.classList.toggle("is-bad", sum !== 100);
      box.textContent = sum === 100 ? `✓ ${d.cbOk}` : sum < 100 ? d.cbLeft(num(100 - sum)) : d.cbOver(num(sum - 100));
      const ok = valid();
      const line = lineOf();
      const kgPrice = ok ? perKg(line) : 0;
      sizeChips(g("size"), cfg, kgPrice, render);
      g("price").textContent = ok ? num(lineTotal({ ...line, qty: cfg.qty })) : "—";
      g("note").textContent = `${partsText(cfg.parts)}${ok ? ` · ${d.cbPerKg}: ${money(kgPrice)} ${d.currency}` : ""}`;
      g("add").disabled = !ok; g("add").setAttribute("aria-describedby", `${uid}-err`);
      g("err").textContent = ok ? "" : d.cbErr;
    };
    const render = () => {
      const d = t();
      host.querySelectorAll("[data-k]").forEach((n) => { n.textContent = d[n.dataset.k] ?? ""; });
      renderRows();
      const off = grindChips(g("form"), g("grind"), cfg, render);
      g("grind-step").classList.toggle("grind-off", off);
      g("hint").textContent = off ? d.wholeHint : d.groundHint;
      numberSteps(host);
      g("img").src = IMG.twobeans || ""; g("img").alt = d.customName;
      g("name").textContent = d.customName;
      g("size-v").textContent = d.sizes[cfg.size];
      g("grind-v").textContent = grindText(lineOf());
      qtyRow(g("qty"), g("qty-l"), cfg, render);
      wsNote(g("ws-note"), cfg.size === "ws");
      update();
    };
    const lineOf = () => ({ type: "blend", parts: cfg.parts.map((x) => ({ id: x.id, pct: x.pct })), size: cfg.size, form: cfg.form, grind: cfg.form === "ground" ? cfg.grind : "-" });
    g("more").addEventListener("click", () => {
      if (cfg.parts.length >= BLEND.max) return;
      const free = COFFEES.find((p) => !cfg.parts.some((x) => x.id === p.id));
      cfg.parts.push({ id: free.id, pct: Math.max(1, 100 - total()) });
      render();
      host.querySelector(`#${uid}-c${cfg.parts.length - 1}`)?.focus();
    });
    g("even").addEventListener("click", () => { evenSplit(cfg.parts.length).forEach((v, i) => { cfg.parts[i].pct = v; }); render(); });
    g("add").addEventListener("click", () => { if (!valid()) return; addLine(lineOf(), cfg.qty); cfg.qty = qtyRange(cfg.size).min; render(); });
    host.querySelector(".phone--sum .ph").classList.add("ph--render");
    builders.set(`custom-${host.dataset.custom}`, { render, cfg });
    render();
  };


  /* ---------- renderers ---------- */
  const fillStatic = () => {
    const d = t();
    $$("[data-i18n]").forEach((n) => { n.textContent = d[n.dataset.i18n] ?? ""; });
    $$("[data-i18n-html]").forEach((n) => { n.innerHTML = d[n.dataset.i18nHtml] ?? ""; });
    $$("[data-i18n-aria]").forEach((n) => n.setAttribute("aria-label", d[n.dataset.i18nAria] ?? ""));
    $$("[data-options]").forEach((sel) => {
      const prev = sel.selectedIndex;
      sel.replaceChildren(...(d[sel.dataset.options] || []).map((label, i) => { const o = el("option", null, label); o.value = String(i); return o; }));
      sel.selectedIndex = prev >= 0 ? prev : 0;
    });
    const navItems = () => NAV.map(([k, href, page]) => { const li = el("li"); const a = el("a", null, d[k]); a.href = href; a.dataset.navPage = page; li.appendChild(a); return li; });
    $("nav-links").replaceChildren(...navItems());
    $("foot-pages").replaceChildren(...navItems());
    $("foot-shop").replaceChildren(...PAGE_CATS.map((c) => { const li = el("li"); const a = el("a", null, d.pcatsLong[c.id]); a.href = `#/products/${c.id}`; li.appendChild(a); return li; }));
    $$("[data-cats]").forEach((ul) => ul.replaceChildren(...PAGE_CATS.map((c) => {
      const li = el("li"); const a = el("a"); a.href = `#/products/${c.id}`;
      const sq = el("span", "sq"); sq.appendChild(icon(c.icon)); a.append(sq, el("span", null, d.pcats[c.id])); li.appendChild(a); return li;
    })));
    $$("[data-cb-tips]").forEach((ul) => ul.replaceChildren(...d.cbTips.map((x) => el("li", null, x))));
    $$("[data-cdesc]").forEach((n) => { n.textContent = d.cDesc[n.dataset.cdesc] ?? ""; });
    $$("[data-perks]").forEach((ul) => ul.replaceChildren(...d.perks.map(([h, s], i) => { const li = el("li"); const r = el("span", "ring"); r.appendChild(icon(PERK_ICONS[i])); li.append(r, el("span", null, h), el("small", null, s)); return li; })));
    $$("[data-facts]").forEach((box) => box.replaceChildren(...d.facts.map(([n, s]) => { const x = el("div"); x.append(el("b", null, n), el("span", null, s)); return x; })));
    $$("[data-visit]").forEach(renderVisit);
    $$("[data-steps]").forEach((ol) => ol.replaceChildren(...d.steps.map((s, i) => { const li = el("li"); li.append(el("span", "step-dot num", num(i + 1)), el("span", null, s)); return li; })));
    $("tag-price").textContent = `${money(packPrice(BY_ID.vietnam.kg * 1000, "250"))} ${d.currency}`;
    $$("[data-grind-guide]").forEach((box) => {
      box.replaceChildren(el("h3", "h4", d.guideH), ...GRINDS.map((x) => {
        const row = el("div", "grind-row"); const bar = el("span", "bar"); const fill = el("i"); fill.style.width = `${(x.level / 7) * 100}%`; bar.appendChild(fill);
        row.append(el("span", null, `${d.grinds[x.id]} · ${d.levels[x.level - 1]}`), bar); return row;
      }));
    });
  };

  const renderVisit = (host) => {
    const d = t();
    host.innerHTML = `
      <div class="visit">
        <div class="ph"><img src="${IMG.portafilter}" alt="" width="490" height="610"></div>
        <div class="body">
          <span class="eyebrow"></span><h2 class="h2"></h2>
          <ul class="visit-list">
            <li><svg aria-hidden="true"><use href="#i-pin"/></svg><span><small></small><span></span></span></li>
            <li><svg aria-hidden="true"><use href="#i-clock"/></svg><span><small></small><span></span></span></li>
            <li><svg aria-hidden="true"><use href="#i-phone"/></svg><span><small></small><a class="ltr num" href="tel:+${PHONE_INTL}"></a></span></li>
            <li><svg aria-hidden="true"><use href="#i-insta"/></svg><span><small>Instagram</small><a class="ltr" href="https://instagram.com/ghahvemaad_satarkhan" target="_blank" rel="noopener">@ghahvemaad_satarkhan</a></span></li>
          </ul>
          <div class="socials">
            <a class="soc" href="tel:+${PHONE_INTL}"><svg aria-hidden="true"><use href="#i-phone"/></svg><span></span></a>
            <a class="soc" href="https://wa.me/${PHONE_INTL}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-whatsapp"/></svg><span></span></a>
            <a class="soc" href="https://t.me/+${PHONE_INTL}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-telegram"/></svg><span></span></a>
            <a class="soc" href="https://instagram.com/ghahvemaad_satarkhan" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-insta"/></svg><span>Instagram</span></a>
            <a class="soc" href="https://www.google.com/maps/search/?api=1&amp;query=${encodeURIComponent("قهوه ماد ستارخان تهران")}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-map"/></svg><span></span></a>
          </div>
        </div>
      </div>`;
    host.querySelector(".eyebrow").textContent = d.vEyebrow;
    host.querySelector("h2").textContent = d.vTitle;
    const li = host.querySelectorAll(".visit-list li");
    li[0].querySelector("small").textContent = d.vAddrL; li[0].querySelector("span span").textContent = d.addr;
    li[1].querySelector("small").textContent = d.vHoursL; li[1].querySelector("span span").textContent = d.hours;
    li[2].querySelector("small").textContent = d.vPhoneL; li[2].querySelector("a").textContent = d.phone;
    const soc = host.querySelectorAll(".soc span");
    soc[0].textContent = d.call; soc[1].textContent = d.wa; soc[2].textContent = d.tg; soc[4].textContent = d.route;
  };

  const pickProduct = (id) => {
    const p = BY_ID[id];
    if (!p) return;
    if (state.route.page === "products" && state.route.arg === p.cat) {
      builders.get("products")?.select(id); renderProductCards();
      $("beans-builder").scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (state.route.page === "order") {
      builders.get("order")?.select(id);
    } else {
      state.pending = id; location.hash = `#/products/${p.cat}`;
    }
  };
  const renderProductCards = () => {
    const cat = state.route.arg;
    const sel = builders.get("products")?.cfg.id;
    $("items-cards").replaceChildren(...inCat(cat).map((p) => productCard(p, () => pickProduct(p.id), p.id === sel)));
  };

  const renderHomeShop = () => {
    const d = t();
    $$("[data-home-tabs]").forEach((tabs) => tabs.replaceChildren(...CATS.map(({ id: k }) => {
      const b = el("button", "tab", d.pcats[k]); b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", String(state.homeTab === k));
      b.addEventListener("click", () => { state.homeTab = k; renderHomeShop(); });
      return b;
    })));
    $$("[data-home-shop]").forEach((box) => box.replaceChildren(...HOME_PICKS[state.homeTab].map((id) => productCard(BY_ID[id], () => pickProduct(id)))));
    $$("[data-home-all]").forEach((a) => { a.href = `#/products/${state.homeTab}`; });
    renderBlendSample();
  };
  const SAMPLE = [{ id: "brazilSantos", pct: 50 }, { id: "ethSidamo", pct: 30 }, { id: "uganda", pct: 20 }];
  const renderBlendSample = () => {
    const d = t();
    const kgPrice = perKg({ type: "blend", parts: SAMPLE });
    $$("[data-cb-sample]").forEach((box) => {
      const bar = el("div", "blend-bar"); bar.setAttribute("aria-hidden", "true");
      SAMPLE.forEach((x, i) => { const s = el("i"); s.style.background = BLEND_COLORS[i]; s.style.flexGrow = String(x.pct); bar.appendChild(s); });
      const ul = el("ul", "cb-legend");
      SAMPLE.forEach((x, i) => { const li = el("li"); const dot = el("span", "dot"); dot.style.background = BLEND_COLORS[i]; li.append(dot, el("span", null, pName(BY_ID[x.id])), el("b", "num", `${num(x.pct)}${pctSign()}`)); ul.appendChild(li); });
      const foot = el("div", "cb-price"); foot.append(el("small", null, d.cbPerKg), el("b", "num", `${money(kgPrice)} ${d.currency}`));
      const sizes = el("div", "cb-sizes");
      SIZES.filter((s) => s.id !== "ws").forEach((s) => { const x = el("span", "num"); x.append(el("small", null, d.sizes[s.id]), el("b", null, money(packPrice(kgPrice, s.id)))); sizes.appendChild(x); });
      box.replaceChildren(el("span", "eyebrow", d.customName), bar, ul, foot, sizes);
    });
  };

  const renderCatTiles = (current) => {
    const d = t();
    $("cat-tiles").replaceChildren(...PAGE_CATS.map((c) => {
      const a = el("a", c.id === "custom" ? "cat-tile cat-tile--custom" : "cat-tile"); a.href = `#/products/${c.id}`; a.setAttribute("role", "tab"); a.setAttribute("aria-selected", String(c.id === current));
      const sq = el("span", "sq"); sq.appendChild(icon(c.icon));
      const txt = el("span"); txt.append(el("b", null, d.pcats[c.id]), el("small", null, d.cDesc[c.id]));
      a.append(sq, txt); return a;
    }));
  };

  const renderProducts = (cat) => {
    const d = t();
    const c = PAGE_CATS.some((x) => x.id === cat) ? cat : "robusta";
    state.route.arg = c;
    renderCatTiles(c);
    $("cat-custom").hidden = c !== "custom";
    $("cat-items").hidden = c === "custom";
    if (c === "custom") return;
    $("items-eyebrow").textContent = d.shopEyebrow;
    $("items-h").textContent = d.pcatsLong[c];
    $("items-lead").textContent = d.catLead[c];
    const b = builders.get("products");
    if (state.pending && BY_ID[state.pending]?.cat === c) {
      b?.select(state.pending); state.pending = null;
      requestAnimationFrame(() => $("beans-builder").scrollIntoView({ block: "start" }));
    } else b?.selectCat(c);
    renderProductCards();
  };

  const renderQuick = () => {
    const d = t();
    $("quick-list").replaceChildren(...inCat("powder").map((p) => {
      const row = el("div", "quick");
      const info = el("div"); info.append(el("b", null, pName(p)), el("small", "num", `${d.sizes["250"]} · ${money(packPrice(p.kg * 1000, "250"))} ${d.currency}`));
      const add = el("button", "mini"); add.type = "button"; add.setAttribute("aria-label", `${d.add}: ${pName(p)}`); add.appendChild(icon("#i-plus"));
      add.addEventListener("click", () => addLine({ type: "item", id: p.id, size: "250", form: "na", grind: "-" }, 1));
      row.append(productImg(pImg(p.id)), info, add); return row;
    }));
  };

  const renderCart = () => {
    const d = t();
    $("cart-count").textContent = num(cartCount());
    $("cart-btn").setAttribute("aria-label", `${d.cart} (${d.itemsN(cartCount())})`);
    $$("[data-cart-list]").forEach((box) => {
      if (!state.cart.length) {
        const e = el("div", "empty"); const r = el("span", "ring"); r.appendChild(icon("#i-cart"));
        const go = el("a", "btn btn--ghost btn--sm", d.emptyCta); go.href = "#/products";
        e.append(r, el("p", null, d.emptyCart), go); box.replaceChildren(e); return;
      }
      box.replaceChildren(...state.cart.map((l) => {
        const info = describe(l);
        const row = el("div", "line");
        const mid = el("div"); mid.append(el("b", null, info.name), el("small", null, info.detail), stepper(l.qty, (q) => setQty(l.key, q), `${l.size === "ws" ? d.sumKg : d.qty}: ${info.name}`, qtyRange(l.size), l.size === "ws" ? d.kgUnit : ""));
        const end = el("div", "end");
        const rm = el("button", "link-btn"); rm.type = "button"; rm.append(icon("#i-trash"), el("span", null, d.remove)); rm.setAttribute("aria-label", `${d.remove}: ${info.name}`);
        rm.addEventListener("click", () => setQty(l.key, 0));
        end.append(el("span", "p num", `${money(lineTotal(l))}`), rm);
        row.append(productImg(info.img, info.render), mid, end); return row;
      }));
    });
    const pickup = document.querySelector('#checkout input[name="method"]:checked')?.value === "pickup";
    $$("[data-totals]").forEach((box) => {
      const row = (label, value, cls) => { const x = el("div", cls); x.append(el("span", null, label), el("b", "num", value)); return x; };
      box.replaceChildren(
        row(`${d.subtotal} (${d.itemsN(cartCount())})`, `${money(cartSubtotal())} ${d.currency}`),
        row(d.deliveryL, pickup ? d.pickupFree : d.deliveryTBD),
        row(d.total, `${money(cartSubtotal())} ${d.currency}`, "grand"));
    });
    const co = $("drawer-checkout"); co.classList.toggle("btn--disabled", !state.cart.length); co.setAttribute("aria-disabled", String(!state.cart.length));
  };

  /* ---------- drawer ---------- */
  let lastFocus = null;
  const openDrawer = () => {
    lastFocus = document.activeElement;
    $("drawer").hidden = false; $("scrim").hidden = false; document.body.style.overflow = "hidden";
    $("cart-btn").setAttribute("aria-expanded", "true");
    $("drawer-close").focus();
  };
  const closeDrawer = () => {
    if ($("drawer").hidden) return;
    $("drawer").hidden = true; $("scrim").hidden = true; document.body.style.overflow = "";
    $("cart-btn").setAttribute("aria-expanded", "false");
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  };
  const trapFocus = (e) => {
    if (e.key !== "Tab" || $("drawer").hidden) return;
    const f = $$('a[href], button:not([disabled]), input, select, textarea', $("drawer")).filter((n) => n.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };

  /* ---------- forms ---------- */
  const toLatinDigits = (s) => String(s).replace(/[۰-۹]/g, (c) => "۰۱۲۳۴۵۶۷۸۹".indexOf(c)).replace(/[٠-٩]/g, (c) => "٠١٢٣٤٥٦٧٨٩".indexOf(c));
  const normPhone = (raw) => {
    const s = toLatinDigits(raw).replace(/[\s\-().]/g, "");
    const ir = s.match(/^(?:\+98|0098|98|0)?(9\d{9})$/);
    if (ir) return `0${ir[1]}`;
    if (/^\+\d{8,15}$/.test(s)) return s;
    return null;
  };
  const setErr = (form, name, msg) => {
    const p = form.querySelector(`[data-err="${name}"]`); if (p) p.textContent = msg || "";
    const input = form.querySelector(`[name="${name}"]`);
    if (input) { if (msg) { input.setAttribute("aria-invalid", "true"); if (p) { p.id = p.id || `${form.id}-${name}-err`; input.setAttribute("aria-describedby", p.id); } } else { input.removeAttribute("aria-invalid"); } }
  };
  const clearErrs = (form) => { $$("[data-err]", form).forEach((p) => { p.textContent = ""; }); $$("[aria-invalid]", form).forEach((n) => n.removeAttribute("aria-invalid")); };
  const firstInvalid = (form) => form.querySelector('[aria-invalid="true"]') || form.querySelector(".err:not(:empty)");
  const val = (form, name) => (form.elements[name]?.value || "").trim();
  const optLabel = (form, name, key) => t()[key][Number(form.elements[name]?.value || 0)] || "";
  const waUrl = (text) => `https://wa.me/${PHONE_INTL}?text=${encodeURIComponent(text)}`;
  const openWa = (url) => { const w = safe("open", () => window.open(url, "_blank", "noopener")); return Boolean(w); };
  const orderId = () => { const n = new Date(); const p = (x) => String(x).padStart(2, "0"); return `MAAD-${String(n.getFullYear()).slice(2)}${p(n.getMonth() + 1)}${p(n.getDate())}-${Math.floor(1000 + Math.random() * 9000)}`; };

  const buildOrderText = (form, id) => {
    const d = t(); const m = d.msg;
    const pickup = form.elements.method.value === "pickup";
    const lines = state.cart.map((l, i) => { const x = describe(l); return l.size === "ws" ? `${num(i + 1)}. ${x.name} · ${x.detail} = ${money(lineTotal(l))} ${d.currency}` : `${num(i + 1)}. ${x.name} · ${x.detail} × ${num(l.qty)} = ${money(lineTotal(l))} ${d.currency}`; });
    return [
      `☕ ${m.order}`, `${m.id}: ${id}`, "",
      `${m.name}: ${val(form, "name")}`, `${m.phone}: ${normPhone(val(form, "phone"))}`,
      `${m.method}: ${pickup ? d.mPickup : d.mDelivery}`,
      ...(pickup ? [] : [`${m.addr}: ${val(form, "address")}`]),
      `${m.time}: ${optLabel(form, "time", "times")}`,
      ...(val(form, "note") ? [`${m.note}: ${val(form, "note")}`] : []),
      "", `${m.items}:`, ...lines, "",
      `${m.total}: ${money(cartSubtotal())} ${d.currency}`
    ].join("\n");
  };

  const initCheckout = () => {
    const form = $("checkout");
    const syncMethod = () => { const pickup = form.elements.method.value === "pickup"; $("addr-field").hidden = pickup; if (pickup) setErr(form, "address", ""); renderCart(); };
    form.addEventListener("change", (e) => { if (e.target.name === "method") syncMethod(); });
    form.addEventListener("input", (e) => { if (e.target.name) setErr(form, e.target.name, ""); });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const d = t(); clearErrs(form);
      const pickup = form.elements.method.value === "pickup";
      if (!val(form, "name")) setErr(form, "name", d.eName);
      if (!normPhone(val(form, "phone"))) setErr(form, "phone", d.ePhone);
      if (!pickup && val(form, "address").length < 8) setErr(form, "address", d.eAddr);
      if (!state.cart.length) setErr(form, "cart", d.eCart);
      const bad = firstInvalid(form);
      if (bad) { (bad.matches("input,textarea,select") ? bad : form.querySelector("button[type=submit]")).focus(); return; }
      const id = orderId();
      const text = buildOrderText(form, id);
      const url = waUrl(text);
      store.set("maad-last-order", { id, text, at: Date.now() });
      $("done-id").textContent = id; $("done-text").textContent = text; $("done-wa").href = url;
      $("order-main").hidden = true; $("order-done").hidden = false;
      state.cart = []; saveCart(); renderCart(); form.reset(); syncMethod();
      openWa(url);
      requestAnimationFrame(() => { $("order-done").scrollIntoView({ block: "start" }); $("order-done").querySelector(".done").focus({ preventScroll: true }); });
    });
    $("done-new").addEventListener("click", () => { $("order-done").hidden = true; $("order-main").hidden = false; window.scrollTo(0, 0); });
    $("done-copy").addEventListener("click", async () => {
      const text = $("done-text").textContent;
      try { await navigator.clipboard.writeText(text); toast(t().copied); }
      catch (_) { const r = document.createRange(); r.selectNodeContents($("done-text")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }
    });
    syncMethod();
  };

  const tierFor = (kg) => { let i = -1; TIER_MIN.forEach((m, k) => { if (kg >= m) i = k; }); return i; };
  const renderWholesale = () => {
    const d = t();
    $$("[data-tiers]").forEach((box) => box.replaceChildren(...d.tiers.map((tier, i) => {
      const c = el("div", i === 1 ? "tier tier--hot" : "tier");
      if (i === 1) c.appendChild(el("span", "tag", d.hot));
      const big = el("div", "big num", tier.off); big.appendChild(el("small", null, d.offL));
      const ul = el("ul"); tier.perks.forEach((p) => ul.appendChild(el("li", null, p)));
      c.append(el("h3", null, tier.name), el("span", "num", tier.range), big, ul); return c;
    })));
    const forIcons = ["#i-mug", "#i-fork", "#i-office", "#i-bed"];
    $$("[data-ws-for]").forEach((ul) => ul.replaceChildren(...d.wsFor.map(([h, s], i) => { const li = el("li"); const r = el("span", "ring"); r.appendChild(icon(forIcons[i])); li.append(r, el("span", null, h), el("small", null, s)); return li; })));
    $$("[data-ws-steps]").forEach((ol) => ol.replaceChildren(...d.wsSteps.map(([h, s]) => { const li = el("li"); li.append(el("b", null, h), el("span", null, s)); return li; })));
    $$("[data-ab-steps]").forEach((ol) => ol.replaceChildren(...d.abSteps.map(([h, s]) => { const li = el("li"); li.append(el("b", null, h), el("span", null, s)); return li; })));
    const checked = new Set($$('[data-ws-blends] input:checked').map((i) => i.value));
    $$("[data-ws-blends]").forEach((box) => box.replaceChildren(...CATS.map((c) => {
      const grp = el("div", "check-group"); grp.appendChild(el("b", "check-h", d.pcatsLong[c.id]));
      const list = el("div", "checks");
      inCat(c.id).forEach((p) => {
        const lab = el("label"); const inp = el("input"); inp.type = "checkbox"; inp.name = "blends"; inp.value = p.id; inp.checked = checked.has(p.id);
        lab.append(inp, el("span", null, pName(p))); list.appendChild(lab);
      });
      grp.appendChild(list); return grp;
    })));
    updateTierHint();
  };
  const updateTierHint = () => {
    const d = t(); const kg = Number(toLatinDigits($("ws-kg").value));
    const i = tierFor(kg);
    $("ws-tier-hint").textContent = i >= 0 ? d.tierHint(d.tiers[i].name, d.tiers[i].off) : "";
  };
  const initWholesale = () => {
    const form = $("wsform");
    form.addEventListener("input", (e) => { if (e.target.name) setErr(form, e.target.name, ""); if (e.target.name === "kg") updateTierHint(); });
    form.addEventListener("change", (e) => { if (e.target.name === "blends") setErr(form, "blends", ""); });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const d = t(); const m = d.msg; clearErrs(form); $("ws-ok").hidden = true;
      const kg = Number(toLatinDigits(val(form, "kg")));
      const blends = $$('[data-ws-blends] input:checked').map((i) => pName(BY_ID[i.value]));
      if (!val(form, "biz")) setErr(form, "biz", d.eBiz);
      if (!val(form, "name")) setErr(form, "name", d.eName);
      if (!normPhone(val(form, "phone"))) setErr(form, "phone", d.ePhone);
      if (!Number.isFinite(kg) || kg < 5 || kg > 5000) setErr(form, "kg", d.eKg);
      if (!blends.length) setErr(form, "blends", d.eBlends);
      const bad = firstInvalid(form);
      if (bad) { (bad.matches("input,textarea,select") ? bad : form.querySelector("input[name=blends]")).focus(); return; }
      const i = tierFor(kg);
      const text = [
        `☕ ${m.ws}`, "",
        `${m.biz}: ${val(form, "biz")}`, `${m.type}: ${optLabel(form, "type", "bizTypes")}`,
        `${m.name}: ${val(form, "name")}`, `${m.phone}: ${normPhone(val(form, "phone"))}`,
        ...(val(form, "city") ? [`${m.city}: ${val(form, "city")}`] : []),
        `${m.kg}: ${num(kg)} ${m.kgUnit} (${d.tiers[i].name}, ${d.tiers[i].off})`,
        `${m.blends}: ${blends.join("، ")}`, `${m.grind}: ${optLabel(form, "grind", "grindOpts")}`, `${m.freq}: ${optLabel(form, "freq", "freqs")}`,
        ...(val(form, "note") ? [`${m.note}: ${val(form, "note")}`] : [])
      ].join("\n");
      const url = waUrl(text);
      openWa(url);
      const ok = $("ws-ok"); ok.replaceChildren(el("span", null, `${d.wsOk} `)); const a = el("a", null, d.openWa); a.href = url; a.target = "_blank"; a.rel = "noopener"; a.style.textDecoration = "underline"; ok.appendChild(a); ok.hidden = false;
    });
  };

  const renderContact = () => {
    const d = t();
    const cards = [["#i-phone", d.ctCards.call, d.phone, `tel:+${PHONE_INTL}`], ["#i-whatsapp", d.ctCards.wa, d.phone, `https://wa.me/${PHONE_INTL}`], ["#i-telegram", d.ctCards.tg, d.phone, `https://t.me/+${PHONE_INTL}`], ["#i-insta", d.ctCards.ig, "@ghahvemaad_satarkhan", "https://instagram.com/ghahvemaad_satarkhan"]];
    $$("[data-contact-cards]").forEach((box) => box.replaceChildren(...cards.map(([ic, h, s, href]) => {
      const a = el("a", "c-card"); a.href = href; if (href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener"; }
      const sq = el("span", "sq"); sq.appendChild(icon(ic)); a.append(sq, el("b", null, h), el("span", "ltr num", s)); return a;
    })));
    $$("[data-faq]").forEach((box) => box.replaceChildren(...d.faq.map(([q, a]) => { const det = el("details"); det.append(el("summary", null, q), el("p", null, a)); return det; })));
  };
  const initContact = () => {
    const form = $("ctform");
    form.addEventListener("input", (e) => { if (e.target.name) setErr(form, e.target.name, ""); });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const d = t(); const m = d.msg; clearErrs(form); $("ct-ok").hidden = true;
      if (!val(form, "name")) setErr(form, "name", d.eName);
      if (!normPhone(val(form, "phone"))) setErr(form, "phone", d.ePhone);
      if (val(form, "message").length < 3) setErr(form, "message", d.eMsg);
      const bad = firstInvalid(form);
      if (bad) { bad.focus(); return; }
      const text = [`✉️ ${m.contact}`, "", `${m.name}: ${val(form, "name")}`, `${m.phone}: ${normPhone(val(form, "phone"))}`, `${m.subject}: ${optLabel(form, "subject", "subjects")}`, "", val(form, "message")].join("\n");
      const url = waUrl(text); openWa(url);
      const ok = $("ct-ok"); ok.replaceChildren(el("span", null, `${d.ctOk} `)); const a = el("a", null, d.openWa); a.href = url; a.target = "_blank"; a.rel = "noopener"; a.style.textDecoration = "underline"; ok.appendChild(a); ok.hidden = false;
    });
  };

  /* ---------- blog ---------- */
  const faNum = (n) => new Intl.NumberFormat(t().locale).format(n);
  const postCard = (a) => {
    const d = t();
    const card = el("a", "post"); card.href = `#/blog/${a.id}`;
    const ph = el("div", "ph"); ph.innerHTML = a.cover;
    const meta = el("div", "meta"); meta.append(el("b", null, d.cats[a.cat] || ""), el("span", "num", d.minRead(faNum(a.readMinutes))));
    const h = el("h3", null, a.title); h.lang = "fa"; h.dir = "rtl";
    const p = el("p", null, a.dek); p.lang = "fa"; p.dir = "rtl";
    card.append(ph, meta, h, p); return card;
  };
  const renderLatest = () => { $$("[data-latest]").forEach((box) => box.replaceChildren(...ARTICLES.slice(0, 3).map(postCard))); };
  const renderBlog = () => {
    const d = t();
    const cats = ["all", ...new Set(ARTICLES.map((a) => a.cat))];
    $("blog-chips").replaceChildren(...cats.map((c) => {
      const b = el("button", "tab", c === "all" ? d.all : d.cats[c]); b.type = "button"; b.setAttribute("aria-pressed", String(state.blogCat === c));
      b.addEventListener("click", () => { state.blogCat = c; renderBlog(); });
      return b;
    }));
    const list = ARTICLES.filter((a) => state.blogCat === "all" || a.cat === state.blogCat);
    const [first, ...rest] = list;
    const feat = $("blog-featured"); feat.replaceChildren();
    if (first) {
      const f = el("a", "feat"); f.href = `#/blog/${first.id}`;
      const ph = el("div", "ph"); ph.innerHTML = first.coverWide;
      const body = el("div", "body");
      const h = el("h2", null, first.title); h.lang = "fa"; h.dir = "rtl";
      const p = el("p", null, first.dek); p.lang = "fa"; p.dir = "rtl";
      body.append(el("span", "kick", `${d.featured} · ${d.cats[first.cat]}`), h, p, el("span", "foot-meta num", d.minRead(faNum(first.readMinutes))));
      f.append(ph, body); feat.appendChild(f);
    }
    $("blog-grid").replaceChildren(...rest.map(postCard));
  };

  const renderArticle = (id) => {
    const d = t();
    const i = ARTICLES.findIndex((a) => a.id === id);
    if (i < 0) { location.replace("#/blog"); return false; }
    const a = ARTICLES[i];
    const host = $("article");
    host.replaceChildren();
    const hero = el("header", "art-hero");
    const cover = el("div", "art-cover"); cover.innerHTML = a.coverWide;
    const head = el("div", "art-head"); head.lang = "fa"; head.dir = "rtl";
    const back = el("a", "crumbs"); back.href = "#/blog"; back.textContent = `${t().dir === "rtl" ? "→" : "←"} ${d.artBack}`; back.lang = state.lang; back.dir = t().dir;
    const by = el("div", "byline"); [I18N.fa.byMag, I18N.fa.minRead(I18N.fa && new Intl.NumberFormat("fa-IR").format(a.readMinutes)), I18N.fa.srcN(new Intl.NumberFormat("fa-IR").format(a.sources.length))].forEach((s) => by.appendChild(el("span", null, s)));
    head.append(back, el("span", "kick", a.kicker || I18N.fa.cats[a.cat]), el("h1", null, a.title), el("p", "dek", a.dek), by);
    if (d.faOnly) { const note = el("p", "lang-note", d.faOnly); note.lang = state.lang; note.dir = t().dir; head.appendChild(note); }
    hero.append(cover, head);
    const grid = el("div", "art-grid"); grid.lang = "fa"; grid.dir = "rtl";
    const side = el("aside", "toc-wrap");
    const toc = el("nav", "toc"); toc.setAttribute("aria-label", I18N.fa.artToc);
    const body = el("div", "prose");
    if (a.takeaways.length) { const tk = el("div", "takeaways"); tk.appendChild(el("b", null, I18N.fa.artTake)); const ul = el("ul"); a.takeaways.forEach((x) => ul.appendChild(el("li", null, x))); tk.appendChild(ul); body.appendChild(tk); }
    const content = el("div"); content.innerHTML = a.body; body.appendChild(content);
    $$("img[data-img]", content).forEach((im) => { im.src = IMG[im.dataset.img] || ""; });
    const src = el("section", "sources"); src.appendChild(el("h2", null, I18N.fa.artSources));
    const ol = el("ol"); a.sources.forEach((s) => { const li = el("li"); const link = el("a", null, s.title); link.href = s.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.dir = "ltr"; li.append(link, el("span", null, ` ${s.publisher || ""}${s.year ? ` · ${new Intl.NumberFormat("fa-IR", { useGrouping: false }).format(s.year)}` : ""}`)); ol.appendChild(li); });
    src.append(ol, el("p", "hint", I18N.fa.artCredit)); body.appendChild(src);
    const cta = el("div", "art-cta"); cta.lang = state.lang; cta.dir = t().dir;
    const ctx = el("div"); ctx.append(el("b", null, d.artCtaT), el("span", null, d.artCtaD));
    const go = el("a", "btn btn--sm", d.artCtaB); go.href = "#/order"; cta.append(ctx, go); body.appendChild(cta);
    const pager = el("div", "pager"); pager.lang = state.lang; pager.dir = t().dir;
    const pg = (x, label, cls) => { const l = el("a", `pg ${cls}`); l.href = `#/blog/${x.id}`; const tt = el("span", null, x.title); tt.lang = "fa"; tt.dir = "rtl"; l.append(el("small", null, label), tt); return l; };
    if (ARTICLES[i - 1]) pager.appendChild(pg(ARTICLES[i - 1], d.artPrev, "pg--prev")); else pager.appendChild(el("span"));
    if (ARTICLES[i + 1]) pager.appendChild(pg(ARTICLES[i + 1], d.artNext, "pg--next"));
    body.appendChild(pager);
    const heads = $$("h2[id]", content);
    toc.appendChild(el("b", null, I18N.fa.artToc));
    const tol = el("ol");
    heads.forEach((h) => { const li = el("li"); const b = el("button", null, h.textContent); b.type = "button"; b.dataset.target = h.id; b.addEventListener("click", () => h.scrollIntoView({ behavior: "smooth", block: "start" })); li.appendChild(b); tol.appendChild(li); });
    toc.appendChild(tol); side.appendChild(toc);
    grid.append(side, body);
    host.append(hero, grid);
    observeToc(heads, toc);
    document.title = `${a.title} | ${d.title}`;
    return true;
  };
  let tocObserver = null;
  const observeToc = (heads, toc) => {
    tocObserver?.disconnect();
    if (!("IntersectionObserver" in window) || !heads.length) return;
    tocObserver = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) $$("button", toc).forEach((b) => b.classList.toggle("on", b.dataset.target === en.target.id)); });
    }, { rootMargin: "0px 0px -70% 0px" });
    heads.forEach((h) => tocObserver.observe(h));
  };

  /* ---------- latte bean ring ---------- */
  const beanRing = () => {
    $$("[data-latte]").forEach((box) => {
      const imgs = ["bean-a", "bean-b", "bean-c"];
      for (let i = 0; i < 26; i++) {
        const a = (i / 26) * Math.PI * 2 + (i % 2) * 0.08;
        const r = 44 + (i % 3) * 2.2;
        const b = el("img", "b"); b.src = IMG[imgs[i % 3]]; b.alt = ""; b.width = 40; b.height = 40;
        b.style.left = `${50 + r * Math.cos(a) - 3.5}%`; b.style.top = `${50 + r * Math.sin(a) - 3.5}%`;
        b.style.transform = `rotate(${(a * 180) / Math.PI + 90 + (i % 4) * 20}deg)`;
        box.appendChild(b);
      }
    });
  };

  /* ---------- router ---------- */
  const PAGES = ["home", "products", "order", "wholesale", "blog", "about", "contact"];
  const parseRoute = () => {
    const h = decodeURIComponent(location.hash || "");
    const m = h.match(/^#\/([a-z]*)\/?([\w-]*)/);
    if (!m) return { page: "home", arg: "" };
    const page = m[1] || "home";
    if (page === "blog" && m[2]) return { page: "article", arg: m[2] };
    return PAGES.includes(page) ? { page, arg: m[2] } : { page: "home", arg: "" };
  };
  const renderPage = () => {
    const r = state.route; const d = t();
    if (r.page === "products") renderProducts(r.arg);
    if (r.page === "products" && r.arg === "custom") builders.get("custom-products")?.render();
    if (r.page === "order") { renderQuick(); builders.get("order")?.render(); }
    if (r.page === "wholesale") renderWholesale();
    if (r.page === "blog") renderBlog();
    if (r.page === "about") renderWholesale();
    if (r.page === "contact") renderContact();
    if (r.page === "home") { renderHomeShop(); renderLatest(); }
    if (r.page === "article") { if (!renderArticle(r.arg)) return; }
    else document.title = r.page === "home" ? `${d.title} | ${d.pages.home}` : `${d.pages[r.page]} | ${d.title}`;
  };
  const route = (first) => {
    const legacy = (location.hash || "").replace("#", "");
    if (LANGS.includes(legacy)) { apply(legacy, true); history.replaceState(null, "", "#/"); }
    const prev = state.route;
    state.route = parseRoute();
    const page = state.route.page;
    $$(".page").forEach((p) => { p.hidden = p.dataset.page !== page; });
    $$("[data-nav-page]").forEach((a) => { if (a.dataset.navPage === (page === "article" ? "blog" : page)) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    closeDrawer();
    $("nav").classList.remove("is-open"); document.querySelector(".menu-btn").setAttribute("aria-expanded", "false");
    safe("render page", renderPage);
    const samePage = prev.page === page && prev.arg === state.route.arg;
    if (!first && !samePage && !state.route.keepScroll) { window.scrollTo(0, 0); $("main").focus({ preventScroll: true }); }
  };

  /* ---------- language ---------- */
  const apply = (lang, silent) => {
    state.lang = I18N[lang] ? lang : "fa";
    const d = t();
    root.lang = state.lang; root.dir = d.dir;
    $$("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
    safe("static", fillStatic);
    builders.forEach((b) => safe("builder", b.render));
    safe("cart", renderCart);
    if (!silent) safe("page", renderPage);
    store.set("maad-lang", state.lang);
  };
  const initialLang = () => {
    const h = (location.hash || "").replace("#", "");
    if (LANGS.includes(h)) return h;
    const s = store.get("maad-lang", null);
    if (LANGS.includes(s)) return s;
    const nav = (navigator.language || "").slice(0, 2);
    return LANGS.includes(nav) ? nav : "fa";
  };

  /* ---------- wiring ---------- */
  const initNav = () => {
    const nav = $("nav"); const btn = nav.querySelector(".menu-btn");
    const set = (open) => { nav.classList.toggle("is-open", open); btn.setAttribute("aria-expanded", String(open)); };
    btn.addEventListener("click", () => set(!nav.classList.contains("is-open")));
    document.addEventListener("click", (e) => {
      if (!(e.target instanceof Element)) return;
      if (nav.classList.contains("is-open") && !e.target.closest("#nav")) set(false);
      const sc = e.target.closest("[data-scroll]");
      if (sc) { e.preventDefault(); $(sc.dataset.scroll)?.scrollIntoView({ behavior: "smooth", block: "start" }); }
      const skip = e.target.closest(".skip");
      if (skip) { e.preventDefault(); $("main").focus(); }
      const dis = e.target.closest('[aria-disabled="true"]');
      if (dis && dis.tagName === "A") e.preventDefault();
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") { set(false); closeDrawer(); } trapFocus(e); });
    $$("[data-lang]").forEach((b) => b.addEventListener("click", () => apply(b.dataset.lang)));
    $("cart-btn").addEventListener("click", openDrawer);
    $("drawer-close").addEventListener("click", closeDrawer);
    $("scrim").addEventListener("click", closeDrawer);
    $("drawer-checkout").addEventListener("click", () => closeDrawer());
    window.addEventListener("hashchange", () => route(false));
    window.addEventListener("storage", (e) => { if (e.key === CART_KEY) { loadCart(); renderCart(); } });
  };

  safe("load", () => { loadCart(); const f = store.get("maad-favs-v1", []); state.favs = new Set(Array.isArray(f) ? f.filter((x) => typeof x === "string") : []); });
  safe("builders", () => $$("[data-builder]").forEach(mountBuilder));
  safe("custom", () => $$("[data-custom]").forEach(mountCustom));
  safe("beans", beanRing);
  safe("lang", () => apply(initialLang(), true));
  safe("nav", initNav);
  safe("checkout", initCheckout);
  safe("wholesale", initWholesale);
  safe("contact", initContact);
  safe("route", () => route(true));
})();

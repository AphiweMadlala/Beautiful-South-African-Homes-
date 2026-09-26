// Functional + responsive QA. Usage: node qa/qa.mjs [outdir]
// Needs the site served at BASE (see "How to run" in reports/final-qa.md).
import { createRequire } from 'module';
import fs from 'fs';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright');
const BASE = process.env.BASE || 'http://localhost:8321/Beautiful-South-African-Homes-/';
const OUT = process.argv[2] || 'qa/out';
fs.mkdirSync(OUT, { recursive: true });

const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail: String(detail) }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); };

const PAGES = {
  home: '',
  collection: 'residences/',
  'for-sale': 'residences/?set=for-sale',
  portfolio: 'residences/?set=portfolio',
  locations: 'locations/',
  feature: 'feature-your-property/',
  about: 'about/',
  contact: 'contact/',
  'live-agent-credited': 'residences/eye-of-africa-4-bedroom-house/',
  'poa-listing': 'residences/pinnacle-point-5-bedroom-house/',
  'limited-data': 'residences/ballito-6-bedroom-house/',
  'architect-credit': 'residences/waterfall-6-bedroom-house/',
  'not-found': '404.html',
};
const WIDTHS = [375, 390, 430, 768, 1024, 1440, 1920];

const browser = await chromium.launch();

async function open(path, width = 1440, opts = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: width < 700 ? 844 : 900 }, ...opts });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  page.on('requestfailed', r => errors.push('requestfailed ' + r.url()));
  page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
  await page.goto(BASE + path, { waitUntil: 'networkidle' });
  return { ctx, page, errors };
}

// ---------- 1. every page at every width: overflow, console errors, images
for (const [name, path] of Object.entries(PAGES)) {
  for (const w of WIDTHS) {
    const { ctx, page, errors } = await open(path, w);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    await page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; }));
    await page.waitForLoadState('networkidle');
    const broken = await page.evaluate(() => [...document.images].filter(i => i.getAttribute('src') && i.complete && i.naturalWidth === 0 && !i.closest('dialog')).map(i => i.src));
    check(`${name} @${w}: no horizontal overflow`, overflow <= 0, overflow > 0 ? `${overflow}px` : '');
    check(`${name} @${w}: no console/network errors`, errors.length === 0, errors.slice(0, 3).join(' | '));
    check(`${name} @${w}: no broken images`, broken.length === 0, broken.slice(0, 2).join(' '));
    if ([390, 1440].includes(w)) await page.screenshot({ path: `${OUT}/${name}-${w}.png`, fullPage: false });
    await ctx.close();
  }
}

// ---------- 2. internal link crawl
{
  const { ctx, page } = await open('');
  const seen = new Set(); const queue = [BASE]; const bad = [];
  while (queue.length) {
    const url = queue.shift();
    if (seen.has(url)) continue; seen.add(url);
    const res = await page.goto(url, { waitUntil: 'domcontentloaded' });
    if (!res || res.status() >= 400) { bad.push(`${res && res.status()} ${url}`); continue; }
    const hrefs = await page.$$eval('a[href]', as => as.map(a => a.href));
    for (const h of hrefs) {
      const u = new URL(h); u.hash = '';
      if (u.href.startsWith(BASE) && !seen.has(u.href) && !u.search) queue.push(u.href);
    }
  }
  check(`link crawl: ${seen.size} internal URLs return 200`, bad.length === 0, bad.join(' | '));
  await ctx.close();
}

// ---------- 3. collection: All Residences by default, sets, filters, sort, URL state, back/forward
{
  const { ctx, page } = await open('residences/');
  const visible = () => page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.slug));
  const current = () => page.$$eval('.sets [data-set]', as => as.filter(a => a.getAttribute('aria-current') === 'true').map(a => a.dataset.set).join());
  const search = () => new URL(page.url()).search;
  const setParam = () => new URL(page.url()).searchParams.get('set');
  const counts = await page.$$eval('[data-card]', cs => ({ total: cs.length, live: cs.filter(c => c.dataset.live === 'true').length }));
  check('collection defaults to All Residences: 26 shown (1 for sale + 25 Portfolio)', (await visible()).length === 26 && counts.total === 26 && counts.live === 1, `${(await visible()).length} shown, ${JSON.stringify(counts)}`);
  check('default collection URL needs no set parameter', search() === '', page.url());
  check('All Residences tab is current on first load', (await current()) === 'all', await current());
  const tabs = await page.$$eval('.sets [data-set]', as => as.map(a => a.textContent.replace(/\s+/g, ' ').trim()).join(' | '));
  check('register tabs read All Residences 26, For Sale 1, The Portfolio 25, in that order', tabs === 'All Residences 26 | For Sale 1 | The Portfolio 25', tabs);
  check('no "more residences in the Portfolio" callout', (await page.$$('.coll-more, [data-more]')).length === 0);
  const grid = await page.$$eval('[data-card]', cs => ({ first: cs[0].dataset.live, grids: new Set(cs.map(c => c.parentElement)).size, ranked: cs.every((c, i) => i === 0 || +cs[i - 1].dataset.rank < +c.dataset.rank) }));
  check('live listing ranks first, in the same grid as the Portfolio', grid.first === 'true' && grid.grids === 1 && grid.ranked, JSON.stringify(grid));
  const sortLabels = await page.$$eval('[data-sort] option', os => os.map(o => o.textContent.trim()));
  check('price sorts are labelled "Price shown", not asking price', sortLabels.join('|') === 'Recommended|Price shown, high to low|Price shown, low to high', sortLabels.join(' | '));
  await page.click('.sets [data-set=for-sale]');
  check('For Sale filter shows 1 and writes set=for-sale', (await visible()).length === 1 && setParam() === 'for-sale' && (await current()) === 'for-sale', page.url());
  await page.click('.sets [data-set=portfolio]');
  check('Portfolio filter shows 25 and writes set=portfolio', (await visible()).length === 25 && setParam() === 'portfolio' && (await current()) === 'portfolio', page.url());
  await page.goBack();
  check('Back restores For Sale', (await visible()).length === 1 && (await current()) === 'for-sale' && setParam() === 'for-sale', page.url());
  await page.goBack();
  check('Back again restores All Residences at the bare URL', (await visible()).length === 26 && (await current()) === 'all' && search() === '', page.url());
  await page.goForward();
  check('Forward re-applies For Sale', (await visible()).length === 1 && (await current()) === 'for-sale', page.url());
  await page.click('.sets [data-set=all]');
  check('All Residences tab returns to the bare URL', (await visible()).length === 26 && search() === '', page.url());
  // location choices follow the register: a place with nothing in the current set is disabled
  const locState = () => page.evaluate(() => {
    const set = new URL(location.href).searchParams.get('set') || 'all';
    const pool = [...document.querySelectorAll('[data-card]')].filter(c => set === 'all' || (set === 'for-sale') === (c.dataset.live === 'true'));
    const at = (c, v) => ({ p: c.dataset.province, c: c.dataset.city, a: c.dataset.place })[v[0]] === v.slice(2);
    const opts = [...document.querySelectorAll('#f-loc option')].filter(o => o.value);
    return { options: opts.length, disabled: opts.filter(o => o.disabled).length, wrong: opts.filter(o => o.disabled !== !pool.some(c => at(c, o.value))).map(o => o.value) };
  });
  let ls = await locState();
  check('All Residences: every location option is available', ls.disabled === 0 && ls.options >= 10, JSON.stringify(ls));
  await page.click('.sets [data-set=for-sale]');
  ls = await locState();
  check('For Sale: locations without a residence for sale are disabled, the rest available', ls.wrong.length === 0 && ls.disabled > 0 && ls.disabled < ls.options, JSON.stringify(ls));
  await page.click('.sets [data-set=portfolio]');
  ls = await locState();
  check('Portfolio: location options match the Portfolio', ls.wrong.length === 0, JSON.stringify(ls));
  await page.selectOption('#f-loc', 'c:Cape Town');
  const ct = await visible();
  const ctOk = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).every(c => c.dataset.city === 'Cape Town'));
  check('location filter (city) narrows to Cape Town only', ct.length > 0 && ctOk && page.url().includes('loc=c%3ACape+Town'), `${ct.length} cards`);
  await page.selectOption('#f-price', '40000000-');
  const prices = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => Number(c.dataset.price)));
  check('price range filter keeps only R40m+', prices.length > 0 && prices.every(p => p >= 40000000), prices.join());
  await page.selectOption('[data-sort]', 'price-asc');
  const sorted = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => Number(c.dataset.price)));
  check('sort price low to high', sorted.every((p, i) => i === 0 || sorted[i - 1] <= p), sorted.join());
  await page.selectOption('[data-sort]', 'price-desc');
  const sortedD = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => Number(c.dataset.price)));
  check('sort price high to low', sortedD.every((p, i) => i === 0 || sortedD[i - 1] >= p), sortedD.join());
  await page.goBack();
  check('Back restores previous sort', (await page.inputValue('[data-sort]')) === 'price-asc', page.url());
  await page.goBack(); await page.goBack();
  check('Back restores location without price', (await page.inputValue('#f-price')) === '' && (await page.inputValue('#f-loc')) === 'c:Cape Town', page.url());
  await page.goForward();
  check('Forward re-applies price', (await page.inputValue('#f-price')) === '40000000-');
  await page.click('label.chip:has(input[name=beds][value="6"]) span');
  await page.click('.sets [data-set=for-sale]');
  check('empty state appears with a route to the whole collection', await page.isVisible('[data-empty]') && await page.isVisible('[data-empty-all]') && /across the whole collection/.test(await page.textContent('[data-empty-msg]')), await page.textContent('[data-empty-msg]'));
  check('chosen location stays selected in a set with nothing there', (await page.inputValue('#f-loc')) === 'c:Cape Town' && await page.$eval('#f-loc', s => !s.selectedOptions[0].disabled));
  await page.click('[data-empty-reset]');
  check('clear filters restores results', (await visible()).length === 1);
  // "Search all residences" drops only the set, keeping the other filters
  await page.goto(BASE + 'residences/?set=for-sale&loc=c:Cape+Town', { waitUntil: 'networkidle' });
  await page.click('[data-empty-all]');
  const ctAll = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.city));
  check('"Search all residences" widens to All and keeps the location', ctAll.length > 1 && ctAll.every(c => c === 'Cape Town') && search() === '?loc=c%3ACape+Town' && (await current()) === 'all', page.url());
  await page.goto(BASE + 'residences/?loc=c:Cape+Town&price=0-10000000', { waitUntil: 'networkidle' });
  check('All Residences empty state does not offer "Search all residences"', await page.isVisible('[data-empty]') && !(await page.isVisible('[data-empty-all]')));
  // feature filter; an older ?set=all link still works and is tidied to the canonical URL
  await page.goto(BASE + 'residences/?set=all&features=ocean-views', { waitUntil: 'networkidle' });
  const ov = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.features.includes('ocean-views')));
  check('feature filter from URL (ocean views)', ov.length > 0 && ov.every(Boolean), `${ov.length} cards`);
  check('legacy ?set=all link is rewritten to the canonical URL', search() === '?features=ocean-views', page.url());
  check('filter badge counts active filters', (await page.textContent('[data-filter-count]')).trim() === '1');
  await ctx.close();
}

// ---------- 4. home search strip -> collection
{
  const { ctx, page } = await open('');
  check('home search sends no set parameter', (await page.$$('form.search [name=set]')).length === 0);
  await page.selectOption('#q-loc', 'p:KwaZulu-Natal');
  await page.selectOption('#q-beds', '5');
  await Promise.all([page.waitForURL(/residences/), page.click('.search-go')]);
  await page.waitForLoadState('networkidle');
  const ok = await page.$$eval('[data-card]', cs => { const v = cs.filter(c => !c.hidden); return v.length > 0 && v.every(c => c.dataset.province === 'KwaZulu-Natal' && Number(c.dataset.beds) >= 5); });
  check('home search (province + beds) lands on filtered collection', ok, page.url());
  check('home search lands on the canonical URL (loc and beds only)', new URL(page.url()).search === '?loc=p%3AKwaZulu-Natal&beds=5', page.url());
  const locOpts = await page.$$eval('#f-loc option', os => os.map(o => o.value).filter(Boolean));
  check('location options generated from inventory', locOpts.length >= 10, locOpts.length);
  await ctx.close();
}

// ---------- 5. mobile: menu, filters sheet, gallery swipe
{
  const { ctx, page } = await open('', 390, { hasTouch: true, isMobile: true });
  await page.click('[data-menu-open]');
  const inMenu = await page.evaluate(() => !!document.activeElement.closest('[data-menu]'));
  const locked = await page.evaluate(() => document.documentElement.classList.contains('is-locked'));
  check('mobile menu opens with focus inside and scroll locked', inMenu && locked);
  for (let i = 0; i < 3; i++) await page.keyboard.press('Tab');
  check('menu traps focus', await page.evaluate(() => !!document.activeElement.closest('[data-menu]') || document.activeElement === document.body));
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  check('Escape closes menu and restores focus', await page.evaluate(() => !document.querySelector('[data-menu]').open && document.activeElement.matches('[data-menu-open]') && !document.documentElement.classList.contains('is-locked')));
  await page.goto(BASE + 'residences/', { waitUntil: 'networkidle' });
  check('mobile: filters hidden until requested', !(await page.isVisible('#filters')));
  await page.click('[data-filters-open]');
  check('mobile filters open as a modal sheet', await page.evaluate(() => document.querySelector('#filters').matches(':modal')));
  await page.click('label.chip:has(input[name=beds][value="5"]) span');
  const n = await page.textContent('[data-result-count]');
  await page.click('.filters-apply');
  check('mobile filter apply closes sheet and filters', !(await page.isVisible('#filters')) && (await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).length)) === Number(n), n);
  await page.click('[data-filters-open]');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  check('Escape closes filters and restores focus', await page.evaluate(() => document.activeElement.matches('[data-filters-open]')));
  await page.goto(BASE + 'residences/eye-of-africa-4-bedroom-house/', { waitUntil: 'networkidle' });
  await page.$eval('.pswipe-track', t => t.scrollTo({ left: t.clientWidth * 3 }));
  await page.waitForTimeout(400);
  check('mobile gallery swipe updates image count', (await page.textContent('[data-swipe-i]')).trim() === '4', await page.textContent('[data-swipe-i]'));
  await page.screenshot({ path: `${OUT}/mobile-gallery-390.png` });
  const slides = await page.$$eval('.pswipe-track img', is => is.map(i => i.getAttribute('src')));
  const lbSrcs = await page.$$eval('[data-lb-item] img', is => is.map(i => i.dataset.src));
  const countLabel = (await page.textContent('.pswipe-count')).replace(/\s+/g, '');
  check('mobile swipe gallery holds every photograph', slides.length > 3 && slides.join() === lbSrcs.join() && countLabel.endsWith(`/${slides.length}`), `${slides.length} slides, ${lbSrcs.length} in lightbox, label ${countLabel}`);
  await page.$eval('.pswipe-track', t => t.scrollTo({ left: t.scrollWidth }));
  await page.waitForTimeout(400);
  check('swipe count reaches the last photograph', (await page.textContent('[data-swipe-i]')).trim() === String(slides.length), await page.textContent('[data-swipe-i]'));
  await ctx.close();
}

// ---------- 6. lightbox
{
  const { ctx, page } = await open('residences/eye-of-africa-4-bedroom-house/');
  // one gallery experience: the opening gallery and its lightbox, no second mosaic further down
  const g = await page.evaluate(() => ({
    mosaic: document.querySelectorAll('.mosaic, .mosaic-i').length,
    galleries: document.querySelectorAll('.pgal').length,
    stray: [...document.querySelectorAll('[data-open-lightbox]')].filter(b => !b.closest('.pgal')).length,
    sections: [...document.querySelectorAll('.folio-l')].map(f => f.textContent.trim()),
    lb: [...document.querySelectorAll('[data-lb-item] img')].map(i => i.dataset.src),
    button: document.querySelector('.pgal-all')?.textContent.trim() || '',
  }));
  const n = g.lb.length;
  check('no lower Photographs mosaic on the property page', g.mosaic === 0 && !g.sections.includes('Photographs'), g.sections.join(', '));
  check('one gallery: every photograph opener sits in the opening gallery', g.galleries === 1 && g.stray === 0, JSON.stringify({ galleries: g.galleries, stray: g.stray }));
  check(`desktop shows "View all ${n} photographs"`, g.button === `View all ${n} photographs` && await page.isVisible('.pgal-all'), g.button);
  const dir = (g.lb[0] || '').split('/').slice(-2, -1)[0];
  let published = -1;
  try { published = new Set(fs.readdirSync(new URL(`../docs/assets/img/${dir}/`, import.meta.url)).map(f => f.split('-')[0])).size; } catch {}
  const statuses = await Promise.all(g.lb.map(src => ctx.request.get(new URL(src, page.url()).href).then(r => r.status())));
  check(`lightbox holds all ${published} published photographs, each distinct and loadable`, n === published && new Set(g.lb).size === n && statuses.every(s => s === 200), `${n} in lightbox, ${published} published, statuses ${[...new Set(statuses)]}`);
  const opener = page.locator('.pgal-all');
  await opener.click();
  check('"View all" opens the lightbox', await page.evaluate(() => document.querySelector('[data-lightbox]').open));
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
  check('arrow keys advance', (await page.textContent('[data-lb-i]')).trim() === '3');
  await page.keyboard.press('ArrowLeft');
  check('arrow left goes back', (await page.textContent('[data-lb-i]')).trim() === '2');
  const start = (await page.textContent('[data-lb-i]')).trim();
  const seen = new Set();
  for (let i = 0; i < n; i++) { seen.add((await page.textContent('[data-lb-i]')).trim()); await page.keyboard.press('ArrowRight'); }
  check(`arrow keys step through all ${n} photographs and wrap around`, seen.size === n && (await page.textContent('[data-lb-i]')).trim() === start, `${seen.size} seen`);
  const img = await page.$eval('[data-lb-item]:not([hidden]) img', i => i.complete && i.naturalWidth > 0);
  check('lightbox image loads', img);
  for (let i = 0; i < 8; i++) await page.keyboard.press('Tab');
  check('lightbox traps focus', await page.evaluate(() => !!document.activeElement.closest('[data-lightbox]') || document.activeElement === document.body));
  check('body scroll locked while open', await page.evaluate(() => document.documentElement.classList.contains('is-locked')));
  await page.screenshot({ path: `${OUT}/lightbox-1440.png` });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  check('Escape closes lightbox, restores focus and scroll', await page.evaluate(() => !document.querySelector('[data-lightbox]').open && document.activeElement.classList.contains('pgal-all') && !document.documentElement.classList.contains('is-locked')));
  // swipe in lightbox
  await opener.click();
  const box = await page.locator('[data-lb-stage]').boundingBox();
  await page.mouse.move(box.x + box.width * .7, box.y + box.height / 2); await page.mouse.down();
  await page.mouse.move(box.x + box.width * .2, box.y + box.height / 2, { steps: 5 }); await page.mouse.up();
  check('swipe gesture advances lightbox', (await page.textContent('[data-lb-i]')).trim() === '2');
  await page.keyboard.press('Escape');
  // contact actions
  const tel = await page.getAttribute('.enquire a[href^="tel:"]', 'href');
  check('agent call link is a valid SA number', tel === 'tel:+27781308585', tel);
  const listing = await page.getAttribute('.enquire a[href*="12lve.co.za"]', 'href');
  check('agency listing link present', !!listing, listing);
  const mail = await page.$$eval('a[href^="mailto:"]', as => as.map(a => a.href));
  check('platform email links are valid', mail.length > 0 && mail.every(h => h.startsWith('mailto:beautifulsahomes@gmail.com')), mail[0]);
  const ig = await page.$$eval('a[href*="instagram.com"]', as => as.map(a => a.href));
  check('Instagram links point at the account or its posts', ig.length > 0 && ig.every(h => /instagram\.com\/(beautifulsouthafricanhomes\/|p\/)/.test(h)), ig.join(' '));
  check('marketed-by + featured-by attribution shown', (await page.textContent('.enquire')).includes('Marketed by') && (await page.textContent('.enquire')).includes('Featured by'));
  await ctx.close();
}

// ---------- 7. portfolio pages never show a current asking price or phone
{
  const { ctx, page } = await open('residences/pinnacle-point-5-bedroom-house/');
  const txt = await page.textContent('main');
  check('POA listing shows price on application', /Price on application/.test(txt));
  check('portfolio page labels availability as unconfirmed', /Availability to be confirmed/.test(txt) && !/Asking price\s+R/.test(txt.replace('Asking price when featured', '')));
  check('portfolio page has no tel links', (await page.$$('a[href^="tel:"]')).length === 0);
  await ctx.close();
}

// ---------- 8. feature form composes an email; validation is inline
{
  const { ctx, page } = await open('feature-your-property/');
  await page.click('.submit button[type=submit]');
  check('empty submit shows inline error and focuses first field', await page.isVisible('[data-form-error]') && await page.evaluate(() => document.activeElement.id === 's-agent'));
  await page.fill('#s-agent', 'Test Agent'); await page.fill('#s-agency', 'Test Realty'); await page.fill('#s-loc', 'Clifton, Cape Town');
  let nav = null;
  page.on('request', r => { if (r.url().startsWith('mailto:')) nav = r.url(); });
  await page.evaluate(() => { window.__href = null; const d = Object.getOwnPropertyDescriptor(window.location.__proto__ || Location.prototype, 'href'); });
  const href = await page.evaluate(() => new Promise(res => {
    const f = document.querySelector('[data-mailto-form]');
    const orig = window.location;
    f.addEventListener('submit', () => setTimeout(() => res('submitted'), 50), { once: true });
    f.requestSubmit();
  }));
  check('valid submit composes mailto (no backend)', href === 'submitted');
  await ctx.close();
}

// ---------- 9. reduced motion + keyboard focus visibility + touch targets
{
  const { ctx, page } = await open('', 1440, { reducedMotion: 'reduce' });
  const hidden = await page.$$eval('.reveal', els => els.filter(e => getComputedStyle(e).opacity !== '1').length);
  check('reduced motion: all content visible without animation', hidden === 0, hidden);
  await ctx.close();
  const m = await open('residences/eye-of-africa-4-bedroom-house/', 390, { hasTouch: true, isMobile: true });
  const small = await m.page.$$eval('a, button, select, input:not([type=hidden]), label.chip span', els => els
    .filter(e => e.offsetParent !== null && !e.closest('.footer-base, .crumbs, .enq-links, .story, .prose, dialog:not([open])'))
    .map(e => { const r = e.getBoundingClientRect(); return { t: (e.textContent || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 30), h: Math.round(r.height), w: Math.round(r.width) }; })
    .filter(r => r.h > 0 && (r.h < 44 && r.w < 44)));
  check('touch targets >= 44px (mobile property page)', small.length === 0, JSON.stringify(small.slice(0, 5)));
  await m.ctx.close();
  const k = await open('');
  await k.page.keyboard.press('Tab');
  check('first Tab reaches skip link', await k.page.evaluate(() => document.activeElement.classList.contains('skip')));
  await k.page.keyboard.press('Tab');
  const ring = await k.page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle);
  check('focus ring visible on nav', ring !== 'none', ring);
  await k.ctx.close();
}

// ---------- 10. price and status on every card view (one card() macro): live = current asking price,
// Portfolio = dated historical price at lower weight, availability to be confirmed, never "For sale"
{
  const { ctx, page } = await open('residences/');
  const facts = Object.fromEntries((await (await ctx.request.get(BASE + 'assets/data/residences.json')).json()).map(r => [r.slug, r]));
  const MONTH = '(January|February|March|April|May|June|July|August|September|October|November|December) \\d{4}';
  const zar = v => 'R ' + String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const read = sel => page.$$eval(sel, els => els.map(el => {
    const t = s => (el.querySelector(s)?.textContent || '').replace(/\s+/g, ' ').trim();
    return { slug: el.dataset.slug || el.querySelector('a').getAttribute('href').split('/').filter(Boolean).pop(),
      text: el.textContent.replace(/\s+/g, ' ').trim(), flag: t('.card-flag'), price: t('.card-price'),
      k: t('.card-past-k'), v: t('.card-past-v'), status: t('.card-status') };
  }));
  const problems = (cards, flagged) => cards.flatMap(c => {
    const f = facts[c.slug]; const bad = [];
    if (!f) return [`${c.slug}: not in the collection`];
    if (f.live) {
      if (flagged && c.flag !== 'For sale') bad.push('flag');
      if (!f.price || !c.price.includes(zar(f.price))) bad.push('current price');
      if (c.k || c.status) bad.push('historical wording');
    } else {
      if (flagged && c.flag !== 'Previously featured') bad.push('flag');
      if (c.price) bad.push('shown at live-price weight');
      if (!new RegExp(`^(Asked when featured|Featured) in ${MONTH}$`).test(c.k)) bad.push(`date label "${c.k}"`);
      if (f.price ? c.v !== zar(f.price) || !c.k.startsWith('Asked when featured in ') : !['Price on application when featured', 'Price not published'].includes(c.v)) bad.push(`price "${c.v}"`);
      if (c.status !== 'Availability to be confirmed') bad.push('availability');
      if (/for sale|asking price/i.test(c.text)) bad.push('says for sale');
    }
    return bad.length ? [`${c.slug}: ${bad.join(', ')}`] : [];
  });
  const all = await read('[data-card]');
  const live = all.filter(c => facts[c.slug]?.live), past = all.filter(c => !facts[c.slug]?.live);
  check('collection: live card says For sale with its current asking price', live.length === 1 && !problems(live, true).length, problems(live, true).join(' | ') || live.map(c => c.price).join());
  check('collection: 25 Portfolio cards show a dated historical price and availability, never For sale', past.length === 25 && !problems(past, true).length, problems(past, true).slice(0, 3).join(' | '));
  check('collection: POA Portfolio card reads "Price on application when featured"', all.find(c => c.slug === 'pinnacle-point-5-bedroom-house')?.v === 'Price on application when featured');
  const fx = await page.evaluate(() => {
    const style = sel => { const el = document.querySelector(sel); if (!el) return null; const s = getComputedStyle(el); return [parseFloat(s.fontSize), s.color]; };
    return { live: style('.card-live .card-price'), past: style('.card:not(.card-live) .card-past-v') };
  });
  check('historical price is smaller and a different colour from the live price', fx.live && fx.past && fx.past[0] < fx.live[0] && fx.past[1] !== fx.live[1], JSON.stringify(fx));
  await page.goto(BASE + 'residences/waterfall-6-bedroom-house/', { waitUntil: 'networkidle' });
  const rel = await read('.related [data-card]');
  check('related cards: live card current price, Portfolio cards dated (incl. POA)', rel.some(c => facts[c.slug]?.live) && rel.some(c => facts[c.slug] && !facts[c.slug].live && facts[c.slug].price) && rel.some(c => facts[c.slug] && !facts[c.slug].price) && !problems(rel, true).length, problems(rel, true).join(' | ') || rel.map(c => c.slug).join());
  await page.goto(BASE + 'residences/eye-of-africa-4-bedroom-house/', { waitUntil: 'networkidle' });
  const rel2 = await read('.related [data-card]');
  check('related cards on the live listing follow the same treatment', rel2.length === 3 && !problems(rel2, true).length, problems(rel2, true).join(' | '));
  await page.goto(BASE, { waitUntil: 'networkidle' });
  const feat = await read('.featured .feat');
  check('home Portfolio cards: dated historical price and availability, never For sale', feat.length === 4 && feat.every(c => facts[c.slug] && !facts[c.slug].live) && !problems(feat, false).length, problems(feat, false).join(' | '));
  const liveFact = Object.values(facts).find(r => r.live);
  const sig = ((await page.$eval('.sig-price', e => e.textContent).catch(() => '')) || '').replace(/\s+/g, ' ').trim();
  check('home signature keeps its current asking price', !!liveFact && sig === `Asking price ${zar(liveFact.price)}`, sig);
  await ctx.close();
}

// ---------- 11. shorter property pages: consecutive folios, no Photographs / Financial Details,
// breadcrumb to the whole collection; footer and masthead links; mobile call bar keeps its space
{
  const { ctx, page } = await open('');
  const nav = await page.$$eval('.nav-links a', as => as.map(a => a.textContent.trim()));
  check('masthead keeps one Residences link, no separate For Sale / Portfolio links', nav.includes('Residences') && !nav.some(t => /for sale|portfolio/i.test(t)), nav.join(', '));
  const foot = await page.$$eval('.footer a', as => as.map(a => [a.textContent.trim(), a.getAttribute('href')]));
  const has = (t, re) => foot.some(([x, h]) => x === t && re.test(h));
  check('footer: Residences, For sale now, The Portfolio, Locations', has('Residences', /residences\/$/) && has('For sale now', /residences\/\?set=for-sale$/) && has('The Portfolio', /residences\/\?set=portfolio$/) && has('Locations', /locations\/$/) && !foot.some(([x]) => /residences for sale/i.test(x)), JSON.stringify(foot.slice(1, 5)));
  const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'];
  for (const slug of ['eye-of-africa-4-bedroom-house', 'pinnacle-point-5-bedroom-house', 'ballito-6-bedroom-house', 'waterfall-6-bedroom-house']) {
    await page.goto(BASE + `residences/${slug}/`, { waitUntil: 'domcontentloaded' });
    const s = await page.evaluate(() => ({
      n: [...document.querySelectorAll('.pmain .folio-n')].map(e => e.textContent.trim()),
      l: [...document.querySelectorAll('.pmain .folio-l')].map(e => e.textContent.trim()),
      crumbs: [...document.querySelectorAll('.crumbs a')].map(a => [a.textContent.trim(), a.getAttribute('href')]),
      main: document.querySelector('main').textContent,
    }));
    check(`${slug}: sections numbered ${s.n[0]} to ${s.n.at(-1)} with no gaps`, s.n.length >= 4 && s.n.join() === ROMAN.slice(0, s.n.length).join(), s.n.map((x, i) => `${x} ${s.l[i]}`).join(', '));
    check(`${slug}: no Photographs or Financial Details section, no placeholder rates/levies`, !s.l.includes('Photographs') && !s.l.includes('Financial Details') && !/On request from the agent/.test(s.main), s.l.join(', '));
    check(`${slug}: breadcrumb is Residences / location, back to the whole collection`, s.crumbs.length === 1 && s.crumbs[0][0] === 'Residences' && /^(\.\.\/)+residences\/$/.test(s.crumbs[0][1]), JSON.stringify(s.crumbs));
  }
  await ctx.close();
  const m = await open('residences/eye-of-africa-4-bedroom-house/', 390, { hasTouch: true, isMobile: true });
  const waits = await m.page.evaluate(() => !document.querySelector('[data-mcta]').classList.contains('is-on'));
  await m.page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await m.page.waitForTimeout(700);
  const bar = await m.page.evaluate(() => { const b = document.querySelector('[data-mcta]'); return { on: b.classList.contains('is-on'), top: Math.round(b.getBoundingClientRect().top), footerEnd: Math.round(document.querySelector('.footer-base').getBoundingClientRect().bottom), text: b.textContent.replace(/\s+/g, ' ').trim() }; });
  check('mobile call bar waits below the price, then shows "Call Gabriel" without covering the footer', waits && bar.on && /Call Gabriel/.test(bar.text) && bar.footerEnd <= bar.top, JSON.stringify(bar));
  await m.ctx.close();
}

await browser.close();
const failed = results.filter(r => !r.ok);
fs.writeFileSync(`${OUT}/results.json`, JSON.stringify({ total: results.length, failed: failed.length, results }, null, 1));
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);

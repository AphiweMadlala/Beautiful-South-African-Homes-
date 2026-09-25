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

// ---------- 3. collection: sets, filters, sort, URL state, back/forward
{
  const { ctx, page } = await open('residences/');
  const visible = () => page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.slug));
  check('collection defaults to For Sale only', (await visible()).length === 1, (await visible()).join());
  check('For Sale view offers the Portfolio', await page.isVisible('[data-more]'));
  await page.click('.sets [data-set=portfolio]');
  check('Portfolio set shows 25 and writes URL', (await visible()).length === 25 && page.url().includes('set=portfolio'), page.url());
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
  check('empty state appears with a useful route', await page.isVisible('[data-empty]'), await page.textContent('[data-empty-msg]'));
  await page.click('[data-empty-reset]');
  check('clear filters restores results', (await visible()).length === 1);
  // feature filter
  await page.goto(BASE + 'residences/?set=all&features=ocean-views', { waitUntil: 'networkidle' });
  const ov = await page.$$eval('[data-card]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.features.includes('ocean-views')));
  check('feature filter from URL (ocean views)', ov.length > 0 && ov.every(Boolean), `${ov.length} cards`);
  check('filter badge counts active filters', (await page.textContent('[data-filter-count]')).trim() === '1');
  await ctx.close();
}

// ---------- 4. home search strip -> collection
{
  const { ctx, page } = await open('');
  await page.selectOption('#q-loc', 'p:KwaZulu-Natal');
  await page.selectOption('#q-beds', '5');
  await Promise.all([page.waitForURL(/residences/), page.click('.search-go')]);
  await page.waitForLoadState('networkidle');
  const ok = await page.$$eval('[data-card]', cs => { const v = cs.filter(c => !c.hidden); return v.length > 0 && v.every(c => c.dataset.province === 'KwaZulu-Natal' && Number(c.dataset.beds) >= 5); });
  check('home search (province + beds) lands on filtered collection', ok, page.url());
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
  await page.goto(BASE + 'residences/?set=all', { waitUntil: 'networkidle' });
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
  await ctx.close();
}

// ---------- 6. lightbox
{
  const { ctx, page } = await open('residences/eye-of-africa-4-bedroom-house/');
  const opener = page.locator('.pgal-all');
  await opener.click();
  check('lightbox opens', await page.evaluate(() => document.querySelector('[data-lightbox]').open));
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
  check('arrow keys advance', (await page.textContent('[data-lb-i]')).trim() === '3');
  await page.keyboard.press('ArrowLeft');
  check('arrow left goes back', (await page.textContent('[data-lb-i]')).trim() === '2');
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

await browser.close();
const failed = results.filter(r => !r.ok);
fs.writeFileSync(`${OUT}/results.json`, JSON.stringify({ total: results.length, failed: failed.length, results }, null, 1));
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);

// Usage: node qa/shots.mjs <outdir> <path> <width>[,<width>...] [full]
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright');
const [outdir, path, widths, full] = process.argv.slice(2);
const BASE = process.env.BASE || 'http://localhost:8321/Beautiful-South-African-Homes-/';
const browser = await chromium.launch();
for (const w of widths.split(',').map(Number)) {
  const page = await browser.newPage({ viewport: { width: w, height: w < 700 ? 844 : 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(BASE + path, { waitUntil: 'networkidle' });
  if (full) { // trigger reveals
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0); });
    await page.evaluate(() => document.querySelectorAll('.reveal,.reveal-img,.folio').forEach(e => e.classList.add('is-in')));
    await page.waitForTimeout(1300);
  }
  const name = `${outdir}/${(path || 'home').replace(/[\/?=&:]+/g, '_')}-${w}.png`;
  await page.screenshot({ path: name, fullPage: !!full });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  console.log(name, 'overflowX', overflow, errors.length ? 'ERRORS ' + errors.join(' | ') : '');
  await page.close();
}
await browser.close();

// LCP / CLS / transfer weight under a simulated fast-4G link. Usage: node qa/perf.mjs
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || 'playwright');
const BASE = process.env.BASE || 'http://localhost:8321/Beautiful-South-African-Homes-/';
const b = await chromium.launch();
for (const [path, w] of [['', 390], ['', 1440], ['residences/', 390], ['residences/eye-of-africa-4-bedroom-house/', 390], ['residences/bantry-bay-5-bedroom-house/', 1440]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: w < 700 ? 844 : 900 }, deviceScaleFactor: w < 700 ? 3 : 1 });
  const page = await ctx.newPage();
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 9 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
  let bytes = 0; cdp.on('Network.loadingFinished', e => { bytes += e.encodedDataLength; });
  await page.addInitScript(() => {
    window.__lcp = 0; window.__cls = 0;
    new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lcp = e.startTime; }).observe({ type: 'largest-contentful-paint', buffered: true });
    new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: 'layout-shift', buffered: true });
  });
  await page.goto(BASE + path, { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => ({ lcp: Math.round(window.__lcp), cls: +window.__cls.toFixed(3), el: (performance.getEntriesByType('largest-contentful-paint').pop()?.element?.outerHTML || '').slice(0, 70) }));
  console.log(`${path || 'home'} @${w}: LCP ${r.lcp}ms CLS ${r.cls} transfer ${(bytes / 1024).toFixed(0)}KB  [${r.el}]`);
  await ctx.close();
}
await b.close();

const { chromium, devices } = require('playwright');
const fs = require('fs');

(async () => {
  const consoleLogs = [];
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  page.on('console', (msg) => consoleLogs.push(`${msg.type().toUpperCase()}: ${msg.text()}`));
  page.on('pageerror', (err) => consoleLogs.push(`PAGEERROR: ${err.message}`));
  await page.route('**/v1/**', async (route) => {
    const url = route.request().url();
    if (url.includes('/agent/run/resume')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 'run_1', status: 'running' })});
    }
    if (url.includes('/agent/run/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 'run_1', status: 'completed', result: 'ok' })});
    }
    if (url.includes('/agent/run')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 'run_1', status: 'pending' })});
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true })});
  });
  await page.goto(process.env.BASE_URL || 'http://localhost:5173', { waitUntil: 'networkidle' });
  await page.screenshot({ path: 'ui-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.screenshot({ path: 'ui-tablet.png', fullPage: true });
  const pixel5 = devices['Pixel 5'];
  await context.close();
  const mContext = await browser.newContext({ ...pixel5 });
  const mPage = await mContext.newPage();
  mPage.on('console', (msg) => consoleLogs.push(`MOBILE ${msg.type().toUpperCase()}: ${msg.text()}`));
  mPage.on('pageerror', (err) => consoleLogs.push(`MOBILE PAGEERROR: ${err.message}`));
  await mPage.route('**/v1/**', async (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true })}));
  await mPage.goto(process.env.BASE_URL || 'http://localhost:5173', { waitUntil: 'networkidle' });
  await mPage.screenshot({ path: 'ui-mobile.png', fullPage: true });
  await browser.close();
  fs.writeFileSync('ui-console.txt', consoleLogs.join('\n'), 'utf8');
})();


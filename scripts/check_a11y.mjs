import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import puppeteer from 'puppeteer';
import pa11y from 'pa11y';

const fixture = process.argv[2] === '--sequence-fixture';
const publicDir = fixture ? resolve(process.argv[3]) : 'public';
const port = fixture ? 8081 : 8080;
const origin = `http://127.0.0.1:${port}`;
let browserPath = process.env.PUPPETEER_EXECUTABLE_PATH;
if (!browserPath) {
  try { browserPath = puppeteer.executablePath(); } catch { /* Use an installed browser below. */ }
  if ((!browserPath || !existsSync(browserPath)) && process.platform === 'win32') {
    browserPath = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
    if (browserPath) process.env.PUPPETEER_EXECUTABLE_PATH = browserPath;
  }
}

const server = spawn(process.execPath, ['node_modules/http-server/bin/http-server',
  publicDir, '-p', String(port), '-s'], { stdio: 'inherit' });
let serverError;
server.on('error', (error) => { serverError = error; });

function waitForExit(child) {
  return new Promise((resolve) => child.once('exit', resolve));
}

async function waitForServer() {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    if (serverError) throw serverError;
    if (server.exitCode !== null) {
      throw new Error(`Static server exited with status ${server.exitCode}`);
    }
    try {
      const response = await fetch(`${origin}/`);
      if (response.ok) return;
    } catch {
      // The server is still starting.
    }
    await delay(250);
  }
  throw new Error('Static server did not become ready within 30 seconds');
}

async function checkSequence(page, url, viewport) {
  await page.setViewport(viewport);
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  // A controlled clock exercises timer cancellation without wall-clock flakiness.
  await page.evaluateOnNewDocument(() => {
    const pending = new Map();
    let id = 0;
    window.setTimeout = (callback) => { pending.set(++id, callback); return id; };
    window.clearTimeout = (key) => pending.delete(key);
    window.__sequenceClock = {
      size: () => pending.size,
      tick: () => { const callbacks = [...pending.values()]; pending.clear(); callbacks.forEach((callback) => callback()); },
    };
  });
  await page.goto(url, { waitUntil: 'networkidle0' });
  const sequenceCount = await page.$$eval('[data-research-sequence]', (nodes) => nodes.length);
  for (let position = 0; position < sequenceCount; position += 1) {
    // Use an explicit marker so multiple sequences need not share a parent.
    await page.evaluate((index) => {
      document.querySelectorAll('[data-research-sequence]')[index].setAttribute('data-audit-sequence', '');
    }, position);
    const state = () => page.evaluate(() => {
      const sequence = document.querySelector('[data-audit-sequence]');
      const frames = [...sequence.querySelectorAll('[data-sequence-frame]')];
      const button = sequence.querySelector('[data-sequence-control]');
      return { index: frames.findIndex((frame) => !frame.hidden), count: frames.length,
        button: button.textContent, disabled: button.disabled,
        status: sequence.querySelector('[data-sequence-status]').textContent,
        active: [...sequence.querySelectorAll('[data-sequence-step]')].findIndex((step) => step.hasAttribute('aria-current')),
        timers: window.__sequenceClock.size(), overflow: document.documentElement.scrollWidth > window.innerWidth };
    });
    const tick = () => page.evaluate(() => window.__sequenceClock.tick());
    const control = '[data-audit-sequence] [data-sequence-control]';
    let current = await state();
    assert.equal(current.index, current.count - 1, 'Reduced motion starts on the final poster');
    assert.equal(current.disabled, false, 'The enhanced control is available');
    assert.equal(current.timers, 0, 'No automatic playback on initialization');
    assert.equal(current.overflow, false, `${viewport.width}px page must not overflow`);
    await page.focus(control);
    await page.keyboard.press('Space');
    current = await state();
    assert.equal(current.index, 0, 'Space advances a single step in reduced motion');
    assert.equal(current.active, 0, 'Active label follows the displayed frame');
    assert.equal(current.timers, 0, 'Reduced motion never schedules automatic playback');
    await tick();
    assert.equal((await state()).index, 0, 'Reduced motion stays on the chosen frame');
    await page.keyboard.press('Enter');
    assert.equal((await state()).index, 1, 'Enter advances the next labelled step');
    assert.equal(await page.$eval(control, (button) => getComputedStyle(button).outlineStyle), 'solid', 'Keyboard focus is visible');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
    await page.waitForFunction(() => document.querySelector('[data-audit-sequence] [data-sequence-control]').textContent === 'Play sequence');
    assert.equal((await state()).timers, 0, 'Changing preferences does not autoplay');
    await page.keyboard.press('Space');
    assert.equal((await state()).button, 'Pause sequence', 'Play exposes Pause');
    assert.equal((await state()).timers, 1, 'User-triggered Play schedules progression');
    await page.keyboard.press('Space');
    assert.equal((await state()).timers, 0, 'Pause cancels progression');
    await page.keyboard.press('Space');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.waitForFunction(() => document.querySelector('[data-audit-sequence] [data-sequence-control]').textContent === 'Next step');
    assert.equal((await state()).timers, 0, 'Runtime reduced motion cancels playback');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
    await page.waitForFunction(() => document.querySelector('[data-audit-sequence] [data-sequence-control]').textContent === 'Play sequence');
    await page.keyboard.press('Space');
    await page.evaluate(() => {
      Object.defineProperty(document, 'hidden', { configurable: true, value: true });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    assert.equal((await state()).timers, 0, 'Hidden page pauses playback');
    await page.evaluate(() => {
      delete document.hidden;
      document.dispatchEvent(new Event('visibilitychange'));
    });
    assert.equal((await state()).timers, 0, 'Returning to the page does not resume automatically');
    await page.keyboard.press('Space');
    for (let frame = 0; frame < current.count; frame += 1) await tick();
    current = await state();
    assert.equal(current.index, current.count - 1, 'Playback ends on the final frame');
    assert.equal(current.timers, 0, 'Completed playback stops without looping');
    assert.match(current.status, /complete/i, 'Completion is announced');
    await page.keyboard.press('Space');
    assert.equal((await state()).index, 0, 'Play replays from the first frame');
    await page.emulateMediaType('print');
    const print = await page.evaluate(() => {
      const sequence = document.querySelector('[data-audit-sequence]');
      return [...sequence.querySelectorAll('[data-sequence-frame]')].map((frame) => getComputedStyle(frame).display);
    });
    assert.ok(print.slice(0, -1).every((display) => display === 'none'), 'Print hides intermediate frames');
    assert.equal(print.at(-1), 'block', 'Print overrides hidden to show the static final frame');
    assert.equal(await page.$eval('[data-audit-sequence] .research-sequence-controls', (node) => getComputedStyle(node).display), 'none');
    await page.emulateMediaType('screen');
    await page.keyboard.press('Space');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.waitForFunction(() => document.querySelector('[data-audit-sequence] [data-sequence-control]').textContent === 'Next step');
    await page.evaluate(() => document.querySelector('[data-audit-sequence]').removeAttribute('data-audit-sequence'));
  }
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
  await page.reload({ waitUntil: 'networkidle0' });
  assert.equal(await page.evaluate(() => window.__sequenceClock.size()), 0, 'Normal-motion initialization also waits for Play');
  if (process.env.RESEARCH_VISUAL_SCREENSHOTS) {
    await page.screenshot({ path: join(process.env.RESEARCH_VISUAL_SCREENSHOTS, `sequence-${viewport.width}.png`), fullPage: true });
  }
  if (fixture) {
    const audit = await pa11y(url, { browser: page.browser(), viewport,
      standard: 'WCAG2AA', timeout: 60000 });
    assert.deepEqual(audit.issues, [], `Fixture Pa11y issues at ${viewport.width}px: ${JSON.stringify(audit.issues)}`);
  }
}

async function checkSequences() {
  const routes = readdirSync(publicDir, { recursive: true }).filter((path) =>
    path.endsWith('.html') && /<[^>]+data-research-sequence/.test(readFileSync(join(publicDir, path), 'utf8')));
  if (!routes.length) {
    if (fixture) throw new Error('Fixture has no rendered research sequences');
    console.log('No research sequences in current site output; component fixtures cover playback.');
    return;
  }
  const browser = await puppeteer.launch({ executablePath: browserPath,
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  try {
    for (const route of routes) {
      const url = `${origin}/${route.replaceAll('\\', '/')}`;
      const poster = await browser.newPage();
      await poster.setJavaScriptEnabled(false);
      await poster.goto(url, { waitUntil: 'networkidle0' });
      assert.ok(await poster.$$eval('[data-sequence-poster]', (frames) => frames.every((frame) => getComputedStyle(frame).display !== 'none')), 'No-JS final posters remain visible');
      await poster.close();
      for (const viewport of [{ width: 360, height: 800 }, { width: 1440, height: 900 }]) {
        const page = await browser.newPage();
        try { await checkSequence(page, url, viewport); } finally { await page.close(); }
      }
    }
    console.log(`Sequence browser checks passed (${routes.length} routes; 360x800 and 1440x900).`);
  } finally { await browser.close(); }
}

try {
  await waitForServer();
  if (!fixture) {
    const audit = spawn(process.execPath, ['node_modules/pa11y-ci/bin/pa11y-ci.js'],
      { stdio: 'inherit' });
    audit.on('error', (error) => console.error(error));
    const exitCode = await waitForExit(audit);
    if (exitCode !== 0) process.exitCode = exitCode ?? 1;
  }
  await checkSequences();
} catch (error) {
  console.error(error);
  process.exitCode = 1;
} finally {
  if (server.pid && server.exitCode === null) {
    server.kill();
    await waitForExit(server);
  }
}

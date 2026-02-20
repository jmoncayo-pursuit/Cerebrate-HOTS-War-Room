import { isCrawler } from './crawlers.js';
import puppeteer from 'puppeteer';

const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 min
const cache = new Map(); // url -> { html, ts }

/**
 * @param {string} baseUrl - e.g. http://localhost:5173
 * @param {{ ttlMs?: number, skipPaths?: Set<string> }} [opts]
 * @returns {(req: import('http').IncomingMessage, res: import('http').ServerResponse, next: () => void) => void}
 */
export function createPrerenderMiddleware(baseUrl, opts = {}) {
  const ttlMs = opts.ttlMs ?? DEFAULT_TTL_MS;
  const skipPaths = opts.skipPaths ?? new Set(['/api', '/llms.txt', '/sitemap.xml', '/favicon', '/src/', '/@', '/node_modules/']);
  let browser = null;

  async function getBrowser() {
    if (!browser) browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    return browser;
  }

  return function prerenderMiddleware(req, res, next) {
    const ua = req.headers['user-agent'];
    const method = req.method;
    const accept = (req.headers['accept'] || '').toLowerCase();
    if (method !== 'GET' || !accept.includes('text/html') || !isCrawler(ua)) {
      return next();
    }
    const path = req.url?.split('?')[0] || '/';
    if ([...skipPaths].some(p => path.startsWith(p))) return next();

    const fullUrl = baseUrl.replace(/\/$/, '') + (path.startsWith('/') ? path : '/' + path);
    const cached = cache.get(fullUrl);
    if (cached && Date.now() - cached.ts < ttlMs) {
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.setHeader('X-Prerender', 'cache');
      return res.end(cached.html);
    }

    (async () => {
      try {
        const b = await getBrowser();
        const page = await b.newPage();
        await page.goto(fullUrl, { waitUntil: 'networkidle0', timeout: 15000 });
        const html = await page.content();
        await page.close();
        cache.set(fullUrl, { html, ts: Date.now() });
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.setHeader('X-Prerender', 'hit');
        res.end(html);
      } catch (err) {
        console.warn('[prerender]', err?.message || err);
        next();
      }
    })();
  };
}

/**
 * Vite plugin: for requests with crawler User-Agent, serve prerendered HTML via Puppeteer.
 * Requires PRERENDER_DEV=1 to enable in dev (off by default to avoid Puppeteer on every dev start).
 */
export function prerenderPlugin() {
  return {
    name: 'prerender',
    async configureServer(server) {
      if (process.env.PRERENDER_DEV !== '1') return;
      const port = server.config.server.port || 5173;
      const host = server.config.server.host || 'localhost';
      const baseUrl = `http://${host === true ? 'localhost' : host}:${port}`;
      const { createPrerenderMiddleware } = await import('./middleware.js');
      server.middlewares.use(createPrerenderMiddleware(baseUrl));
    },
  };
}

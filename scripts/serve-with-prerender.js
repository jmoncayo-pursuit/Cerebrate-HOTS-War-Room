#!/usr/bin/env node
/**
 * Serve Vite build (dist/) with prerendering for crawler User-Agents.
 * Run after `npm run build`. Port via PORT env (default 5173).
 */
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createPrerenderMiddleware } from './prerender/middleware.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(__dirname, '..', 'dist');
const port = Number(process.env.PORT) || 5173;
const baseUrl = `http://localhost:${port}`;

const app = express();
app.use(createPrerenderMiddleware(baseUrl));
app.use(express.static(dist, { index: false }));
app.get('*', (req, res) => res.sendFile(path.join(dist, 'index.html')));

app.listen(port, () => console.log(`Prerender server http://localhost:${port} (crawlers get pre-rendered HTML)`));

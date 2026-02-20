/** AI and common crawler User-Agent substrings (case-insensitive). */
const CRAWLER_UA_SUBSTRINGS = [
  'gptbot', 'chatgpt-user', 'openai/chatgpt', 'anthropic-ai', 'anthropic/claude',
  'perplexitybot', 'perplexity/', 'google-extended', 'googleother',
  'bingbot', 'microsoft/bing', 'bingpreview', 'cohere-ai', 'cohere-crawler',
  'bytespider', 'baiduspider-render', 'youbot', 'yourbot', 'meta-externalagent',
  'facebookexternalhit', 'twitterbot', 'linkedinbot', 'slurp', 'duckduckbot',
  'prerender', 'bot ', 'crawler', 'spider', 'crawling',
];

/**
 * @param {string} [ua]
 * @returns {boolean}
 */
function isCrawler(ua) {
  if (!ua || typeof ua !== 'string') return false;
  const lower = ua.toLowerCase();
  return CRAWLER_UA_SUBSTRINGS.some(s => lower.includes(s.toLowerCase()));
}

export { isCrawler, CRAWLER_UA_SUBSTRINGS };

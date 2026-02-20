/**
 * WebMCP tool registration for Cerebrate War Room (Imperative API).
 * Aligns with Chrome WebMCP Early Preview and W3C WebMCP draft:
 * - Imperative API: registerTool(name, description, inputSchema, execute)
 * - Secure Context required (HTTPS or http://localhost)
 * - Return shape: { content: [{ type: 'text', text }], isError? }
 * Tools call the same /api as the UI (proxy in dev, same-origin in prod).
 * When navigator.modelContext is available (native or @mcp-b/global), agents
 * can invoke these tools while the user has the War Room open.
 * If you see "listTools is not a function", Chrome's native API may be partial—
 * turn off the "WebMCP for testing" flag to use the polyfill only.
 * @see https://developer.chrome.com/blog/webmcp-epp (Chrome Early Preview)
 * @see https://webmachinelearning.github.io/webmcp (W3C draft)
 * @see https://docs.mcp-b.ai/packages/global (polyfill)
 */

const api = async (path, options = {}) => {
  const res = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } })
  const text = await res.text()
  if (!res.ok) return { error: res.status, message: text || res.statusText }
  try {
    return JSON.parse(text)
  } catch {
    return { raw: text }
  }
}

const text = (content, isError = false) => ({ content: [{ type: 'text', text: typeof content === 'string' ? content : JSON.stringify(content, null, 2) }], isError })

function registerWarRoomTools() {
  try {
    if (!navigator.modelContext || typeof navigator.modelContext.registerTool !== 'function') return []
  } catch (_) {
    return []
  }

  const tools = [
    {
      name: 'cerebrate_health',
      description: 'Check Cerebrate API health and version.',
      inputSchema: { type: 'object', properties: {} },
      async execute() {
        const data = await api('/health')
        return text(data.error ? `Error: ${data.message}` : JSON.stringify(data), !!data.error)
      },
    },
    {
      name: 'cerebrate_match_history',
      description: 'Get the player\'s match history (replays). Optional limit and search query.',
      inputSchema: {
        type: 'object',
        properties: {
          limit: { type: 'number', description: 'Max matches to return (default 100)' },
          search: { type: 'string', description: 'Optional search filter' },
        },
      },
      async execute({ limit = 100, search } = {}) {
        const q = new URLSearchParams({ limit: String(limit), pagination: 'true' })
        if (search) q.set('search', search)
        const data = await api(`/match_history?${q}`)
        if (data.error) return text(`Error: ${data.message}`, true)
        const list = data.matches ?? data
        return text(Array.isArray(list) ? { count: list.length, matches: list.slice(0, 20) } : data)
      },
    },
    {
      name: 'cerebrate_player_profile',
      description: 'Get the current player profile (toon, region, stats summary).',
      inputSchema: { type: 'object', properties: {} },
      async execute() {
        const data = await api('/player_profile')
        return text(data.error ? `Error: ${data.message}` : data, !!data.error)
      },
    },
    {
      name: 'cerebrate_map_stats',
      description: 'Get map performance stats (games, wins, losses, win_rate per map).',
      inputSchema: { type: 'object', properties: {} },
      async execute() {
        const data = await api('/map_stats')
        return text(Array.isArray(data) ? data : (data.error ? `Error: ${data.message}` : data), !!data.error)
      },
    },
    {
      name: 'cerebrate_hero_dossier',
      description: 'Get tactical dossier for a hero (builds, strengths, map fit).',
      inputSchema: {
        type: 'object',
        properties: { hero: { type: 'string', description: 'Hero name (e.g. Kharazim, Stitches)' } },
        required: ['hero'],
      },
      async execute({ hero }) {
        if (!hero) return text('hero is required', true)
        const data = await api(`/hero_dossier?hero=${encodeURIComponent(hero)}`)
        return text(data.error ? `Error: ${data.message}` : data, !!data.error)
      },
    },
    {
      name: 'cerebrate_ask',
      description: 'Ask Cerebrate a natural-language question (draft, strategy, stats). Sends to the War Room AI.',
      inputSchema: {
        type: 'object',
        properties: { question: { type: 'string', description: 'Natural language question' } },
        required: ['question'],
      },
      async execute({ question }) {
        if (!question) return text('question is required', true)
        const data = await api('/chat', { method: 'POST', body: JSON.stringify({ message: question }) })
        if (data.error) return text(`Error: ${data.message}`, true)
        return text(data.response ?? data.reply ?? data)
      },
    },
    {
      name: 'cerebrate_strategies',
      description: 'Get current draft/strategy config (roster constraints, strategies).',
      inputSchema: { type: 'object', properties: {} },
      async execute() {
        const data = await api('/strategies')
        return text(data.error ? `Error: ${data.message}` : data, !!data.error)
      },
    },
  ]

  const regs = []
  for (const t of tools) {
    try {
      const r = navigator.modelContext.registerTool(t)
      if (r && typeof r.unregister === 'function') regs.push(r)
    } catch (_) {
      // Duplicate tool name (Strict Mode remount) or broken native adapter: skip this tool
    }
  }
  return regs
}

export default registerWarRoomTools

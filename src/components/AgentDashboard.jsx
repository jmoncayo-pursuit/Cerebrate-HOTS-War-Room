import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const getAgentIcon = (agentName) => {
  const icons = {
    'ANALYST': '🔍',
    'SCOUT': '🎯',
    'COACH': '📈',
    'TACTICIAN': '⚔️',
    'SOCIAL': '🤝',
    'QUARTERMASTER': '📦'
  }
  return icons[agentName] || '🤖'
}

const AgentCard = ({ agent, active }) => {
  const expertise = Array.isArray(agent.expertise) ? agent.expertise : [agent.expertise]
  const exampleQueries = agent.example_queries || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-black/30 border rounded-xl p-6 transition-all duration-300 ${active
        ? 'border-cyan-500 shadow-[0_0_20px_rgba(6,182,212,0.3)]'
        : 'border-white/10 hover:border-cyan-500/50 hover:shadow-lg'
        }`}
    >
      <div className="flex items-start gap-3 mb-4">
        <span className="text-4xl flex-shrink-0">{getAgentIcon(agent.name)}</span>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-bold text-white break-words leading-tight mb-1">{agent.name}</h3>
          <p className="text-xs text-gray-400 break-words">{agent.role}</p>
        </div>
      </div>

      {expertise.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-cyan-300 mb-2">Expertise:</h4>
          <ul className="space-y-1">
            {expertise.map((skill, idx) => (
              <li key={idx} className="text-xs text-gray-300 pl-2 break-words">• {skill}</li>
            ))}
          </ul>
        </div>
      )}

      {exampleQueries.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-purple-300 mb-2">Example Queries:</h4>
          <ul className="space-y-1">
            {exampleQueries.map((query, idx) => (
              <li key={idx} className="text-xs text-gray-400 italic pl-2 break-words">"{query}"</li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}

const AgentDashboard = () => {
  const [usage, setUsage] = useState(null)
  const [modelHealth, setModelHealth] = useState(null)
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeAgent, setActiveAgent] = useState(null)
  const [testQuery, setTestQuery] = useState('')
  const [routingResult, setRoutingResult] = useState(null)
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null)

  useEffect(() => {
    fetchAgents()
    checkUsage()
    const interval = setInterval(() => {
      checkUsage()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchAgents = () => {
    fetch('/api/cerebrate/agents')
      .then(res => res.json())
      .then(data => {
        setAgents(data.agents || [])
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }

  const checkUsage = async () => {
    try {
      const res = await fetch(`/api/usage?t=${Date.now()}`)
      if (res.ok) {
        const data = await res.json()
        setUsage(data.usage)
        setModelHealth({
          quality: data.model_status,
          last_model: data.last_model
        })
      }
    } catch (e) {
      console.error("Telemetry link failure", e)
    }
  }

  const testRouting = async () => {
    if (!testQuery.trim()) return

    try {
      const response = await fetch('/api/cerebrate/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: testQuery,
          context: {}
        })
      })
      const data = await response.json()
      setRoutingResult(data)
      if (data.orchestrator?.selected_agent) {
        setActiveAgent(data.orchestrator.selected_agent)
      }
      // Re-trigger usage check after query
      checkUsage()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading agent swarm...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <p className="text-red-400 mb-4">Error: {error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-cyan-500/20 text-cyan-300 rounded-lg hover:bg-cyan-500/30"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-6">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Cerebrate Agent Swarm</h1>
            <p className="text-gray-400 italic">Specialized tactical intelligence agents working across the Neural Link</p>
          </div>

          {/* Neural Link Telemetry - COMPREHENSIVE VIEW */}
          {usage && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-black/40 border border-white/10 rounded-2xl p-4 backdrop-blur-md min-w-[300px]"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full animate-pulse ${modelHealth?.quality?.includes('Nexus') ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]' :
                    modelHealth?.quality?.includes('Neural') ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]' :
                      'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]'
                    }`} />
                  <div>
                    <div className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">Neural Link Status</div>
                    <div className={`text-xs font-bold font-mono ${modelHealth?.quality?.includes('Nexus') ? 'text-cyan-400' :
                      modelHealth?.quality?.includes('Neural') ? 'text-blue-400' :
                        'text-green-400'
                      }`}>
                      {modelHealth?.quality} // {modelHealth?.last_model}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">Total Tokens</div>
                  <div className="text-sm font-bold text-white font-mono">{usage.total_tokens?.toLocaleString() || usage.quota?.[Object.keys(usage.quota)[0]]?.used.toLocaleString() || '0'}</div>
                </div>
              </div>

              {/* Nexus Integrity Block (PIPELINE HEALING) */}
              <div className="grid grid-cols-2 gap-2 py-2 border-t border-white/5 mb-2">
                <div className="bg-cyan-500/5 rounded p-2 border border-cyan-500/10">
                  <div className="text-[8px] text-cyan-500/70 font-mono uppercase tracking-tighter">Self-Heal Pipeline</div>
                  <div className="flex items-center gap-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${usage.services?.healer === 'ACTIVE' ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`} />
                    <div className="text-[10px] font-black text-slate-200 font-mono italic">{usage.services?.healer || 'STANDBY'}</div>
                  </div>
                </div>
                <div className="bg-purple-500/5 rounded p-2 border border-purple-500/10">
                  <div className="text-[8px] text-purple-500/70 font-mono uppercase tracking-tighter">Combat Ingestion</div>
                  <div className="flex items-center gap-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${usage.services?.watcher === 'ACTIVE' ? 'bg-purple-400 animate-pulse' : 'bg-slate-600'}`} />
                    <div className="text-[10px] font-black text-slate-200 font-mono italic">{usage.services?.watcher || 'OFFLINE'}</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 py-2 border-t border-white/5">
                <div>
                  <div className="text-[8px] text-slate-600 font-mono uppercase">Prompt</div>
                  <div className="text-[10px] text-blue-400 font-bold font-mono">{usage.prompt_tokens?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div className="text-[8px] text-slate-600 font-mono uppercase">Response</div>
                  <div className="text-[10px] text-green-400 font-bold font-mono">{usage.response_tokens?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div className="text-[8px] text-slate-600 font-mono uppercase">Version</div>
                  <div className="text-[10px] text-cyan-400 font-bold font-mono">{usage.pipeline_version || '2.1.0'}</div>
                </div>
              </div>

              {/* History Sparklines */}
              {usage.history && usage.history.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/5">
                  <div className="text-[8px] text-slate-600 font-mono uppercase mb-2">Neural Pulse History</div>
                  <div className="flex gap-1 h-6 items-end">
                    {usage.history.map((item, i) => (
                      <motion.button
                        key={i}
                        whileHover={{ scale: 1.1, y: -2 }}
                        onClick={() => setSelectedHistoryItem(item)}
                        className={`flex-1 min-w-[4px] rounded-t-sm transition-colors ${item.model?.includes('pro') ? 'bg-blue-500/60 hover:bg-blue-400' :
                          item.model?.includes('2.0') ? 'bg-cyan-500/60 hover:bg-cyan-400' :
                            'bg-slate-500/60 hover:bg-slate-400'
                          }`}
                        style={{ height: `${Math.max(20, Math.min(100, (item.total_t / 2000) * 100))}%` }}
                        title={`${item.total_t} tokens - ${item.model}`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Telemetry Detail Modal */}
        <AnimatePresence>
          {selectedHistoryItem && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="bg-slate-900 border border-white/10 rounded-2xl p-6 max-w-md w-full shadow-2xl"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white">Neural Transaction</h3>
                    <p className="text-xs text-slate-400 font-mono">{new Date(selectedHistoryItem.timestamp * 1000).toLocaleString()}</p>
                  </div>
                  <button
                    onClick={() => setSelectedHistoryItem(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-black/40 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-500 font-mono uppercase mb-1">Model Tier</div>
                    <div className="text-lg font-bold text-cyan-400 font-mono">{selectedHistoryItem.model}</div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-black/20 rounded-lg border border-white/5">
                      <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">Prompt Input</div>
                      <div className="text-lg font-bold text-blue-400 font-mono">{selectedHistoryItem.prompt_t?.toLocaleString()}</div>
                      <div className="text-[10px] text-slate-600">Tokens</div>
                    </div>
                    <div className="p-3 bg-black/20 rounded-lg border border-white/5">
                      <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">AI Response</div>
                      <div className="text-lg font-bold text-green-400 font-mono">{selectedHistoryItem.resp_t?.toLocaleString()}</div>
                      <div className="text-[10px] text-slate-600">Tokens</div>
                    </div>
                  </div>

                  <div className="p-4 bg-cyan-500/10 rounded-xl border border-cyan-500/20 text-center">
                    <div className="text-[10px] text-cyan-300 font-mono uppercase mb-1">Total Payload Cost</div>
                    <div className="text-2xl font-bold text-white font-mono">{selectedHistoryItem.total_t?.toLocaleString()}</div>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedHistoryItem(null)}
                  className="w-full mt-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors font-bold uppercase tracking-widest text-xs"
                >
                  Close Diagnostic
                </button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* Query Routing Test */}
        <div className="mb-8 bg-black/30 border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Test Query Routing</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="Try: 'How do I improve my macro?' or 'Best tank for Dragon Shire?'"
              className="flex-1 px-4 py-2 bg-black/50 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              onKeyPress={(e) => e.key === 'Enter' && testRouting()}
            />
            <button
              onClick={testRouting}
              className="px-6 py-2 bg-cyan-500/20 text-cyan-300 rounded-lg hover:bg-cyan-500/30 transition-colors"
            >
              Route Query
            </button>
          </div>

          {routingResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-cyan-300 font-semibold">Selected Agent:</span>
                <span className="text-white">{routingResult.orchestrator?.selected_agent || 'Unknown'}</span>
              </div>
              {routingResult.orchestrator?.capable_agents?.length > 1 && (
                <div className="text-sm text-gray-400">
                  Also capable: {routingResult.orchestrator.capable_agents.filter(a => a !== routingResult.orchestrator.selected_agent).join(', ')}
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Agent Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {agents.map((agent, idx) => (
              <AgentCard
                key={agent.name}
                agent={agent}
                active={activeAgent === agent.name}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default AgentDashboard

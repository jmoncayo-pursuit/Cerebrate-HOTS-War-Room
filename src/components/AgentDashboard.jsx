import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart3 } from 'lucide-react'

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
    fetch('/api/nexus/agents')
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
        setUsage(data)
        setModelHealth({
          quality: data.link_quality,
          last_model: data.current_model
        })
      }
    } catch (e) {
      console.error("Telemetry link failure", e)
    }
  }

  const testRouting = async () => {
    if (!testQuery.trim()) return

    try {
      const response = await fetch('/api/nexus/ask', {
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
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-white">Agent Routing Debugger</h1>
            <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-lg text-sm font-mono font-bold">DEVELOPMENT ONLY</span>
          </div>
          <p className="text-gray-400 italic">Test query routing and verify which agent handles specific questions. This page is for debugging the multi-agent system.</p>
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

        {/* Agent Grid (Ops link + swarm) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Ops — Token usage and transaction history */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-black/30 border border-cyan-500/30 rounded-xl p-6 transition-all duration-300 hover:border-cyan-500/50 hover:shadow-[0_0_20px_rgba(6,182,212,0.2)]"
          >
            <div className="flex items-start gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center flex-shrink-0">
                <BarChart3 className="w-7 h-7 text-cyan-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold text-white break-words leading-tight mb-1">Ops</h3>
                <p className="text-xs text-gray-400 break-words">Token usage and transaction history</p>
              </div>
            </div>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('nav_to_healer_ops'))}
              className="w-full mt-2 text-xs font-bold uppercase tracking-wider text-cyan-400 hover:text-cyan-300 border border-cyan-500/40 hover:border-cyan-400/60 rounded-lg px-3 py-2 transition-colors"
            >
              View Ops
            </button>
          </motion.div>

          <AnimatePresence>
            {agents.map((agent) => (
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

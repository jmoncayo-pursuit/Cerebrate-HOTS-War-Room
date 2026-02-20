import { useState, useEffect } from 'react'
import { BarChart3 } from 'lucide-react'
import './HealerDevPage.css'

function formatTime(ts) {
  if (!ts) return '—'
  const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function HealerOpsPage() {
  const [usage, setUsage] = useState(null)
  const [apiUp, setApiUp] = useState(true)
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/health')
      setApiUp(res.ok)
    } catch {
      setApiUp(false)
    }
  }

  const fetchUsage = async () => {
    try {
      if (!apiUp) return
      const res = await fetch(`/api/usage?t=${Date.now()}`)
      if (res.ok) setUsage(await res.json())
    } catch {}
  }

  useEffect(() => {
    fetchStatus()
    fetchUsage()
    const t1 = setInterval(fetchStatus, 4000)
    const t2 = setInterval(fetchUsage, 5000)
    return () => {
      clearInterval(t1)
      clearInterval(t2)
    }
  }, [apiUp])

  const history = usage?.history || []
  const quota = usage?.quota || {}
  const remaining = Object.values(quota).reduce((s, v) => s + (v?.remaining ?? 0), 0)

  return (
    <div className="healer-dev-page">
      <div className="healer-dev-overlay" />
      <div className="healer-dev-header">
        <div className="healer-dev-title-row">
          <div className="healer-dev-icon" style={{ background: 'rgba(6, 182, 212, 0.15)', borderColor: 'rgba(6, 182, 212, 0.3)', color: '#06b6d4' }}>
            <BarChart3 size={28} />
          </div>
          <div>
            <h1 className="healer-dev-title">Ops</h1>
            <p className="healer-dev-subtitle">Token usage and transaction history</p>
          </div>
        </div>
      </div>

      {!apiUp && <p className="healer-dev-warn mb-4">API offline — token usage unavailable.</p>}
      {/* Token Usage */}
      <div className="healer-dev-card">
        <h3 className="healer-dev-loop-title">
          <BarChart3 size={16} />
          Token Usage
        </h3>
        {usage ? (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2">
              <div className="p-3 bg-black/30 rounded-lg border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase mb-1">Quota remaining</div>
                <div className="text-xl font-bold text-white font-mono">{remaining.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-black/30 rounded-lg border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase mb-1">Total tokens used</div>
                <div className="text-lg font-bold text-blue-400 font-mono">{(usage.total_tokens ?? 0).toLocaleString()}</div>
              </div>
              <div className="p-3 bg-black/30 rounded-lg border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase mb-1">API calls</div>
                <div className="text-lg font-bold text-green-400 font-mono">{(usage.total_calls ?? 0).toLocaleString()}</div>
              </div>
              <div className="p-3 bg-black/30 rounded-lg border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase mb-1">Status</div>
                <div className="text-sm font-bold text-emerald-400">{usage.link_quality ?? '—'}</div>
              </div>
            </div>
            {history.length > 0 && (
              <div className="mt-4">
                <div className="text-[10px] text-slate-500 font-mono uppercase mb-2">Recent transactions — click to read</div>
                <div className="space-y-2 max-h-[220px] overflow-y-auto custom-scrollbar pr-2">
                  {history.slice(0, 12).map((h, i) => (
                    <button
                      key={i}
                      onClick={() => setSelectedHistoryItem(h)}
                      className="w-full text-left p-2 rounded-lg bg-black/30 border border-white/5 hover:border-cyan-500/30 text-xs flex justify-between items-center gap-3 cursor-pointer"
                    >
                      <span className="text-slate-300 truncate">{(h.model || 'model').replace('models/', '')}</span>
                      <span className="text-slate-500 shrink-0 text-[10px]">{formatTime(h.timestamp)}</span>
                      <span className="text-cyan-400 shrink-0 font-mono">{(h.total_t ?? ((h.prompt_t || 0) + (h.resp_t || 0))).toLocaleString()} tokens</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-slate-500 text-sm mt-2">Loading token usage…</p>
        )}
      </div>

      {/* Transaction detail modal — like pulses before */}
      {selectedHistoryItem && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          onClick={() => setSelectedHistoryItem(null)}
        >
          <div
            className="bg-slate-900 border border-white/10 rounded-xl p-6 max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Transaction details</h3>
                <p className="text-xs text-slate-500 mt-1">
                  {formatTime(selectedHistoryItem.timestamp)} · {(selectedHistoryItem.model || '').replace('models/', '')}
                </p>
              </div>
              <button onClick={() => setSelectedHistoryItem(null)} className="text-slate-400 hover:text-white p-1">✕</button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                <div className="p-3 bg-black/30 rounded-lg text-center">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Prompt tokens</div>
                  <div className="font-bold text-blue-400 font-mono">{(selectedHistoryItem.prompt_t ?? 0).toLocaleString()}</div>
                </div>
                <div className="p-3 bg-black/30 rounded-lg text-center">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Response tokens</div>
                  <div className="font-bold text-green-400 font-mono">{(selectedHistoryItem.resp_t ?? 0).toLocaleString()}</div>
                </div>
                <div className="p-3 bg-cyan-500/10 rounded-lg text-center border border-cyan-500/20">
                  <div className="text-[10px] text-cyan-300 uppercase mb-1">Total</div>
                  <div className="font-bold text-white font-mono">{(selectedHistoryItem.total_t ?? ((selectedHistoryItem.prompt_t || 0) + (selectedHistoryItem.resp_t || 0))).toLocaleString()}</div>
                </div>
              </div>
              {selectedHistoryItem.prompt_text && (
                <div>
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Prompt sent</div>
                  <div className="p-3 bg-black/30 rounded-lg text-xs text-slate-300 font-mono whitespace-pre-wrap break-words max-h-32 overflow-y-auto">{selectedHistoryItem.prompt_text}</div>
                </div>
              )}
              {selectedHistoryItem.response_text && (
                <div>
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Response received</div>
                  <div className="p-3 bg-black/30 rounded-lg text-xs text-slate-300 font-mono whitespace-pre-wrap break-words max-h-40 overflow-y-auto">{selectedHistoryItem.response_text}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Activity, ArrowLeft, Shield, Zap } from 'lucide-react'
import './HealerDevPage.css'

export default function HealerDevPage({ onBack }) {
  const [status, setStatus] = useState({ running: false, last_pulse: null, mode: 'OFFLINE' })
  const [loading, setLoading] = useState(false)
  const [apiUp, setApiUp] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/health')
      setApiUp(res.ok)
      if (!res.ok) return
      const healerRes = await fetch('/api/healer/status')
      if (healerRes.ok) setStatus(await healerRes.json())
    } catch {
      setApiUp(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const t = setInterval(fetchStatus, 3000)
    return () => clearInterval(t)
  }, [])

  const toggle = async () => {
    setLoading(true)
    try {
      await fetch(status.running ? '/api/healer/stop' : '/api/healer/start', { method: 'POST' })
      await fetchStatus()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="healer-dev-page">
      <div className="healer-dev-overlay" />
      <div className="healer-dev-header">
        <button
          type="button"
          onClick={onBack}
          className="healer-dev-back"
          aria-label="Back to Services"
        >
          <ArrowLeft size={18} />
          <span>Services</span>
        </button>
        <div className="healer-dev-title-row">
          <div className="healer-dev-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#10b981' }}>
            <Shield size={28} />
          </div>
          <div>
            <h1 className="healer-dev-title">Cerebrate Healer</h1>
            <p className="healer-dev-subtitle">Self-improving agent · Observe → Diagnose → Repair</p>
          </div>
        </div>
      </div>

      <div className="healer-dev-card">
        <div className="healer-dev-status-row">
          <div className="flex items-center gap-3">
            <div className={`healer-dev-dot ${status.running ? 'running' : 'stopped'}`} />
            <div>
              <div className="healer-dev-mode">{status.running ? status.mode : 'Integrity Guard Offline'}</div>
              {status.running && status.last_pulse && (
                <div className="healer-dev-pulse">
                  <Activity size={12} className="animate-pulse" />
                  Last pulse: {status.last_pulse}
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={toggle}
            disabled={loading || !apiUp}
            className={`healer-dev-btn ${status.running ? 'stop' : 'start'}`}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="healer-dev-spinner" />
                {status.running ? 'Halting…' : 'Deploying…'}
              </span>
            ) : status.running ? (
              'Halt Healer'
            ) : (
              'Turn On Healer'
            )}
          </button>
        </div>
        {!apiUp && (
          <p className="healer-dev-warn">API offline — start the backend to control the Healer.</p>
        )}
      </div>

      <div className="healer-dev-card healer-dev-loop">
        <h3 className="healer-dev-loop-title">
          <Zap size={16} />
          What the Healer does
        </h3>
        <ul className="healer-dev-loop-list">
          <li><strong>Observe</strong> — API health, <code>api_server.log</code> (exceptions), replay DB (drift).</li>
          <li><strong>Neural Reflection</strong> — On traceback, writes a report to <code>.diagnostics/</code> with proposed remedy.</li>
          <li><strong>Data-Centric Evolution</strong> — Compares forensic vs scoreboard kills; sets recalibration flag if drift is high.</li>
          <li><strong>Repair</strong> — Fixes profile wins/losses math, invalid dates, and re-triggers analysis for <code>ANALYSIS FAILED</code> matches.</li>
        </ul>
        <p className="healer-dev-loop-footer">Runs every 1 min (health), 10 min (reflection), 30 min (evolution), 1 h (integrity).</p>
      </div>
    </div>
  )
}

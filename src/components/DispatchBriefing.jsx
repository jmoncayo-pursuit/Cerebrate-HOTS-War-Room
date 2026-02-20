import { useState } from 'react'
import { Satellite } from 'lucide-react'
import QuickStatsPanel from './QuickStatsPanel'
import VerificationModal from './VerificationModal'
import './DispatchBriefing.css'

export default function DispatchBriefing({ onSelectMatch }) {
  const [showVerificationModal, setShowVerificationModal] = useState(false)

  return (
    <div className="briefing-container">

      {/* Header */}
      <div className="cerebrate-header-card shrink-0">
        <div className="flex items-center">
          <div className="header-icon-box">
            <Satellite size={28} />
          </div>
          <div>
            <h1 className="header-title hots-text-glow">
              Performance Overview
            </h1>
            <p className="header-subtitle">
              Overview of your current performance and draft recommendations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap justify-end">
          <button
            onClick={() => setShowVerificationModal(true)}
            className="px-4 py-1.5 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-[10px] font-bold uppercase tracking-widest text-cyan-400 hover:bg-cyan-500/20 transition-all flex items-center gap-2"
          >
            📸 Verify Stats
          </button>
          <span className="text-[10px] text-slate-600 font-mono tracking-widest opacity-60 uppercase">Cerebrate Core v2.5.0</span>
        </div>
      </div>

      <VerificationModal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
        onSuccess={() => {
          window.dispatchEvent(new CustomEvent('profileRefreshed'))
          setShowVerificationModal(false)
        }}
      />

      {/* Primary Intelligence Layer */}
      <QuickStatsPanel onSelectMatch={onSelectMatch} />
    </div >
  )
}

import { useState, useEffect } from 'react'
import { Satellite, Activity } from 'lucide-react'
import QuickStatsPanel from './QuickStatsPanel'
import './DispatchBriefing.css'

export default function DispatchBriefing({ onSelectMatch }) {
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

        <div className="hidden md:flex flex-col items-end gap-2">
          <span className="text-[10px] text-slate-600 font-mono tracking-widest opacity-60 uppercase">Cerebrate Core v2.5.0</span>
        </div>
      </div>

      {/* Primary Intelligence Layer */}
      <QuickStatsPanel onSelectMatch={onSelectMatch} />
    </div >
  )
}

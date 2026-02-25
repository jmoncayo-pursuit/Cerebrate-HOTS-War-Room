import { useState, useEffect, lazy, Suspense } from 'react'
import { useReplayData } from './hooks/useReplayData'
import LoadingSpinner from './components/LoadingSpinner'
import registerWarRoomTools from './webmcp/registerWarRoomTools'

// Lazy load heavy components for code splitting
const AllHeroesGrid = lazy(() => import('./components/AllHeroesGrid'))
const ReplaySelector = lazy(() => import('./components/ReplaySelector'))
const MatchStatsOverlay = lazy(() => import('./components/MatchStatsOverlay'))
const ServicesPanel = lazy(() => import('./components/ServicesPanel'))
const PlayerNetwork = lazy(() => import('./components/PlayerNetwork'))
const WarRoom = lazy(() => import('./pages/WarRoom'))
const DataProvenance = lazy(() => import('./pages/DataProvenance'))
const AgentDashboard = lazy(() => import('./components/AgentDashboard'))
const TemporalAnalysis = lazy(() => import('./components/TemporalAnalysis'))
const CompositionMatrix = lazy(() => import('./components/tactical/CompositionMatrix'))
const DossierHub = lazy(() => import('./pages/DossierHub'))
const DispatchBriefing = lazy(() => import('./components/DispatchBriefing'))
const UnifiedChat = lazy(() => import('./components/UnifiedChat'))
const HealerOpsPage = lazy(() => import('./pages/HealerOpsPage'))

function App() {
  const { matches, heroes, profile, loading, error, refresh, search } = useReplayData()
  const [selectedHeroes, setSelectedHeroes] = useState(() => {
    try {
      const saved = localStorage.getItem('selectedHeroes')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  const [viewMode, setViewMode] = useState('draft')
  const [selectedMap, setSelectedMap] = useState(null)
  const [excludedHeroes, setExcludedHeroes] = useState(() => {
    try {
      const saved = localStorage.getItem('excludedHeroes')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  const [queryContext, setQueryContext] = useState(null)
  const [activeMatchStats, setActiveMatchStats] = useState(null)
  const [serverAvailable, setServerAvailable] = useState(true)
  const [strategies, setStrategies] = useState({})

  // WebMCP: expose War Room tools to browser agents (preview + production-ready)
  useEffect(() => {
    let regs = []
    try {
      regs = registerWarRoomTools().filter((r) => r && typeof r.unregister === 'function')
    } catch (_) {
      regs = []
    }
    return () => regs.forEach((r) => r.unregister())
  }, [])

  useEffect(() => {
    const handleReplayParsed = () => refresh()
    window.addEventListener('replayParsed', handleReplayParsed)

    // Cross-component navigation handlers
    const handleNavToReplay = (e) => {
      const matchId = e.detail;
      const match = matches.find(m => m.id === matchId);
      if (match) {
        setViewMode('replays');
        setActiveMatchStats(match);
      }
    };

    const handleNavToDossier = (e) => {
      setViewMode('dossier-hub');
      // The DossierHub will listen for this event and load the hero
    };

    const handleNavToHealerDev = () => setViewMode('healer-ops');
    const handleNavToHealerOps = () => setViewMode('healer-ops');
    window.addEventListener('nav_to_replay', handleNavToReplay);
    window.addEventListener('nav_to_dossier', handleNavToDossier);
    window.addEventListener('nav_to_healer_dev', handleNavToHealerDev);
    window.addEventListener('nav_to_healer_ops', handleNavToHealerOps);

    return () => {
      window.removeEventListener('replayParsed', handleReplayParsed);
      window.removeEventListener('nav_to_replay', handleNavToReplay);
      window.removeEventListener('nav_to_dossier', handleNavToDossier);
      window.removeEventListener('nav_to_healer_dev', handleNavToHealerDev);
      window.removeEventListener('nav_to_healer_ops', handleNavToHealerOps);
    };
  }, [refresh, matches]);

  useEffect(() => {
    localStorage.setItem('excludedHeroes', JSON.stringify(excludedHeroes))
  }, [excludedHeroes])

  useEffect(() => {
    localStorage.setItem('selectedHeroes', JSON.stringify(selectedHeroes))
  }, [selectedHeroes])

  const loadStrategies = async () => {
    if (!serverAvailable) return
    try {
      const response = await fetch('/api/strategies')
      if (response.ok) {
        const data = await response.json()
        setStrategies(data)
        setServerAvailable(true)
      } else {
        setServerAvailable(false)
      }
    } catch (e) {
      setServerAvailable(false)
    }
  }

  useEffect(() => {
    loadStrategies()
    const interval = setInterval(() => {
      if (serverAvailable) loadStrategies()
    }, 30000)
    return () => clearInterval(interval)
  }, [serverAvailable])

  const handleTileQuery = (context) => {
    setQueryContext(context)
    setTimeout(() => {
      const chatInput = document.querySelector('[data-chat-input]')
      if (chatInput) {
        chatInput.focus()
        chatInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
        <div className="text-slate-400 font-mono tracking-widest text-xs uppercase">Initializing Nexus...</div>
      </div>
    </div>
  )

  if (error) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-red-500 font-bold uppercase tracking-widest">
        Connection Failure: {error}
      </div>
    </div>
  )

  return (
    <div className="h-screen flex flex-col text-white overflow-hidden relative bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="fixed inset-0 opacity-100 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-40 h-40 bg-indigo-500/8 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <header className="border-b border-white/10 p-4 md:p-6 bg-transparent backdrop-blur-xl z-30 flex-shrink-0">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-black bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tighter">
              Cerebrate
            </h1>
            <p className="text-[10px] text-slate-500 uppercase font-mono tracking-[0.2em]">Neural Intelligence Network</p>
          </div>
          <div className="flex flex-wrap gap-1.5 bg-black/40 p-1.5 rounded-xl border border-white/5">
            {[
              { id: 'draft', label: 'Briefing', icon: '🌐', active: 'border-cyan-500/50 bg-cyan-500/10 text-cyan-400' },
              { id: 'arsenal', label: 'War Room', icon: '🎯', active: 'border-red-500/50 bg-red-500/10 text-red-400' },
              { id: 'replays', label: 'Archive', icon: '📂', active: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
              { id: 'players', label: 'Social', icon: '🤝', active: 'border-purple-500/50 bg-purple-500/10 text-purple-400' },
              { id: 'dossier-hub', label: 'Protocols', icon: '📁', active: 'border-slate-500/50 bg-slate-500/10 text-slate-300' },
              { id: 'provenance', label: 'Sources', icon: '📈', active: 'border-indigo-500/50 bg-indigo-500/10 text-indigo-400' },
              { id: 'heroes', label: 'Mastery', icon: '⚔️', active: 'border-amber-500/50 bg-amber-500/10 text-amber-400' },
              { id: 'agents', label: 'Agents', icon: '🤖', active: 'border-purple-500/50 bg-purple-500/10 text-purple-400' },
              { id: 'services', label: 'Services', icon: '⚡', active: 'border-orange-500/50 bg-orange-500/10 text-orange-400' },
              { id: 'healer-ops', label: 'Healer & Ops', icon: '🩺', active: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => setViewMode(btn.id)}
                className={`px-3 py-1.5 rounded-lg font-black text-[10px] uppercase tracking-widest transition-all ${viewMode === btn.id
                  ? `${btn.active} shadow-lg shadow-black/50 border`
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border border-transparent'
                  }`}
              >
                <span>{btn.icon}</span>
                <span className="ml-2 hidden sm:inline">
                  {btn.label}
                  {(btn.id === 'agents' || btn.id === 'heroes') && (
                    <span className="text-[8px] px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded font-mono font-bold ml-1">DEV</span>
                  )}
                </span>
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="flex flex-col md:flex-row flex-1 overflow-hidden relative">
        <main className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar">
          <Suspense fallback={<LoadingSpinner text="Synchronizing..." />}>
            {viewMode === 'draft' && <DispatchBriefing onSelectMatch={setActiveMatchStats} />}
            {viewMode === 'heroes' && (
              <AllHeroesGrid
                selectedHeroes={selectedHeroes}
                onSelectHero={(h) => setSelectedHeroes(prev => prev.includes(h) ? prev.filter(x => x !== h) : [...prev, h])}
                matchHistory={matches}
                excludedHeroes={excludedHeroes}
                onExcludeHeroes={setExcludedHeroes}
              />
            )}
            {viewMode === 'replays' && (
              <ReplaySelector
                onSelectMatch={setActiveMatchStats}
                matches={matches}
                onProcessReplays={refresh}
                onSearch={search}
              />
            )}
            {viewMode === 'players' && <PlayerNetwork />}
            {viewMode === 'arsenal' && <WarRoom selectedMap={selectedMap} setSelectedMap={setSelectedMap} />}
            {viewMode === 'dossier-hub' && <DossierHub />}
            {viewMode === 'provenance' && <DataProvenance />}
            {viewMode === 'agents' && <AgentDashboard />}
            {viewMode === 'services' && <ServicesPanel />}
            {viewMode === 'healer-ops' && <HealerOpsPage />}
          </Suspense>

          {activeMatchStats && (
            <Suspense fallback={<LoadingSpinner text="Retrieving Record..." />}>
              <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
                <MatchStatsOverlay
                  match={activeMatchStats}
                  onClose={() => setActiveMatchStats(null)}
                  onDiscuss={handleTileQuery}
                />
              </div>
            </Suspense>
          )}
        </main>

        <aside className="w-full md:w-[500px] border-t md:border-t-0 md:border-l border-white/10 bg-black/20 flex flex-col shrink-0 h-[400px] md:h-auto">
          <Suspense fallback={<LoadingSpinner text="Neural Link Active..." />}>
            <UnifiedChat
              matches={matches}
              heroes={heroes}
              profile={profile}
              strategies={strategies}
              onStrategyUpdate={loadStrategies}
              selectedHeroes={selectedHeroes}
              onExcludeHeroes={setExcludedHeroes}
              queryContext={queryContext}
              onQueryContextClear={() => setQueryContext(null)}
              isMaximized={true}
              onShowMatchStats={setActiveMatchStats}
              viewMode={viewMode}
            />
          </Suspense>
        </aside>
      </div>
    </div>
  )
}

export default App

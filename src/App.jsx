import { useState, useEffect, lazy, Suspense } from 'react'
import { useReplayData } from './hooks/useReplayData'
import LoadingSpinner from './components/LoadingSpinner'

// Lazy load heavy components for code splitting
const HeroGrid = lazy(() => import('./components/HeroGrid'))
const MatchDetail = lazy(() => import('./components/MatchDetail'))
const UnifiedChat = lazy(() => import('./components/UnifiedChat'))
const DispatchBriefing = lazy(() => import('./components/DispatchBriefing'))
const AllHeroesGrid = lazy(() => import('./components/AllHeroesGrid'))
const ReplaySelector = lazy(() => import('./components/ReplaySelector'))
const MatchStatsOverlay = lazy(() => import('./components/MatchStatsOverlay'))
const ServicesPanel = lazy(() => import('./components/ServicesPanel'))
const PlayerNetwork = lazy(() => import('./components/PlayerNetwork'))
const WarRoom = lazy(() => import('./pages/WarRoom'))
const DataProvenance = lazy(() => import('./pages/DataProvenance'))
const AlphaSpec = lazy(() => import('./pages/AlphaSpec'))
const AgentDashboard = lazy(() => import('./components/AgentDashboard'))
const DraftSimulation = lazy(() => import('./components/DraftSimulation'))

function App() {
  const { matches, heroes, profile, loading, error, refresh } = useReplayData()
  const [selectedHero, setSelectedHero] = useState(null)
  const [selectedMatch, setSelectedMatch] = useState(null)
  const [strategies, setStrategies] = useState({})
  const [viewMode, setViewMode] = useState('draft') // 'draft', 'analytics', 'heroes', or 'replays'
  const [selectedMap, setSelectedMap] = useState(null)
  const [selectedHeroes, setSelectedHeroes] = useState([]) // For draft recommendations
  const [excludedHeroes, setExcludedHeroes] = useState(() => {
    // Load from localStorage
    try {
      const saved = localStorage.getItem('excludedHeroes')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }) // Heroes to hide/exclude
  const [queryContext, setQueryContext] = useState(null) // { type: 'map'|'hero'|'match', item: string, map?: string, match?: object }
  const [selectedReplayMatch, setSelectedReplayMatch] = useState(null) // Selected match for chat discussion
  const [activeMatchStats, setActiveMatchStats] = useState(null) // Global match stats overlay
  const [chatHeight, setChatHeight] = useState('400px') // Resizable chat panel height
  const [isChatMaximized, setIsChatMaximized] = useState(false) // Toggle full height
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 768)
  const [serverAvailable, setServerAvailable] = useState(true) // Track server availability to stop polling when down

  useEffect(() => {
    const handleResize = () => setIsDesktop(window.innerWidth >= 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Listen for replay parsed events and refresh match data
  useEffect(() => {
    const handleReplayParsed = () => {
      refresh()
    }
    window.addEventListener('replayParsed', handleReplayParsed)
    return () => window.removeEventListener('replayParsed', handleReplayParsed)
  }, [refresh])

  // Save excluded heroes to localStorage
  useEffect(() => {
    localStorage.setItem('excludedHeroes', JSON.stringify(excludedHeroes))
  }, [excludedHeroes])

  const handleTileQuery = (context) => {
    setQueryContext(context)
    // Scroll to chat or focus chat input
    setTimeout(() => {
      const chatInput = document.querySelector('[data-chat-input]')
      if (chatInput) {
        chatInput.focus()
        chatInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  // Load strategies on mount and auto-refresh
  const loadStrategies = async () => {
    if (!serverAvailable) return // Don't poll when server is down

    try {
      const response = await fetch('/api/strategies')
      if (response.ok) {
        const data = await response.json()
        setStrategies(data)
        setServerAvailable(true) // Server is up
      } else {
        setServerAvailable(false) // Server returned error
      }
    } catch (e) {
      // Server is down - stop polling
      setServerAvailable(false)
    }
  }

  useEffect(() => {
    loadStrategies()

    // Auto-refresh strategies every 3 seconds, but only if server is available
    const interval = setInterval(() => {
      if (serverAvailable) {
        loadStrategies()
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [serverAvailable])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
          <div className="text-slate-400">Loading War Room...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-obsidian flex items-center justify-center">
        <div className="text-red-danger text-xl">
          Error loading data: {error}
          <div className="text-sm mt-2 text-gray-400">
            Make sure db.json exists. Run: python3 deep_parser.py --directory /path/to/replays
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col text-white overflow-hidden relative bg-gradient-to-b from-slate-950/90 via-slate-900/80 to-slate-950/90">
      {/* Unified nexus void background with particles - shared across all views */}
      <div className="fixed inset-0 opacity-100 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-40 h-40 bg-indigo-500/8 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 right-1/3 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      <header className="border-b border-white/10 p-4 md:p-6 bg-transparent backdrop-blur-xl z-30 flex-shrink-0 relative overflow-hidden">
        {/* Animated gradient glow */}
        <div className="absolute top-0 left-0 w-0.5 h-full bg-gradient-to-b from-cyan-500 via-blue-500 to-purple-500 shadow-[0_0_20px_rgba(6,182,212,0.6)]" style={{ animation: 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}></div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent hots-text-glow">
              Cerebrate
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base tracking-wide font-medium opacity-80">Draft Intelligence</p>
          </div>
          <div className="flex flex-wrap gap-2 bg-[#1e293b]/30 p-1 rounded-full border border-white/5 backdrop-blur-sm">
            {[
              { id: 'draft', label: 'Dashboard', icon: '🌐', activeClass: 'bg-cyan-600/20 text-cyan-400 border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.3)]' },
              { id: 'replays', label: 'Replays', icon: '📂', activeClass: 'bg-emerald-600/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]' },
              { id: 'services', label: 'Services', icon: '⚙️', activeClass: 'bg-orange-600/20 text-orange-400 border-orange-500/30 shadow-[0_0_20px_rgba(249,115,22,0.3)]' },
              { id: 'players', label: 'Social', icon: '🤝', activeClass: 'bg-purple-600/20 text-purple-400 border-purple-500/30 shadow-[0_0_20px_rgba(168,85,247,0.3)]' },
              { id: 'arsenal', label: 'Strategy', icon: '🎯', activeClass: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/30 shadow-[0_0_20px_rgba(234,179,8,0.3)]' },
              { id: 'agents', label: 'Agents', icon: '🤖', activeClass: 'bg-pink-600/20 text-pink-400 border-pink-500/30 shadow-[0_0_20px_rgba(236,72,153,0.3)]' },
              { id: 'live-draft', label: 'Strategic Vision', icon: '👁️', activeClass: 'bg-cyan-600/20 text-cyan-400 border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.3)]' },
              { id: 'provenance', label: 'Sources', icon: '📊', activeClass: 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30 shadow-[0_0_20px_rgba(99,102,241,0.3)]' },
              { id: 'alpha-spec', label: 'Alpha Spec', icon: '👑', activeClass: 'bg-gradient-to-r from-cyan-600/20 to-purple-600/20 text-cyan-400 border-cyan-500/30 shadow-[0_0_20px_rgba(168,85,247,0.3)] animate-pulse' }
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => setViewMode(btn.id)}
                className={`px-4 py-2 rounded-full font-bold text-xs uppercase tracking-widest transition-all duration-300 flex items-center gap-2 ${viewMode === btn.id
                  ? btn.activeClass
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border border-transparent'
                  }`}
              >
                <span>{btn.icon}</span>
                <span className="hidden lg:inline">{btn.label}</span>
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Responsive Layout: Sidebar on Desktop, bottom on mobile */}
      <div className="flex flex-col md:flex-row flex-1 overflow-hidden relative">

        {/* Main Content (Left/Top) */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 relative z-0 custom-scrollbar bg-transparent">
          {viewMode === 'draft' ? (
            <Suspense fallback={<LoadingSpinner text="Loading Dashboard..." />}>
              <DispatchBriefing onSelectMatch={setActiveMatchStats} />
            </Suspense>

          ) : viewMode === 'heroes' ? (
            <Suspense fallback={<LoadingSpinner text="Loading Heroes..." />}>
              <AllHeroesGrid
                onSelectHero={(hero) => {
                  setSelectedHeroes(prev =>
                    prev.includes(hero)
                      ? prev.filter(h => h !== hero)
                      : [...prev, hero]
                  )
                }}
                selectedHeroes={selectedHeroes}
                matchHistory={matches}
                excludedHeroes={excludedHeroes}
                onExcludeHeroes={setExcludedHeroes}
              />
            </Suspense>
          ) : viewMode === 'replays' ? (
            <div className="h-full">
              <Suspense fallback={<LoadingSpinner text="Loading Replays..." />}>
                <ReplaySelector
                  onSelectMatch={setActiveMatchStats}
                  matches={matches}
                  onProcessReplays={refresh}
                />
              </Suspense>
            </div>
          ) : viewMode === 'services' ? (
            <div className="max-w-4xl mx-auto">
              <Suspense fallback={<LoadingSpinner text="Loading Services..." />}>
                <ServicesPanel />
              </Suspense>
            </div>
          ) : viewMode === 'players' ? (
            <div className="h-full overflow-y-auto custom-scrollbar">
              <Suspense fallback={<LoadingSpinner text="Loading Social Network..." />}>
                <PlayerNetwork />
              </Suspense>
            </div>
          ) : viewMode === 'arsenal' ? (
            <div className="h-full overflow-y-auto custom-scrollbar">
              <Suspense fallback={<LoadingSpinner text="Loading Strategy..." />}>
                <WarRoom selectedMap={selectedMap} setSelectedMap={setSelectedMap} />
              </Suspense>
            </div>
          ) : viewMode === 'agents' ? (
            <div className="h-full overflow-y-auto custom-scrollbar">
              <Suspense fallback={<LoadingSpinner text="Loading Agent Swarm..." />}>
                <AgentDashboard />
              </Suspense>
            </div>
          ) : viewMode === 'live-draft' ? (
            <div className="h-full overflow-y-auto custom-scrollbar">
              <Suspense fallback={<LoadingSpinner text="Connecting to Live Draft Nexus..." />}>
                <DraftSimulation />
              </Suspense>
            </div>
          ) : viewMode === 'provenance' ? (
            <div className="h-full overflow-y-auto custom-scrollbar">
              <Suspense fallback={<LoadingSpinner text="Loading Data Sources..." />}>
                <DataProvenance />
              </Suspense>
            </div>
          ) : viewMode === 'alpha-spec' ? (
            <div className="h-full overflow-y-auto custom-scrollbar pr-2">
              <Suspense fallback={<LoadingSpinner text="Accessing Elite Dossier..." />}>
                <AlphaSpec />
              </Suspense>
            </div>
          ) : null}

          {activeMatchStats && (
            <Suspense fallback={<LoadingSpinner text="Loading Match Details..." />}>
              <MatchStatsOverlay
                match={activeMatchStats}
                onClose={() => setActiveMatchStats(null)}
                onDiscuss={handleTileQuery}
                className="fixed inset-y-0 left-0 right-0 md:right-[600px] z-[9999] bg-black/90 backdrop-blur-sm flex items-center justify-center p-4"
              />
            </Suspense>
          )}
        </main>

        {/* Chat Sidebar (Right/Bottom) */}
        <aside
          className="w-full md:w-[600px] border-t md:border-t-0 md:border-l border-white/10 bg-transparent flex flex-col shrink-0 shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-20 h-[400px] md:h-auto transition-all"
        >
          <div className="flex-1 overflow-hidden h-full flex flex-col">
            <Suspense fallback={<LoadingSpinner text="Loading Chat..." />}>
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
                // Sidebar mode = always maximized effectively inside its container
                isMaximized={true}
                onToggleMaximize={() => { }}
                showMaximizeControl={false}
                onShowMatchStats={setActiveMatchStats}
                // Active Site Context
                viewMode={viewMode}
                activeMatch={activeMatchStats}
              />
            </Suspense>
          </div>
        </aside>
      </div>

    </div>
  )
}

export default App

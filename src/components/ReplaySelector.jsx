import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, CheckCircle, AlertTriangle, XCircle, Clock, Calendar, Hash, ChevronRight, Activity, Search } from 'lucide-react'
import HeroPortrait from './HeroPortrait'
import { formatElegantDate } from '../utils/dateUtils'
import BuildDisplay from './BuildDisplay'
import { normalizeHeroName } from '../utils/heroUtils'
import FileProgressBar from './FileProgressBar'
import { useReplayData } from '../hooks/useReplayData'
import VirtualList from './VirtualList'
import './ReplaySelector.css'

export default function ReplaySelector({ onSelectReplay, onProcessReplays, onSelectMatch, matches, onSearch, contained = true }) {
  const PLAYER_NAME = 'CerebrateUser';
  const { heroData, talentMap: talentMapData, talentData, loading: replayLoading, refresh } = useReplayData()
  const [processedMatches, setProcessedMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [fileStatuses, setFileStatuses] = useState({})
  const [sortBy, setSortBy] = useState('date')
  const [sortDir, setSortDir] = useState('desc')
  const [rejectedMatches, setRejectedMatches] = useState([])
  const [showIncompatible, setShowIncompatible] = useState(false)
  const [loadingRejected, setLoadingRejected] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Effect: Sync with external matches or load hook matches
  // Effect: Sync matches from props
  useEffect(() => {
    if (matches) {
      setProcessedMatches(matches)
      setLoading(false)
    }
  }, [matches])

  // Server-side search debounce to find matches beyond the initial 500
  useEffect(() => {
    if (searchTerm === undefined) return;
    const timer = setTimeout(() => {
      if (onSearch) onSearch(searchTerm);
    }, 600);
    return () => clearTimeout(timer);
  }, [searchTerm, onSearch]);

  const loadRejectedMatches = async () => {
    try {
      setLoadingRejected(true)
      const res = await fetch('/api/rejected_replays')
      if (res.ok) {
        const data = await res.json()
        setRejectedMatches(data.rejected || [])
      }
    } catch (e) {
      console.error('Failed to load rejected matches:', e)
    } finally {
      setLoadingRejected(false)
    }
  }

  // Removed loadProcessedMatches as it's now handled by useReplayData hook

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files)
    const validFiles = files.filter(f => f.name.toLowerCase().endsWith('.stormreplay'))

    // Reset statuses for new selection
    const initialStatuses = {}
    validFiles.forEach(f => {
      initialStatuses[f.name] = { status: 'pending', msg: 'Ready to process' }
    })
    setFileStatuses(initialStatuses)
    setSelectedFiles(validFiles)
  }

  const handleProcessSelected = async () => {
    if (selectedFiles.length === 0) return

    setProcessing(true)

    // Refresh matches from hook first
    await refresh();
    const currentMatchIds = new Set(processedMatches.map(m => m.id))

    try {
      for (const file of selectedFiles) {
        // Build initial stages for fancy progress bar
        const stages = {
          file_check: 'active',
          history_match: 'pending',
          completeness: 'pending',
          upload: 'pending',
          done: 'pending'
        };
        const details = {
          file_check: `${(file.size / 1024).toFixed(0)} KB`,
          history_match: 'Searching...',
          completeness: 'Validating...',
          upload: 'Syncing...',
          done: 'Pending'
        };

        setFileStatuses(prev => ({
          ...prev,
          [file.name]: {
            status: 'processing',
            message: 'In Processing',
            filename: file.name,
            timestamp: Date.now() / 1000,
            stages: { ...stages },
            details: { ...details }
          }
        }))

        // Step 1: Neural Match Check
        await new Promise(r => setTimeout(r, 600)); // Dramatic pause
        stages.file_check = 'complete';
        stages.history_match = 'active';
        setFileStatuses(prev => ({
          ...prev,
          [file.name]: { ...prev[file.name], stages: { ...stages } }
        }));

        const formData = new FormData()
        formData.append('file', file)

        try {
          // Step 2 & 3: Telemetry & Ingest
          await new Promise(r => setTimeout(r, 400));
          stages.history_match = 'complete';
          stages.completeness = 'complete';
          stages.upload = 'active';
          setFileStatuses(prev => ({
            ...prev,
            [file.name]: { ...prev[file.name], message: 'Synchronizing...', stages: { ...stages } }
          }));

          const response = await fetch('/api/analyze_replay', {
            method: 'POST',
            body: formData
          })

          if (response.ok) {
            const data = await response.json()
            const matchId = data.id
            const isDuplicate = currentMatchIds.has(matchId)

            stages.upload = 'complete';
            stages.done = 'complete';
            details.done = isDuplicate ? 'Roster Updated' : 'Indexed';

            if (isDuplicate) {
              setFileStatuses(prev => ({
                ...prev,
                [file.name]: {
                  ...prev[file.name],
                  status: 'duplicate',
                  message: 'Updated Analysis',
                  stages: { ...stages },
                  details: { ...details }
                }
              }))
            } else {
              setFileStatuses(prev => ({
                ...prev,
                [file.name]: {
                  ...prev[file.name],
                  status: 'success',
                  message: 'Complete',
                  stages: { ...stages },
                  details: { ...details }
                }
              }))
              currentMatchIds.add(matchId)
            }

            // Refresh match list after successful parse
            if (onProcessReplays) {
              onProcessReplays()
            }
            // Refresh via hook
            if (!matches) {
              refresh()
            }
          } else {
            const err = await response.json()
            stages.upload = 'error';
            details.upload = 'Failed';
            setFileStatuses(prev => ({
              ...prev,
              [file.name]: {
                ...prev[file.name],
                status: 'error',
                message: err.error || 'Failed',
                stages: { ...stages },
                details: { ...details }
              }
            }))
          }
        } catch (e) {
          stages.upload = 'error';
          setFileStatuses(prev => ({
            ...prev,
            [file.name]: {
              ...prev[file.name],
              status: 'error',
              message: e.message,
              stages: { ...stages }
            }
          }))
        }

        // Pacing delay
        await new Promise(r => setTimeout(r, 300))
      }

      await refresh()
      if (onProcessReplays) {
        await onProcessReplays()
      }

    } catch (error) {
      console.error('Critical processing error:', error)
    } finally {
      setProcessing(false)
    }
  }

  // --- UI HELPERS ---

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing': return <div className="animate-spin h-3 w-3 border-2 border-cyan-400 border-t-transparent rounded-full" />
      case 'success': return <CheckCircle size={14} className="text-green-400" />
      case 'duplicate': return <AlertTriangle size={14} className="text-yellow-400" />
      case 'error': return <XCircle size={14} className="text-red-400" />
      default: return <div className="h-3 w-3 rounded-full bg-gray-600" />
    }
  }

  const handleSort = (column) => {
    if (sortBy !== column) {
      setSortBy(column)
      setSortDir('desc')
    } else if (sortDir === 'desc') {
      setSortDir('asc')
    } else {
      setSortBy('date')
      setSortDir('desc')
    }
  }

  const SortableHeader = ({ column, children, className = "" }) => {
    const isActive = sortBy === column
    return (
      <div
        className={`cursor-pointer hover:text-cyan-400 transition-colors flex items-center gap-1 ${className}`}
        onClick={() => handleSort(column)}
      >
        {children}
        {isActive && <span className="text-cyan-400 text-xs">{sortDir === 'desc' ? '↓' : '↑'}</span>}
      </div>
    )
  }

  // Memoized filtered and sorted matches for virtual list
  const filteredAndSortedMatches = useMemo(() => {
    let results = [...processedMatches]

    if (searchTerm) {
      const lowSearch = searchTerm.toLowerCase()
      results = results.filter(m => {
        const heroMatch = m.hero?.toLowerCase().includes(lowSearch)
        const mapMatch = m.map?.toLowerCase().includes(lowSearch)
        const idMatch = (m.id || '').toLowerCase().includes(lowSearch)
        const playerMatch = m.players?.some(p =>
          (p.name || p.player_name || '').toLowerCase().includes(lowSearch)
        )
        return heroMatch || mapMatch || playerMatch || idMatch
      })
    }

    return results.sort((a, b) => {
      let aVal, bVal
      switch (sortBy) {
        case 'result':
          aVal = (a.result === 'WIN' || a.result === true || a.win === true) ? 1 : 0
          bVal = (b.result === 'WIN' || b.result === true || b.win === true) ? 1 : 0
          break
        case 'hero':
          aVal = a.hero || ''
          bVal = b.hero || ''
          return sortDir === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal)
        case 'date':
          aVal = a.timestamp_iso || a.date || ''
          bVal = b.timestamp_iso || b.date || ''
          return sortDir === 'desc' ? (bVal > aVal ? 1 : -1) : (aVal > bVal ? 1 : -1)
        case 'duration':
          const timeToSeconds = (timeStr) => {
            if (!timeStr || timeStr === '--:--') return 0;
            const parts = timeStr.split(':');
            if (parts.length !== 2) return 0;
            return parseInt(parts[0]) * 60 + parseInt(parts[1]);
          };
          const aDuration = a.game_length || a.advanced_stats?.game_length_sec ||
            timeToSeconds((a.players?.find(p => p.name === PLAYER_NAME || p.hero === a.hero) || a.players?.[0] || {}).kv_stats?.time_played);
          const bDuration = b.game_length || b.advanced_stats?.game_length_sec ||
            timeToSeconds((b.players?.find(p => p.name === PLAYER_NAME || p.hero === b.hero) || b.players?.[0] || {}).kv_stats?.time_played);
          aVal = aDuration;
          bVal = bDuration;
          break
        case 'kills':
          const aP = a.players?.find(p => p.name === PLAYER_NAME || p.hero === a.hero) || a.players?.[0] || {}
          const bP = b.players?.find(p => p.name === PLAYER_NAME || p.hero === b.hero) || b.players?.[0] || {}
          aVal = (aP.stats || aP.kv_stats || {}).SoloKill || 0
          bVal = (bP.stats || bP.kv_stats || {}).SoloKill || 0
          break
        case 'xp':
          const aPlayer = a.players?.find(p => p.name === PLAYER_NAME || p.hero === a.hero) || a.players?.[0] || {}
          const bPlayer = b.players?.find(p => p.name === PLAYER_NAME || p.hero === b.hero) || b.players?.[0] || {}
          aVal = (aPlayer.stats || aPlayer.kv_stats || {}).ExperienceContribution || 0
          bVal = (bPlayer.stats || bPlayer.kv_stats || {}).ExperienceContribution || 0
          break
        default:
          aVal = 0
          bVal = 0
      }
      return sortDir === 'desc' ? bVal - aVal : aVal - bVal
    })
  }, [processedMatches, sortBy, sortDir, searchTerm])

  // Render function for virtual list item
  const renderMatchItem = (match, index) => {
    const player = match.players?.find(p => p.name === PLAYER_NAME || p.hero === match.hero) || match.players?.[0] || {};
    const stats = player.stats || player.kv_stats || {};
    const isWin =
      match.result === 'WIN' ||
      match.result === 'Win' ||
      match.result === true ||
      match.win === true;
    const dateStr = formatElegantDate(match.timestamp_iso || match.date);

    const formatDuration = (sec) => {
      if (!sec) return '--:--';
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return `${m}:${s.toString().padStart(2, '0')}`;
    };

    let duration = '--:--';
    if (match.game_length) {
      duration = formatDuration(match.game_length);
    } else if (match.advanced_stats?.game_length_sec) {
      duration = formatDuration(match.advanced_stats.game_length_sec);
    } else if (player.kv_stats?.time_played) {
      duration = player.kv_stats.time_played;
    }

    return (
      <div
        onClick={() => onSelectMatch(match)}
        className="match-row group"
      >
        {/* Outcome */}
        <div className={`text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded w-fit ${isWin ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
          {isWin ? 'VICTORY' : 'DEFEAT'}
        </div>

        {/* Hero & Map */}
        <div className="flex items-center gap-3 min-w-0">
          <div className={`relative w-8 h-8 rounded-lg border overflow-hidden shrink-0 shadow-lg ${isWin ? 'border-cyan-500/40' : 'border-red-500/40'}`}>
            <HeroPortrait heroName={match.hero} size="full" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors truncate">
              {match.hero}
            </span>
            <span className="text-[9px] text-slate-500 truncate uppercase tracking-tight">{match.map}</span>
          </div>
        </div>

        {/* Date */}
        <div className="text-[10px] text-slate-400 font-medium">
          {dateStr}
        </div>

        {/* Duration */}
        <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
          <Clock size={10} className="text-slate-600" />
          {duration}
        </div>

        {/* Kills */}
        <div className="text-[10px] font-bold text-slate-300">
          {stats.SoloKill ?? 0}
        </div>

        {/* Talent Build & Insight */}
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
            {(() => {
              const tiers = [1, 4, 7, 10, 13, 16, 20];
              const builds = tiers.map((tier, i) => {
                const tierId = i + 1;
                let index = stats[`Tier${tierId}Talent`];
                if (!index && player.talents) {
                  const tObj = player.talents[i];
                  if (tObj?.talent_name) {
                    const m = tObj.talent_name.match(/(?:Index|#)\s*(\d+)/i);
                    if (m) index = parseInt(m[1]) + (tObj.talent_name.includes('Index') ? 1 : 0);
                  }
                }
                return index || 0;
              });

              if (builds.every(b => b === 0)) {
                return <span className="text-[9px] text-slate-700 uppercase font-bold tracking-widest">No Data</span>;
              }

              return (
                <BuildDisplay
                  hero={match.hero}
                  buildStr={builds}
                  source="HISTORY"
                  compact={true}
                  heroData={heroData}
                  talentMap={talentMapData}
                  talentData={talentData}
                />
              );
            })()}
          </div>
          {match.analysis?.verdict && !['WIN', 'LOSS', 'VICTORY', 'DEFEAT'].includes(match.analysis.verdict.toUpperCase()) && (
            <div className="text-[9px] text-cyan-400/60 font-medium truncate italic max-w-full">
              {match.analysis.verdict}
            </div>
          )}
        </div>

        {/* Summary Snippet / XP */}
        <div className="text-[10px] text-slate-400/80 group-hover:text-slate-300 transition-colors line-clamp-1 italic">
          {match.analysis?.summary ? match.analysis.summary.substring(0, 100).replace(/\*\*/g, '') + '...' : `XP: ${(stats.ExperienceContribution || 0).toLocaleString()}`}
        </div>

        {/* Arrow */}
        <div className="flex justify-end text-slate-700 group-hover:text-cyan-400 transition-colors transform group-hover:translate-x-1 duration-300">
          <ChevronRight size={14} />
        </div>
      </div>
    )
  }

  return (
    <div className={`replay-container flex flex-col gap-6 ${contained ? 'h-full overflow-hidden' : 'h-auto'}`}>
      <div className="services-overlay" />

      {/* Premium Page Header */}
      <div className="cerebrate-header-card !mb-0 shrink-0">
        <div className="flex items-center">
          <div className="header-icon-box">
            <Activity size={24} />
          </div>
          <div>
            <h1 className="header-title hots-text-glow">Replay Archive</h1>
            <p className="header-subtitle uppercase tracking-widest text-[10px] opacity-70">Storm League Replay Directory · {processedMatches.length} Records</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Search Bar */}
          <div className="relative group/search">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within/search:text-cyan-400 transition-colors">
              <Search size={14} />
            </div>
            <input
              id="replay-search-input"
              name="replay-search-input"
              type="text"
              placeholder="Search Hero, Map, or Player..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-black/40 border border-white/10 rounded-full pl-9 pr-4 py-1.5 text-[11px] w-[220px] focus:w-[300px] focus:outline-none focus:border-cyan-500/50 focus:bg-black/60 transition-all placeholder:text-slate-600 text-slate-200"
            />
          </div>

          <div className="flex bg-black/40 p-1 rounded-full border border-white/5 backdrop-blur-sm mr-2">
            <button
              onClick={() => setShowIncompatible(false)}
              className={`px-4 py-1.5 rounded-full font-bold text-[10px] uppercase tracking-wider transition-all ${!showIncompatible
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-500 hover:text-slate-300'
                }`}
            >
              Verified
            </button>
            <button
              onClick={() => setShowIncompatible(true)}
              className={`px-4 py-1.5 rounded-full font-bold text-[10px] uppercase tracking-wider transition-all ${showIncompatible
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'text-slate-500 hover:text-slate-300'
                }`}
            >
              Rejected
            </button>
          </div>
        </div>
      </div>

      {/* --- MATCH LIST SECTION --- */}
      <div className={`history-card z-10 flex flex-col min-h-0 shrink-0 ${contained ? 'overflow-hidden flex-1' : ''}`}>

        {/* Table Header */}
        {!showIncompatible && (
          <div className="table-header-row shrink-0">
            <SortableHeader column="result">Outcome</SortableHeader>
            <SortableHeader column="hero">Hero / Map</SortableHeader>
            <SortableHeader column="date">Date</SortableHeader>
            <SortableHeader column="duration">Duration</SortableHeader>
            <SortableHeader column="kills">Kills</SortableHeader>
            <div className="text-slate-500">Talent Build / Insights</div>
            <div></div>
          </div>
        )}

        {showIncompatible && (
          <div className="grid grid-cols-[1fr_300px] gap-2 px-6 py-3 bg-amber-900/10 text-[10px] font-bold text-amber-500/70 uppercase tracking-widest border-b border-amber-500/10">
            <div>Replay Filename</div>
            <div>Rejection Reason</div>
          </div>
        )}

        {/* Scrollable List */}
        <div className="overflow-y-auto custom-scrollbar flex-1 bg-black/20">
          {loading || loadingRejected ? (
            <div className="h-full flex flex-col items-center justify-center text-cyan-500/40 gap-4">
              <div className="animate-spin h-8 w-8 border-2 border-current border-t-transparent rounded-full" />
              <div className="text-xs font-black uppercase tracking-widest animate-pulse">Quantum Synchronizing...</div>
            </div>
          ) : showIncompatible ? (
            <div className="divide-y divide-white/5">
              {rejectedMatches.length === 0 ? (
                <div className="h-32 flex items-center justify-center text-slate-600 italic text-sm">No incompatible files detected.</div>
              ) : (
                rejectedMatches.map((rm, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[1fr_300px] gap-2 px-6 py-4 items-center text-xs hover:bg-white/5 transition-colors"
                  >
                    <div className="text-slate-300 font-mono truncate opacity-70">{rm.filename}</div>
                    <div className="text-amber-500 font-bold flex items-center gap-2">
                      <AlertTriangle size={12} />
                      {rm.reason}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : processedMatches.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-50 gap-4">
              <FileText size={48} strokeWidth={1} />
              <p className="font-light tracking-wide">No replays currently indexed.</p>
            </div>
          ) : (
            <VirtualList
              items={filteredAndSortedMatches}
              itemHeight={60}
              containerHeight={600}
              renderItem={renderMatchItem}
              className="custom-scrollbar"
            />
          )}
        </div>
      </div>

      {/* --- UPLOAD SECTION --- */}
      <div className="ingest-panel z-10 shrink-0 flex-col md:flex-row">

        {/* Dropzone */}
        <div className="flex-1 w-full min-w-0">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
              <Upload size={16} className="text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Ingest Replays</h3>
              <p className="text-[10px] text-slate-400 font-mono">DRAG & DROP OR CLICK TO UPLOAD</p>
            </div>
          </div>

          <div className="relative group h-[90px] transition-all duration-300">
            <input
              id="replay-file-upload"
              name="replay-file-upload"
              type="file"
              multiple
              accept=".StormReplay,.stormreplay"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
            />
            <div className="dropzone-area">
              <div className="dropzone-icon">
                <Upload size={32} />
              </div>
              <div className="text-sm font-bold text-slate-300 group-hover:text-white transition-colors">
                {selectedFiles.length > 0
                  ? <span className="text-cyan-400">{selectedFiles.length} FILES QUEUED</span>
                  : 'INITIALIZE UPLOAD SEQUENCE'}
              </div>
              <div className="text-[10px] text-slate-500 mt-2 font-mono uppercase tracking-widest opacity-60">
                .StormReplay Archives Only
              </div>
            </div>
          </div>
        </div>

        {/* Queue Process */}
        {selectedFiles.length > 0 && (
          <div className="w-full md:w-[450px] queue-panel shadow-2xl">
            <div className="queue-header">
              <div className="queue-title">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Ingestion Queue
              </div>
              {!processing && (
                <button
                  onClick={handleProcessSelected}
                  className="process-btn"
                >
                  Execute Analysis
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              {selectedFiles.map((file, idx) => {
                const activity = fileStatuses[file.name] || {
                  status: 'pending',
                  message: 'READY',
                  filename: file.name,
                  timestamp: Date.now() / 1000,
                  stages: {},
                  details: {}
                }
                return (
                  <FileProgressBar
                    key={idx}
                    activity={activity}
                    isWatcherRunning={true}
                  />
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

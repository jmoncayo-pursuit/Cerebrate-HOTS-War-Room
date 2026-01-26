import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from 'lucide-react'
import { formatElegantDate } from '../utils/dateUtils'

export default function MapTrends({ onSelectMatch }) {
    const [matchHistory, setMatchHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [expandedMap, setExpandedMap] = useState(null)

    useEffect(() => {
        fetchMatchHistory()
    }, [])

    const fetchMatchHistory = async () => {
        try {
            // Reduced limit for performance
            const res = await fetch('/api/match_history?limit=100')
            if (res.ok) {
                const history = await res.json()
                setMatchHistory(history)
            }
        } catch (e) {
            console.error('Failed to load match history:', e)
        } finally {
            setLoading(false)
        }
    }

    // Calculate map statistics
    const mapStats = matchHistory.reduce((acc, match) => {
        const map = match.map || 'Unknown'
        if (!acc[map]) {
            acc[map] = {
                wins: 0,
                losses: 0,
                total: 0,
                winRate: 0,
                matches: []
            }
        }

        acc[map].total++
        acc[map].matches.push(match)

        if (match.result === 'WIN') {
            acc[map].wins++
        } else if (match.result === 'LOSS') {
            acc[map].losses++
        }

        acc[map].winRate = acc[map].total > 0
            ? Math.round((acc[map].wins / acc[map].total) * 100)
            : 0

        return acc
    }, {})

    // Sort maps by total games played (descending)
    const sortedMaps = Object.entries(mapStats).sort((a, b) => b[1].total - a[1].total)

    const getTrendIcon = (winRate) => {
        if (winRate >= 55) return <TrendingUp className="text-green-400" size={16} />
        if (winRate <= 45) return <TrendingDown className="text-red-400" size={16} />
        return <Minus className="text-gray-400" size={16} />
    }

    const getWinRateColor = (winRate) => {
        if (winRate >= 55) return 'text-green-400'
        if (winRate <= 45) return 'text-red-400'
        return 'text-yellow-400'
    }

    if (loading) {
        return (
            <div className="bg-md-surface-container rounded-md-xl p-6 shadow-md-elevation-1">
                <div className="text-center text-md-on-surface-variant">Loading map trends...</div>
            </div>
        )
    }

    if (sortedMaps.length === 0) {
        return (
            <div className="bg-md-surface-container rounded-md-xl p-6 shadow-md-elevation-1">
                <div className="text-center text-md-on-surface-variant">No match data available</div>
            </div>
        )
    }

    return (
        <div className="bg-[#0f172a]/60 backdrop-blur-xl rounded-xl border border-white/5 overflow-hidden flex flex-col h-full tile-glow">
            {/* Header */}
            <div className="bg-white/5 px-6 py-4 border-b border-white/5 flex-shrink-0">
                <h2 className="text-xl font-bold flex items-center gap-2 text-slate-100">
                    <TrendingUp size={20} className="text-cyan-400" />
                    Map Performance Trends
                </h2>
                <p className="text-sm mt-1 text-slate-400">Win rates and match history by map</p>
            </div>

            {/* Map List */}
            <div className="divide-y divide-white/5 flex-1 overflow-y-auto min-h-0">
                {sortedMaps.map(([mapName, stats]) => (
                    <div key={mapName} className="hover:bg-white/5 transition-colors">
                        {/* Map Row */}
                        <button
                            onClick={() => setExpandedMap(expandedMap === mapName ? null : mapName)}
                            className="w-full px-6 py-4 flex items-center justify-between gap-4 text-left"
                        >
                            {/* Map Name & Stats */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="font-bold text-slate-200 truncate">{mapName}</span>
                                    {getTrendIcon(stats.winRate)}
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                    <span className="text-slate-400">
                                        {stats.total} {stats.total === 1 ? 'game' : 'games'}
                                    </span>
                                    <span className="text-slate-600">•</span>
                                    <span className={`font-bold ${getWinRateColor(stats.winRate)}`}>
                                        {stats.winRate}% WR
                                    </span>
                                    <span className="text-slate-600">•</span>
                                    <span className="text-green-400">{stats.wins}W</span>
                                    <span className="text-red-400">{stats.losses}L</span>
                                </div>
                            </div>

                            {/* Expand/Collapse Icon */}
                            <div className="flex items-center">
                                {expandedMap === mapName ? (
                                    <ChevronUp size={20} className="text-slate-400" />
                                ) : (
                                    <ChevronDown size={20} className="text-slate-400" />
                                )}
                            </div>
                        </button>

                        {/* Expanded Match List */}
                        {expandedMap === mapName && (
                            <div className="px-6 pb-4 bg-black/20">
                                <div className="text-xs uppercase tracking-wider text-slate-500 mb-2 font-bold pt-4">
                                    Match History ({stats.matches.length})
                                </div>
                                <div className="space-y-2">
                                    {stats.matches.slice(0, 10).map((match, idx) => (
                                        <button
                                            key={idx}
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                if (onSelectMatch) onSelectMatch(match)
                                            }}
                                            className="w-full flex items-center justify-between gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-left border border-transparent hover:border-white/10"
                                        >
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <span className={`px-2 py-1 rounded text-xs font-bold ${match.result === 'WIN'
                                                    ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                                    : 'bg-red-500/10 text-red-400 border border-red-500/20'
                                                    }`}>
                                                    {match.result}
                                                </span>
                                                <span className="font-medium text-slate-300 truncate">{match.hero}</span>
                                                <span className="text-xs text-slate-500 tabular-nums">{formatElegantDate(match.date || match.timestamp_iso)}</span>
                                            </div>
                                            <div className="text-xs text-cyan-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">View →</div>
                                        </button>
                                    ))}
                                    {stats.matches.length > 10 && (
                                        <div className="text-center text-xs text-slate-500 italic pt-2">
                                            + {stats.matches.length - 10} more matches
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

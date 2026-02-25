import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Target, Flame, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { calculateYourStats } from '../utils/statsUtils'
import { normalizeHeroName } from '../utils/heroUtils'
import BuildDisplay from './BuildDisplay'

export default function MetaComparison() {
    const [globalMeta, setGlobalMeta] = useState(null)
    const [yourStats, setYourStats] = useState(null)
    const [verifiedStats, setVerifiedStats] = useState(null)
    const [expandedHero, setExpandedHero] = useState(null)
    const [loading, setLoading] = useState(true)
    const [talentMap, setTalentMap] = useState({})
    const [talentData, setTalentData] = useState({})

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            // Load global meta
            const metaRes = await fetch('/api/data/global_hero_stats_stormleague_plus_talents.json')
            if (metaRes.ok) {
                const metaData = await metaRes.json()
                setGlobalMeta(metaData)
            }

            // Load talent data for BuildDisplay
            const talentMapRes = await fetch('/api/data/talent_id_map.json')
            if (talentMapRes.ok) {
                const mapData = await talentMapRes.json()
                setTalentMap(mapData)
            }

            const talentDataRes = await fetch('/api/data/talents.json')
            if (talentDataRes.ok) {
                const tData = await talentDataRes.json()
                setTalentData(tData)
            }

            // Calculate your stats from match history
            const matchRes = await fetch('/api/match_history?limit=50')
            if (matchRes.ok) {
                const matches = await matchRes.json()

                const profileRes = await fetch('/api/player_profile')
                let profile = null
                if (profileRes.ok) {
                    profile = await profileRes.json()
                    setVerifiedStats(profile)
                }

                const stats = calculateYourStats(matches, profile)
                setYourStats(stats)
            }
        } catch (e) {
            console.error('Failed to load meta comparison:', e)
        } finally {
            setLoading(false)
        }
    }

    const getMetaForHero = (heroName) => {
        if (!globalMeta) return null
        const normalizedInput = normalizeHeroName(heroName)
        return globalMeta.find(h => normalizeHeroName(h.name) === normalizedInput)
    }

    const getPerformanceStatus = (delta) => {
        if (delta > 10) return { label: 'DOMINATING', color: 'text-purple-400', bg: 'bg-purple-500/20', icon: Flame }
        if (delta > 5) return { label: 'CRUSHING', color: 'text-green-400', bg: 'bg-green-500/20', icon: TrendingUp }
        if (delta > 0) return { label: 'ABOVE META', color: 'text-blue-400', bg: 'bg-blue-500/20', icon: Target }
        if (delta > -5) return { label: 'BELOW META', color: 'text-yellow-400', bg: 'bg-yellow-500/20', icon: AlertCircle }
        return { label: 'STRUGGLING', color: 'text-red-400', bg: 'bg-red-500/20', icon: TrendingDown }
    }

    if (loading) {
        return (
            <div className="bg-md-surface-container rounded-md-xl p-6">
                <div className="animate-pulse text-md-on-surface-variant">Loading meta comparison...</div>
            </div>
        )
    }

    if (!yourStats || yourStats.length === 0) {
        return (
            <div className="bg-md-surface-container rounded-md-xl p-6">
                <div className="text-md-on-surface-variant">Play at least 5 games with a hero to see meta comparison</div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <div>
                    <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent flex items-center gap-3">
                        <Target className="text-cyan-400" size={28} />
                        HeroesProfile Comparison
                    </h3>
                    <p className="text-sm text-slate-400 mt-1 font-mono tracking-wide">
                        Your performance vs HeroesProfile Storm League meta
                    </p>
                </div>
            </div>

            {/* Hero Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {yourStats.map((hero) => {
                    let meta = getMetaForHero(hero.hero)

                    // Fallback if global meta is missing (e.g. hero not in cached json)
                    // We still want to show the User's stats and the link.
                    if (!meta) {
                        meta = {
                            name: hero.hero,
                            win_rate: null, // Signal that we don't have this
                            games_played: 0,
                            popularity: 0,
                            pick_rate: 0,
                            ban_rate: 0,
                            change: 0,
                            builds: []
                        }
                    }


                    // Compare S3 WR if available (min 5 games), else Lifetime
                    const userWR = hero.s3.games >= 5 ? hero.s3.wr : hero.lifetime.wr
                    const seasonName = verifiedStats?.active_season?.name || 'SEASON 1'
                    const comparisonLabel = hero.s3.games >= 5 ? seasonName : 'LIFETIME'

                    const delta = meta.win_rate !== null ? userWR - meta.win_rate : null
                    const status = getPerformanceStatus(delta)
                    const StatusIcon = status.icon
                    const isExpanded = expandedHero === hero.hero

                    return (
                        <div
                            key={hero.hero}
                            className={`bg-[#0f172a]/60 backdrop-blur-md rounded-xl border border-white/5 transition-all overflow-hidden hover:border-white/10 ${status.bg} tile-glow`}
                        >
                            {/* Hero Header */}
                            <button
                                onClick={() => setExpandedHero(isExpanded ? null : hero.hero)}
                                className="w-full p-4 hover:bg-white/5 transition-colors"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h4 className="text-xl font-black text-slate-100">{hero.hero}</h4>
                                            <div className={`px-2 py-0.5 rounded text-[10px] font-black tracking-wider uppercase ${status.color} bg-black/40 flex items-center gap-1`}>
                                                <StatusIcon size={12} />
                                                {status.label}
                                            </div>
                                        </div>

                                        {/* Stats Row */}
                                        <div className="grid grid-cols-3 gap-4 text-sm items-center">
                                            {/* Col 1: Current Season + Delta */}
                                            <div className="border-r border-white/10 pr-4">
                                                <div className="text-cyan-400 text-[10px] font-black uppercase tracking-wider mb-2">
                                                    CURRENT SEASON (S3)
                                                </div>
                                                <div className="flex items-center justify-between mb-1">
                                                    {hero.s3.games > 0 ? (
                                                        <span className={`text-xl font-black ${hero.s3.wr >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                            {hero.s3.wr.toFixed(1)}%
                                                        </span>
                                                    ) : (
                                                        <span className="text-xl text-slate-600 italic">--</span>
                                                    )}
                                                    <span className="text-[10px] text-slate-500 font-mono">({hero.s3.games} games)</span>
                                                </div>

                                                {/* S3 Delta */}
                                                <div className="flex items-center gap-2 mt-1">
                                                    {hero.s3.games >= 5 ? (
                                                        meta.win_rate !== null ? (
                                                            <div className={`text-sm font-bold flex items-center gap-1 ${hero.s3.wr - meta.win_rate > 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                                                                {hero.s3.wr - meta.win_rate > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                                                {hero.s3.wr - meta.win_rate > 0 ? '+' : ''}{(hero.s3.wr - meta.win_rate).toFixed(1)}%
                                                            </div>
                                                        ) : (
                                                            <div className="text-[10px] text-slate-500 italic">No HP Data</div>
                                                        )
                                                    ) : (
                                                        <div className="text-[10px] text-slate-600 italic">Need 5 games</div>
                                                    )}
                                                    <span className="text-[9px] text-slate-500 uppercase tracking-wide">vs HP Avg</span>
                                                </div>
                                            </div>

                                            {/* Col 2: Lifetime Stats + Delta */}
                                            <div className="border-r border-white/10 pr-4 pl-2">
                                                <div className="text-purple-400 text-[10px] font-black uppercase tracking-wider mb-2">
                                                    LIFETIME MASTERY
                                                </div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className={`text-xl font-black ${hero.lifetime.wr >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                        {hero.lifetime.wr.toFixed(1)}%
                                                    </span>
                                                    <span className="text-[10px] text-slate-500 font-mono">({hero.lifetime.games} games)</span>
                                                </div>

                                                {/* Delta */}
                                                <div className="flex items-center gap-2 mt-1">
                                                    {meta.win_rate !== null ? (
                                                        <div className={`text-sm font-bold flex items-center gap-1 ${hero.lifetime.wr - meta.win_rate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                            {hero.lifetime.wr - meta.win_rate > 0 ? '+' : ''}{(hero.lifetime.wr - meta.win_rate).toFixed(1)}%
                                                        </div>
                                                    ) : (
                                                        <div className="text-[10px] text-slate-500 italic">No HP Data</div>
                                                    )}
                                                    <div className="text-[9px] text-slate-500 uppercase tracking-wide">vs HP Avg</div>
                                                </div>
                                            </div>

                                            {/* Col 3: Global SL (Source) */}
                                            <div className="pl-2">
                                                <div className="text-slate-500 text-[10px] font-black uppercase tracking-wider mb-2">
                                                    HEROESPROFILE AVG
                                                </div>
                                                <div className="text-2xl font-black text-slate-200">
                                                    {meta.win_rate !== null ? `${meta.win_rate.toFixed(1)}%` : 'N/A'}
                                                </div>
                                                <a
                                                    href={`https://www.heroesprofile.com/Global/Hero?hero=${hero.hero}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="text-[10px] text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1 mt-1 transition-colors"
                                                >
                                                    View on HeroesProfile ↗
                                                </a>
                                                <div className="text-[9px] text-slate-600 mt-0.5">
                                                    {meta.games_played ? `${((meta.games_played ?? 0) / 1000).toFixed(1)}k games analyzed` : 'No data'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="ml-4">
                                        {isExpanded ? <ChevronUp size={20} className="text-md-on-surface-variant" /> : <ChevronDown size={20} className="text-md-on-surface-variant" />}
                                    </div>
                                </div>
                            </button>

                            {/* Expanded Details */}
                            {isExpanded && (
                                <div className="px-4 pb-4 space-y-4 border-t border-md-outline-variant/30">
                                    {/* Meta Stats */}
                                    <div className="pt-4">
                                        <div className="text-xs font-bold text-md-on-surface-variant mb-2">HP STATS</div>
                                        <div className="grid grid-cols-3 gap-2 text-xs">
                                            <div>
                                                <span className="text-slate-500 font-bold uppercase">Popularity:</span>
                                                <span className="ml-2 text-slate-200 font-mono font-bold">{(meta.popularity ?? 0).toFixed(1)}%</span>
                                            </div>
                                            <div>
                                                <span className="text-slate-500 font-bold uppercase">Pick Rate:</span>
                                                <span className="ml-2 text-slate-200 font-mono font-bold">{(meta.pick_rate ?? 0).toFixed(1)}%</span>
                                            </div>
                                            <div>
                                                <span className="text-slate-500 font-bold uppercase">Ban Rate:</span>
                                                <span className="ml-2 text-slate-200 font-mono font-bold">{(meta.ban_rate ?? 0).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Top Builds */}
                                    <div>
                                        <div className="text-xs font-bold text-md-on-surface-variant mb-2">TOP 3 HEROESPROFILE BUILDS</div>
                                        <div className="space-y-2">
                                            {meta.builds && Array.isArray(meta.builds) ? meta.builds.slice(0, 3).map((build, idx) => (
                                                <div key={idx} className="bg-md-surface-container-high rounded-lg p-2">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-xs font-black text-cyan-400">#{idx + 1}</span>
                                                        <div className="flex items-center gap-3">
                                                            <span className="text-[10px] text-slate-500 font-mono uppercase">{(build.games ?? 0)} games</span>
                                                            <span className={`text-sm font-bold ${(build.win_chance ?? 0) > 55 ? 'text-green-400' : (build.win_chance ?? 0) > 50 ? 'text-blue-400' : 'text-slate-300'}`}>
                                                                {(build.win_chance ?? 0).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="mt-1">
                                                        <BuildDisplay
                                                            hero={hero.hero}
                                                            buildStr={build.talent_code || ''}
                                                            source="META"
                                                            compact={true}
                                                            talentMap={talentMap}
                                                            talentData={talentData}
                                                        />
                                                    </div>
                                                </div>
                                            )) : (
                                                <div className="text-xs text-slate-500 italic">No build data available</div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Recommendation */}
                                    <div className={`rounded-lg p-3 bg-black/20 border border-white/5`}>
                                        <div className="text-[10px] font-black text-cyan-400 uppercase tracking-widest mb-1 flex items-center gap-2">
                                            <Flame size={12} /> Strategic Recommendation
                                        </div>

                                        {/* Show player's current build */}
                                        {verifiedStats?.talent_builds?.[hero.hero] && (() => {
                                            const builds = verifiedStats.talent_builds[hero.hero]
                                            let mostPlayed = null
                                            let maxGames = 0

                                            Object.entries(builds).forEach(([buildStr, buildData]) => {
                                                if (buildData.games > maxGames && buildStr.length >= 7) {
                                                    maxGames = buildData.games
                                                    mostPlayed = { build: buildStr, ...buildData }
                                                }
                                            })

                                            if (mostPlayed) {
                                                return (
                                                    <div className="mb-3 pb-3 border-b border-white/10">
                                                        <div className="text-[10px] text-slate-400 mb-1">
                                                            Your Build: <span className="text-slate-200">{mostPlayed.wr.toFixed(1)}% WR</span> ({mostPlayed.games} games)
                                                        </div>
                                                        <BuildDisplay
                                                            hero={hero.hero}
                                                            buildStr={mostPlayed.build}
                                                            source="LIFETIME"
                                                            compact={true}
                                                            talentMap={talentMap}
                                                            talentData={talentData}
                                                        />
                                                    </div>
                                                )
                                            }
                                        })()}

                                        <div className="text-xs text-slate-300 leading-relaxed font-medium">
                                            {delta > 10 && `🔥 You're crushing it! Keep playing ${hero.hero} - your build is working!`}
                                            {delta > 5 && delta <= 10 && `✅ Great performance! Consider trying the #1 HP build to optimize further.`}
                                            {delta > 0 && delta <= 5 && `✅ Above average. Compare your build to top 3 HP builds.`}
                                            {delta > -5 && delta <= 0 && `⚠️ Slightly below meta. Try switching to build #1 above.`}
                                            {delta <= -5 && `❌ Underperforming. Switch to build #1 for 10 games or consider dropping this hero.`}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div >
    )
}

import { useState, useEffect } from 'react'
import { BarChart3 } from 'lucide-react'
import { calculateYourStats } from '../utils/statsUtils'
import BuildDisplay from './BuildDisplay'
import { normalizeHeroName } from '../utils/heroUtils'
import ConfidenceScore from './ConfidenceScore'

export default function QuickSummaryTile({ matches, profile, talentMap }) {

    const [globalMeta, setGlobalMeta] = useState(null)
    const [yourStats, setYourStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [isEmergencyBaseline, setIsEmergencyBaseline] = useState(false)

    useEffect(() => {
        const loadData = async () => {
            try {
                const metaRes = await fetch('/api/data/global_hero_stats_stormleague_plus_talents.json')
                let metaData = []
                if (metaRes.ok) {
                    metaData = await metaRes.json()
                    setGlobalMeta(metaData)
                    // Check if using emergency baseline (all heroes at 50%)
                    const isBaseline = metaData.length > 0 && metaData.every(h => h.win_rate === 50.0)
                    setIsEmergencyBaseline(isBaseline)
                } else {
                    console.error("Failed to load global meta stats", metaRes.status)
                    // Fallback to empty to allow rendering personal stats
                    setGlobalMeta([])
                    setIsEmergencyBaseline(true)
                }

                // Use prop profile
                const stats = calculateYourStats(matches, profile)
                setYourStats(stats)
            } catch (e) {
                console.error('QuickSummaryTile failed to load:', e)
                setGlobalMeta([]) // Fallback
            } finally {
                setLoading(false)
            }
        }
        if (profile) loadData()
    }, [matches, profile])

    if (loading) {
        return (
            <div className="stats-card recent h-full tile-glow">
                <div className="card-header">
                    <BarChart3 size={18} className="text-blue-400 opacity-50" />
                    <h4 className="card-title text-blue-400 opacity-50">Quick Summary</h4>
                </div>
                <div className="space-y-3">
                    {/* Shimmer skeleton */}
                    <div className="relative overflow-hidden bg-white/5 h-4 rounded animate-pulse">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
                    </div>
                    <div className="relative overflow-hidden bg-white/5 h-4 rounded animate-pulse w-3/4">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
                    </div>
                    <div className="relative overflow-hidden bg-white/5 h-4 rounded animate-pulse w-1/2">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
                    </div>
                </div>
            </div>
        )
    }

    if (!yourStats) return null;

    const getMetaForHero = (heroName) => {
        const normalizedInput = normalizeHeroName(heroName)
        return globalMeta.find(h => normalizeHeroName(h.name) === normalizedInput)
    }

    // Helper to find best meta build (always return highest WR, no threshold)
    const getBestMetaBuild = (meta) => {
        if (!meta || !meta.builds || meta.builds.length === 0) return null

        // Find highest WR build (removed 50% threshold)
        let best = null
        for (const b of meta.builds) {
            if (!best || b.win_chance > best.win_chance) {
                best = b
            }
        }
        return best
    }

    // Helper to find best build (Personal > Meta, always return something)
    const getBestBuild = (heroName, meta) => {
        // Try Personal -> return bestP if > 50%
        if (profile?.talent_builds?.[heroName]) {
            const builds = profile.talent_builds[heroName]
            let bestP = null
            let maxScore = -1

            Object.entries(builds).forEach(([bStr, bData]) => {
                // Skips shorter builds, but we now ALLOW 'Talent Index' if it's a good build
                if (bStr.includes('-') && bStr.split('-').length < 7) return

                const score = (bData.games * 10) + (bData.wr / 10)
                if (score > maxScore) {
                    maxScore = score
                    bestP = { build: bStr, wr: bData.wr, games: bData.games, source: 'Personal History' }
                }
            })
            // Only recommend Personal if it's actually winning (>50%)
            if (bestP && bestP.wr > 50.0) return bestP
        }

        // Fallback Meta - always return meta build if available, even if < 50%
        if (meta && meta.builds && meta.builds.length > 0) {
            // Find highest WR build (remove 50% threshold)
            let metaBest = null
            for (const b of meta.builds) {
                if (!metaBest || b.win_chance > metaBest.win_chance) {
                    metaBest = b
                }
            }
            if (metaBest) {
                return {
                    build: metaBest.talent_code,
                    wr: metaBest.win_chance,
                    source: 'Global Meta'
                }
            }
        }
        return null
    }

    // Helper for Fix or Drop - shows builds even if WR is low
    const getBuildForFix = (heroName, meta) => {
        // Try Personal first - show most-played build regardless of WR
        if (profile?.talent_builds?.[heroName]) {
            const builds = profile.talent_builds[heroName]
            let bestP = null
            let maxGames = -1

            Object.entries(builds).forEach(([bStr, bData]) => {
                if (bStr.includes('-') && bStr.split('-').length < 7) return

                if (bData.games > maxGames) {
                    maxGames = bData.games
                    bestP = { build: bStr, wr: bData.wr, games: bData.games, source: 'Your Current Build' }
                }
            })
            if (bestP) return bestP
        }

        // Fallback to Meta
        if (meta && meta.builds && meta.builds.length > 0) {
            const metaBest = meta.builds[0]
            return {
                build: metaBest.talent_code,
                wr: metaBest.win_chance,
                source: 'Try Meta Build',
                games: metaBest.games
            }
        }
        return null
    }

    const spamHeroes = yourStats.filter((h) => {
        const meta = getMetaForHero(h.hero)
        return meta && (h.s3.games >= 5 ? h.s3.wr : h.lifetime.wr) - meta.win_rate > 0
    }).slice(0, 4)

    const fixHeroes = yourStats.filter((h) => {
        const meta = getMetaForHero(h.hero)
        const userWR = h.s3.games >= 5 ? h.s3.wr : h.lifetime.wr
        return meta && (userWR - meta.win_rate) < -3
    }).slice(0, 2)

    return (
        <div className="stats-card recent h-full tile-glow">
            <div className="card-header">
                <BarChart3 size={18} className="text-blue-400" />
                <h4 className="card-title text-blue-400">Quick Summary</h4>
            </div>

            {/* Data Source Attribution */}
            <div className="mb-3 pb-2 border-b border-white/5">
                <div className="text-[10px] text-slate-400 flex items-center gap-2">
                    <span className="opacity-60">Data Source:</span>
                    <span className="text-cyan-300">{yourStats[0]?.source || 'Match History'}</span>
                    {isEmergencyBaseline && (
                        <span className="text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">
                            vs Baseline (50%)
                        </span>
                    )}
                    {!isEmergencyBaseline && globalMeta?.length > 0 && (
                        <span className="text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/30">
                            vs Real Meta
                        </span>
                    )}
                </div>
            </div>

            <div className="space-y-4">
                {/* Spam These */}
                <div>
                    <div className="text-sm font-semibold text-orange-400 mb-2 flex items-center gap-1">
                        🔥 Spam These:
                    </div>
                    {spamHeroes.length > 0 ? (
                        <div className="space-y-2">
                            {spamHeroes.map(h => {
                                const meta = getMetaForHero(h.hero)
                                const userWR = h.s3.games >= 5 ? h.s3.wr : h.lifetime.wr
                                const delta = userWR - meta.win_rate
                                const isDependent = h.mapStats?.isMapDependent
                                const recBuild = getBestBuild(h.hero, meta)

                                return (
                                    <div key={h.hero} className="text-xs">
                                        <div className="flex items-baseline gap-1 mb-1">
                                            <span className="text-slate-200">• {h.hero}:</span>
                                            <ConfidenceScore
                                                value={userWR.toFixed(1)}
                                                n={h.s3.games >= 5 ? h.s3.games : h.lifetime.games}
                                                className="scale-75 origin-left"
                                            />
                                            <span className="text-slate-400">
                                                (+{delta.toFixed(1)}% vs Global)
                                            </span>
                                        </div>

                                        {/* Game count and role */}
                                        <div className="ml-3 text-[10px] text-slate-400 flex items-center gap-1.5 mb-1">
                                            <span>{h.s3.games >= 5 ? h.s3.games : h.lifetime.games} games</span>
                                            {h.role && (
                                                <>
                                                    <span className="w-0.5 h-0.5 rounded-full bg-white/20"></span>
                                                    <span>{h.role}</span>
                                                </>
                                            )}
                                        </div>

                                        {/* Map Specific Badge */}
                                        {isDependent && h.mapStats?.bestMaps?.length > 0 && (
                                            <div className="ml-3 mb-1 text-[10px] text-amber-300">
                                                Best: {h.mapStats.bestMaps.map(m => `${m.name} (${m.wr.toFixed(0)}%)`).join(', ')}
                                            </div>
                                        )}

                                        {/* Build Display - Always show if available */}
                                        {recBuild ? (
                                            <div className="ml-3">
                                                <div className="text-xs text-slate-200 mb-0.5">
                                                    <span className="text-cyan-200">{recBuild.source}</span> <span className="opacity-50">•</span> <span className="text-slate-200">{recBuild.wr.toFixed(1)}% Build WR</span>
                                                    {recBuild.games && (
                                                        <> <span className="opacity-50">•</span> <span className="text-slate-300">{recBuild.games} Games</span></>
                                                    )}
                                                </div>
                                                <BuildDisplay
                                                    hero={h.hero}
                                                    buildStr={recBuild.build}
                                                    source={recBuild.source === 'Personal History' ? 'LIFETIME' : 'META'}
                                                    talentMap={talentMap}
                                                    compact={true}
                                                />
                                            </div>
                                        ) : (
                                            <div className="ml-3 text-[10px] text-slate-500 italic">
                                                No build data available
                                            </div>
                                        )}

                                        {isDependent && (
                                            <div className="ml-3 mt-1">
                                                <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30 font-bold uppercase">
                                                    Map Specific
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500 italic pl-3">No standout heroes found yet. Keep playing!</div>
                    )}
                </div>

                {/* Fix or Drop */}
                <div>
                    <div className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-1">
                        ⚠️ Fix or Drop:
                    </div>
                    {fixHeroes.length > 0 ? (
                        <div className="space-y-2">
                            {fixHeroes.map(h => {
                                const meta = getMetaForHero(h.hero)
                                const userWR = h.s3.games >= 5 ? h.s3.wr : h.lifetime.wr
                                const delta = userWR - meta.win_rate
                                const topBuild = getBuildForFix(h.hero, meta)

                                return (
                                    <div key={h.hero} className="text-xs">
                                        <div className="flex items-baseline gap-1 mb-1">
                                            <span className="text-slate-200">• {h.hero}:</span>
                                            <ConfidenceScore
                                                value={userWR.toFixed(1)}
                                                n={h.s3.games >= 5 ? h.s3.games : h.lifetime.games}
                                                className="scale-75 origin-left"
                                            />
                                            <span className="text-slate-400">
                                                ({delta.toFixed(1)}% vs Global)
                                            </span>
                                        </div>

                                        {/* Game count and role */}
                                        <div className="ml-3 text-[10px] text-slate-400 flex items-center gap-1.5 mb-1">
                                            <span>{h.s3.games >= 5 ? h.s3.games : h.lifetime.games} games</span>
                                            {h.role && (
                                                <>
                                                    <span className="w-0.5 h-0.5 rounded-full bg-white/20"></span>
                                                    <span>{h.role}</span>
                                                </>
                                            )}
                                        </div>

                                        {topBuild ? (
                                            <>
                                                <div className="ml-3 text-[10px] text-slate-400 mb-1">
                                                    {topBuild.source}: <span className="text-slate-200">{topBuild.wr.toFixed(1)}% WR</span>
                                                    {topBuild.games && <span className="text-slate-500"> ({topBuild.games} games)</span>}
                                                </div>
                                                <div className="ml-3">
                                                    <BuildDisplay
                                                        hero={h.hero}
                                                        buildStr={topBuild.build}
                                                        source={topBuild.source.includes('Your') ? 'LIFETIME' : 'META'}
                                                        talentMap={talentMap}
                                                        compact={true}
                                                    />
                                                </div>
                                            </>
                                        ) : (
                                            <div className="ml-3 text-[10px] text-slate-500 italic">
                                                No meta build data available
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <div className="text-xs text-slate-500 italic pl-3">No critical underperformers detected.</div>
                    )}
                </div>
            </div>
        </div>
    )
}

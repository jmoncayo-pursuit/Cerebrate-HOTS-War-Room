import { useState, useEffect } from 'react'
import BuildDisplay from './BuildDisplay'
import ConfidenceScore from './ConfidenceScore'

export default function AvoidFixHeroCard({ hero, profile, heroData, talentMap, talentData }) {
    const [topBuilds, setTopBuilds] = useState([])

    useEffect(() => {
        const loadBuild = async () => {
            const builds = profile?.talent_builds?.[hero.hero] || {}
            let scoredBuilds = []

            Object.entries(builds).forEach(([buildStr, buildData]) => {
                // Ignore defective builds
                if (buildStr.includes('Talent Index')) return
                // Enforce completeness
                if (buildStr.length < 7) return

                // Score logic: heavily weight games, but let WR tiebreak
                const score = (buildData.games * 10) + (buildData.wr / 10)
                scoredBuilds.push({
                    build: buildStr,
                    stats: buildData,
                    score
                })
            })

            scoredBuilds.sort((a, b) => b.score - a.score)

            // Get top build
            let finalBuilds = [scoredBuilds[0]].filter(Boolean)

            // Fallback to meta if no personal builds
            if (finalBuilds.length === 0) {
                try {
                    const metaRes = await fetch('/api/data/global_hero_stats_stormleague_plus_talents.json')
                    if (metaRes.ok) {
                        const metaData = await metaRes.json()
                        const heroMeta = metaData.find(h => h.name.toLowerCase() === hero.hero.toLowerCase())
                        if (heroMeta && heroMeta.builds && heroMeta.builds.length > 0) {
                            const topBuild = heroMeta.builds[0]
                            finalBuilds.push({
                                build: topBuild.talent_code,
                                stats: { wr: topBuild.win_chance, games: topBuild.games },
                                isMeta: true
                            })
                        }
                    }
                } catch (e) {
                    console.error('Failed to load meta build:', e)
                }
            }

            setTopBuilds(finalBuilds)
        }

        loadBuild()
    }, [hero, profile])

    const delta = (hero.season_wr - hero.lt_wr).toFixed(1)
    const deltaColor = delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-slate-400'

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <span className="text-md-on-surface font-semibold">{hero.hero}</span>
                <div className="text-right">
                    <div className="flex items-center justify-end gap-2">
                        {hero.lt_wr > 0 && (
                            <span className={`${deltaColor} text-[10px] font-bold`}>
                                {delta > 0 ? '+' : ''}{delta}%
                            </span>
                        )}
                        <ConfidenceScore
                            value={hero.season_wr}
                            n={hero.season_games}
                            className="scale-75 origin-right"
                        />
                    </div>
                    <div className="text-[9px] text-slate-500 uppercase flex items-center justify-end gap-1">
                        S3 WR {hero.lt_wr > 0 && <span className="opacity-50">vs {hero.lt_wr}% LT</span>}
                    </div>
                </div>
            </div>

            <div className="text-xs text-md-on-surface-variant flex items-center gap-1.5">
                <span>{hero.season_games} games</span>
                <span className="w-1 h-1 rounded-full bg-white/20"></span>
                <span>{hero.role}</span>
                <span className="w-1 h-1 rounded-full bg-white/20"></span>
                <span className="text-[10px] text-red-400/60">Season 3 2025</span>
            </div>

            {hero.fix && (
                <div className="text-[11px] text-orange-300 italic border-l-2 border-red-500/30 pl-2">
                    {hero.fix}
                </div>
            )}

            {/* Display build if available */}
            <div className="space-y-2 mt-1">
                {topBuilds.length > 0 && (
                    <div className="bg-black/20 rounded p-1.5 border border-white/5">
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-70">
                                {topBuilds[0].isMeta ? 'Try Meta Build' : 'Your Build'}
                            </span>
                            <span className="text-[10px] text-slate-400">
                                <ConfidenceScore
                                    value={Number(topBuilds[0].stats.wr).toFixed(1)}
                                    n={topBuilds[0].stats.games || 0}
                                    className="scale-[0.6] origin-right"
                                />
                            </span>
                        </div>
                        <BuildDisplay
                            hero={hero.hero}
                            buildStr={topBuilds[0].build}
                            source={topBuilds[0].isMeta ? 'META' : 'LIFETIME'}
                            compact={true}
                            heroData={heroData}
                            talentMap={talentMap}
                            talentData={talentData}
                        />
                    </div>
                )}
            </div>

            {/* Legacy spec_context support */}
            {hero.spec_context && hero.spec_context.match(/\(T([0-9]+)\)/) && (
                <div className="mt-1">
                    <div className="text-[10px] text-orange-300 italic mb-0.5">
                        {hero.spec_context.replace(/\s*\(T[0-9]+\)/, '')}
                    </div>
                    <div className="bg-black/20 rounded p-1 border border-white/5 w-fit">
                        <BuildDisplay
                            hero={hero.hero}
                            buildStr={hero.spec_context.match(/\(T([0-9]+)\)/)[1]}
                            source="META"
                            compact={true}
                            heroData={heroData}
                            talentMap={talentMap}
                            talentData={talentData}
                        />
                    </div>
                </div>
            )}

            {hero.map_context && (
                <div className="text-[10px] text-orange-200/60 mt-0.5">
                    Problem Maps: {hero.map_context}
                </div>
            )}
        </div>
    )
}

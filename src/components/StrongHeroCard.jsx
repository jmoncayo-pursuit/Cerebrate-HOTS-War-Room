import { useState, useEffect } from 'react'
import BuildDisplay from './BuildDisplay'

export default function StrongHeroCard({ hero, profile, heroData, talentMap, talentData }) {
    const [topBuilds, setTopBuilds] = useState([])
    const [showSecondary, setShowSecondary] = useState(false)

    useEffect(() => {
        const loadBuild = async () => {
            const builds = profile?.talent_builds?.[hero.hero] || {}
            let scoredBuilds = []

            Object.entries(builds).forEach(([buildStr, buildData]) => {
                // 1. Ignore defective builds
                if (buildStr.includes('Talent Index')) return

                // 2. Enforce Completeness (Must have 7 tiers)
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

            // Primary is always #1
            // Secondary is #2 ONLY if WR >= 50%
            let finalBuilds = [scoredBuilds[0]].filter(Boolean)

            if (scoredBuilds.length > 1) {
                const second = scoredBuilds[1]
                if (second.stats.wr >= 50.0) {
                    finalBuilds.push(second)
                }
            }

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
                        <span className="text-green-400 font-bold">{hero.season_wr}%</span>
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
                <span className="text-[10px] text-cyan-400/60">Season 3 2025</span>
            </div>

            {hero.notes && (
                <div className="text-[11px] text-cyan-200/80 italic border-l-2 border-cyan-500/30 pl-2">
                    {hero.notes}
                </div>
            )}

            <div className="space-y-2 mt-1">
                {topBuilds.length > 0 && (
                    <div className="bg-black/20 rounded p-1.5 border border-white/5">
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-70">Recommended Build</span>
                            <span className="text-[10px] text-slate-400">
                                {Number(topBuilds[0].stats.wr).toFixed(1)}% WR
                                {topBuilds[0].stats.games && (
                                    topBuilds[0].stats.games === hero.lifetime_games ?
                                        <span className="text-cyan-400 opacity-80 ml-1 font-bold text-[9px] uppercase tracking-wide">(Signature)</span> :
                                        <span className="text-slate-500 opacity-80 ml-1">({topBuilds[0].stats.games} Games)</span>
                                )}
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

                {topBuilds.length > 1 && (
                    <div className="pt-1">
                        <button
                            onClick={() => setShowSecondary(!showSecondary)}
                            className="text-[10px] text-cyan-400/70 hover:text-cyan-400 flex items-center gap-1 w-full justify-center py-1 transition-colors bg-white/5 rounded hover:bg-white/10"
                        >
                            {showSecondary ? 'Hide Alternative' : 'Show Alternative Variant'}
                            <span className={`transition-transform duration-200 ${showSecondary ? 'rotate-180' : ''}`}>▼</span>
                        </button>

                        {showSecondary && (
                            <div className="bg-black/20 rounded p-1.5 border border-white/5 mt-1 animate-fadeIn border-t-0 rounded-t-none">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-[10px] uppercase font-bold tracking-wider opacity-70">Variant</span>
                                    <span className="text-[10px] text-slate-400">
                                        {Number(topBuilds[1].stats.wr).toFixed(1)}% WR
                                        {topBuilds[1].stats.games && (
                                            topBuilds[1].stats.games === hero.lifetime_games ?
                                                <span className="text-cyan-400 opacity-80 ml-1 font-bold text-[9px] uppercase tracking-wide">(Signature)</span> :
                                                <span className="text-slate-500 opacity-80 ml-1">({topBuilds[1].stats.games} Games)</span>
                                        )}
                                    </span>
                                </div>
                                <BuildDisplay
                                    hero={hero.hero}
                                    buildStr={topBuilds[1].build}
                                    source="LIFETIME"
                                    compact={true}
                                    heroData={heroData}
                                    talentMap={talentMap}
                                    talentData={talentData}
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Award, AlertTriangle, Upload, History } from 'lucide-react'
import ReplaySelector from './ReplaySelector'
import { formatElegantDate } from '../utils/dateUtils'
import './QuickStatsPanel.css'
import StrongHeroCard from './StrongHeroCard'
import AvoidFixHeroCard from './AvoidFixHeroCard'
import MapTrends from './MapTrends'
import MetaComparison from './MetaComparison'
import BuildDisplay from './BuildDisplay'
import QuickSummaryTile from './QuickSummaryTile'
import DataUpdateNotification from './DataUpdateNotification'
import { useReplayData } from '../hooks/useReplayData'
import { normalizeHeroName } from '../utils/heroUtils'
import RankIcon from './RankIcon'
import ConfidenceScore from './ConfidenceScore'

export default function QuickStatsPanel({ onSelectMatch }) {
    const { matches: allMatches, profile, heroData, talentMap: talentMapData, talentData, loading: replayLoading, dataChanged, lastUpdated } = useReplayData()
    const [recentMatches, setRecentMatches] = useState([])
    const [loading, setLoading] = useState(true)
    const [showReplayUpload, setShowReplayUpload] = useState(false)

    useEffect(() => {
        if (!replayLoading && allMatches) {
            // Sort descending (newest first) - only process what we need
            const sorted = [...allMatches].sort((a, b) => new Date(b.date || b.timestamp_iso) - new Date(a.date || a.timestamp_iso))
            setRecentMatches(sorted.slice(0, 12)) // Reduced from 16 to 12
            setLoading(false)
        }
    }, [replayLoading, allMatches])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-md-on-surface-variant">Loading performance data...</div>
            </div>
        )
    }

    if (!profile) return null

    const audit = profile.storm_league_audit || {}
    const slumping = audit.slumping_heroes || []
    const maps = profile.map_preferences || {}

    // Calculate Season 3 Strong Heroes: Baseline + Parsed Replays
    const SEASON_START_DATE = '2025-09-01' // Season 3 2025 start
    const BASELINE_CUTOFF = '2026-01-06' // Date when we established baseline
    const s3Matches = allMatches.filter(m => new Date(m.date || m.timestamp_iso) > new Date(SEASON_START_DATE))
    const newReplays = s3Matches.filter(m => new Date(m.date || m.timestamp_iso) > new Date(BASELINE_CUTOFF))

    let strong = []
    if (heroData) {
        const heroStats = {}

        // 1. Prioritize Verified S3 Stats (The "Operational Ledger")
        const verifiedHeroes = profile.hero_stats || {};
        const hasVerifiedStats = Object.keys(verifiedHeroes).length > 0;

        if (hasVerifiedStats) {
            Object.entries(verifiedHeroes).forEach(([heroName, data]) => {
                const s3 = data.verified_season_2025_3;
                if (s3 && parseInt(s3.games) > 0) {
                    // Start with verified stats as baseline
                    let wins = parseInt(s3.wins);
                    let total = parseInt(s3.games);

                    // ADD parsed matches after baseline cutoff to verified stats
                    const parsedAfterBaseline = newReplays.filter(m => m.hero === heroName);
                    parsedAfterBaseline.forEach(match => {
                        total++;
                        if (match.result === 'WIN') wins++;
                    });

                    heroStats[heroName] = {
                        wins: wins,
                        total: total,
                        hero: heroName,
                        role: null // will be filled below
                    };
                }
            });
        }

        // 2. If NO verified stats exist, fall back to purely replay-based parsing
        // Also add heroes that have parsed matches but no verified stats
        s3Matches.forEach(match => {
            const hero = match.hero
            if (!heroStats[hero]) {
                heroStats[hero] = { wins: 0, total: 0, hero, role: null }
            }
            // Only count matches if hero doesn't have verified stats (already counted above)
            if (!hasVerifiedStats || !verifiedHeroes[hero] || !verifiedHeroes[hero].verified_season_2025_3) {
                heroStats[hero].total++
                if (match.result === 'WIN') heroStats[hero].wins++
            }
        })

        strong = Object.values(heroStats)
            .filter(h => h.total >= 10) // Min 10 games in Season 3
            .map(h => {
                const normalizedName = normalizeHeroName(h.hero)
                const role = h.role || heroData[normalizedName]?.expandedRole || talentMapData[normalizedName]?.role || 'Assassin'

                // Get true lifetime stats from profile
                const ltStats = profile.hero_stats?.[h.hero]?.verified_lifetime || {};
                const ltWR = parseFloat(ltStats.win_rate || 0);
                const ltGames = parseInt(ltStats.games_played || 0);

                return {
                    hero: h.hero,
                    season_wr: parseFloat(((h.wins / h.total) * 100).toFixed(1)),
                    season_games: h.total,
                    lt_wr: ltWR,
                    lt_games: ltGames,
                    role: role,
                    notes: `Season 3 2025`
                }
            })
            .sort((a, b) => b.season_wr - a.season_wr)
            .slice(0, 3)
    }

    // Calculate Avoid/Fix heroes (low WR with enough games)
    let avoidFix = []
    if (heroData) {
        const heroStats = {}

        // Use the same logic as strong heroes to build heroStats
        const verifiedHeroes = profile.hero_stats || {};
        const hasVerifiedStats = Object.keys(verifiedHeroes).length > 0;

        if (hasVerifiedStats) {
            Object.entries(verifiedHeroes).forEach(([heroName, data]) => {
                const s3 = data.verified_season_2025_3;
                if (s3 && parseInt(s3.games) > 0) {
                    let wins = parseInt(s3.wins);
                    let total = parseInt(s3.games);

                    const parsedAfterBaseline = newReplays.filter(m => m.hero === heroName);
                    parsedAfterBaseline.forEach(match => {
                        total++;
                        if (match.result === 'WIN') wins++;
                    });

                    heroStats[heroName] = { wins, total, hero: heroName, role: null };
                }
            });
        }

        s3Matches.forEach(match => {
            const hero = match.hero
            if (!heroStats[hero]) {
                heroStats[hero] = { wins: 0, total: 0, hero, role: null }
            }
            if (!hasVerifiedStats || !verifiedHeroes[hero] || !verifiedHeroes[hero].verified_season_2025_3) {
                heroStats[hero].total++
                if (match.result === 'WIN') heroStats[hero].wins++
            }
        })

        avoidFix = Object.values(heroStats)
            .filter(h => h.total >= 5 && ((h.wins / h.total) * 100) < 45)
            .map(h => {
                const normalizedName = normalizeHeroName(h.hero)
                const role = h.role || heroData[normalizedName]?.expandedRole || talentMapData[normalizedName]?.role || 'Assassin'
                const wr = parseFloat(((h.wins / h.total) * 100).toFixed(1))

                // Get true lifetime stats from profile
                const ltStats = profile.hero_stats?.[h.hero]?.verified_lifetime || {};
                const ltWR = parseFloat(ltStats.win_rate || 0);

                return {
                    hero: h.hero,
                    season_wr: wr,
                    season_games: h.total,
                    lt_wr: ltWR,
                    role: role,
                    fix: `${wr}% WR - Consider alternative builds or avoid`
                }
            })
            .sort((a, b) => a.season_wr - b.season_wr)
            .slice(0, 3)
    }

    return (
        <div className="space-y-6">
            {/* Data Update Notification */}
            <DataUpdateNotification show={dataChanged} lastUpdated={lastUpdated} />

            {/* Header */}
            <div className="dashboard-header">
                <h3 className="section-title">Performance Dashboard</h3>
                <div className="section-stat flex items-center gap-3">
                    {(() => {
                        const s3Stats = profile?.rank_data?.storm_league?.verified_season_2025_3 || {};
                        const displayGames = s3Stats.total_games || s3Matches.length;
                        const displayWR = s3Stats.win_rate || (s3Matches.length > 0 ? ((s3Matches.filter(m => m.result === 'WIN').length / s3Matches.length) * 100).toFixed(1) : 0);
                        const peakRank = profile?.rank_data?.peak_rank;

                        return (
                            <>
                                <RankIcon rank={profile?.rank_data?.storm_league?.current_rank} size="xs" />
                                <ConfidenceScore
                                    value={displayWR}
                                    n={displayGames}
                                    label="S3 Performance"
                                    className="scale-75 origin-left"
                                />
                                {peakRank && (
                                    <span className="text-purple-400 font-semibold border-l border-purple-600/30 pl-3">
                                        🎯 Peak: {peakRank.rank} ({peakRank.season})
                                    </span>
                                )}
                                {profile?.rank_data?.storm_league?.rank_points !== undefined && (
                                    <span className="text-slate-500 text-[10px] font-mono border-l border-slate-700/30 pl-3 uppercase">
                                        {profile.rank_data.storm_league.rank_points} PTS TO PROMO: {profile.rank_data.storm_league.points_required_for_promotion}
                                    </span>
                                )}
                            </>
                        );
                    })()}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="dashboard-grid">
                {/* Strong Heroes */}
                <div className="stats-card strong tile-glow">
                    <div className="card-header">
                        <Award size={18} className="text-green-400" />
                        <h4 className="card-title text-green-400">Strong Picks</h4>
                    </div>
                    <div className="space-y-3">
                        {strong.slice(0, 3).map((hero, idx) => (
                            <StrongHeroCard key={idx} hero={hero} profile={profile} heroData={heroData} talentMap={talentMapData} talentData={talentData} />
                        ))}
                    </div>
                </div>

                {/* Avoid / Fix Heroes */}
                <div className="stats-card weak tile-glow">
                    <div className="card-header">
                        <AlertTriangle size={18} className="text-red-400" />
                        <h4 className="card-title text-red-400">Avoid / Fix</h4>
                    </div>
                    <div className="space-y-3">
                        {avoidFix.length > 0 ? (
                            avoidFix.slice(0, 3).map((hero, idx) => (
                                <AvoidFixHeroCard
                                    key={idx}
                                    hero={hero}
                                    profile={profile}
                                    heroData={heroData}
                                    talentMap={talentMapData}
                                    talentData={talentData}
                                />
                            ))
                        ) : (
                            <div className="text-slate-500 text-sm italic text-center py-4">No critical slumps detected</div>
                        )}
                    </div>
                </div>

                {/* Quick Summary */}
                <div className="bg-transparent h-full">
                    <QuickSummaryTile matches={s3Matches} profile={profile} talentMap={talentMapData} />
                </div>
            </div>

            <div className="trends-container">
                {/* Map Trends - Half width */}
                <div className="trends-column">
                    <MapTrends onSelectMatch={onSelectMatch} />
                </div>

                {/* Recent Matches - Half width, side-by-side with MapTrends */}
                <div className="trends-column">
                    {recentMatches.length > 0 && (
                        <div className="stats-card recent h-full flex flex-col tile-glow">
                            <div className="card-header">
                                <History size={18} className="text-blue-400" />
                                <h4 className="card-title">Recent Matches</h4>
                            </div>
                            <div className="recent-match-list">
                                {recentMatches.map((match, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => onSelectMatch?.(match)}
                                        className="recent-match-item group"
                                    >
                                        <div className="flex items-center gap-4 text-xs">
                                            <span className={`match-result ${match.result === 'WIN' ? 'win' : 'loss'}`}>
                                                {match.result === 'WIN' ? 'WIN' : 'LOSS'}
                                            </span>
                                            <div className="match-info">
                                                <span className="match-hero font-bold group-hover:text-cyan-300 transition-colors">{match.hero}</span>
                                                <span className="match-map text-[10px] opacity-60 uppercase">{match.map}</span>
                                            </div>
                                        </div>
                                        <span className="match-date text-[10px] tabular-nums">{formatElegantDate(match.date || match.timestamp_iso)}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Meta Comparison - NEW! */}
            <MetaComparison />

        </div>
    )
}

import { normalizeHeroName } from './heroUtils'
import { ACTIVE_SEASON } from '../config/season'

export const calculateYourStats = (matches, profileData = null) => {
    const getVerifiedOverride = (heroName) => {
        if (!profileData) return null

        // Check hero_stats first (primary location for verified stats)
        const heroStats = profileData.hero_stats?.[heroName]
        if (heroStats) {
            const sSlug = profileData.active_season?.slug || 'season_2026_1'
            const sVerified = heroStats[`verified_${sSlug}`]
            const lifetimeVerified = heroStats.verified_lifetime || heroStats.verified

            if (sVerified) {
                const wr = sVerified.wr || sVerified.win_rate || 0
                const games = sVerified.games || 0
                return {
                    s3: {
                        wr: wr,
                        games: games,
                        wins: sVerified.wins || Math.round(games * (wr / 100)),
                        losses: sVerified.losses || (games - Math.round(games * (wr / 100)))
                    },
                    lifetime: lifetimeVerified ? {
                        wr: lifetimeVerified.wr || lifetimeVerified.win_rate || 0,
                        games: lifetimeVerified.games || 0,
                        wins: lifetimeVerified.wins || Math.round((lifetimeVerified.games || 0) * ((lifetimeVerified.wr || lifetimeVerified.win_rate || 0) / 100)),
                        losses: lifetimeVerified.losses || ((lifetimeVerified.games || 0) - Math.round((lifetimeVerified.games || 0) * ((lifetimeVerified.wr || lifetimeVerified.win_rate || 0) / 100)))
                    } : null,
                    source: sVerified.source || "Verified In-Game"
                }
            }

            if (lifetimeVerified) {
                const wr = lifetimeVerified.wr || lifetimeVerified.win_rate || 0
                const games = lifetimeVerified.games || 0
                return {
                    s3: null,
                    lifetime: {
                        wr: wr,
                        games: games,
                        wins: lifetimeVerified.wins || Math.round(games * (wr / 100)),
                        losses: lifetimeVerified.losses || (games - Math.round(games * (wr / 100)))
                    },
                    source: lifetimeVerified.source || "Verified In-Game"
                }
            }
        }

        // Fallback to hero_map_stats (legacy structure)
        const heroData = profileData.hero_map_stats?.[heroName]
        if (!heroData) return null

        const sSlug = profileData.active_season?.slug || 'season_2026_1'
        const sData = heroData[`verified_${sSlug}`]
        if (sData) {
            const wr = sData.win_rate || sData.wr || 0
            const games = sData.games || 0
            return {
                s3: {
                    wr: wr,
                    games: games,
                    wins: sData.wins || Math.round(games * (wr / 100)),
                    losses: sData.losses || (games - Math.round(games * (wr / 100)))
                },
                lifetime: heroData.verified_ingame ? {
                    wr: heroData.verified_ingame.win_rate || heroData.verified_ingame.wr || 0,
                    games: heroData.verified_ingame.games || 0,
                    wins: heroData.verified_ingame.wins || Math.round((heroData.verified_ingame.games || 0) * ((heroData.verified_ingame.win_rate || heroData.verified_ingame.wr || 0) / 100)),
                    losses: heroData.verified_ingame.losses || ((heroData.verified_ingame.games || 0) - Math.round((heroData.verified_ingame.games || 0) * ((heroData.verified_ingame.win_rate || heroData.verified_ingame.wr || 0) / 100)))
                } : null,
                source: sData.source || "Verified In-Game"
            }
        }

        if (heroData.verified_ingame) {
            const lifetime = heroData.verified_ingame
            const wr = lifetime.win_rate || lifetime.wr || 0
            const games = lifetime.games || 0
            return {
                s3: null,
                lifetime: {
                    wr: wr,
                    games: games,
                    wins: lifetime.wins || Math.round(games * (wr / 100)),
                    losses: lifetime.losses || (games - Math.round(games * (wr / 100)))
                },
                source: lifetime.source || "Verified In-Game"
            }
        }
        return null
    }

    const heroStats = {}
    const SEASON_START = new Date(profileData?.active_season?.start_date || ACTIVE_SEASON.start_date)

    // 1. Initialize from Profile Data
    // A. Verified Stats (hero_map_stats)
    if (profileData && profileData.hero_map_stats) {
        Object.keys(profileData.hero_map_stats).forEach(hero => {
            heroStats[hero] = {
                lifetime: { wins: 0, losses: 0, total: 0 },
                s3: { wins: 0, losses: 0, total: 0 }
            }
        })
    }

    // B. Audit Data (strong_heroes & slumping_heroes) - Critical for "Fix or Drop"
    if (profileData && profileData.storm_league_audit) {
        const { strong_heroes, slumping_heroes } = profileData.storm_league_audit
        const auditHeroes = [...(strong_heroes || []), ...(slumping_heroes || [])]

        auditHeroes.forEach(h => {
            if (!heroStats[h.hero]) {
                heroStats[h.hero] = {
                    lifetime: { wins: 0, losses: 0, total: 0 },
                    s3: { wins: 0, losses: 0, total: 0 }
                }
            }
            // Pre-populate with audit values if they exist, to ensure they pass filters
            // These are "virtual" stats derived from the audit if real parsed games are missing
            heroStats[h.hero].auditData = {
                s3: h.season_wr ? { wr: h.season_wr, games: h.games || 0 } : null,
                lifetime: { wr: h.lifetime_wr, games: h.lifetime_games }
            }
        })
    }

    // 2. Aggregate from Matches
    matches.forEach(match => {
        const hero = match.hero
        if (!heroStats[hero]) {
            heroStats[hero] = {
                lifetime: { wins: 0, losses: 0, total: 0 },
                s3: { wins: 0, losses: 0, total: 0 }
            }
        }

        heroStats[hero].lifetime.total++
        if (match.result === 'WIN' || match.win === true) {
            heroStats[hero].lifetime.wins++
        } else {
            heroStats[hero].lifetime.losses++
        }

        const matchDate = new Date(match.date || match.timestamp_iso)
        if (matchDate > SEASON_START) {
            heroStats[hero].s3.total++
            if (match.result === 'WIN' || match.win === true) {
                heroStats[hero].s3.wins++
            } else {
                heroStats[hero].s3.losses++
            }
        }

        if (!heroStats[hero].maps) heroStats[hero].maps = {}
        if (!heroStats[hero].maps[match.map]) heroStats[hero].maps[match.map] = { wins: 0, total: 0 }
        heroStats[hero].maps[match.map].total++
        if (match.result === 'WIN' || match.win === true) {
            heroStats[hero].maps[match.map].wins++
        }
    })

    return Object.entries(heroStats)
        .filter(([hero, stats]) => {
            // Allow if verified stats exist OR audit data exists OR if parsed total >= 3
            // Relaxed from 5 to 3 to ensure we fill the 8-slot roster
            const verified = getVerifiedOverride(hero)
            if (verified && verified.lifetime && verified.lifetime.games >= 3) return true
            if (stats.auditData) return true // Always include audit heroes
            return stats.lifetime.total >= 3
        })
        .map(([hero, stats]) => {
            const verified = getVerifiedOverride(hero)
            const audit = stats.auditData

            // Priority: Verified > Audit > Parsed
            // BUT: If verified exists, ADD parsed matches after baseline cutoff
            let finalS3, finalLifetime, source

            if (verified && verified.s3) {
                // Start with verified stats as baseline
                const baselineDate = new Date('2026-02-10')
                const parsedAfterBaseline = matches.filter(m =>
                    m.hero === hero &&
                    new Date(m.date || m.timestamp_iso) > baselineDate &&
                    new Date(m.date || m.timestamp_iso) > SEASON_START
                )

                // Add parsed matches after baseline to verified stats
                let combinedWins = verified.s3.wins
                let combinedGames = verified.s3.games

                parsedAfterBaseline.forEach(m => {
                    combinedGames++
                    if (m.result === 'WIN' || m.win === true) {
                        combinedWins++
                    }
                })

                finalS3 = {
                    wr: combinedGames > 0 ? (combinedWins / combinedGames) * 100 : verified.s3.wr,
                    games: combinedGames,
                    wins: combinedWins,
                    losses: combinedGames - combinedWins
                }
                source = verified.source || "Verified In-Game + Parsed"
            } else if (audit && audit.s3) {
                finalS3 = {
                    wr: audit.s3.wr,
                    games: audit.s3.games,
                    wins: Math.round(audit.s3.games * (audit.s3.wr / 100)),
                    losses: audit.s3.games - Math.round(audit.s3.games * (audit.s3.wr / 100))
                }
                source = "Cerebrate Audit"
            } else {
                finalS3 = {
                    wr: stats.s3.total > 0 ? (stats.s3.wins / stats.s3.total) * 100 : 0,
                    games: stats.s3.total,
                    wins: stats.s3.wins,
                    losses: stats.s3.losses
                }
                source = "Match History"
            }

            if (verified && verified.lifetime) {
                // Add parsed matches after baseline to verified lifetime stats
                const baselineDate = new Date('2026-02-10') // BASELINE_CUTOFF
                const parsedAfterBaseline = matches.filter(m =>
                    m.hero === hero &&
                    new Date(m.date || m.timestamp_iso) > baselineDate
                )

                let combinedWins = verified.lifetime.wins
                let combinedGames = verified.lifetime.games

                parsedAfterBaseline.forEach(m => {
                    combinedGames++
                    if (m.result === 'WIN' || m.win === true) {
                        combinedWins++
                    }
                })

                finalLifetime = {
                    wr: combinedGames > 0 ? (combinedWins / combinedGames) * 100 : verified.lifetime.wr,
                    games: combinedGames,
                    wins: combinedWins,
                    losses: combinedGames - combinedWins
                }
            } else if (audit && audit.lifetime) {
                finalLifetime = {
                    wr: audit.lifetime.wr,
                    games: audit.lifetime.games,
                    wins: Math.round(audit.lifetime.games * (audit.lifetime.wr / 100)),
                    losses: audit.lifetime.games - Math.round(audit.lifetime.games * (audit.lifetime.wr / 100))
                }
            } else {
                finalLifetime = {
                    wr: (stats.lifetime.wins / stats.lifetime.total) * 100,
                    games: stats.lifetime.total,
                    wins: stats.lifetime.wins,
                    losses: stats.lifetime.losses
                }
            }

            return {
                hero,
                source,
                lifetime: finalLifetime,
                s3: finalS3,
                mapStats: (() => {
                    const maps = Object.entries(stats.maps || {})
                        .filter(([_, m]) => m.total >= 2)
                        .map(([name, m]) => ({ name, wr: (m.wins / m.total) * 100, games: m.total }))
                        .sort((a, b) => b.wr - a.wr);

                    if (maps.length < 2) return { isMapDependent: false, bestMaps: [] };

                    const best = maps[0];
                    const worst = maps[maps.length - 1];
                    const variance = best.wr - worst.wr;
                    const isDependent = variance > 25 && worst.wr < 45;

                    return {
                        isMapDependent: isDependent,
                        bestMaps: maps.slice(0, 2),
                        variance
                    };
                })()
            }
        })
        .sort((a, b) => b.lifetime.wr - a.lifetime.wr)
        .slice(0, 8)
}

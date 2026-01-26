/**
 * Calculate talent builds from match history
 */
export const calculateTalentBuilds = (matches, heroName) => {
    const builds = {}

    matches.forEach(match => {
        if (match.hero !== heroName) return

        // Find the player in this match
        const player = match.players?.find(p =>
            p.name === 'CerebrateUser' ||
            p.hero === heroName ||
            p.name === match.player_name
        )

        if (!player) return

        // Extract talents from stats (Tier1Talent through Tier7Talent)
        const talents = []
        for (let tier = 1; tier <= 7; tier++) {
            const talentIndex = player.stats?.[`Tier${tier}Talent`] ||
                player.kv_stats?.[`Tier${tier}Talent`] ||
                0
            talents.push(talentIndex)
        }

        // Skip if no valid talents (all zeros means no data)
        if (talents.every(t => t === 0)) return

        // Create build string
        const buildStr = talents.join('')

        // Skip incomplete builds (less than 7 talents)
        if (buildStr.length < 7) return

        // Initialize build stats if needed
        if (!builds[buildStr]) {
            builds[buildStr] = { wins: 0, games: 0, wr: 0 }
        }

        // Update stats
        builds[buildStr].games += 1
        if (match.result === 'WIN' || match.win === true) {
            builds[buildStr].wins += 1
        }
    })

    // Calculate win rates
    Object.keys(builds).forEach(buildStr => {
        const build = builds[buildStr]
        build.wr = build.games > 0 ? (build.wins / build.games) * 100 : 0
    })

    return builds
}

/**
 * Get the best build for a hero from calculated builds
 */
export const getBestBuild = (builds, minGames = 3) => {
    if (!builds || Object.keys(builds).length === 0) return null

    // Filter builds with minimum games
    const validBuilds = Object.entries(builds)
        .filter(([_, stats]) => stats.games >= minGames)
        .map(([buildStr, stats]) => ({ build: buildStr, ...stats }))

    if (validBuilds.length === 0) return null

    // Score: heavily weight games, use WR as tiebreaker
    validBuilds.forEach(b => {
        b.score = (b.games * 10) + (b.wr / 10)
    })

    // Sort by score descending
    validBuilds.sort((a, b) => b.score - a.score)

    return validBuilds[0]
}

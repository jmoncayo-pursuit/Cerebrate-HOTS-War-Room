/**
 * Uses match history dates and win rates to suggest heroes
 */
import { normalizeHeroName } from './heroUtils'

export function getDraftRecommendations(selectedHeroes, matchHistory, strategies, mapName) {
  if (!mapName || !matchHistory) return []

  // Get recent matches (last 30 days)
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

  const recentMatches = matchHistory.filter(m => {
    if (!m.timestamp_iso) return false
    return new Date(m.timestamp_iso) > thirtyDaysAgo
  })

  // Get map-specific strategy
  const mapStrategy = strategies[mapName] || {}
  const primaryHero = mapStrategy.primary?.name || mapStrategy.primary?.hero
  const backupHeroes = (mapStrategy.backups || []).map(b => b.name || b.hero)

  // Calculate recommendations
  const recommendations = []

  // 1. Primary hero from strategy
  if (primaryHero) {
    const stats = getHeroStats(primaryHero, recentMatches)
    recommendations.push({
      hero: primaryHero,
      reason: 'Primary strategy pick',
      priority: 'high',
      stats,
      type: 'primary'
    })
  }

  // 2. Backup heroes from strategy
  backupHeroes.forEach(hero => {
    const stats = getHeroStats(hero, recentMatches)
    recommendations.push({
      hero,
      reason: 'Backup strategy option',
      priority: 'medium',
      stats,
      type: 'backup'
    })
  })

  // 3. Recently played heroes with good win rate
  const recentHeroes = getRecentHeroes(recentMatches, 7) // Last 7 days
  recentHeroes.forEach(({ hero, winRate, games }) => {
    if (winRate >= 60 && games >= 2 && !recommendations.find(r => r.hero === hero)) {
      recommendations.push({
        hero,
        reason: `Recent success (${winRate}% WR, ${games} games)`,
        priority: 'medium',
        stats: { winRate, games },
        type: 'recent'
      })
    }
  })

  // 4. Selected heroes (if any)
  selectedHeroes.forEach(hero => {
    if (!recommendations.find(r => r.hero === hero)) {
      const stats = getHeroStats(hero, recentMatches)
      recommendations.push({
        hero,
        reason: 'Selected for draft',
        priority: 'high',
        stats,
        type: 'selected'
      })
    }
  })

  // Sort by priority and win rate
  return recommendations.sort((a, b) => {
    const priorityOrder = { high: 3, medium: 2, low: 1 }
    if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    }
    return (b.stats?.winRate || 0) - (a.stats?.winRate || 0)
  })
}

function getHeroStats(heroName, matches) {
  const normalizedHero = normalizeHeroName(heroName)
  const heroMatches = matches.filter(m =>
    m.players?.some(p => normalizeHeroName(p.hero) === normalizedHero)
  )

  const wins = heroMatches.filter(m =>
    m.players?.some(p => normalizeHeroName(p.hero) === normalizedHero && p.won === true)
  ).length

  const losses = heroMatches.filter(m =>
    m.players?.some(p => normalizeHeroName(p.hero) === normalizedHero && p.won === false)
  ).length

  const total = wins + losses
  const winRate = total > 0 ? Math.round((wins / total) * 100) : 0

  return { wins, losses, games: total, winRate }
}

function getRecentHeroes(matches, days) {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - days)

  const recentMatches = matches.filter(m => {
    if (!m.timestamp_iso) return false
    return new Date(m.timestamp_iso) > cutoff
  })

  const heroMap = new Map()

  recentMatches.forEach(match => {
    match.players?.forEach(player => {
      const hero = player.hero
      if (!hero) return

      if (!heroMap.has(hero)) {
        heroMap.set(hero, { hero, wins: 0, losses: 0, games: 0 })
      }

      const stats = heroMap.get(hero)
      stats.games++
      if (player.won === true) stats.wins++
      if (player.won === false) stats.losses++
    })
  })

  return Array.from(heroMap.values())
    .map(s => ({
      hero: s.hero,
      winRate: s.games > 0 ? Math.round((s.wins / s.games) * 100) : 0,
      games: s.games
    }))
    .filter(s => s.games > 0)
    .sort((a, b) => b.games - a.games)
}


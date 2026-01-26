import { useState, useEffect } from 'react'
import HeroPortrait from './HeroPortrait'

export default function AllHeroesGrid({ onSelectHero, selectedHeroes = [], matchHistory = [], excludedHeroes = [], onExcludeHeroes = () => { } }) {
  const [heroes, setHeroes] = useState([])
  const [roles, setRoles] = useState({}) // Store role mappings
  const [filterRole, setFilterRole] = useState('All')
  const [sortBy, setSortBy] = useState('name') // 'name', 'games', 'winrate', 'recent'
  const [showExcluded, setShowExcluded] = useState(false)

  useEffect(() => {
    // Load all heroes and roles
    fetch('/api/data/allHeroes.json')
      .then(res => res.json())
      .then(data => {
        setHeroes(data.heroes || [])
        setRoles(data.roles || {})
      })
      .catch(() => {
        // Fallback list if file doesn't load
        setHeroes([
          "Abathur", "Alarak", "Alexstrasza", "Ana", "Anub'arak", "Artanis", "Arthas", "Auriel", "Azmodan",
          "Blaze", "Brightwing", "Cassia", "Chen", "Chromie", "Deathwing", "Deckard", "Dehaka", "Diablo",
          "D.Va", "E.T.C.", "Falstad", "Fenix", "Gall", "Gazlowe", "Genji", "Greymane", "Gul'dan",
          "Hanzo", "Hogger", "Illidan", "Imperius", "Jaina", "Johanna", "Junkrat", "Kael'thas", "Kel'Thuzad",
          "Kerrigan", "Kharazim", "Leoric", "Li Li", "Li-Ming", "Lt. Morales", "Lunara", "Maiev", "Malfurion",
          "Malthael", "Medivh", "Mei", "Muradin", "Murky", "Nazeebo", "Nova", "Orphea", "Probius",
          "Qhira", "Ragnaros", "Raynor", "Rehgar", "Rexxar", "Samuro", "Sgt. Hammer", "Sonya", "Stitches",
          "Stukov", "Sylvanas", "Tassadar", "The Butcher", "The Lost Vikings", "Thrall", "Tracer", "Tychus",
          "Tyrael", "Tyrande", "Uther", "Valeera", "Valla", "Varian", "Whitemane", "Xul", "Yrel", "Zagara",
          "Zarya", "Zeratul", "Zul'jin"
        ])
      })
  }, [])

  // Helper to find role for a hero
  const getHeroRole = (heroName) => {
    for (const [role, heroList] of Object.entries(roles)) {
      if (heroList.includes(heroName)) return role
    }
    return 'Unknown'
  }

  // Calculate stats for each hero from match history
  const getHeroStats = (heroName) => {
    const heroMatches = matchHistory.filter(m =>
      m.players?.some(p => p.hero === heroName)
    )

    const wins = heroMatches.filter(m =>
      m.players?.some(p => p.hero === heroName && p.won === true)
    ).length

    const losses = heroMatches.filter(m =>
      m.players?.some(p => p.hero === heroName && p.won === false)
    ).length

    // Get most recent match date
    const recentMatch = heroMatches
      .filter(m => m.timestamp_iso)
      .sort((a, b) => new Date(b.timestamp_iso) - new Date(a.timestamp_iso))[0]

    return {
      games: wins + losses,
      wins,
      losses,
      winRate: wins + losses > 0 ? Math.round((wins / (wins + losses)) * 100) : 0,
      lastPlayed: recentMatch?.timestamp_iso || null
    }
  }

  // Sort and filter heroes
  const processedHeroes = heroes
    .map(hero => ({
      name: hero,
      role: getHeroRole(hero),
      ...getHeroStats(hero),
      isSelected: selectedHeroes.includes(hero),
      isExcluded: excludedHeroes.includes(hero)
    }))
    .filter(hero => {
      // Filter excluded heroes (unless showing them)
      if (!showExcluded && hero.isExcluded) return false

      if (filterRole === 'All') return true
      return hero.role === filterRole
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'games':
          return b.games - a.games
        case 'winrate':
          return b.winRate - a.winRate
        case 'recent':
          if (!a.lastPlayed && !b.lastPlayed) return 0
          if (!a.lastPlayed) return 1
          if (!b.lastPlayed) return -1
          return new Date(b.lastPlayed) - new Date(a.lastPlayed)
        default:
          return a.name.localeCompare(b.name)
      }
    })

  return (
    <div className="w-full">
      {/* Filters and Sort */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-[#1e293b] rounded-2xl border border-white/5">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400 font-bold">Filter:</label>
          <select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            className="bg-[#0f172a] border border-white/10 rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option>All</option>
            <option>Tank</option>
            <option>Bruiser</option>
            <option>Melee Assassin</option>
            <option>Ranged Assassin</option>
            <option>Healer</option>
            <option>Support</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400 font-bold">Sort:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-[#0f172a] border border-white/10 rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="name">Name</option>
            <option value="games">Games Played</option>
            <option value="winrate">Win Rate</option>
            <option value="recent">Most Recent</option>
          </select>
        </div>

        {excludedHeroes.length > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-sm text-gray-500">
              Excluded: {excludedHeroes.length}
            </label>
            <button
              onClick={() => setShowExcluded(!showExcluded)}
              className="bg-[#0f172a] border border-white/10 rounded-lg px-3 py-1 text-xs text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              {showExcluded ? 'Hide' : 'Show'} Excluded
            </button>
          </div>
        )}
      </div>

      {/* Hero Grid */}
      <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-4 px-2 pb-20">
        {processedHeroes.map(hero => (
          <button
            key={hero.name}
            onClick={() => onSelectHero && onSelectHero(hero.name)}
            className={`relative group flex flex-col items-center p-3 rounded-xl border transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/20 hover:z-10 ${hero.isExcluded
              ? 'bg-red-900/10 border-red-900/30 opacity-40 grayscale'
              : hero.isSelected
                ? 'bg-cyan-900/30 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                : hero.games > 0
                  ? 'bg-[#1e293b] border-white/10 hover:border-cyan-400/50'
                  : 'bg-[#0f172a] border-white/5 opacity-70 hover:opacity-100 hover:border-white/20'
              }`}
          >
            {/* Aspect Ratio Container for Portrait */}
            <div className="relative w-full aspect-square mb-2 rounded-lg overflow-hidden border border-black/50 group-hover:border-white/20 transition-colors bg-black">
              <HeroPortrait heroName={hero.name} size="full" />

              {/* Win Rate Overlay */}
              {hero.games > 0 && (
                <div className="absolute bottom-0 left-0 right-0 bg-black/80 backdrop-blur-[2px] p-0.5 text-center border-t border-white/10">
                  <div className={`text-[10px] font-bold ${hero.winRate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                    {hero.winRate}%
                  </div>
                </div>
              )}
            </div>

            {/* Hero Name */}
            <div className="h-8 flex items-center justify-center w-full">
              <span className={`text-xs font-medium text-center leading-tight line-clamp-2 px-1 ${hero.isSelected ? 'text-cyan-300' : 'text-gray-300 group-hover:text-white'}`}>
                {hero.name}
              </span>
            </div>

            {/* Stats Badge (Top Right) */}
            {hero.games > 0 && (
              <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm text-white text-[9px] font-bold px-1.5 py-0.5 rounded border border-white/10 shadow-sm z-10">
                {hero.games}G
              </div>
            )}

            {/* Selection Indicator */}
            {hero.isSelected && (
              <div className="absolute top-2 left-2 text-cyan-400 z-10 drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
                <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" /></svg>
              </div>
            )}

            {/* Hover Tooltip - FIXED BACKGROUND */}
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-3 w-max max-w-[180px] bg-[#020617] text-white rounded-lg p-3 shadow-[0_4px_20px_rgba(0,0,0,0.5)] border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 text-center">
              <div className="font-bold text-sm mb-1 text-cyan-400">{hero.name}</div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">{hero.role || 'Unknown'}</div>
              {hero.games > 0 ? (
                <div className="space-y-1 bg-white/5 rounded p-2">
                  <div className="text-xs font-mono flex justify-between gap-4">
                    <span className="text-green-400">{hero.wins} W</span>
                    <span className="text-red-400">{hero.losses} L</span>
                  </div>
                  {hero.lastPlayed && (
                    <div className="text-[10px] text-gray-400 pt-1 border-t border-white/10">
                      Last: {new Date(hero.lastPlayed).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-gray-500 italic">No match history</div>
              )}
              {/* Arrow */}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-[#020617]"></div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

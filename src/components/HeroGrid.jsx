import { useState } from 'react'
import { normalizeHeroName } from '../utils/heroUtils'

export default function HeroGrid({ heroes, matches, onSelectHero }) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredHeroes = heroes.filter(hero => {
    const term = searchTerm.toLowerCase();
    return hero.hero.toLowerCase().includes(term) ||
      normalizeHeroName(hero.hero).includes(term);
  })

  const getWinRateColor = (winRate) => {
    if (winRate >= 55) return 'text-md-primary' // Good
    if (winRate < 45) return 'text-md-error'   // Bad
    return 'text-md-secondary'                 // Average
  }

  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <div className="relative max-w-md w-full">
          <input
            id="hero-grid-search"
            name="hero-grid-search"
            type="text"
            placeholder="Search heroes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-5 py-3 bg-md-surface-container-high border border-md-outline rounded-full text-md-on-surface placeholder-md-on-surface-variant focus:outline-none focus:border-md-primary focus:ring-1 focus:ring-md-primary transition-all shadow-md-elevation-1"
          />
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-md-on-surface-variant">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {filteredHeroes.map((hero) => (
          <div
            key={hero.hero}
            onClick={() => onSelectHero(hero.hero)}
            className="group bg-md-surface-container border border-md-outline-variant rounded-md-lg p-4 cursor-pointer hover:border-md-primary hover:bg-md-surface-container-high transition-all hover:shadow-md-elevation-2 active:scale-95"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-bold text-md-on-surface group-hover:text-md-primary transition-colors">{hero.hero}</h3>
              <span className={`text-sm font-bold ${getWinRateColor(hero.win_rate)}`}>
                {hero.win_rate}%
              </span>
            </div>

            <div className="text-sm text-md-on-surface-variant space-y-1 mb-3">
              <div>Games: {hero.games_played}</div>
              <div className="flex justify-between">
                <span className="text-md-primary">W: {hero.wins}</span>
                <span className="text-md-error">L: {hero.losses}</span>
              </div>
            </div>

            {/* Hero portrait */}
            <div className="aspect-square bg-md-surface-container-highest rounded-md-md flex items-center justify-center overflow-hidden relative">
              <img
                src={`/images/heroes/${normalizeHeroName(hero.hero)}.png`}
                alt={hero.hero}
                className="w-full h-full object-cover transition-transform group-hover:scale-110"
                onError={(e) => {
                  e.target.style.display = 'none'
                }}
              />
              {/* Fallback Initial if image fails */}
              <span className="absolute text-4xl font-bold text-md-on-surface-variant opacity-20 pointer-events-none">
                {hero.hero.charAt(0)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {filteredHeroes.length === 0 && (
        <div className="text-center text-md-on-surface-variant py-12">
          No heroes found matching "{searchTerm}"
        </div>
      )}
    </div>
  )
}

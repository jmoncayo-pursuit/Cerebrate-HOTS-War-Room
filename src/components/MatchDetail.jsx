import { useState, useEffect } from 'react'
import { normalizeHeroName } from '../utils/heroUtils'
import BuildDisplay from './BuildDisplay'

export default function MatchDetail({ hero, matches, onBack, onSelectMatch }) {
  const [sortBy, setSortBy] = useState('date') // 'date', 'win', 'loss'
  const [talentMap, setTalentMap] = useState({})

  // Load talent ID map on mount
  useEffect(() => {
    fetch('/api/data/talent_id_map.json')
      .then(res => res.json())
      .then(data => setTalentMap(data))
      .catch(err => console.error("Failed to load talent map:", err))
  }, [])

  const sortedMatches = [...matches].sort((a, b) => {
    if (sortBy === 'date') {
      return (b.timestamp || 0) - (a.timestamp || 0)
    }
    // Add more sorting options as needed
    return 0
  })

  const getPlayerData = (match) => {
    return match.players.find(p => p.hero === hero) || {}
  }

  const isFeederMatch = (match) => {
    const player = getPlayerData(match)
    return player.deaths && player.deaths.length > 3
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="mb-6 px-4 py-2 bg-purple-primary text-black rounded hover:bg-purple-400 font-bold"
      >
        ← Back to Heroes
      </button>

      <div className="mb-6 bg-obsidian-panel rounded-lg p-6 border border-gray-800">
        <h2 className="text-2xl font-bold mb-4">{hero} - Deep Stats</h2>
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Total Matches:</span>{' '}
            <span className="text-cyan-safe font-bold">{matches.length}</span>
          </div>
          <div>
            <span className="text-gray-400">Win Rate:</span>{' '}
            <span className="text-cyan-safe font-bold">
              {matches.length > 0
                ? Math.round(
                  (matches.filter(m => getPlayerData(m).won === true).length /
                    matches.length) *
                  100 *
                  10
                ) / 10
                : 0}
              %
            </span>
          </div>
          <div>
            <span className="text-gray-400">Average KDA:</span>{' '}
            <span className="text-purple-400 font-bold">
              {(() => {
                const totalKDA = matches.reduce((acc, m) => {
                  const p = getPlayerData(m);
                  const k = p.stats?.kills || 0;
                  const a = p.stats?.assists || 0;
                  const d = p.stats?.deaths || 0;
                  return acc + ((k + a) / Math.max(1, d));
                }, 0);
                return matches.length ? (totalKDA / matches.length).toFixed(1) : 0;
              })()}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Feeder Matches:</span>{' '}
            <span className="text-red-danger font-bold">
              {matches.filter(isFeederMatch).length}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {sortedMatches.map((match, idx) => {
          const player = getPlayerData(match);
          const isFeeder = isFeederMatch(match);
          const won = player.won === true;
          // Deep Stats Data
          const xpData = player.xp_breakdown?.by_minute || [];
          const talents = player.talents || [];
          const talentTimestamps = player.talent_timestamps || {};

          return (
            <div
              key={idx}
              onClick={() => onSelectMatch(match)}
              className={`bg-obsidian-panel rounded-lg p-4 border cursor-pointer transition-all hover:border-purple-primary ${isFeeder ? 'border-red-danger' : won ? 'border-cyan-safe' : 'border-gray-800'
                }`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold">{match.map}</h3>
                  <div className="text-sm text-gray-400">
                    {match.timestamp_iso
                      ? new Date(match.timestamp_iso).toLocaleDateString() + ' ' + new Date(match.timestamp_iso).toLocaleTimeString()
                      : 'Unknown date'}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-black ${won ? 'text-cyan-safe' : 'text-red-danger'}`}>
                    {won ? 'VICTORY' : 'DEFEAT'}
                  </div>
                  <div className="text-sm text-gray-400">{match.game_length_formatted}</div>
                </div>
              </div>

              {/* XP / LEVEL GRAPH (Mini) */}
              {xpData.length > 0 && (
                <div className="mb-4 p-2 bg-black/40 rounded border border-white/5">
                  <div className="text-xs text-gray-400 mb-1">XP Contribution Flow</div>
                  <div className="h-16 flex items-end gap-[1px]">
                    {xpData.map((d, i) => (
                      <div
                        key={i}
                        className="bg-purple-500/50 hover:bg-purple-500"
                        style={{
                          height: `${Math.min(100, (d.total / 10000) * 100)}%`,
                          width: `${100 / xpData.length}%`
                        }}
                        title={`Min ${d.minute}: ${d.total} XP`}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* STANDARDIZED BUILD DISPLAY */}
              {talents.length > 0 && (
                <div className="mb-3">
                  <BuildDisplay
                    hero={hero}
                    buildStr={talents.map(t => typeof t === 'object' ? t.talent_index : 1).join('')}
                    source="RECENT"
                  />
                </div>
              )}

              {/* STAT GRID */}
              {player.stats && (
                <div className="grid grid-cols-4 gap-2 text-[11px] bg-black/30 p-2.5 rounded border border-white/5">
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">Hero Damage</span>
                    <span className="text-cyan-safe font-mono">{player.stats.hero_damage?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">Siege Damage</span>
                    <span className="text-amber-400 font-mono">{player.stats.siege_damage?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">Healing</span>
                    <span className="text-green-400 font-mono">{player.stats.healing?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">Self Healing</span>
                    <span className="text-emerald-400 font-mono">{player.stats.self_healing?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">K / D / A</span>
                    <span className="text-purple-400 font-mono font-bold">
                      {player.stats.kills || 0} / <span className="text-red-danger">{player.stats.deaths || 0}</span> / {player.stats.assists || 0}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">CC Time</span>
                    <span className="text-white font-mono">{player.stats.time_cc_enemy_heroes?.toFixed(1) || 0}s</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">XP Contribution</span>
                    <span className="text-white font-mono">{player.stats.xp_contribution?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-500 uppercase tracking-tighter">Merc Camps</span>
                    <span className="text-white font-mono">{player.stats.merc_camp_captures || 0}</span>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}


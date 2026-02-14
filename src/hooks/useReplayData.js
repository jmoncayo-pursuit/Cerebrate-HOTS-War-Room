import { useState, useEffect, useRef } from 'react'

export function useReplayData() {
  const [matches, setMatches] = useState([])
  const [heroes, setHeroes] = useState([])
  const [profile, setProfile] = useState(null)
  const [heroData, setHeroData] = useState({})
  const [talentMap, setTalentMap] = useState({})
  const [talentData, setTalentData] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [dataChanged, setDataChanged] = useState(false)
  const previousMatchCount = useRef(0)

  // Cache metadata to avoid re-fetching
  const metadataCache = useRef({
    heroData: null,
    talentMap: null,
    talentData: null,
    cachedAt: null
  })

  const loadData = async (isInitial = false, query = '') => {
    if (isInitial) setLoading(true)
    try {
      // 1. Fetch Core Data (With search support)
      const searchParam = query ? `&search=${encodeURIComponent(query)}` : ''
      const [historyResponse, profileResponse] = await Promise.all([
        fetch(`/api/match_history?limit=500&pagination=true${searchParam}&t=` + Date.now()).catch(() => null),
        fetch('/api/player_profile?t=' + Date.now()).catch(() => null)
      ])

      if (profileResponse && profileResponse.ok) {
        const profileData = await profileResponse.json()
        setProfile(profileData)
      }

      let historyData = []
      if (historyResponse && historyResponse.ok) {
        const responseData = await historyResponse.json()
        // Handle paginated response
        if (responseData.matches) {
          historyData = responseData.matches
        } else if (Array.isArray(responseData)) {
          // Backward compatibility: direct array response
          historyData = responseData
        }
      }

      // 2. Fetch Metadata (cached to avoid re-fetching)
      const cacheAge = metadataCache.current.cachedAt
        ? Date.now() - metadataCache.current.cachedAt
        : Infinity
      const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

      if (cacheAge < CACHE_DURATION && metadataCache.current.heroData) {
        // Use cached data
        setHeroData(metadataCache.current.heroData)
        setTalentMap(metadataCache.current.talentMap)
        setTalentData(metadataCache.current.talentData)
      } else {
        // Fetch fresh data
        const [heroDataRes, talentMapRes, talentDataRes] = await Promise.all([
          fetch('/api/data/hero_data.json?t=' + Date.now()).catch(e => { console.error("Failed to load hero_data:", e); return null; }),
          fetch('/api/data/talent_id_map.json?t=' + Date.now()).catch(e => { console.error("Failed to load talent_id_map:", e); return null; }),
          fetch('/api/data/talents.json?t=' + Date.now()).catch(e => { console.error("Failed to load talents:", e); return null; })
        ])

        if (heroDataRes && heroDataRes.ok) {
          const data = await heroDataRes.json()
          setHeroData(data)
          metadataCache.current.heroData = data
        }
        if (talentMapRes && talentMapRes.ok) {
          const data = await talentMapRes.json()
          setTalentMap(data)
          metadataCache.current.talentMap = data
        }
        if (talentDataRes && talentDataRes.ok) {
          const data = await talentDataRes.json()
          setTalentData(data)
          metadataCache.current.talentData = data
        }
        metadataCache.current.cachedAt = Date.now()
      }

      // 3. Process History
      if (historyData.length > 0) {
        if (previousMatchCount.current > 0 && historyData.length !== previousMatchCount.current) {
          setDataChanged(true)
          setTimeout(() => setDataChanged(false), 3000)
        }
        previousMatchCount.current = historyData.length
        setMatches(historyData)

        const heroMap = new Map()
        historyData.forEach(match => {
          const heroName = match.hero
          if (!heroName) return

          if (!heroMap.has(heroName)) {
            heroMap.set(heroName, {
              hero: heroName,
              matches: [],
              wins: 0,
              losses: 0,
              games_played: 0,
              win_rate: 0
            })
          }
          const hero = heroMap.get(heroName)
          hero.matches.push(match)
          if (match.result === 'WIN') hero.wins++
          else if (match.result === 'LOSS') hero.losses++

          hero.games_played = hero.wins + hero.losses
          hero.win_rate = hero.games_played > 0
            ? Math.round((hero.wins / hero.games_played) * 100 * 10) / 10
            : 0
        })
        setHeroes(Array.from(heroMap.values()))
      } else {
        setMatches([])
        setHeroes([])
      }

      setLastUpdated(new Date().toISOString())
      setLoading(false)
    } catch (err) {
      console.error('Error in useReplayData:', err)
      setError(err.message)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(true)
    // Only auto-refresh if not searching to avoid interrupting the user
    const refreshInterval = setInterval(() => {
      const searchInput = document.querySelector('input[placeholder*="Search"]');
      if (!searchInput || !searchInput.value) {
        loadData();
      }
    }, 60000)
    const handleFocus = () => loadData()
    window.addEventListener('focus', handleFocus)
    return () => {
      clearInterval(refreshInterval)
      window.removeEventListener('focus', handleFocus)
    }
  }, [])

  const refresh = () => loadData(true)
  const search = (query) => loadData(false, query)

  return {
    matches,
    heroes,
    profile,
    heroData,
    talentMap,
    talentData,
    loading,
    error,
    refresh,
    search,
    lastUpdated,
    dataChanged
  }
}

import { useState, useEffect } from 'react';
import { Sword } from 'lucide-react';
import './WarRoom.css';
import MapIcon from '../components/MapIcon';
import { getMapImagePath, getMapColor } from '../utils/mapUtils';
import { normalizeHeroName } from '../utils/heroUtils';
import BuildDisplay from '../components/BuildDisplay';
import ConfidenceScore from '../components/ConfidenceScore';
import VerificationModal from '../components/VerificationModal';
import { calculateYourStats } from '../utils/statsUtils';
import { useReplayData } from '../hooks/useReplayData';

import ACTIVE_SEASON from '../config/season';
const DEFAULT_SEASON = ACTIVE_SEASON;

const MatchList = ({ hero, mapName, filter, matches, seasonStartDate }) => {
  const [expanded, setExpanded] = useState(false);

  if (!matches) return null;

  const relevantMatches = matches.filter(m =>
    m.hero === hero &&
    m.map === mapName &&
    (filter === 'seasonal' && seasonStartDate ? new Date(m.date || m.timestamp_iso) > new Date(seasonStartDate) : true)
  ).sort((a, b) => new Date(b.date || b.timestamp_iso) - new Date(a.date || a.timestamp_iso));

  if (relevantMatches.length === 0) return null;

  return (
    <div className="mt-1 pl-1">
      <button
        onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        className="text-[9px] text-slate-500 hover:text-cyan-400 flex items-center gap-1 transition-colors"
      >
        <span className="text-[8px]">{expanded ? '▼' : '▶'}</span>
        <span className="underline decoration-slate-700 underline-offset-2">Source: {relevantMatches.length} Replays</span>
      </button>
      {expanded && (
        <div className="pl-2 mt-1 space-y-0.5 border-l border-slate-700/50 ml-1">
          {relevantMatches.map(m => (
            <div key={m.id} className="text-[9px] flex items-center gap-2 font-mono">
              <span className={`font-bold ${m.result?.toUpperCase() === 'WIN' ? 'text-green-500' : 'text-red-500'}`}>
                {m.result?.toUpperCase() === 'WIN' ? 'W' : 'L'}
              </span>
              <span className="text-slate-400">{new Date(m.date || m.timestamp_iso).toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' })}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

function MapButton({ map, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`relative w-full rounded-xl border cursor-pointer overflow-hidden min-h-[100px] flex flex-col transition-all duration-200 group ${isActive
        ? 'border-cyan-500 ring-2 ring-cyan-500 ring-offset-2 ring-offset-[#0f1115]'
        : 'border-white/10 hover:border-white/30'
        } shadow-lg hover:shadow-cyan-500/10 animate-fadeIn`}
      style={{
        backgroundColor: 'rgba(30, 41, 59, 0.4)',
      }}
    >
      <div className="flex-1 w-full relative h-20 min-h-[80px]">
        <MapIcon mapName={map} size="absolute" className="shadow-none opacity-60 group-hover:opacity-100 transition-opacity" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0a0c10] to-transparent opacity-40" />
      </div>

      <div className="w-full bg-[#0a0c10]/95 border-t border-white/5 py-3 px-2 z-10 relative flex items-center justify-center">
        <span className="block text-center font-bold text-[10px] uppercase text-gray-300 group-hover:text-cyan-400 tracking-[0.2em] leading-tight break-words transition-all duration-300 drop-shadow-sm">
          {map}
        </span>
      </div>
    </button>
  );
}

export default function WarRoom({ selectedMap, setSelectedMap }) {
  const { profile, matches: matchHistory, heroData, talentMap, talentData, loading: replayLoading, refresh } = useReplayData();
  const [cerebrateConfig, setCerebrateConfig] = useState(null);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [calculatedStats, setCalculatedStats] = useState(null);
  const [configLoading, setConfigLoading] = useState(true);

  useEffect(() => {
    async function loadConfig() {
      try {
        const configRes = await fetch('/api/cerebrate_config');
        if (configRes.ok) {
          const data = await configRes.json();
          setCerebrateConfig(data);
        }
      } catch (error) {
        console.error("Failed to load War Room config", error);
      } finally {
        setConfigLoading(false);
      }
    }
    loadConfig();
  }, []);

  useEffect(() => {
    if (profile && matchHistory) {
      const stats = calculateYourStats(matchHistory, profile);
      setCalculatedStats(stats);
    }
  }, [profile, matchHistory]);

  const loading = replayLoading || configLoading;

  // Get season config from profile (merged from config on server) or fallback
  const ACTIVE_SEASON = profile?.active_season || cerebrateConfig?.active_season || DEFAULT_SEASON;
  const SEASON_START_DATE = ACTIVE_SEASON.start_date;
  const SEASON_SLUG = ACTIVE_SEASON.slug;
  const SEASON_NAME = ACTIVE_SEASON.name;

  const formatDisplayDate = (dateStr) => {
    if (!dateStr) return '';
    if (dateStr.includes('T')) return new Date(dateStr).toLocaleDateString();
    // For YYYY-MM-DD, use local parts to avoid shift
    const [y, m, d] = dateStr.split('-');
    return `${m}/${d}/${y}`;
  };

  // Helper to get hero portrait
  const getHeroPortrait = (heroName) => {
    return `/images/heroes/${normalizeHeroName(heroName)}.png`;
  };

  // Helper to get map image
  const getMapImage = (mapName) => {
    const normalized = mapName.toLowerCase().replace(/'/g, '').replace(/\s+/g, '-');
    return `/images/maps/${normalized}.png`;
  };


  // Helper to get seasonal build
  const getSeasonBuild = (heroName) => {
    if (!matchHistory) return { build: null, stats: null };

    const s3Matches = matchHistory.filter(m =>
      m.hero === heroName &&
      new Date(m.date || m.timestamp_iso) > new Date(SEASON_START_DATE)
    );

    if (s3Matches.length === 0) return { build: null, stats: null };

    const buildCounts = {};
    s3Matches.forEach(m => {
      // Robust player finding
      const player = m.players?.find(p =>
        (profile && (p.name === profile.battletag || p.name === profile.name)) ||
        p.name === 'CerebrateUser' ||
        p.name === 'Player'
      );

      if (player) {
        const talents = [
          player.stats?.Tier1Talent || 0,
          player.stats?.Tier2Talent || 0,
          player.stats?.Tier3Talent || 0,
          player.stats?.Tier4Talent || 0,
          player.stats?.Tier5Talent || 0,
          player.stats?.Tier6Talent || 0,
          player.stats?.Tier7Talent || 0
        ];

        if (talents[3] === 0) return;

        const buildStr = talents.join('');
        if (!buildCounts[buildStr]) {
          buildCounts[buildStr] = { wins: 0, games: 0 };
        }
        buildCounts[buildStr].games += 1;
        if (m.result?.toUpperCase() === 'WIN') buildCounts[buildStr].wins += 1;
      }
    });

    let best = null;
    let maxScore = -1;
    let bestStats = null;

    Object.entries(buildCounts).forEach(([buildStr, stats]) => {
      const isComplete = !buildStr.includes('0');
      const wr = (stats.wins / stats.games) * 100;
      let score = wr * Math.log(stats.games + 1.1);
      if (!isComplete) score *= 0.5;

      if (score > maxScore) {
        maxScore = score;
        best = buildStr;
        bestStats = { wr, games: stats.games, wins: stats.wins, isComplete };
      }
    });

    return { build: best, stats: bestStats, source: 'RECENT' };
  };

  // Helper to get best build
  const getBestBuild = (heroName) => {
    if (!profile) return { build: null, stats: null, source: 'META' };

    const recent = getSeasonBuild(heroName);
    if (recent.build && recent.stats.games >= 3 && recent.stats.wr >= 50 && recent.stats.isComplete) {
      return recent;
    }

    const builds = profile.talent_builds?.[heroName] || {};
    let best = null;
    let maxScore = -1;
    let bestStats = null;

    Object.entries(builds).forEach(([buildStr, stats]) => {
      // Support legacy dash format and new compact format
      const cleanBuild = buildStr.replace(/-/g, '');
      const isComplete = !cleanBuild.includes('0') && cleanBuild.length >= 7;
      if (!isComplete) return;

      if (stats.games >= 5) {
        const score = stats.wr * Math.log(stats.games);
        if (score > maxScore) {
          maxScore = score;
          best = cleanBuild;
          bestStats = stats;
        }
      }
    });

    if (best) return { build: best, stats: bestStats, source: 'LIFETIME' };

    return { build: null, stats: null, source: 'META' };
  };

  const renderBuild = (heroName, buildInfo) => {
    if (!buildInfo || !buildInfo.build) return null;
    return <BuildDisplay hero={heroName} buildStr={buildInfo.build} stats={buildInfo.stats} source={buildInfo.source} heroData={heroData} talentMap={talentMap} talentData={talentData} />;
  };

  const getBuildStats = (heroName, targetBuild) => {
    if (!targetBuild || !heroName || !profile) return null;
    const builds = profile.talent_builds?.[heroName] || {};
    const entry = Object.entries(builds).find(([k, v]) => k.replace(/-/g, '') === targetBuild);
    return entry ? entry[1] : null;
  };

  if (loading) {
    return <div className="p-10 text-center text-cyan-400 animate-pulse">Initializing War Room Connection...</div>;
  }

  if (!profile) {
    return <div className="p-10 text-center text-red-400">Error loading Profile Intelligence.</div>;
  }

  if (!cerebrateConfig) {
    return <div className="p-10 text-center text-yellow-400">Loading strategic directives...</div>;
  }

  // Season maps
  const s3Maps = (() => {
    const maps = {};

    // Seed with strategy maps to ensure all have cards
    Object.keys(cerebrateConfig?.strategies || {}).forEach(name => {
      maps[name] = { name, w: 0, l: 0 };
    });

    matchHistory.forEach(m => {
      if (new Date(m.date || m.timestamp_iso) > new Date(SEASON_START_DATE)) {
        if (!maps[m.map]) maps[m.map] = { name: m.map, w: 0, l: 0 };
        if (m.result?.toUpperCase() === 'WIN') maps[m.map].w += 1;
        else maps[m.map].l += 1;
      }
    });

    return Object.values(maps).map(m => ({
      ...m,
      wr: (m.w + m.l) > 0 ? parseFloat(((m.w / (m.w + m.l)) * 100).toFixed(1)) : 0
    })).sort((a, b) => b.wr - a.wr);
  })();

  const displayMaps = selectedMap ? s3Maps.filter(m => m.name === selectedMap) : s3Maps;

  // Map strategies
  const mapStrategies = (() => {
    const strategies = {};
    Object.entries(cerebrateConfig?.strategies || {}).forEach(([mapName, data]) => {
      strategies[mapName] = {
        wc: data.desc || "Control Objective",
        bruiser: data.primary?.name || "TBD",
        bruiserBuild: {
          build: data.primary?.code?.replace(/[^0-9]/g, '') || "",
          stats: { wr: parseInt(data.primary?.global || 50), games: 'Meta' },
          source: 'META'
        },
        healer: data.backups?.find(b => b.role === 'Healer')?.name || "TBD",
        healerBuild: {
          build: data.backups?.find(b => b.role === 'Healer')?.code?.replace(/[^0-9]/g, '') || "",
          stats: { wr: parseInt(data.backups?.find(b => b.role === 'Healer')?.global || 50), games: 'Meta' },
          source: 'META'
        },
        mission: cerebrateConfig?.mission_cache?.[mapName] || null
      };
    });
    return strategies;
  })();

  // Analyze map performance
  const analyzeMapPerformance = (mapName) => {
    // Use calculatedStats (from calculateYourStats) for overall hero stats
    // But still use hero_map_stats for map-specific data
    const heroMapStats = profile.hero_map_stats || {};
    const heroStatsMap = {};

    // Build a map of hero stats from calculatedStats for quick lookup
    if (calculatedStats) {
      calculatedStats.forEach(heroStat => {
        heroStatsMap[heroStat.hero] = heroStat;
      });
    }

    const result = {
      proven: [],
      hotStreaks: [],
      pockets: [],
      untapped: [],
      avoid: []
    };

    // Iterate through heroes that have map-specific data OR calculated stats
    const allHeroes = new Set([
      ...Object.keys(heroMapStats),
      ...(calculatedStats ? calculatedStats.map(h => h.hero) : [])
    ]);

    allHeroes.forEach((heroName) => {
      // Get map-specific stats - combine verified stats with parsed matches (like Operational Ledger)
      const mapData = heroMapStats[heroName] || {};
      const heroStats = profile.hero_stats?.[heroName];
      const verifiedSeason = heroStats?.[`verified_${SEASON_SLUG}`];
      const verifiedLifetime = heroStats?.verified_lifetime || heroStats?.verified;

      // Baseline cutoff: verified stats snapshot date (if available)
      const BASELINE_CUTOFF = verifiedSeason?.verified_date || verifiedLifetime?.verified_date || SEASON_START_DATE;
      const s3Matches = matchHistory.filter(m =>
        m.hero === heroName &&
        m.map === mapName &&
        new Date(m.date || m.timestamp_iso) > new Date(SEASON_START_DATE)
      );
      const newReplays = s3Matches.filter(m => new Date(m.date || m.timestamp_iso) > new Date(BASELINE_CUTOFF));

      // Calculate seasonal stats: verified baseline + parsed matches after baseline
      let s3Games = 0;
      let s3Wins = 0;
      if (verifiedSeason && mapName) {
        // Check if verified stats include this map
        const verifiedMapData = (mapData[SEASON_SLUG] || []).find(m => m.game_map === mapName);
        if (verifiedMapData) {
          s3Games = parseInt(verifiedMapData.games_played || 0);
          s3Wins = Math.round(s3Games * (parseFloat(verifiedMapData.win_rate || 0) / 100));
        }
        // Add parsed matches after baseline
        newReplays.forEach(match => {
          s3Games++;
          if (match.result?.toUpperCase() === 'WIN') s3Wins++;
        });
      } else {
        // Fallback to parsed matches only
        s3Matches.forEach(match => {
          s3Games++;
          if (match.result?.toUpperCase() === 'WIN') s3Wins++;
        });
      }
      const s3WR = s3Games > 0 ? (s3Wins / s3Games) * 100 : 0;

      // Get map-specific lifetime stats
      const lifetimeMapData = (mapData.lifetime || []).find(m => m.game_map === mapName);

      // Get overall hero stats from calculatedStats (consistent with other pages)
      const heroStat = heroStatsMap[heroName];
      const lifetimeGames = lifetimeMapData?.games_played || heroStat?.lifetime?.games || 0;
      const lifetimeWR = lifetimeMapData?.win_rate || heroStat?.lifetime?.wr || 0;

      // Calculate overall WR from calculatedStats if available, otherwise from map stats
      let overallWR = 0;
      let totalGames = 0;
      if (heroStat) {
        overallWR = heroStat.lifetime.wr;
        totalGames = heroStat.lifetime.games;
      } else {
        const allLifetimeMaps = mapData.lifetime || [];
        totalGames = allLifetimeMaps.reduce((sum, m) => sum + m.games_played, 0);
        const totalWins = allLifetimeMaps.reduce((sum, m) => sum + (m.games_played * m.win_rate / 100), 0);
        overallWR = totalGames > 0 ? (totalWins / totalGames * 100) : 0;
      }

      const buildInfo = getBestBuild(heroName);

      // Check if this hero has verified stats (for display badge)
      const verified = verifiedSeason || mapData[`verified_${SEASON_SLUG}`];
      const verifiedWR = verifiedSeason?.wr || verified?.win_rate || 0;
      const isVerified = !!verified && s3Games > 0;

      if (lifetimeGames >= 20 && lifetimeWR >= 50) {
        result.proven.push({
          hero: heroName,
          games: lifetimeGames,
          wr: lifetimeWR,
          s3Games,
          s3WR,
          confidence: 'high',
          bestBuild: buildInfo
        });
      } else if (lifetimeGames >= 10 && lifetimeWR >= 50) {
        result.proven.push({
          hero: heroName,
          games: lifetimeGames,
          wr: lifetimeWR,
          s3Games,
          s3WR,
          confidence: 'moderate',
          bestBuild: buildInfo
        });
      }

      if (s3Games >= 5 && s3WR >= 60) {
        result.hotStreaks.push({
          hero: heroName,
          s3Games,
          s3WR,
          lifetimeGames,
          lifetimeWR,
          bestBuild: buildInfo,
          isVerified
        });
      }

      const isPocket = (verified && verifiedWR >= 55) || (lifetimeWR >= 60 && lifetimeGames >= 2 && lifetimeGames < 20);

      if (isPocket) {
        result.pockets.push({
          hero: heroName,
          wr: verified ? verifiedWR : lifetimeWR,
          games: verified ? (verifiedSeason?.games || verified?.games || lifetimeGames) : lifetimeGames,
          s3Games: verified ? (verifiedSeason?.games || verified?.games || s3Games) : s3Games,
          s3WR: verified ? verifiedWR : s3WR,
          isVerified: !!verified,
          notes: verified ? "Verified In-Game" : "High Confidence",
          bestBuild: buildInfo
        });
      }

      if (totalGames >= 10 && overallWR >= 50 && lifetimeGames < 5 && !isPocket) {
        result.untapped.push({
          hero: heroName,
          overallWR,
          totalGames,
          mapGames: lifetimeGames,
          mapWR: lifetimeWR,
          bestBuild: buildInfo
        });
      }

      if (lifetimeGames >= 10 && lifetimeWR < 45) {
        result.avoid.push({
          hero: heroName,
          games: lifetimeGames,
          wr: lifetimeWR,
          s3Games,
          s3WR
        });
      }
    });

    result.proven.sort((a, b) => b.wr - a.wr);
    result.hotStreaks.sort((a, b) => b.s3WR - a.s3WR);
    result.pockets.sort((a, b) => b.wr - a.wr);
    result.untapped.sort((a, b) => b.overallWR - a.overallWR);
    result.avoid.sort((a, b) => a.wr - b.wr);

    return result;
  };

  return (
    <div className="arsenal-page">
      {/* Premium Page Header */}
      <div className="cerebrate-header-card">
        <div className="flex items-center">
          <div className="header-icon-box" style={{ background: 'rgba(234, 179, 8, 0.1)', borderColor: 'rgba(234, 179, 8, 0.2)', color: '#eab308' }}>
            <Sword size={24} />
          </div>
          <div>
            <h1 className="header-title hots-text-glow">War Room</h1>
            <p className="header-subtitle uppercase tracking-widest text-[10px] opacity-70">Tactical Map Directives · {SEASON_NAME}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowVerificationModal(true)}
            className="px-4 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded-full text-[10px] font-bold uppercase tracking-widest text-amber-400 hover:bg-amber-500/20 transition-all flex items-center gap-2"
          >
            📸 Verify Stats
          </button>
          {selectedMap && (
            <button
              onClick={() => setSelectedMap(null)}
              className="px-4 py-1.5 bg-black/40 border border-white/5 rounded-full text-[10px] font-bold uppercase tracking-widest text-cyan-400 hover:bg-white/5 transition-all flex items-center gap-2"
            >
              <span>←</span> All Maps
            </button>
          )}
          <div className="status-indicator" style={{ background: 'rgba(234, 179, 8, 0.1)', borderColor: 'rgba(234, 179, 8, 0.2)', color: '#eab308' }}>
            <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse" />
            Combat Ready
          </div>
        </div>
      </div>

      <VerificationModal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
        onSuccess={() => {
          refresh();
          setShowVerificationModal(false);
        }}
      />

      {/* Overall Parsed Performance */}
      {(() => {
        const seasonMatches = (matchHistory || []).filter(m => new Date(m.date || m.timestamp_iso) > new Date(SEASON_START_DATE));
        if (seasonMatches.length === 0) return null;
        const wins = seasonMatches.filter(m => m.result?.toUpperCase() === 'WIN').length;
        const losses = seasonMatches.length - wins;
        const wr = ((wins / seasonMatches.length) * 100).toFixed(1);

        return (
          <div className="mb-6 p-4 rounded-xl border border-cyan-500/20 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="text-[10px] text-cyan-400 font-black uppercase tracking-widest mb-1 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-pulse"></span>
                  Overall Parsed Performance ({SEASON_NAME})
                </div>
                <p className="text-[11px] text-slate-400">Total win rate across all verified replays processed since {formatDisplayDate(SEASON_START_DATE)}.</p>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex flex-col items-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Games</span>
                  <div className="text-xl font-black text-white">{seasonMatches.length}</div>
                </div>
                <div className="flex flex-col items-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Record</span>
                  <div className="text-xl font-black text-white">{wins} - {losses}</div>
                </div>
                <div className="flex flex-col items-center border-l border-white/10 pl-6">
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-1">Win Rate</span>
                  <div className={`text-2xl font-black leading-none ${wr >= 50 ? 'text-emerald-400' : 'text-cyan-400'}`}>{wr}%</div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Map Directives Grid */}
      {!selectedMap ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {displayMaps.map((map) => (
            <MapButton
              key={map.name}
              map={map.name}
              isActive={false}
              onClick={() => setSelectedMap(map.name)}
            />
          ))}
        </div>
      ) : (
        <div className="map-directives-grid focused-view">
          {displayMaps.map((map, idx) => {
            const strategy = mapStrategies[map.name] || { wc: "No Directive", bruiser: "TBD", healer: "TBD" };
            const mapPerf = analyzeMapPerformance(map.name);

            return (
              <div key={idx} className="map-card">
                <div className="map-card-header">
                  <img
                    src={getMapImage(map.name)}
                    alt={map.name}
                    className="map-image"
                    onError={(e) => e.target.style.display = 'none'}
                  />
                  <div className="map-info">
                    <div className="map-name">{map.name}</div>
                    <ConfidenceScore value={map.wr} n={map.w + map.l} className="scale-75 origin-right" />
                  </div>
                </div>

                <div className="win-condition">
                  Win Condition: {strategy.wc}
                </div>

                {/* Pocket Picks */}
                {mapPerf.pockets.length > 0 && (
                  <div className="hero-section">
                    <div className="section-title pocket">✨ Verified / Pocket Picks</div>
                    {mapPerf.pockets.map((h, i) => (
                      <div key={i} className="hero-item pocket">
                        <div className="hero-info">
                          <><img src={getHeroPortrait(h.hero)} alt={h.hero} className="hero-portrait" onError={(e) => e.target.style.display = 'none'} /><span className="hero-name">{h.hero}</span></>
                          {h.isVerified && <span className="verified-badge">VERIFIED</span>}
                          <ConfidenceScore value={h.wr.toFixed(1)} n={h.games} className="scale-75 origin-right" />
                        </div>
                        <MatchList hero={h.hero} mapName={map.name} filter="seasonal" matches={matchHistory} seasonStartDate={SEASON_START_DATE} />
                        <div className="build-container">
                          {renderBuild(h.hero, h.bestBuild)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Proven Winners */}
                {mapPerf.proven.length > 0 && (
                  <div className="hero-section">
                    <div className="section-title proven">🟢 Proven Winners</div>
                    {mapPerf.proven.slice(0, 2).map((h, i) => (
                      <div key={i} className="hero-item proven">
                        <div className="hero-info">
                          <><img src={getHeroPortrait(h.hero)} alt={h.hero} className="hero-portrait" onError={(e) => e.target.style.display = 'none'} /><span className="hero-name">{h.hero}</span></>
                          <ConfidenceScore value={h.wr.toFixed(1)} n={h.games} className="scale-75 origin-right" />
                        </div>
                        <MatchList hero={h.hero} mapName={map.name} filter="seasonal" matches={matchHistory} seasonStartDate={SEASON_START_DATE} />
                        <div className="build-container">
                          {renderBuild(h.hero, h.bestBuild)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Hot Streaks */}
                {mapPerf.hotStreaks.length > 0 && (
                  <div className="hero-section">
                    <div className="section-title hot">🔥 Hot Streaks ({SEASON_NAME})</div>
                    {mapPerf.hotStreaks.slice(0, 2).map((h, i) => (
                      <div key={i} className="hero-item hot">
                        <div className="hero-info">
                          <><img src={getHeroPortrait(h.hero)} alt={h.hero} className="hero-portrait" onError={(e) => e.target.style.display = 'none'} /><span className="hero-name">{h.hero}</span></>
                          <ConfidenceScore value={h.s3WR.toFixed(1)} n={h.s3Games} className="scale-75 origin-right" />
                        </div>
                        <MatchList hero={h.hero} mapName={map.name} filter="seasonal" matches={matchHistory} seasonStartDate={SEASON_START_DATE} />
                        <div className="build-container">
                          {renderBuild(h.hero, h.bestBuild)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Untapped Potential */}
                {mapPerf.untapped.length > 0 && (
                  <div className="hero-section">
                    <div className="section-title untapped">💎 Untapped Potential</div>
                    {mapPerf.untapped.slice(0, 2).map((h, i) => (
                      <div key={i} className="hero-item untapped">
                        <div className="hero-info">
                          <><img src={getHeroPortrait(h.hero)} alt={h.hero} className="hero-portrait" onError={(e) => e.target.style.display = 'none'} /><span className="hero-name">{h.hero}</span></>
                          <ConfidenceScore value={h.overallWR.toFixed(1)} n={h.totalGames} className="scale-75 origin-right" />
                        </div>
                        <MatchList hero={h.hero} mapName={map.name} filter="seasonal" matches={matchHistory} seasonStartDate={SEASON_START_DATE} />
                        <div className="build-container">
                          {renderBuild(h.hero, h.bestBuild)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Mission Cache Intelligence */}
                {strategy.mission && (
                  <div className="strategy-section mission-intel">
                    <div className="section-title mission">📦 Mission Cache: {map.name} Logic</div>

                    {/* Forensic Bans */}
                    <div className="forensic-bans-container mb-3">
                      <span className="text-[10px] text-red-500 font-bold block mb-1">🚫 DRAFT SHIELD BANS:</span>
                      <div className="flex flex-wrap gap-2">
                        {strategy.mission.bans.map((b, i) => (
                          <div key={i} className="text-[9px] bg-red-900/20 border border-red-500/30 px-2 py-0.5 rounded flex flex-col">
                            <span className="font-bold text-red-400">{b.hero}</span>
                            <span className="text-slate-500 italic text-[8px]">{b.reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Quad-Role Compostion */}
                    <div className="space-y-3">
                      {strategy.mission.heroes.map((h, i) => {
                        const slump = profile.slumping_heroes?.find(s => s.hero === h.hero);
                        return (
                          <div key={i} className={`mission-hero-item p-2 rounded ${h.is_meta ? 'bg-indigo-900/10 border border-indigo-500/20' : 'bg-slate-800/20 border border-slate-700/30'}`}>
                            <div className="flex justify-between items-start mb-1">
                              <div className="flex items-center gap-2">
                                <img src={getHeroPortrait(h.hero)} alt={h.hero} className="w-6 h-6 rounded border border-slate-600" />
                                <div className="flex flex-col">
                                  <span className="text-[11px] font-bold text-slate-200">{h.hero} <span className="text-[8px] text-slate-500">({h.role})</span></span>
                                  <span className="text-[9px] text-cyan-400 font-mono">
                                    {h.wr > 0 && h.games >= 5 ? (
                                      <span className="flex items-center gap-1">
                                        {h.wr}% WR {h.source}
                                        <span className="text-slate-500 text-[8px] italic">(Meta: {h.global_wr})</span>
                                      </span>
                                    ) : (
                                      h.is_meta ? `[Global Meta: ${h.global_wr}]` : `${h.wr}% WR ${h.source}`
                                    )}
                                  </span>
                                </div>
                              </div>
                              {h.is_meta && <span className="text-[8px] bg-indigo-500/20 text-indigo-300 px-1 rounded">SCOUTED</span>}
                            </div>

                            {slump && (
                              <div className="slump-indicator mb-2">
                                <span className="font-bold">⚠️ SLUMP ALERT:</span> {slump.fix}
                              </div>
                            )}

                            <div className="text-[9px] text-slate-400 mb-2 leading-tight">
                              <span className="text-cyan-500/80 font-bold uppercase text-[8px] mr-1">{h.trigger}:</span>
                              {h.insight || "Standard tactical execution required."}
                            </div>
                            <BuildDisplay hero={h.hero} buildStr={h.talent_code} stats={{ wr: h.wr, games: h.games }} source={h.source} heroData={heroData} talentMap={talentMap} talentData={talentData} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Avoid */}
                {mapPerf.avoid.length > 0 && (
                  <div className="avoid-section">
                    <div className="section-title avoid">⚠️ Avoid (WR &lt; 45%)</div>
                    {mapPerf.avoid.slice(0, 5).map((h, i) => (
                      <div key={i} className="avoid-item">
                        <><img src={getHeroPortrait(h.hero)} alt={h.hero} className="hero-portrait" onError={(e) => e.target.style.display = 'none'} /><span className="hero-name">{h.hero}</span></>
                        <ConfidenceScore value={h.wr.toFixed(1)} n={h.games} className="scale-75 origin-right" />
                      </div>
                    ))}
                  </div>
                )}

                {/* Map Status */}
                <div className="map-status">
                  <span className="status-label">Status</span>
                  <div className={`status-badge ${map.wr >= 55 ? 'dominant' : map.wr >= 45 ? 'contested' : 'weak'}`}>
                    {map.wr >= 55 ? 'DOMINANT' : map.wr >= 45 ? 'CONTESTED' : 'WEAK'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

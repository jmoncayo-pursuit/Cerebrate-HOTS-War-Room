import React, { useState, useEffect, useRef, Fragment } from 'react'
import ReactDOM from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Award, AlertTriangle, Target, TrendingUp, Shield, Swords, Heart, Zap, Clock, MessageSquare, CheckCircle, Skull, Crown, ArrowUpCircle, Settings, FileText, Activity, Terminal, BarChart3, Timer, RefreshCw, Users, BrainCircuit, ChevronDown, ChevronUp, Flame } from 'lucide-react'
import HeroPortrait from './HeroPortrait'
import talentData from '../data/talents.json'
// import profileData from '../data/player_profile.json' // Removed
import { formatFullDateTime } from '../utils/dateUtils'
import { normalizeHeroName } from '../utils/heroUtils'
import MatchTimeline from './MatchTimeline'
import HeroText from './HeroText'
import { processHeroIcons } from './HeroText'
import heroData from '../data/hero_data.json'
import talentMapData from '../data/talent_id_map.json'
import BuildDisplay from './BuildDisplay'

const getHeroPortrait = (heroName) => {
    if (!heroName) return '';
    return `/images/heroes/${normalizeHeroName(heroName)}.png`;
};

// --- CUSTOM HOOKS ---

function useEncounteredPlayers() {
    const [interactions, setInteractions] = useState({})
    useEffect(() => {
        fetch('/api/player_interactions')
            .then(res => res.json())
            .then(data => setInteractions(data))
            .catch(err => console.error('Failed to load interactions:', err))
    }, [])
    return interactions
}

// --- HELPER COMPONENTS ---

const EncounterBadge = ({ stats }) => {
    if (!stats || !stats.games) return null;

    const wr = stats.win_rate !== undefined ? Math.round(stats.win_rate) : null;
    const wrColor = wr >= 60 ? 'text-green-300' : wr <= 40 ? 'text-red-300' : 'text-purple-200';

    return (
        <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded bg-purple-500/20 border border-purple-500/40 text-[10px] font-bold shrink-0 cursor-help"
            title={`Played ${stats.games} games together${wr !== null ? ` (${wr}% Win Rate)` : ''}`}>
            <Activity size={10} className="text-purple-300" />
            <span className="text-purple-200">{stats.games}g</span>
            {wr !== null && (
                <span className={`${wrColor} border-l border-white/10 pl-1.5`}>{wr}%</span>
            )}
        </div>
    )
}

const Questionable = ({ children, title, value, context, onDiscuss }) => {
    const [showOption, setShowOption] = useState(false);

    return (
        <>
            {showOption && (
                <div
                    className="fixed inset-0 z-[100] cursor-default"
                    onClick={(e) => {
                        e.stopPropagation()
                        setShowOption(false)
                    }}
                />
            )}
            <div
                className="relative cursor-pointer group"
                onClick={() => setShowOption(!showOption)}
            >
                {children}
                {showOption && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="absolute z-[101] bottom-full mb-2 left-1/2 -translate-x-1/2 bg-[#0f172a] py-2 px-3 rounded text-left border border-cyan-500/50 shadow-xl flex items-center gap-2 hover:bg-cyan-900/40 transition-colors cursor-pointer min-w-[150px] z-50 whitespace-nowrap"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDiscuss({
                                type: 'match_discussion',
                                text: `I want to discuss the ${title}: "${value}".\n\n${context || ''}\n\nWhy is this the assessment?`,
                                topic: title
                            });
                            setShowOption(false);
                        }}
                    >
                        <MessageSquare size={14} className="text-cyan-400 shrink-0" />
                        <span className="text-xs font-bold text-cyan-200">Discuss with Coach?</span>
                    </motion.div>
                )}
            </div>
        </>
    )
}

const TalentImage = ({ hero, tier, talentIndex, talentName, talentMap, size = "md" }) => {
    const [error, setError] = useState(false)

    const tierToLevel = {
        1: 1, 2: 4, 3: 7, 4: 10, 5: 13, 6: 16, 7: 20
    }

    const level = tierToLevel[tier] || tier
    const heroId = normalizeHeroName(hero)

    // Try constructed key first
    let iconFilename = talentMap[`${heroId}-${level}-${talentIndex}`]

    // Fallback to talent name
    if (!iconFilename && talentName) {
        iconFilename = talentMap[talentName]
    }

    // Size classes
    const dims = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'

    if (!iconFilename) {
        return (
            <div className={`${dims} bg-[#1e293b] rounded flex items-center justify-center border border-white/20`} title={talentName || `Lvl ${level}`}>
                <span className="text-[9px] text-gray-500 font-bold">{level}</span>
            </div>
        )
    }

    return (
        <img
            src={`/images/talents/${iconFilename}`}
            alt={`Lvl ${level}`}
            title={talentName || `Lvl ${level}`}
            loading="lazy"
            decoding="async"
            className={`${dims} rounded border border-white/20 shadow-sm bg-black object-cover`}
            onError={() => setError(true)}
        />
    )
}

const formatMMSS = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// --- BANKING LEDGER COMPONENT ---

function EconomyTab({ match, players }) {
    const mapName = match.map || '';
    const ECONOMY_MAPS = [
        "Blackheart's Bay",
        "Tomb of the Spider Queen",
        "Warhead Junction",
        "Cursed Hollow",
        "Garden of Terror",
        "Towers of Doom"
    ];

    const isEconomyMap = ECONOMY_MAPS.some(map => mapName.includes(map));

    // Determine asset name and icon based on map
    const getAssetInfo = (map) => {
        if (map.includes("Blackheart")) return { name: "Doubloons", icon: "🪙", collectedKey: "BlackheartDoubloonsCollected", turnedInKey: "BlackheartDoubloonsTurnedIn" };
        if (map.includes("Spider Queen")) return { name: "Gems", icon: "💎", collectedKey: "GemsCollected", turnedInKey: "GemsTurnedIn" };
        if (map.includes("Warhead")) return { name: "Warheads", icon: "☢️", collectedKey: "WarheadsCollected", turnedInKey: "WarheadsActivated" };
        if (map.includes("Cursed")) return { name: "Tributes", icon: "🏺", collectedKey: "TributesCollected", turnedInKey: "TributesTurnedIn" };
        if (map.includes("Garden")) return { name: "Seeds", icon: "🌱", collectedKey: "SeedsCollected", turnedInKey: "SeedsTurnedIn" };
        if (map.includes("Towers")) return { name: "Altars", icon: "⛩️", collectedKey: "AltarsCaptured", turnedInKey: null };
        return { name: "Objectives", icon: "📦", collectedKey: null, turnedInKey: null };
    };

    const { name: assetName, icon: assetIcon, collectedKey, turnedInKey } = getAssetInfo(mapName);

    if (!collectedKey) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500 uppercase tracking-widest bg-black/20 rounded-lg border border-white/5 gap-4">
                <AlertTriangle size={48} className="text-gray-700" />
                <span>No economy data for this battleground.</span>
            </div>
        );
    }

    // Calculate totals per player
    const playerTotals = players.map(p => {
        const stats = { ...p.stats, ...p.kv_stats };
        const collected = stats[collectedKey] || 0;
        const turnedIn = turnedInKey ? (stats[turnedInKey] || 0) : 0;

        // Calculate likely dropped (collected - turned in)
        // If turned in > collected, they picked up coins from deaths
        const likelyDropped = Math.max(0, collected - turnedIn);
        const pickedUpFromDeaths = Math.max(0, turnedIn - collected);

        return {
            ...p,
            collected,
            turnedIn,
            likelyDropped,
            pickedUpFromDeaths,
            efficiency: collected > 0 ? ((turnedIn / collected) * 100).toFixed(1) : 0
        };
    }).filter(p => p.collected > 0 || p.turnedIn > 0);

    if (playerTotals.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500 uppercase tracking-widest bg-black/20 rounded-lg border border-white/5 gap-4">
                <AlertTriangle size={48} className="text-gray-700" />
                <span>No {assetName.toLowerCase()} activity recorded.</span>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            <div className="bg-[#0f0518]/90 rounded-2xl border border-white/10 overflow-hidden shadow-2xl backdrop-blur-xl">
                <div className="bg-white/5 px-8 py-5 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <TrendingUp size={20} className="text-cyan-400" />
                        <h3 className="text-sm font-black uppercase tracking-[0.2em] text-cyan-400">{assetName} Summary: {mapName}</h3>
                    </div>
                    <div className="px-3 py-1 rounded bg-cyan-500/20 border border-cyan-500/30 text-[10px] font-bold text-cyan-300">
                        {playerTotals.length} PLAYERS
                    </div>
                </div>
                <div className="px-8 py-6">
                    <div className="space-y-4">
                        {playerTotals.map((p, idx) => (
                            <div key={idx} className="bg-white/5 rounded-lg border border-white/10 p-4 hover:bg-white/10 transition-colors">
                                <div className="flex items-center gap-4 mb-3">
                                    <div className="relative shrink-0">
                                        <HeroPortrait heroName={p.hero} size="md" />
                                        <div className="absolute -bottom-1 -right-1 bg-cyan-600 rounded-full w-5 h-5 flex items-center justify-center text-[10px] font-bold border border-white/20">
                                            {p.team === 0 ? 'A' : 'B'}
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <div className="font-black text-sm text-white">{p.name}</div>
                                        <div className="text-[10px] text-gray-400 uppercase">{p.hero}</div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-cyan-500/10 rounded p-3 border border-cyan-500/20">
                                        <div className="text-[10px] text-cyan-400 uppercase font-bold mb-1">Collected</div>
                                        <div className="text-2xl font-black text-white">{assetIcon} {p.collected}</div>
                                    </div>

                                    {turnedInKey && (
                                        <div className="bg-green-500/10 rounded p-3 border border-green-500/20">
                                            <div className="text-[10px] text-green-400 uppercase font-bold mb-1">Turned In</div>
                                            <div className="text-2xl font-black text-white">{assetIcon} {p.turnedIn}</div>
                                        </div>
                                    )}

                                    {p.likelyDropped > 0 && (
                                        <div className="bg-red-500/10 rounded p-3 border border-red-500/20">
                                            <div className="text-[10px] text-red-400 uppercase font-bold mb-1">Likely Dropped</div>
                                            <div className="text-2xl font-black text-white">{assetIcon} {p.likelyDropped}</div>
                                            <div className="text-[9px] text-red-300 mt-1">On death</div>
                                        </div>
                                    )}

                                    {p.pickedUpFromDeaths > 0 && (
                                        <div className="bg-yellow-500/10 rounded p-3 border border-yellow-500/20">
                                            <div className="text-[10px] text-yellow-400 uppercase font-bold mb-1">Picked Up</div>
                                            <div className="text-2xl font-black text-white">{assetIcon} {p.pickedUpFromDeaths}</div>
                                            <div className="text-[9px] text-yellow-300 mt-1">From deaths</div>
                                        </div>
                                    )}

                                    {turnedInKey && p.collected > 0 && (
                                        <div className="bg-purple-500/10 rounded p-3 border border-purple-500/20">
                                            <div className="text-[10px] text-purple-400 uppercase font-bold mb-1">Efficiency</div>
                                            <div className="text-2xl font-black text-white">{p.efficiency}%</div>
                                            <div className="text-[9px] text-purple-300 mt-1">Turn-in rate</div>
                                        </div>
                                    )}
                                </div>

                                {/* Insight messages */}
                                {p.likelyDropped > 0 && (
                                    <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-[11px] text-red-300">
                                        ⚠️ Lost {p.likelyDropped} {assetName.toLowerCase()} on death - critical mistake
                                    </div>
                                )}
                                {p.efficiency < 50 && p.collected > 3 && (
                                    <div className="mt-3 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-[11px] text-yellow-300">
                                        ⚠️ Low turn-in rate ({p.efficiency}%) - holding too long
                                    </div>
                                )}
                                {p.pickedUpFromDeaths > 0 && (
                                    <div className="mt-3 p-2 bg-green-500/10 border border-green-500/30 rounded text-[11px] text-green-300">
                                        ✓ Picked up {p.pickedUpFromDeaths} {assetName.toLowerCase()} from enemy deaths
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded text-[11px] text-blue-300">
                        <strong>Note:</strong> Replay files only contain end-game totals, not per-transaction events.
                        "Likely Dropped" is calculated as (Collected - Turned In).
                        If Turned In &gt; Collected, player picked up coins from enemy deaths.
                    </div>
                </div>
            </div>
        </div>
    );
}

// --- MAIN COMPONENT ---

export default function MatchStatsOverlay({ match: initialMatch, onClose, onDiscuss, className }) {
    if (!initialMatch) return null

    const [activeTab, setActiveTab] = useState('summary')
    const [showChallengeConfirm, setShowChallengeConfirm] = useState(false)
    const [localMatch, setLocalMatch] = useState(initialMatch)
    const [isVerifying, setIsVerifying] = useState(false)
    const [playerProfile, setPlayerProfile] = useState(null)
    const [talentMap, setTalentMap] = useState({})
    const isSyncing = useRef(false)

    useEffect(() => {
        fetch('/api/data/talent_id_map.json')
            .then(res => res.json())
            .then(data => setTalentMap(data))
            .catch(err => console.error("Failed to load talent map", err))
    }, [])

    useEffect(() => {
        if (initialMatch) {
            setLocalMatch(initialMatch)
        }
    }, [initialMatch, initialMatch?.id, initialMatch?.timestamp_iso])

    useEffect(() => {
        fetch('/api/player_profile')
            .then(res => res.json())
            .then(setPlayerProfile)
            .catch(err => console.error(err))
    }, [])

    // NEURAL RE-SYNC: If analysis missing or Stitches/Kharazim/Azmodan missing forensics, fetch full analysis
    useEffect(() => {
        if (!localMatch?.id || isSyncing.current) return
        const a = localMatch.analysis || {}
        const needsForensics = ['Stitches', 'Kharazim', 'Azmodan'].includes(localMatch.hero)
        const hasForensics = a.forensics?.tactical_highlights?.length > 0 || a.forensics?.mechanics?.length > 0
        const needsSync = !a.verdict && Object.keys(a).length === 0
            || (needsForensics && !hasForensics)

        if (!needsSync) return
        isSyncing.current = true
        fetch(`/api/analyze_replay`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ match_id: localMatch.id, force: needsForensics && !hasForensics })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'complete' && data.analysis) {
                    setLocalMatch(prev => ({ ...prev, analysis: data.analysis }))
                }
            })
            .catch(() => {})
            .finally(() => { isSyncing.current = false })
    }, [localMatch?.id, localMatch?.hero, localMatch?.analysis?.forensics])

    const handleForceRefresh = async () => {
        if (isVerifying) return; // Use isVerifying for the refresh state
        setIsVerifying(true);
        console.log(`[Match] Forcing re-analysis for ${localMatch.id}...`);
        try {
            const res = await fetch(`/api/analyze_replay`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ match_id: localMatch.id, force: true }) // Changed True to true
            });
            const data = await res.json();
            if (data.status === 'complete' && data.analysis) {
                console.log(`[Match] Re-analysis complete for ${localMatch.id}`);
                setLocalMatch(prev => ({ ...prev, analysis: data.analysis }));
            }
        } catch (err) {
            console.error("[Match] Forced refresh failed:", err);
        } finally {
            setIsVerifying(false);
        }
    };
    useEffect(() => {
        const handleEscape = (e) => {
            if (e.key === 'Escape' && onClose) {
                onClose()
            }
        }
        window.addEventListener('keydown', handleEscape)
        return () => window.removeEventListener('keydown', handleEscape)
    }, [onClose])

    const { map, hero, result, date, analysis, advanced_stats, players } = localMatch
    const isWin = result?.toUpperCase() === 'WIN'
    const interactions = useEncounteredPlayers()

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className={className || "fixed inset-0 z-50 bg-black/95 backdrop-blur-sm flex items-center justify-center p-4"}
                onClick={onClose}
            >
                {/* Main Container - Full Screen Overlay Style */}
                <div
                    className="w-full h-full flex flex-col relative"
                    onClick={(e) => e.stopPropagation()}
                    style={{
                        background: 'radial-gradient(circle at 50% 50%, #1a0b2e 0%, #050505 100%)'
                    }}
                >

                    {/* Top Bar: Title & Resources */}
                    <div className="flex justify-between items-center px-8 py-4 border-b border-white/10 bg-[#0f0518]/80 shrink-0">
                        {/* Title Section */}
                        <div className="flex flex-col">
                            <h1 className="text-3xl font-black text-white uppercase tracking-wider italic">
                                <span className="text-purple-300 mr-3">{map || 'Unknown Map'}</span>
                                <span className={isWin ? 'text-[#38bdf8] drop-shadow-[0_0_10px_rgba(56,189,248,0.5)]' : 'text-red-500'}>
                                    {isWin ? 'VICTORY' : 'DEFEAT'}
                                </span>
                            </h1>
                            <div className="flex items-center gap-2 text-sm text-gray-400 font-medium">
                                <span>{hero}</span>
                                <span className="w-1 h-1 bg-gray-600 rounded-full" />
                                <span>{formatFullDateTime(date || initialMatch.timestamp_iso)}</span>
                                <span className="w-1 h-1 bg-gray-600 rounded-full" />
                                <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_5px_#22d3ee] animate-pulse" />
                                    <span className="text-[10px] text-cyan-500 font-black uppercase tracking-widest">Analysis v{localMatch.pipeline_version || '2.1.0'}</span>
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-4">
                            <button
                                onClick={onClose}
                                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all"
                            >
                                <X size={24} />
                            </button>
                        </div>
                    </div>


                    <div className="px-8 pt-6 flex gap-8 border-b border-white/5 mx-8 shrink-0">
                        {['summary', 'stats', 'talents', 'personnel', 'timeline'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`pb-4 text-lg font-bold uppercase tracking-widest transition-colors relative ${activeTab === tab ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
                            >
                                {tab}
                                {activeTab === tab && (
                                    <motion.div layoutId="tabLine" className="absolute bottom-0 left-0 right-0 h-1 bg-[#38bdf8] shadow-[0_0_10px_#38bdf8]" />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 overflow-y-auto p-4 md:p-8 flex justify-center">
                        <div className="w-full">
                            {activeTab === 'stats' && <StatsScoreboard match={localMatch} players={players} onDiscuss={onDiscuss} />}
                            {activeTab === 'summary' && <SummaryTab match={localMatch} analysis={localMatch.analysis} onDiscuss={onDiscuss} localMatch={localMatch} setLocalMatch={setLocalMatch} onClose={onClose} handleForceRefresh={handleForceRefresh} isVerifying={isVerifying} playerProfile={playerProfile} talentMap={talentMap} talentData={talentData} heroData={heroData} />}
                            {activeTab === 'talents' && <TalentGrid match={localMatch} players={players} talentMap={talentMap} onDiscuss={onDiscuss} playerProfile={playerProfile} />}
                            {activeTab === 'personnel' && <PersonnelTab match={localMatch} analysis={localMatch.analysis} interactions={interactions} heroData={heroData} />}
                            {activeTab === 'timeline' && (
                                <MatchTimeline
                                    matchId={localMatch.id}
                                    match={localMatch}
                                    userPlayer={localMatch.players?.find(p => p.name === 'Discerning' || p.hero === localMatch.hero)}
                                />
                            )}
                        </div>
                    </div>

                    {/* Footer / Close Button */}
                    <div className="mt-auto py-6 flex justify-center shrink-0 bg-[#0f0518] border-t border-white/5">
                        <button
                            onClick={onClose}
                            className="w-12 h-12 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white/50 hover:text-white transition-all group"
                        >
                            <X size={20} className="group-hover:scale-110 transition-transform" />
                        </button>
                    </div>

                </div>
            </motion.div>
        </AnimatePresence >
    )
}

// --- SCOREBOARD ---

function StatsScoreboard({ match, players, onDiscuss }) {
    const interactions = useEncounteredPlayers()
    const [sortBy, setSortBy] = useState('HeroDamage')
    const [sortDir, setSortDir] = useState('desc')

    // Safety check: ensure players exists and is an array
    if (!players || !Array.isArray(players) || players.length === 0) {
        return (
            <div className="text-center text-gray-400 py-8">
                No player data available for this match.
            </div>
        )
    }

    // Identify user
    const userPlayer = players.find(p =>
        p.name === 'Discerning' ||
        p.name === 'CerebrateUser' ||
        (p.name && p.name.includes('CerebrateUser')) ||
        p.hero === match.hero
    );
    const userTeamId = userPlayer ? userPlayer.team : 0;

    // Sort ALL players together (mixed teams)
    const sortedPlayers = [...players].sort((a, b) => {
        const aVal = a.stats?.[sortBy] || 0
        const bVal = b.stats?.[sortBy] || 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
    })

    // Split into teams AFTER sorting
    const team0 = sortedPlayers.filter(p => p.team === 0)
    const team1 = sortedPlayers.filter(p => p.team === 1)

    // User team on top
    const topTeam = userTeamId === 0 ? team0 : team1;
    const botTeam = userTeamId === 0 ? team1 : team0;

    // Levels - accessing .stats
    const topLvl = topTeam[0]?.stats?.TeamLevel || 0;
    const botLvl = botTeam[0]?.stats?.TeamLevel || 0;

    // Handle column header click
    const handleSort = (column) => {
        if (sortBy !== column) {
            setSortBy(column)
            setSortDir('desc')
        } else if (sortDir === 'desc') {
            setSortDir('asc')
        } else {
            setSortBy('HeroDamage')
            setSortDir('desc')
        }
    }

    return (
        <div className="w-full flex justify-center mt-4">
            <div className="w-full border-[3px] border-[#4c3b7f] bg-[#0c0518] shadow-2xl relative">

                {/* HEADERS */}
                <div className="grid grid-cols-[300px_repeat(7,1fr)] bg-[#1a1033] border-b border-[#2e2158] h-10 select-none pl-[6px]">
                    <div className="pl-4 flex items-center text-xs font-bold text-gray-400 uppercase tracking-wider">
                        Hero
                    </div>
                    <StatHeader label="Kills" sub="Combat" icon={Swords} color="#94a3b8" column="SoloKill" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="Assists" sub="Combat" icon={Heart} color="#fbbf24" column="Assists" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="Deaths" sub="Combat" icon={Skull} color="#a855f7" column="Deaths" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="Siege" sub="Damage" icon={Award} color="#94a3b8" column="SiegeDamage" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="Hero" sub="Damage" icon={Target} color="#94a3b8" column="HeroDamage" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="Healing" sub="Support" icon={Shield} color="#94a3b8" column="Healing" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                    <StatHeader label="XP" sub="Contrib" icon={ArrowUpCircle} color="#c084fc" column="ExperienceContribution" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                </div>

                {/* ALL PLAYERS - MIXED */}
                <div>
                    {sortedPlayers.map((p, i) => {
                        const isUserTeam = p.team === userTeamId
                        return (
                            <PlayerRow
                                key={i}
                                player={p}
                                isUser={p === userPlayer}
                                isTop={isUserTeam}
                                onDiscuss={onDiscuss}
                                interactions={interactions}
                            />
                        )
                    })}
                </div>

            </div>
        </div>
    )
}

function StatHeader({ icon: Icon, color, label, sub, column, sortBy, sortDir, onSort }) {
    const isActive = sortBy === column
    return (
        <div
            className="flex flex-col items-center justify-center border-l border-[#2e2158] h-full relative group cursor-pointer bg-[#1e1b30] hover:bg-[#2a2640] transition-colors"
            onClick={() => onSort && onSort(column)}
        >
            <div className="flex items-center gap-2">
                <Icon size={14} style={{ color: color }} strokeWidth={2.5} />
                <span className="text-xs font-bold text-gray-200 uppercase tracking-wide">{label}</span>
                {isActive && (
                    <span className="text-cyan-400 text-xs">{sortDir === 'desc' ? '↓' : '↑'}</span>
                )}
            </div>
        </div>
    )
}

function PlayerRow({ player, isUser, isTop, onDiscuss, interactions }) {
    // CORRECTED: .stats
    const s = player.stats || {}
    const fmt = (n) => n ? n.toLocaleString() : '-'

    // Team colors: Blue for your team, Red for enemy
    // User gets special cyan highlight
    const rowClass = isUser
        ? 'bg-[#1e3a8a]/50 border-l-[6px] border-l-cyan-400 shadow-lg shadow-cyan-900/20'
        : isTop
            ? 'bg-[#172554]/30 border-l-[6px] border-l-blue-500/60 hover:bg-[#172554]/40'
            : 'bg-[#450a0a]/20 border-l-[6px] border-l-red-500/60 hover:bg-[#450a0a]/30'

    return (
        <div className={`grid grid-cols-[300px_repeat(7,1fr)] h-16 border-b border-[#2e2158] items-center transition-colors ${rowClass}`}>
            {/* Player Info - NOW WITH HERO PORTRAIT */}
            <div className="pl-4 flex items-center gap-4 h-full">
                {/* Hero Portrait Frame */}
                <div className={`relative w-12 h-12 rounded border-2 overflow-hidden shrink-0 shadow-lg group ${isUser ? 'border-cyan-400 shadow-cyan-900/50' : isTop ? 'border-blue-500/50' : 'border-red-500/50'}`}>
                    <HeroPortrait heroName={player.hero} size="full" />
                    {/* Level Badge */}
                    <div className="absolute bottom-0 right-0 bg-black/80 text-[10px] text-white font-bold px-1 border-tl rounded-tl border-white/20">
                        {player.stats?.Level}
                    </div>
                </div>

                {/* Names */}
                <div className="flex flex-col justify-center min-w-0">
                    <span className={`text-sm font-bold truncate ${isUser ? 'text-white' : isTop ? 'text-blue-200' : 'text-red-200'}`}>
                        {player.hero}
                    </span>
                    <div className="flex items-center gap-1.5 min-w-0">
                        <span className={`text-xs truncate ${isUser ? 'text-cyan-300 font-black' : isTop ? 'text-blue-400/70' : 'text-red-400/70'}`}>
                            {player.name}
                        </span>
                        {interactions[player.name] && !isUser && (
                            <EncounterBadge stats={interactions[player.name]} />
                        )}
                    </div>
                </div>
            </div>

            {/* Stats - using s which is .stats */}
            <div className="flex items-center justify-center font-bold text-lg border-l border-[#ffffff]/5 h-full">
                {s.SoloKill > 5 ? (
                    <Questionable
                        title={`${player.hero} Kills`}
                        value={s.SoloKill}
                        context={`${player.name} had ${s.SoloKill} kills in this match`}
                        onDiscuss={onDiscuss}
                    >
                        <span className={`${isTop ? 'text-cyan-400' : 'text-red-400'} cursor-pointer`}>{s.SoloKill ?? 0}</span>
                    </Questionable>
                ) : (
                    <span className="text-white">{s.SoloKill ?? 0}</span>
                )}
            </div>
            <div className="flex items-center justify-center text-white font-bold text-lg border-l border-[#ffffff]/5 h-full">{s.Assists ?? 0}</div>
            <div className="flex items-center justify-center font-bold text-lg border-l border-[#ffffff]/5 h-full">
                {s.Deaths > 5 ? (
                    <Questionable
                        title={`${player.hero} Deaths`}
                        value={s.Deaths}
                        context={`${player.name} died ${s.Deaths} times in this match`}
                        onDiscuss={onDiscuss}
                    >
                        <span className="text-purple-400 cursor-pointer">{s.Deaths ?? 0}</span>
                    </Questionable>
                ) : (
                    <span className="text-[#94a3b8]">{s.Deaths ?? 0}</span>
                )}
            </div>

            <div className="flex items-center justify-center text-white font-medium text-sm border-l border-[#ffffff]/5 h-full">{fmt(s.SiegeDamage)}</div>
            <div className="flex items-center justify-center text-white font-medium text-sm border-l border-[#ffffff]/5 h-full">{fmt(s.HeroDamage)}</div>
            <div className="flex items-center justify-center text-white font-medium text-sm border-l border-[#ffffff]/5 h-full">
                {s.Healing > 0 ? fmt(s.Healing) : (s.SelfHealing > 2000 ? <span className="text-gray-600 text-xs">{fmt(s.SelfHealing)}</span> : '-')}
            </div>
            <div className="flex items-center justify-center text-[#c084fc] font-medium text-sm border-l border-[#ffffff]/5 h-full">{fmt(s.ExperienceContribution)}</div>
        </div>
    )
}

// --- SUMMARY TAB ---

// Sanitize AI output: ensure spaces around **bold** so words don't run together
function sanitizeMarkdown(s) {
    if (!s || typeof s !== 'string') return s;
    return s
        .replace(/\*\*([^*]+)\*\*(?=[^\s])/g, '**$1** ')
        .replace(/([^\s])\*\*([^*]+)\*\*/g, '$1 **$2**');
}

// Helper function to render text with **bold** markdown and hero icons
function renderMarkdown(text) {
    if (!text) return text;
    text = sanitizeMarkdown(text);

    // 1. Process hero names with optional possessives (e.g. "Sylvanas's")
    const HERO_NAMES = Object.keys(heroData).sort((a, b) => b.length - a.length);
    let parts = [text];

    HERO_NAMES.forEach(hero => {
        if (!hero) return;
        let newParts = [];
        parts.forEach(part => {
            if (typeof part !== 'string') {
                newParts.push(part);
                return;
            }

            // Regex for hero name with optional 's (case insensitive, whole word)
            const regex = new RegExp(`\\b(${hero.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})('\\s*s)?\\b`, 'gi');
            const split = part.split(regex);

            // split results in [non-match, hero, 's, non-match, hero, 's, ...]
            // because of the two capturing groups in our regex
            for (let i = 0; i < split.length; i += 3) {
                // The non-matching part
                if (split[i]) newParts.push(split[i]);

                // If we have a hero match at this position
                if (i + 1 < split.length && split[i + 1]) {
                    const heroMatch = split[i + 1];
                    const possessiveMatch = split[i + 2] || '';

                    newParts.push(
                        <span
                            key={`${hero}-${i}-${Math.random()}`}
                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800/80 rounded border border-slate-700/50 mx-0.5 align-middle shadow-sm"
                        >
                            <img
                                src={`/images/heroes/${normalizeHeroName(hero)}.png`}
                                alt={hero}
                                className="w-5 h-5 rounded shadow-inner border border-white/5"
                                onError={(e) => e.target.style.display = 'none'}
                            />
                            <span className="font-bold text-cyan-300 text-[11px] leading-none tracking-tight">
                                {heroMatch}{possessiveMatch}
                            </span>
                        </span>
                    );
                }
            }
        });
        parts = newParts;
    });


    // 2. Process bolding (**text**) on remaining string parts
    const finalParts = [];
    parts.forEach((part, partIdx) => {
        if (typeof part === 'string') {
            const boldSplit = part.split(/(\*\*[^*]+\*\*)/g);
            boldSplit.forEach((bPart, splitIdx) => {
                if (bPart.startsWith('**') && bPart.endsWith('**')) {
                    finalParts.push(
                        <strong key={`bold-${partIdx}-${splitIdx}`} className="text-white font-bold">
                            {bPart.slice(2, -2)}
                        </strong>
                    );
                } else if (bPart) {
                    finalParts.push(bPart);
                }
            });
        } else {
            finalParts.push(part);
        }
    });

    // 3. Process Headers (##)
    const headerProcessedParts = [];
    finalParts.forEach((part, i) => {
        if (typeof part === 'string') {
            // Split by markdown headers
            const headerSplit = part.split(/^(#{1,6})\s+(.+)$/gm);

            // If split has matches, it looks like [pre-text, ##, Header Text, post-text...]
            for (let j = 0; j < headerSplit.length; j++) {
                const chunk = headerSplit[j];
                // Check if this chunk is a header marker
                if (/^#{1,6}$/.test(chunk) && headerSplit[j + 1]) {
                    const level = chunk.length;
                    const content = headerSplit[j + 1];

                    headerProcessedParts.push(
                        <div key={`h${level}-${i}-${j}`} className={`font-bold text-cyan-400 mt-4 mb-2 ${level === 1 ? 'text-xl' : 'text-lg'}`}>
                            {content}
                        </div>
                    );
                    j++; // Skip the content chunk since we used it
                } else if (chunk) {
                    headerProcessedParts.push(chunk);
                }
            }
        } else {
            headerProcessedParts.push(part);
        }
    });


    // 4. Process horizontal rules (---)
    const hrProcessedParts = [];
    headerProcessedParts.forEach((part, i) => {
        if (typeof part === 'string') {
            const hrSplit = part.split(/(^---\s*$)/gm);
            hrSplit.forEach((hrPart, j) => {
                if (hrPart.trim() === '---') {
                    hrProcessedParts.push(<hr key={`hr-${i}-${j}`} className="border-t border-white/10 my-4" />);
                } else if (hrPart) {
                    hrProcessedParts.push(hrPart);
                }
            });
        } else {
            hrProcessedParts.push(part);
        }
    });

    // 5. Process newlines and block elements with an inline accumulator
    const blockProcessedParts = [];
    let currentInlineItems = [];

    const flushInline = (keyBase) => {
        if (currentInlineItems.length > 0) {
            blockProcessedParts.push(
                <div key={keyBase} className="mb-2 text-inherit text-sm leading-relaxed last:mb-0">
                    {currentInlineItems.map((item, idx) => (
                        <Fragment key={idx}>{item}</Fragment>
                    ))}
                </div>
            );
            currentInlineItems = [];
        }
    };

    hrProcessedParts.forEach((part, i) => {
        // Distinguish between block elements (div, hr) and inline elements (string, span, strong)
        const isBlockElement = React.isValidElement(part) && (part.type === 'div' || part.type === 'hr');

        if (isBlockElement) {
            flushInline(`para-before-block-${i}`);
            blockProcessedParts.push(part);
        } else if (typeof part !== 'string') {
            // Inline components (Hero icons, bold text)
            currentInlineItems.push(part);
        } else {
            // Split by newline to respect paragraph breaks and list items
            const lines = part.split('\n');
            lines.forEach((line, j) => {
                const trimmed = line.trim();

                // Double newline or significantly empty line acts as a paragraph break
                if (line === '' && currentInlineItems.length > 0) {
                    flushInline(`para-${i}-${j}`);
                    return;
                }

                if (!trimmed) return;

                // Handle list items
                if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                    flushInline(`para-before-list-${i}-${j}`);
                    blockProcessedParts.push(
                        <div key={`li-${i}-${j}`} className="flex gap-2 mb-1 pl-4 text-cyan-100/80 text-sm">
                            <span className="text-cyan-500/50">•</span>
                            <span className="flex-1">{trimmed.substring(2)}</span>
                        </div>
                    );
                } else {
                    // Normal text line - join with previous if it's a continuation
                    if (currentInlineItems.length > 0) {
                        // Check if the last item was a string and if we need a space
                        const lastItem = currentInlineItems[currentInlineItems.length - 1];
                        if (typeof lastItem === 'string' && !lastItem.endsWith(' ') && !trimmed.startsWith(' ')) {
                            currentInlineItems.push(" ");
                        }
                    }
                    currentInlineItems.push(trimmed);
                }
            });
        }
    });

    // Final flush
    flushInline(`para-final`);

    return <div className="space-y-1">{blockProcessedParts}</div>;
}


function SummaryTab({ match, analysis, onDiscuss, localMatch, setLocalMatch, onClose, handleForceRefresh, isVerifying, playerProfile, talentMap = {}, talentData = {}, heroData = {} }) {
    const [showChallengeConfirm, setShowChallengeConfirm] = useState(false)

    // Get user's stats and team stats for comparison
    const userPlayer = match.players?.find(p =>
        p.name === 'Discerning' ||
        p.name === 'CerebrateUser' ||
        (p.name && p.name.includes('CerebrateUser')) ||
        p.hero === match.hero
    );
    const userStats = userPlayer?.stats || userPlayer?.kv_stats || {};
    const buildKey = userPlayer ? [1, 2, 3, 4, 5, 6, 7].map(tier => userStats[`Tier${tier}Talent`] || 0).join('') : '';
    const buildSpec = userPlayer ? [1, 2, 3, 4, 5, 6, 7].map(tier => userStats[`Tier${tier}Talent`] || 0).join('-') : '';
    const tb = playerProfile?.talent_builds;
    const heroBuilds = tb?.[match.hero] ?? tb?.[match.hero?.toLowerCase()];
    const buildData = (buildKey && heroBuilds?.[buildKey]) ? heroBuilds[buildKey] : null;
    const buildWr = buildData?.wr ?? null;
    const buildGames = buildData?.games ?? null;
    const userTeam = match.players?.filter(p => p.team === userPlayer?.team) || [];

    // Calculate team max for each stat
    const teamMax = {
        HeroDamage: Math.max(0, ...userTeam.map(p => p.stats?.HeroDamage || 0)),
        SiegeDamage: Math.max(0, ...userTeam.map(p => p.stats?.SiegeDamage || 0)),
        Healing: Math.max(0, ...userTeam.map(p => p.stats?.Healing || 0)),
        ExperienceContribution: Math.max(0, ...userTeam.map(p => p.stats?.ExperienceContribution || 0)),
        Assists: Math.max(0, ...userTeam.map(p => p.stats?.Assists || 0)),
    };

    // Helper to render a stat bar
    const StatBar = ({ label, value, max, color, icon: Icon }) => {


        const percentage = max > 0 ? (value / max) * 100 : 0;
        const isTop = value === max && value > 0;

        return (
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Icon size={14} className={color} />
                        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${isTop ? 'text-yellow-400' : 'text-white'}`}>
                            {value.toLocaleString()}
                        </span>
                        {isTop && <Crown size={12} className="text-yellow-400" />}
                    </div>
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/5">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className={`h-full ${color.replace('text-', 'bg-')} shadow-lg`}
                        style={{
                            boxShadow: isTop ? `0 0 10px ${color.replace('text-', '')}` : 'none'
                        }}
                    />
                </div>
            </div>
        );
    };

    // Economy Ranking Logic
    const getEconomyInsight = () => {
        if (!match.players) return null;

        const mapName = match.map || '';
        let key = null;
        let assetName = '';
        let icon = '';

        if (mapName.includes("Blackheart")) {
            key = 'BlackheartDoubloonsTurnedIn';
            assetName = 'Doubloons';
            icon = '🪙';
        } else if (mapName.includes("Spider Queen")) {
            key = 'GemsTurnedIn';
            assetName = 'Gems';
            icon = '💎';
        } else if (mapName.includes("Warhead")) {
            key = 'WarheadsActivated';
            assetName = 'Warheads';
            icon = '☢️';
        } else if (mapName.includes("Cursed")) {
            key = 'TributesCollected';
            assetName = 'Tributes';
            icon = '🏺';
        } else if (mapName.includes("Garden")) {
            key = 'SeedsTurnedIn';
            assetName = 'Seeds';
            icon = '🌱';
        } else if (mapName.includes("Towers")) {
            key = 'AltarsCaptured';
            assetName = 'Altars';
            icon = '⛩️';
        }

        if (!key) return null;

        // Get all players stats for this key
        const playersWithStats = match.players.map(p => ({
            name: p.name,
            hero: p.hero,
            val: (p.stats?.[key] || p.kv_stats?.[key] || 0)
        })).sort((a, b) => b.val - a.val);

        const userStat = userPlayer?.stats?.[key] || userPlayer?.kv_stats?.[key] || 0;
        if (userStat <= 0) return null;

        const rank = playersWithStats.findIndex(p => p.hero === userPlayer?.hero && p.name === userPlayer?.name) + 1;
        const totalPlayers = playersWithStats.length;

        let rankSuffix = 'th';
        if (rank === 1) rankSuffix = 'st';
        else if (rank === 2) rankSuffix = 'nd';
        else if (rank === 3) rankSuffix = 'rd';

        return {
            assetName,
            icon,
            value: userStat,
            rank,
            rankText: rank <= 3 ? (rank === 1 ? 'MOST' : `${rank}${rankSuffix} MOST`) : `${rank}${rankSuffix}`,
            isTop: rank <= 3
        };
    };

    const economyInsight = getEconomyInsight();

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-white relative">
            {/* Background Watermark */}
            <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none overflow-hidden">
                <FileText size={400} />
            </div>

            <div className="space-y-8 z-10">
                {/* Verdict Card */}
                <div className="bg-[#0f172a] border-l-4 border-cyan-500 p-8 shadow-2xl relative rounded-r-lg group hover:bg-[#162038] transition-colors">
                    <div className="absolute right-0 top-0 opacity-10 p-4 transition-transform group-hover:scale-110 duration-700">
                        <Crown size={150} />
                    </div>
                    <div className="flex items-center gap-3 mb-4">
                        <Award className="text-cyan-500" size={24} />
                        <h2 className="text-cyan-500 text-sm font-bold uppercase tracking-widest">Analytical Verdict</h2>
                    </div>
                    <div className="text-5xl font-black text-white mb-6 italic tracking-tight">{analysis?.verdict || "ANALYZING..."}</div>
                    {(buildWr != null || buildSpec) && (
                        <div className="flex items-center gap-3 mb-4 text-sm flex-wrap">
                            <span className="text-slate-500 uppercase tracking-wider font-bold">Build WR</span>
                            {buildWr != null && (
                                <>
                                    <span className={buildWr >= 50 ? 'text-green-400 font-bold' : 'text-red-400 font-bold'}>{Number(buildWr).toFixed(1)}%</span>
                                    {buildGames != null && <span className="text-slate-500">({buildGames}g)</span>}
                                </>
                            )}
                            {buildKey && match.hero && (
                                <span className="inline-block transform scale-90 origin-left">
                                    <BuildDisplay hero={match.hero} buildStr={buildKey} compact stats={{ wr: buildWr ?? undefined, games: buildGames ?? undefined }} source="LIFETIME" talentMap={Object.keys(talentMap || {}).length ? talentMap : talentMapData} talentData={talentData} heroData={heroData} />
                                </span>
                            )}
                        </div>
                    )}
                    <div className="text-gray-300 leading-relaxed text-base font-normal border-t border-white/10 pt-4 space-y-2">
                        {renderMarkdown(analysis?.summary)}
                    </div>
                </div>

                {/* Critical Mistake — hide "None detected" placeholders and offer re-analyze */}
                {(() => {
                    const cm = analysis?.critical_mistake?.trim() || '';
                    const cmLower = cm.toLowerCase();
                    const isPlaceholder = [
                        'none detected', 'no mistakes', 'no mistake', 'none found',
                        'no critical mistake', 'no errors', 'no error', 'perfect game'
                    ].some(p => cmLower.includes(p));
                    if (!cm) return null;
                    if (isPlaceholder) {
                        return (
                            <div className="bg-slate-800/50 border border-amber-500/30 p-6 rounded relative shadow-xl mb-8">
                                <div className="flex items-center gap-3 mb-3 pb-2 border-b border-white/5">
                                    <Activity className="text-amber-400" size={24} />
                                    <h3 className="text-amber-400 font-bold uppercase tracking-wider text-sm">Critical Mistake</h3>
                                </div>
                                <p className="text-gray-400 text-sm mb-4">
                                    This summary was generated before we required opportunity-cost insights. Re-analyze to get a concrete critical mistake (what prevented carrying harder).
                                </p>
                                {handleForceRefresh && (
                                    <button
                                        type="button"
                                        onClick={() => handleForceRefresh()}
                                        disabled={isVerifying}
                                        className="px-4 py-2 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 font-bold text-sm uppercase tracking-wider disabled:opacity-50"
                                    >
                                        {isVerifying ? 'Re-analyzing…' : 'Re-analyze match'}
                                    </button>
                                )}
                            </div>
                        );
                    }
                    return (
                        <div className="bg-[#2a1d0a] border border-orange-500/20 p-6 rounded relative hover:border-orange-500/40 transition-colors shadow-xl mb-8">
                            <div className="flex items-center gap-3 mb-4 pb-2 border-b border-white/5">
                                <div className="p-2 bg-orange-500/10 rounded">
                                    <Activity className="text-orange-400" size={24} />
                                </div>
                                <h3 className="text-orange-400 font-bold uppercase tracking-wider text-sm">Critical Mistake</h3>
                            </div>
                            <Questionable title="Critical Mistake" value={analysis.critical_mistake} onDiscuss={onDiscuss}>
                                <div className="text-orange-100/90 leading-relaxed text-lg font-medium italic">
                                    {renderMarkdown(analysis.critical_mistake)}
                                </div>
                            </Questionable>
                        </div>
                    );
                })()}

                {/* Win Condition */}
                {(analysis?.win_condition || analysis?.win_condition_analysis) && (
                    <div className="bg-[#0f2026] border border-emerald-500/20 p-6 rounded relative hover:border-emerald-500/40 transition-colors shadow-xl mb-8">
                        <div className="flex items-center gap-3 mb-4 pb-2 border-b border-white/5">
                            <div className="p-2 bg-white/5 rounded">
                                <Target className={(match.result?.toUpperCase() === 'WIN') ? 'text-cyan-400' : 'text-red-400'} size={24} />
                            </div>
                            <h3 className="text-emerald-400 font-bold uppercase tracking-wider text-sm">Win Condition</h3>
                        </div>
                        <Questionable title="Win Condition" value={analysis.win_condition || analysis.win_condition_analysis} onDiscuss={onDiscuss}>
                            <p className="text-gray-300 leading-relaxed text-lg whitespace-pre-wrap">{renderMarkdown(analysis.win_condition || analysis.win_condition_analysis)}</p>
                        </Questionable>
                    </div>
                )}

                {/* Summary Stats Visualization */}
                <div className="bg-gradient-to-br from-[#1a0b2e] to-[#0f172a] border border-purple-500/20 rounded-lg p-6 shadow-2xl">
                    <div className="flex items-center gap-2 mb-6 pb-3 border-b border-purple-500/20">
                        <Activity className="text-purple-400" size={24} />
                        <h3 className="text-purple-300 font-bold uppercase tracking-wider text-base">Key Insights</h3>
                    </div>

                    <div className="space-y-4">
                        {/* Display AI-generated Key Insights if available */}
                        {analysis?.key_insights && (
                            <>
                                {(() => {
                                    // Medals / Awards
                                    const user = match.players?.find(p => p.name === 'CerebrateUser' || (p.name && p.name.includes('CerebrateUser')) || p.hero === match.hero);
                                    // Standard parser output often puts awards in 'awards' array or directly in stats as booleans
                                    let awards = user?.awards || [];

                                    // Fallback: Check stats for Boolean awards if array is empty
                                    if (awards.length === 0 && user?.stats) {
                                        Object.keys(user.stats).forEach(key => {
                                            if (key.startsWith('EndOfMatchAward') && key.endsWith('Boolean') && user.stats[key] === 1) {
                                                // Extract name: EndOfMatchAwardMostKillsBoolean -> Most Kills
                                                let name = key.replace('EndOfMatchAward', '').replace('Boolean', '');
                                                // Add spaces to CamelCase
                                                name = name.replace(/([A-Z])/g, ' $1').trim();
                                                awards.push(name);
                                            }
                                        });
                                    }

                                    if (!awards || awards.length === 0) return null;

                                    return (
                                        <div className="bg-black/30 rounded-lg p-5 border border-yellow-500/20">
                                            <div className="text-sm text-yellow-400 uppercase tracking-wider mb-3 font-bold">Medals Earned</div>
                                            <div className="flex flex-wrap gap-2">
                                                {awards.map((a, i) => {
                                                    const name = typeof a === 'string' ? a : (a.award || 'Unknown');
                                                    return (
                                                        <div key={i} className="flex items-center gap-2 bg-yellow-500/10 px-3 py-2 rounded border border-yellow-500/30">
                                                            <Award size={20} className="text-yellow-400" />
                                                            <span className="text-base font-bold text-yellow-100">{name.replace(/_/g, ' ')}</span>
                                                            {a.count > 1 && <span className="text-sm text-yellow-500 font-black">x{a.count}</span>}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                })()}
                                {analysis.key_insights.kill_streak && parseInt(analysis.key_insights.kill_streak) > 0 && (
                                    <div className="bg-black/30 rounded-lg p-5 border border-green-500/20">
                                        <div className="text-sm text-green-400 uppercase tracking-wider mb-3 font-bold">Kill Streak</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Swords size={20} className="text-green-400" />
                                                <span className="text-base text-gray-300">Longest streak</span>
                                            </div>
                                            <span className="text-4xl font-black text-green-300">{analysis.key_insights.kill_streak}</span>
                                        </div>
                                    </div>
                                )}
                                {(() => {
                                    const deathsCount = analysis?.key_insights?.deaths ?? userStats?.Deaths ?? 0;
                                    return (
                                        <div className="bg-black/30 rounded-lg p-5 border border-red-500/20">
                                            <div className="text-sm text-red-400 uppercase tracking-wider mb-3 font-bold">Attrition</div>
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <Skull size={20} className="text-red-400" />
                                                    <span className="text-base text-gray-300">Deaths</span>
                                                </div>
                                                <span className="text-4xl font-black text-red-300">{deathsCount}</span>
                                            </div>
                                        </div>
                                    );
                                })()}
                                {analysis.key_insights.mercenary_camps && parseInt(analysis.key_insights.mercenary_camps) > 0 && (
                                    <div className="bg-black/30 rounded-lg p-5 border border-purple-500/20">
                                        <div className="text-sm text-purple-400 uppercase tracking-wider mb-3 font-bold">Mercenary Camps</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TrendingUp size={20} className="text-purple-400" />
                                                <span className="text-base text-gray-300">Camps captured</span>
                                            </div>
                                            <span className="text-4xl font-black text-purple-300">{analysis.key_insights.mercenary_camps}</span>
                                        </div>
                                    </div>
                                )}
                                {analysis.key_insights.downtime && !["Not Available", "0:00", "0s", "0 seconds"].includes(analysis.key_insights.downtime) && (
                                    <div className="bg-black/30 rounded-lg p-5 border border-red-500/20">
                                        <div className="text-sm text-red-400 uppercase tracking-wider mb-3 font-bold">Downtime</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Skull size={20} className="text-red-400" />
                                                <span className="text-base text-gray-300">Time spent dead</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-4xl font-black text-red-300">{analysis.key_insights.downtime}</div>
                                                <div className="text-[10px] text-gray-500">respawn time</div>
                                            </div>
                                        </div>
                                    </div>
                                )}


                                {economyInsight && (
                                    <div className={`bg-black/30 rounded-lg p-4 border ${economyInsight.isTop ? 'border-yellow-500/30' : 'border-blue-500/20'}`}>
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="text-[10px] text-yellow-400 uppercase tracking-wider font-bold">{economyInsight.assetName} Management</div>
                                            {economyInsight.isTop && <Crown size={12} className="text-yellow-400" />}
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className="text-2xl">{economyInsight.icon}</div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm text-gray-300">Turned In</span>
                                                    <span className={`text-[10px] font-black ${economyInsight.isTop ? 'text-yellow-400' : 'text-blue-400'}`}>
                                                        {economyInsight.rankText} in Match
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className={`text-2xl font-black ${economyInsight.isTop ? 'text-yellow-400' : 'text-white'}`}>
                                                    {economyInsight.value}
                                                </div>
                                                <div className="text-[9px] text-gray-500 uppercase">{economyInsight.assetName}</div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}


                        {/* Extract unique stats from match data (not in Stats tab) - Fallback if no AI insights */}
                        {(!analysis?.key_insights) && (() => {
                            const playerStats = match.players?.find(p => p.name === 'CerebrateUser' || (p.name && p.name.includes('CerebrateUser')) || p.hero === match.hero)?.stats;
                            if (!playerStats) return null;

                            const uniqueInsights = [];

                            // Kill Streak (if 5+)
                            if (playerStats.HighestKillStreak >= 5) {
                                uniqueInsights.push(
                                    <div key="killstreak" className="bg-black/30 rounded-lg p-4 border border-green-500/20">
                                        <div className="text-[10px] text-green-400 uppercase tracking-wider mb-3 font-bold">Kill Streak</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Swords size={16} className="text-green-400" />
                                                <span className="text-sm text-gray-300">Longest streak</span>
                                            </div>
                                            <span className="text-2xl font-black text-green-300">{playerStats.HighestKillStreak}</span>
                                        </div>
                                    </div>
                                );
                            }

                            // CC Time (if significant)
                            const totalCC = (playerStats.TimeCCdEnemyHeroes || 0) + (playerStats.TimeRootingEnemyHeroes || 0) + (playerStats.TimeSilencingEnemyHeroes || 0);
                            if (totalCC >= 30) {
                                uniqueInsights.push(
                                    <div key="cctime" className="bg-black/30 rounded-lg p-4 border border-blue-500/20">
                                        <div className="text-[10px] text-blue-400 uppercase tracking-wider mb-3 font-bold">Crowd Control</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Activity size={16} className="text-blue-400" />
                                                <span className="text-sm text-gray-300">Total CC time</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-2xl font-black text-blue-300">{totalCC}s</div>
                                                <div className="text-[9px] text-gray-500">enemies disabled</div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            }

                            // Merc Camps (if captured any)
                            if (playerStats.MercCampCaptures > 0) {
                                uniqueInsights.push(
                                    <div key="mercs" className="bg-black/30 rounded-lg p-4 border border-purple-500/20">
                                        <div className="text-[10px] text-purple-400 uppercase tracking-wider mb-3 font-bold">Mercenary Camps</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TrendingUp size={16} className="text-purple-400" />
                                                <span className="text-sm text-gray-300">Camps captured</span>
                                            </div>
                                            <span className="text-2xl font-black text-purple-300">{playerStats.MercCampCaptures}</span>
                                        </div>
                                    </div>
                                );
                            }

                            // Time Spent Dead (if significant)
                            if (playerStats.TimeSpentDead >= 60) {
                                uniqueInsights.push(
                                    <div key="deadtime" className="bg-black/30 rounded-lg p-4 border border-red-500/20">
                                        <div className="text-[10px] text-red-400 uppercase tracking-wider mb-3 font-bold">Downtime</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Skull size={16} className="text-red-400" />
                                                <span className="text-sm text-gray-300">Time spent dead</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-2xl font-black text-red-300">{playerStats.TimeSpentDead}s</div>
                                                <div className="text-[9px] text-gray-500">respawn time</div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            }

                            return uniqueInsights;
                        })()}

                        {/* Parse killer stats with timestamps - "**Alarak** (4 deaths: 01:59, 08:20, 15:46, 16:56)" */}
                        {(() => {
                            const text = typeof analysis?.areas_for_improvement === 'string' ? analysis.areas_for_improvement : '';
                            const killerMatch = text.match(/\*\*(\w+)\*\*\s*\((\d+)\s+deaths?:\s*([^)]+)\)/i);

                            if (killerMatch) {
                                const hero = killerMatch[1];
                                const count = parseInt(killerMatch[2]);
                                const timestamps = killerMatch[3].split(',').map(t => t.trim());

                                return (
                                    <div className="bg-black/30 rounded-lg p-4 border border-red-500/20">
                                        <div className="text-[10px] text-red-400 uppercase tracking-wider mb-3 font-bold">Hunted By</div>
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center gap-3">
                                                <div className="w-12 h-12 rounded border-2 border-red-500/50 overflow-hidden">
                                                    <HeroPortrait heroName={hero} size="full" />
                                                </div>
                                                <div>
                                                    <div className="text-sm font-bold text-gray-200">{hero}</div>
                                                    <div className="text-xs text-gray-500">killed you {count} times</div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Skull size={16} className="text-red-400" />
                                                <span className="text-2xl font-black text-red-400">×{count}</span>
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {timestamps.map((time, i) => (
                                                <div key={i} className="px-2 py-1 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-300 font-mono">
                                                    {time}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })()}

                        {/* Parse distance from team at death - "distance of **38.1**" */}
                        {(() => {
                            const text = typeof analysis?.areas_for_improvement === 'string' ? analysis.areas_for_improvement : '';
                            const distanceMatch = text.match(/Your death at (\d+:\d+).*?distance of \*\*([\d.]+)\*\*/i);

                            if (distanceMatch) {
                                const timestamp = distanceMatch[1];
                                const distance = parseFloat(distanceMatch[2]);
                                return (
                                    <div className="bg-black/30 rounded-lg p-4 border border-yellow-500/20">
                                        <div className="text-[10px] text-yellow-400 uppercase tracking-wider mb-3 font-bold">Positional Isolation</div>
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <AlertTriangle size={16} className="text-yellow-400" />
                                                <span className="text-sm text-gray-300">Death at <span className="font-mono text-yellow-300">{timestamp}</span></span>
                                            </div>
                                            <span className="text-2xl font-black text-yellow-300">{distance}</span>
                                        </div>
                                        <div className="text-[10px] text-gray-500">units from nearest ally</div>
                                    </div>
                                );
                            }
                            return null;
                        })()}

                        {/* Parse capital losses (dropped gems, coins, etc.) */}
                        {(() => {
                            const text = (analysis?.summary || '') + ' ' + (typeof analysis?.areas_for_improvement === 'string' ? analysis.areas_for_improvement : '');
                            const capitalMatch = text.match(/Capital Losses.*?(\d+)\s+(gems?|coins?)/i);

                            if (capitalMatch) {
                                const amount = parseInt(capitalMatch[1]);
                                const currency = capitalMatch[2];
                                return (
                                    <div className="bg-black/30 rounded-lg p-4 border border-red-500/20">
                                        <div className="text-[10px] text-red-400 uppercase tracking-wider mb-3 font-bold">Capital Losses</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Skull size={16} className="text-red-400" />
                                                <span className="text-sm text-gray-300">Dropped {currency}</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-2xl font-black text-red-300">{amount}</div>
                                                <div className="text-[9px] text-gray-500">{currency}</div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })()}

                        {/* Parse talent tier disadvantages */}
                        {(() => {
                            const text = (analysis?.summary || '') + ' ' + (analysis?.win_condition_analysis || '');
                            const talentMatch = text.match(/(\d+)\s+talent tiers? (?:behind|down)/i);

                            if (talentMatch) {
                                const tiers = parseInt(talentMatch[1]);
                                return (
                                    <div className="bg-black/30 rounded-lg p-4 border border-orange-500/20">
                                        <div className="text-[10px] text-orange-400 uppercase tracking-wider mb-3 font-bold">Talent Disadvantage</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TrendingUp size={16} className="text-orange-400" />
                                                <span className="text-sm text-gray-300">Tiers behind</span>
                                            </div>
                                            <span className="text-2xl font-black text-orange-300">-{tiers}</span>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })()}

                        {/* Parse kill streaks or shutdown mentions */}
                        {(() => {
                            const text = analysis?.win_condition_analysis || '';
                            const streakMatch = text.match(/(\d+)[-\s]kill streak/i);

                            if (streakMatch) {
                                const kills = parseInt(streakMatch[1]);
                                if (kills <= 0) return null;
                                return (
                                    <div className="bg-black/30 rounded-lg p-4 border border-green-500/20">
                                        <div className="text-[10px] text-green-400 uppercase tracking-wider mb-3 font-bold">Kill Streak</div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Swords size={16} className="text-green-400" />
                                                <span className="text-sm text-gray-300">Consecutive kills</span>
                                            </div>
                                            <span className="text-2xl font-black text-green-300">{kills}</span>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        })()}


                    </div>


                    {/* Other Sections (Deaths, etc.) */}
                    {(() => {
                        let sections = [];
                        if (Array.isArray(analysis?.areas_for_improvement)) {
                            sections = analysis.areas_for_improvement;
                        } else if (analysis?.areas_for_improvement && typeof analysis.areas_for_improvement === 'object') {
                            sections = Object.entries(analysis.areas_for_improvement).map(([title, items]) => ({ title, items }));
                        }

                        // Filter out "Your Kills" to prevent redundancy with tactical timeline
                        return sections.filter(s => {
                            if (s.title === "Your Kills") return false;
                            return true;
                        }).map((section, idx) => {

                            if (!section.title || !section.items) return null;

                            // Deaths section with hero portraits
                            if (section.title?.toLowerCase() === "deaths") {
                                // Check if there are actual deaths (filter out NO_DATA, N/A, empty entries)
                                const validDeaths = section.items.filter(death => {
                                    if (!death) return false;
                                    const isObject = typeof death === 'object';
                                    const time = isObject ? death.time : death.match(/(\d+:\d+)/)?.[1];
                                    const killer = isObject ? death.killer : death.match(/Killed by (\w+)/)?.[1] || death.match(/- (\w+) -/)?.[1];
                                    const context = isObject ? death.context : death;
                                    const deathStr = String(death).toUpperCase();
                                    // Filter out placeholder data
                                    return time && time !== 'N/A' && time !== 'NO_DATA' && 
                                           killer && killer !== 'N/A' && killer !== 'NO_DATA' &&
                                           !deathStr.includes('NO_DATA') && !deathStr.includes('NO DEATHS RECORDED');
                                });

                                // If no valid deaths, show flawless victory message or skip entirely
                                if (validDeaths.length === 0) {
                                    const deathsCount = analysis?.key_insights?.deaths ?? userStats?.Deaths ?? 0;
                                    if (deathsCount === 0) {
                                        // Flawless victory - show clean message
                                        return (
                                            <div key={idx} className="bg-black/30 rounded-lg p-4 border border-green-500/20 shadow-lg shadow-green-900/10">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-full bg-green-500/20 border-2 border-green-500/50 flex items-center justify-center shrink-0">
                                                        <span className="text-green-400 text-xl">✓</span>
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="text-[10px] text-green-400 uppercase tracking-wider mb-1 font-bold">Flawless Victory</div>
                                                        <div className="text-xs text-gray-300">No deaths recorded. Perfect uptime maintained.</div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    }
                                    // If deaths count exists but no valid death items, skip rendering
                                    return null;
                                }

                                return (
                                    <div key={idx} className="bg-black/30 rounded-lg p-4 border border-red-500/20 shadow-lg shadow-red-900/10">
                                        <div className="text-[10px] text-red-400 uppercase tracking-wider mb-3 font-bold">Deaths</div>
                                        <div className="space-y-3">
                                            {validDeaths.map((death, i) => {
                                                // Handle both object and string formats
                                                const isObject = typeof death === 'object';
                                                const time = isObject ? death.time : death.match(/(\d+:\d+)/)?.[1];
                                                const killer = isObject ? death.killer : death.match(/Killed by (\w+)/)?.[1] || death.match(/- (\w+) -/)?.[1];
                                                const context = isObject ? death.context : death;

                                                return (
                                                    <div key={i} className="flex items-center gap-3 p-2 bg-red-500/5 rounded border border-red-500/10">
                                                        {killer && killer !== 'Unknown' && (
                                                            <div className="w-10 h-10 rounded border-2 border-red-500/50 overflow-hidden shrink-0">
                                                                <HeroPortrait heroName={killer} size="full" />
                                                            </div>
                                                        )}
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <span className="text-xs font-mono text-red-300 font-bold">{time}</span>
                                                                {killer && <span className="text-xs text-gray-400">Killed by {killer}</span>}
                                                            </div>
                                                            <div className="text-[11px] text-gray-400">{isObject ? context : context.replace(/^\d+:\d+\s*-\s*/, '').replace(/Killed by \w+\s*-\s*/, '')}</div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                            {section.outnumbered && (
                                                <div className="text-[10px] text-yellow-400 mt-2">⚠️ Outnumbered: {section.outnumbered}</div>
                                            )}
                                        </div>
                                    </div>
                                );
                            }

                            return null;

                        });
                    })()}

                    {/* Parse Objective Occupancy (already in place) */}
                    {(() => {
                        const text = (analysis?.summary || '') + ' ' + (analysis?.dominance || '');
                        const objMatch = text.match(/([\d]+:[\d]+|[\d]+)\s+(?:seconds\s+of\s+)?(?:Temple|Objective|Occupancy)/i);

                        if (objMatch) {
                            let timeStr = objMatch[1];
                            if (!timeStr.includes(':')) {
                                const totalSec = parseInt(timeStr);
                                if (totalSec <= 0) return null;
                                const mins = Math.floor(totalSec / 60);
                                const secs = totalSec % 60;
                                timeStr = `${mins}:${secs.toString().padStart(2, '0')}`;
                            }
                            if (timeStr === '0:00' || timeStr === '00:00') return null;
                            return (
                                <div className="bg-black/30 rounded-lg p-4 border border-cyan-500/20">
                                    <div className="text-[10px] text-cyan-400 uppercase tracking-wider mb-3 font-bold">Objective Control</div>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Timer size={16} className="text-cyan-400" />
                                            <span className="text-sm text-gray-300">Time on Point</span>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-2xl font-black text-cyan-300">{timeStr}</div>
                                            <div className="text-[9px] text-gray-500">MM:SS</div>
                                        </div>
                                    </div>
                                </div>
                            );
                        }
                        return null;
                    })()}
                </div>


            </div>

            <div className="space-y-8 z-10">
                {/* Forensic Deep Dive - Dedicated Mechanical Analytics */}
                {analysis?.forensics && (
                    <div className="bg-[#0f172a] border border-cyan-500/30 rounded-lg p-6 shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Terminal size={100} className="text-cyan-400" />
                        </div>
                        <div className="flex items-center gap-2 mb-6 pb-3 border-b border-cyan-500/20">
                            <BrainCircuit className="text-cyan-400" size={20} />
                            <h3 className="text-cyan-300 font-bold uppercase tracking-wider text-xs">{analysis.forensics.hero_deep_dive || 'Forensic Hero Analysis'}</h3>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            {analysis.forensics.mechanics?.filter(m => m.label !== 'Lethality Rate').map((m, i) => (
                                <div key={i} className="bg-black/30 rounded-lg p-3 border border-cyan-500/10 hover:border-cyan-500/30 transition-colors">
                                    <div className="text-[10px] text-cyan-500/70 uppercase tracking-widest mb-1 font-bold">{m.label}</div>
                                    <Questionable title={m.label} value={m.value} context={m.details} onDiscuss={onDiscuss}>
                                        <div className="text-xl font-black text-white">{m.value}</div>
                                    </Questionable>
                                    {m.details && <div className="text-[9px] text-slate-500 uppercase mt-1">{m.details}</div>}
                                </div>
                            ))}
                        </div>

                        {/* Quest & Lethality Split View */}
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            {analysis.forensics.quest_progression ? (
                                <div className="bg-cyan-500/5 rounded-lg border border-cyan-500/20 p-4 hover:bg-cyan-500/10 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <div className="text-[10px] text-cyan-400 uppercase font-black tracking-widest leading-tight">Quest Progress</div>
                                            <div className="text-sm font-bold text-white truncate">{analysis.forensics.quest_progression.name}</div>
                                        </div>
                                        <div className="px-1.5 py-0.5 bg-cyan-500/20 rounded text-[9px] font-black text-cyan-300 border border-cyan-500/30">
                                            {analysis.forensics.quest_progression.verdict}
                                        </div>
                                    </div>
                                    <div className="flex items-end justify-between">
                                        <div>
                                            <div className="text-2xl font-black text-white leading-none">{analysis.forensics.quest_progression.value}</div>
                                            <div className="text-[9px] text-slate-500 uppercase mt-0.5">{analysis.forensics.quest_progression.stat}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-lg font-black text-cyan-400 leading-none">{analysis.forensics.quest_progression.bonus}</div>
                                            <div className="text-[8px] text-slate-500 uppercase">Reward</div>
                                        </div>
                                    </div>
                                </div>
                            ) : <div />}

                            {(() => {
                                const mechanics = analysis.forensics.mechanics || [];

                                // Azmodan Specific Logic
                                if (match.hero === 'Azmodan') {
                                    const quest = analysis.forensics?.quest_progression || {};
                                    const milestones = quest.milestones || [];
                                    const final_val = quest.value || 0;
                                    const efficiency = (final_val / 400 * 100).toFixed(0);


                                    return (
                                        <div className="bg-orange-500/5 rounded-lg border border-orange-500/20 p-4 hover:bg-orange-500/10 transition-colors col-span-2">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <div className="text-[10px] text-orange-400 uppercase font-black tracking-widest leading-tight">Annihilation Milestone Audit</div>
                                                    <div className="text-xs font-bold text-orange-200">Scaling Velocity</div>
                                                </div>
                                                <div className="px-1.5 py-0.5 bg-orange-500/20 rounded text-[9px] font-black text-orange-300 border border-orange-500/30 font-mono">
                                                    {quest.verdict || 'SCALING'}
                                                </div>
                                            </div>

                                            <div className="relative h-12 flex items-center mb-6 mt-4">
                                                {/* Background Track */}
                                                <div className="absolute inset-x-0 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        style={{ width: `${Math.min(100, (final_val / 400) * 100)}%` }}
                                                        className="h-full bg-gradient-to-r from-orange-600 to-orange-400 transition-all duration-1000 shadow-[0_0_10px_rgba(251,146,60,0.3)]"
                                                    ></div>
                                                </div>

                                                {/* Milestone Markers */}
                                                {[75, 150, 225, 300, 400].map((m, i) => {
                                                    const milestone = milestones.find(ms => ms.stacks === m);
                                                    const pos = (m / 400) * 100;
                                                    const achieved = final_val >= m;

                                                    return (
                                                        <div
                                                            key={i}
                                                            className="absolute top-1/2 -translate-y-1/2 flex flex-col items-center"
                                                            style={{ left: `${pos}%` }}
                                                        >
                                                            <div className={`w-3 h-3 rounded-full border-2 transition-all ${achieved ? 'bg-orange-400 border-white/50 scale-125 shadow-[0_0_15px_rgba(251,146,60,0.6)]' : 'bg-slate-900 border-slate-700'}`}></div>
                                                            <div className={`absolute -top-6 whitespace-nowrap text-[8px] font-black uppercase tracking-tighter ${achieved ? 'text-orange-200' : 'text-slate-600'}`}>
                                                                {m === 400 ? 'MAX' : m}
                                                            </div>
                                                            {milestone && (
                                                                <div className="absolute top-4 flex flex-col items-center">
                                                                    <span className="text-orange-400 font-bold text-[9px] animate-in fade-in slide-in-from-top-1 duration-500">{milestone.time}</span>
                                                                    <span className="text-slate-500 text-[7px] font-mono leading-none tracking-tighter">LVL {milestone.level}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            <div className="flex justify-between items-center mt-4 border-t border-white/5 pt-3">
                                                <div className="flex items-center gap-6">
                                                    <div>
                                                        <div className="text-[8px] text-slate-500 uppercase tracking-widest font-bold">Current Stacks</div>
                                                        <div className="text-xl font-black text-white leading-none">{final_val}<span className="text-[10px] text-slate-500 ml-1">/ 400</span></div>
                                                    </div>
                                                    <div>
                                                        <div className="text-[8px] text-slate-500 uppercase tracking-widest font-bold">Efficiency</div>
                                                        <div className="text-xl font-black text-orange-400 leading-none">{efficiency}%</div>
                                                    </div>
                                                </div>
                                                <Flame size={20} className={`${final_val >= 400 ? 'text-orange-400 animate-pulse' : 'text-orange-900/40'}`} />
                                            </div>
                                        </div>
                                    );
                                }

                                // Kharazim Specific Logic
                                if (match.hero === 'Kharazim') {
                                    const saves = mechanics.find(m => m.label === 'Palm Saves')?.value || 0;
                                    const casts = mechanics.find(m => m.label === 'Palm Casts')?.value || 0;
                                    const saveRate = casts > 0 ? (saves / casts * 100).toFixed(0) + '%' : '0%';

                                    return (
                                        <div className="bg-emerald-500/5 rounded-lg border border-emerald-500/20 p-4 hover:bg-emerald-500/10 transition-colors">
                                            <div className="flex justify-between items-start mb-2">
                                                <div>
                                                    <div className="text-[10px] text-emerald-400 uppercase font-black tracking-widest leading-tight">Divine Save Frequency</div>
                                                    <div className="text-xs font-bold text-emerald-200">Anti-Death Conversion</div>
                                                </div>
                                                <div className="px-1.5 py-0.5 bg-emerald-500/20 rounded text-[9px] font-black text-emerald-300 border border-emerald-500/30">
                                                    PROTECTOR
                                                </div>
                                            </div>
                                            <div className="flex items-end justify-between">
                                                <div>
                                                    <div className="text-3xl font-black text-white leading-none">{saveRate}</div>
                                                    <div className="text-[9px] text-slate-500 uppercase mt-1">Landed Palm → Life %</div>
                                                </div>
                                                <Heart size={24} className="text-emerald-500/20 mb-1" />
                                            </div>
                                        </div>
                                    );
                                }

                                // Stitches Specific Logic
                                const lethalHooks = mechanics.find(m => m.label === 'Lethal Hooks')?.value;
                                const landedHooks = mechanics.find(m => m.label === 'Hooks Landed')?.value;

                                let val = '0%';
                                if (lethalHooks !== undefined && landedHooks !== undefined) {
                                    const lethal = parseInt(lethalHooks);
                                    const landed = parseInt(landedHooks);
                                    if (landed > 0) {
                                        val = ((lethal / landed) * 100).toFixed(1) + '%';
                                    }
                                } else {
                                    const lethality = mechanics.find(m => m.label === 'Lethality Rate');
                                    if (lethality) val = lethality.value;
                                }

                                return (
                                    <div className="bg-red-500/5 rounded-lg border border-red-500/20 p-4 hover:bg-red-500/10 transition-colors">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <div className="text-[10px] text-red-400 uppercase font-black tracking-widest leading-tight">Hook Lethality</div>
                                                <div className="text-xs font-bold text-red-200">Kill Conversion</div>
                                            </div>
                                            <div className="px-1.5 py-0.5 bg-red-500/20 rounded text-[9px] font-black text-red-300 border border-red-500/30">
                                                LETHAL
                                            </div>
                                        </div>
                                        <div className="flex items-end justify-between">
                                            <div>
                                                <div className="text-3xl font-black text-white leading-none">{val}</div>
                                                <div className="text-[9px] text-slate-500 uppercase mt-1">Landed → Kill %</div>
                                            </div>
                                            <Skull size={24} className="text-red-500/20 mb-1" />
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>

                        {/* Distribution Views (Hook or Globe) */}
                        {analysis.forensics.tactical_highlights && match.hero !== 'Azmodan' && (
                            <div className="bg-black/30 rounded-lg p-4 border border-cyan-500/10 mb-6 mx-1">
                                {match.hero === 'Kharazim' ? (
                                    <>
                                        <div className="text-[10px] text-emerald-400 uppercase font-black tracking-widest mb-3 flex justify-between items-center">
                                            <div className="flex items-center gap-2">
                                                <Heart size={12} />
                                                <span>Monastic Output Distribution</span>
                                            </div>
                                            <span className="text-slate-500 font-normal">Sustain Analysis</span>
                                        </div>
                                        <div className="relative flex items-center group/bar">
                                            <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden flex ring-1 ring-white/5 relative z-0">
                                                {(() => {
                                                    const highlights = analysis.forensics.tactical_highlights;
                                                    const saves = highlights.filter(h => h.type === 'SAVE');
                                                    const other = highlights.filter(h => h.type !== 'SAVE');
                                                    const total = highlights.length || 1;

                                                    return (
                                                        <>
                                                            <div style={{ width: `${(saves.length / total) * 100}%` }} className="h-full bg-emerald-400 border-r border-black/20" title={`Saves: ${saves.length}`}></div>
                                                            <div style={{ width: `${(other.length / total) * 100}%` }} className="h-full bg-emerald-900" title={`Other Actions: ${other.length}`}></div>
                                                        </>
                                                    );
                                                })()}
                                            </div>
                                        </div>
                                        <div className="flex justify-between mt-2 text-[9px] uppercase font-bold tracking-tighter">
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></div>
                                                <span className="text-emerald-400">Divine Saves: {analysis.forensics.tactical_highlights.filter(h => h.type === 'SAVE').length}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 bg-emerald-900 rounded-full"></div>
                                                <span className="text-emerald-700">Combat Actions: {analysis.forensics.tactical_highlights.filter(h => h.type !== 'SAVE').length}</span>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="text-[10px] text-cyan-400 uppercase font-black tracking-widest mb-3 flex justify-between items-center">
                                            <div className="flex items-center gap-2">
                                                <img
                                                    src="/images/talents/stitches-7-1.png"
                                                    loading="lazy"
                                                    decoding="async"
                                                    className="w-4 h-4 rounded-full border border-white/10 shadow-[0_0_5px_rgba(168,85,247,0.3)]"
                                                    alt="Serrated Edge"
                                                />
                                                <span>Hook Range Distribution</span>
                                            </div>
                                            <span className="text-slate-500 font-normal">Displacement Analysis</span>
                                        </div>
                                        <div className="relative flex items-center group/bar">
                                            <div className="h-4 w-full bg-slate-800 rounded-full overflow-hidden flex ring-1 ring-white/5 relative z-0">
                                                {(() => {
                                                    const hooks = analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK');
                                                    const short = hooks.filter(h => h.displacement < 6);
                                                    const med = hooks.filter(h => h.displacement >= 6 && h.displacement <= 12);
                                                    const long = hooks.filter(h => h.displacement > 12);

                                                    const total = hooks.length || 1;
                                                    const s_lethal = short.filter(h => h.lethal).length;
                                                    const m_lethal = med.filter(h => h.lethal).length;
                                                    const l_lethal = long.filter(h => h.lethal).length;

                                                    return (
                                                        <>
                                                            <div style={{ width: `${(short.length / total) * 100}%` }} className="h-full bg-slate-600 border-r border-black/20" title={`Short: ${short.length} (${s_lethal} lethal)`}></div>
                                                            <div style={{ width: `${(med.length / total) * 100}%` }} className="h-full bg-cyan-700 border-r border-black/20" title={`Medium: ${med.length} (${m_lethal} lethal)`}></div>
                                                            <div style={{ width: `${(long.length / total) * 100}%` }} className="h-full bg-cyan-400" title={`Long: ${long.length} (${l_lethal} lethal)`}></div>
                                                        </>
                                                    );
                                                })()}
                                            </div>
                                        </div>
                                        <div className="flex justify-between mt-2 text-[9px] uppercase font-bold tracking-tighter">
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 bg-slate-600 rounded-full"></div>
                                                <span className="text-slate-400">Short: {analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement < 6).length} </span>
                                                <span className="text-[7px] text-red-400 opacity-70">({analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement < 6 && h.lethal).length} L)</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 bg-cyan-700 rounded-full"></div>
                                                <span className="text-cyan-600">Med: {analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement >= 6 && h.displacement <= 12).length} </span>
                                                <span className="text-[7px] text-red-400 opacity-70">({analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement >= 6 && h.displacement <= 12 && h.lethal).length} L)</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full"></div>
                                                <span className="text-cyan-400">Long: {analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement > 12).length} </span>
                                                <span className="text-[7px] text-red-500 font-black">({analysis.forensics.tactical_highlights.filter(h => h.type === 'HOOK' && h.displacement > 12 && h.lethal).length} L)</span>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}


                    </div >
                )}

                {/* Neural Attrition Audit - Dedicated Death Logic */}
                {
                    analysis?.forensics?.death_highlights && analysis.forensics.death_highlights.length > 0 && (
                        <div className="bg-[#1a0f1a] border border-red-500/30 rounded-lg p-6 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Skull size={100} className="text-red-500" />
                            </div>
                            <div className="flex items-center gap-2 mb-6 pb-3 border-b border-red-500/20">
                                <Skull className="text-red-400" size={20} />
                                <h3 className="text-red-300 font-bold uppercase tracking-wider text-xs">Neural Attrition Audit</h3>
                            </div>

                            <div className="space-y-3">
                                {analysis.forensics.death_highlights.map((d, i) => {
                                    const isNonPlayer = d.killer === 'Minions / Towers / Mercs' || d.killer === 'Environmental / Structure' || d.killer === 'Unknown';

                                    // Try to find matching context from AI analysis
                                    let deathContext = "";
                                    if (analysis.areas_for_improvement) {
                                        const deathSection = Array.isArray(analysis.areas_for_improvement)
                                            ? analysis.areas_for_improvement.find(s => s.title === "Deaths")
                                            : null;

                                        if (deathSection && deathSection.items) {
                                            const aiDeath = deathSection.items.find(item => {
                                                const aiTime = typeof item === 'object' ? item.time : item.match(/(\d+:\d+)/)?.[1];
                                                return aiTime === d.time;
                                            });
                                            if (aiDeath) {
                                                deathContext = typeof aiDeath === 'object' ? aiDeath.context : aiDeath;
                                                // Clean up if it starts with timestamp/killer
                                                deathContext = deathContext.replace(/^\d+:\d+\s*-\s*/, '').replace(/Killed by \w+\s*-\s*/, '');
                                            }
                                        }
                                    }

                                    return (
                                        <div key={i} className="bg-red-500/5 p-3 rounded border border-red-500/10 hover:bg-red-500/10 transition-colors">
                                            <div className="flex items-center gap-3 mb-2">
                                                <span className="font-mono text-red-400 w-12 shrink-0 font-bold">{d.time}</span>
                                                {isNonPlayer ? (
                                                    <div className="w-8 h-8 flex items-center justify-center bg-slate-800 rounded border border-white/10 shrink-0">
                                                        <Shield size={16} className="text-slate-400" />
                                                    </div>
                                                ) : (
                                                    <div className="w-8 h-8 rounded border-2 border-red-500/30 overflow-hidden shrink-0 bg-black">
                                                        <HeroPortrait heroName={d.killer} size="full" />
                                                    </div>
                                                )}
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-xs text-red-100 font-bold">
                                                        {isNonPlayer ? (
                                                            <span>Destroyed by <span className="text-red-400">{d.killer === 'Unknown' ? 'Environment' : d.killer}</span></span>
                                                        ) : (
                                                            <span>Killed by <span className="text-red-400">{d.killer}</span></span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            {deathContext && (
                                                <div className="text-[11px] text-gray-400 pl-15 leading-relaxed pl-[44px]">
                                                    {deathContext}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )
                }



                {/* YOUR KILLS - DEDICATED TILE */}
                {
                    (() => {
                        let sections = [];
                        if (Array.isArray(analysis?.areas_for_improvement)) {
                            sections = analysis.areas_for_improvement;
                        } else if (analysis?.areas_for_improvement && typeof analysis.areas_for_improvement === 'object') {
                            sections = Object.entries(analysis.areas_for_improvement).map(([title, items]) => ({ title, items }));
                        }

                        let killSection = sections.find(s => s.title === "Your Kills");
                        // Fallback 1: forensics.tactical_highlights (Stitches, Azmodan)
                        if (!killSection && analysis?.forensics?.tactical_highlights?.length) {
                            const killItems = analysis.forensics.tactical_highlights
                                .filter(h => h.type === 'KILL')
                                .map(h => ({ time: h.time || '', victim: h.victim || 'Unknown', context: h.event }));
                            if (killItems.length > 0) {
                                killSection = { title: "Your Kills", items: killItems };
                            }
                        }
                        // Fallback 2: SoloKill from stats when AI omitted Your Kills (Jaina, etc.)
                        const soloKill = userStats?.SoloKill ?? 0;
                        if (!killSection && soloKill > 0) {
                            killSection = { title: "Your Kills", items: [{ time: "SUMMARY", victim: "Stats", context: `${soloKill} eliminations this match` }] };
                        }
                        if (!killSection) return null;



                        return (
                            <div className="bg-[#052e16]/30 border border-green-500/30 p-6 rounded-lg relative hover:bg-[#052e16]/40 transition-all shadow-2xl shadow-green-900/20 group">
                                <div className="absolute right-0 top-0 opacity-10 p-4 transition-transform group-hover:scale-110 duration-700 pointer-events-none">
                                    <Swords size={120} className="text-green-500" />
                                </div>
                                <div className="flex items-center gap-3 mb-6 pb-2 border-b border-white/5">
                                    <div className="p-2 bg-green-500/20 rounded-lg border border-green-500/40">
                                        <Target className="text-green-400" size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-green-400 font-black uppercase tracking-[0.2em] text-xs">Combat Dominance</h3>
                                        <div className="text-white font-bold text-sm">Target Eliminations</div>
                                    </div>
                                    <div className="ml-auto flex flex-col items-end">
                                        <div className="text-2xl font-black text-green-400 leading-none">
                                            {userStats.SoloKill || killSection.items.filter(k => (typeof k === 'object' ? (k.time !== 'SUMMARY' && k.victim !== 'Stats') : !k.includes('SUMMARY'))).length}
                                        </div>
                                        <div className="text-[10px] text-green-500 font-bold uppercase tracking-widest">Kills</div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {killSection.items.map((kill, i) => {
                                        const isObject = typeof kill === 'object';
                                        const time = isObject ? kill.time : kill.match(/(\d+:\d+)/)?.[1];
                                        const victim = isObject ? kill.victim : kill.match(/Killed (\w+)/)?.[1];
                                        const context = isObject ? kill.context : kill.split('-')[1]?.trim();

                                        const isSummary = time === 'SUMMARY' || victim === 'Stats';
                                        const isAssist = victim === 'Assisted';

                                        let PortraitComponent = <HeroPortrait heroName={victim} size="full" />;

                                        if (isSummary) {
                                            PortraitComponent = (
                                                <div className="w-full h-full flex items-center justify-center bg-cyan-950/50 text-cyan-400">
                                                    <BarChart3 size={20} />
                                                </div>
                                            );
                                        } else if (isAssist) {
                                            const realVictim = context?.match(/on\s+([A-Za-z0-9'.\s-]+)/)?.[1];
                                            if (realVictim) {
                                                PortraitComponent = <HeroPortrait heroName={realVictim} size="full" />;
                                            } else {
                                                PortraitComponent = (
                                                    <div className="w-full h-full flex items-center justify-center bg-purple-950/50 text-purple-400">
                                                        <Users size={20} />
                                                    </div>
                                                );
                                            }
                                        }

                                        return (
                                            <div key={i} className="flex items-start gap-3 p-2.5 bg-black/40 rounded border border-green-500/20 hover:border-green-400/50 transition-colors">
                                                {victim && (
                                                    <div className="w-10 h-10 rounded border border-green-500/40 overflow-hidden shrink-0 relative bg-black shadow-inner">
                                                        {PortraitComponent}
                                                    </div>
                                                )}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between gap-2 mb-1">
                                                        <span className="text-[10px] font-mono text-green-400 font-bold bg-green-900/30 px-1.5 py-0.5 rounded border border-green-500/20 shrink-0">{time}</span>
                                                        {victim && !isSummary && !isAssist && <span className="text-[11px] font-black text-white uppercase tracking-tight break-words">{victim}</span>}
                                                    </div>
                                                    {context && <div className="text-[10px] text-gray-400 font-medium leading-relaxed break-words">{context}</div>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })()
                }
            </div >
        </div >
    )
}

// --- TALENT GRID ---

/** Personnel tab: social intel only — neural briefs (aiStrategy), relationship history, match notes, rivalry, dc. */
function PersonnelTab({ match, analysis, interactions = {}, heroData: propHeroData }) {
    const userPlayer = match.players?.find(p => p.name === 'Discerning' || p.hero === match.hero);
    const userTeam = userPlayer?.team ?? 0;
    const heroDataForText = propHeroData ?? {};

    const byName = (() => {
        const map = {};
        Object.values(interactions || {}).forEach(p => {
            const name = p?.name;
            if (!name) return;
            const matches = p.matches || [];
            let winsWith = p.wins_with, totalWith = p.total_with, winsAgainst = p.wins_against, totalAgainst = p.total_against;
            if (totalWith === undefined || totalAgainst === undefined) {
                let ww = 0, tw = 0, wa = 0, ta = 0;
                matches.forEach(m => {
                    if (m.team === 'WITH') { tw++; if (m.result === 'WIN') ww++; }
                    else if (m.team === 'AGAINST') { ta++; if (m.result === 'WIN') wa++; }
                });
                if (totalWith === undefined) { winsWith = ww; totalWith = tw; }
                if (totalAgainst === undefined) { winsAgainst = wa; totalAgainst = ta; }
            }
            map[name] = { ...p, wins_with: winsWith, total_with: totalWith, wins_against: winsAgainst, total_against: totalAgainst };
        });
        return map;
    })();

    const { notable_nodes } = analysis?.social_insights || {};
    const noteByPlayer = (notable_nodes || []).reduce((acc, n) => { acc[n.name] = n.note; return acc; }, {});

    const playersList = match.players || [];
    const gameLength = match.game_length || 0;
    const DC_GRACE = 30; // ignore DCs in last 30s (game effectively over)
    const dcList = playersList
        .filter((p) => (p.disconnected === 1 || p.disconnected === true) && (gameLength - (p.dc_timestamp || 0)) > DC_GRACE)
        .map((p) => ({ name: p.name, hero: p.hero, ts: p.dc_timestamp }));
    const fmtTime = (s) => {
        if (s == null || s === undefined) return '—';
        const m = Math.floor(Number(s) / 60);
        const sec = Math.floor(Number(s) % 60);
        return `${m}:${sec.toString().padStart(2, '0')}`;
    };
    const userWasBanner = match.user_was_banner === 1 || match.user_was_banner === true;
    const enemyBannerName = match.enemy_banner_name || null;
    const newEncounterNames = playersList
        .filter((p) => {
            if (p.name === userPlayer?.name) return false;
            const intel = byName[p.name];
            const withG = intel?.total_with ?? 0;
            const vsG = intel?.total_against ?? 0;
            return withG === 0 && vsG === 0;
        })
        .map((p) => p.name);
    const newEncounterCount = newEncounterNames.length;

    const withYouList = playersList
        .filter((p) => (byName[p.name]?.total_with ?? 0) > 0)
        .map((p) => {
            const intel = byName[p.name];
            const g = intel.total_with ?? 0;
            const wr = (intel.wins_with != null && g > 0) ? (intel.wins_with / g * 100).toFixed(0) : null;
            return { name: p.name, hero: p.hero, g, wr };
        });
    const vsYouList = playersList
        .filter((p) => (byName[p.name]?.total_against ?? 0) > 0)
        .map((p) => {
            const intel = byName[p.name];
            const g = intel.total_against ?? 0;
            const theirWins = intel.wins_against ?? 0;
            const yourWins = g - theirWins;
            return { name: p.name, hero: p.hero, g, yourWins, theirWins };
        });
    const hasBriefList = playersList.filter((p) => byName[p.name]?.aiStrategy).map((p) => p.name);

    const yourTeam = playersList.filter((p) => p.team === userTeam);
    const enemyTeam = playersList.filter((p) => p.team !== userTeam);

    const RosterRow = ({ player, isYou, intel, didDC, dcTime }) => {
        const withG = intel?.total_with ?? 0;
        const vsG = intel?.total_against ?? 0;
        const wrWith = (intel?.wins_with != null && withG > 0) ? (intel.wins_with / withG * 100).toFixed(0) : null;
        const theirWins = intel?.wins_against ?? 0;
        const yourWins = vsG - theirWins;
        const isNewEncounter = !isYou && withG === 0 && vsG === 0;

        let badge = '';
        if (isYou) badge = 'You';
        else if (isNewEncounter) badge = 'New';
        else if (withG > 0) badge = `${withG}g ${wrWith}%`;
        else if (vsG > 0) badge = `${vsG}g you ${yourWins}-${theirWins}`;
        if (didDC && dcTime) badge = badge ? `${badge} · DC ${dcTime}` : `DC ${dcTime}`;
        else if (didDC) badge = badge ? `${badge} · DC` : 'DC';

        return (
            <div className={`flex items-center gap-3 px-3 py-2 ${player.team === userTeam ? 'bg-cyan-500/5' : 'bg-red-500/5'} ${didDC ? 'border-l-2 border-l-amber-500/60' : ''}`}>
                <div className="w-8 h-8 rounded overflow-hidden shrink-0 border border-white/10 bg-black/40">
                    <HeroPortrait heroName={player.hero} size="full" />
                </div>
                <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
                    <span className={`font-bold text-sm truncate ${isYou ? 'text-slate-400' : player.team === userTeam ? 'text-cyan-400' : 'text-red-400'}`}>
                        {isYou ? 'You' : player.name}
                    </span>
                    <span className="text-xs text-slate-500 uppercase shrink-0">{player.hero}</span>
                    {badge && <span className="text-xs text-slate-400">· {badge}</span>}
                    {didDC && <span className="text-[10px] font-bold text-amber-400 bg-amber-500/20 px-1.5 py-0.5 rounded shrink-0">DC</span>}
                </div>
                {!!intel?.aiStrategy && (
                    <span className="text-[10px] text-purple-400 font-medium shrink-0" title={intel.aiStrategy?.slice(0, 80)}>brief</span>
                )}
            </div>
        );
    };

    const empty = !userWasBanner && !enemyBannerName && dcList.length === 0 && newEncounterCount === 0 && withYouList.length === 0 && vsYouList.length === 0 && hasBriefList.length === 0;

    return (
        <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Compact summary: pills + two-column relationship grid */}
            <div className="bg-black/40 border border-white/10 rounded-lg p-4 space-y-4">
                <div className="flex flex-wrap gap-2">
                    {newEncounterCount > 0 && (
                        <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-2.5 py-1">
                            {newEncounterCount} new: {newEncounterNames.slice(0, 5).join(', ')}{newEncounterNames.length > 5 ? ' …' : ''}
                        </span>
                    )}
                    {(userWasBanner || enemyBannerName) && (
                        <span className="text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-full px-2.5 py-1">
                            Banner: {userWasBanner && 'You'}{userWasBanner && enemyBannerName && ' · '}{enemyBannerName && `Enemy ${enemyBannerName}`}
                        </span>
                    )}
                    {dcList.length > 0 && (
                        <span className="text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-full px-2.5 py-1">
                            DC: {dcList.map(({ name, hero, ts }) => `${name} @ ${fmtTime(ts)}`).join(', ')}
                        </span>
                    )}
                </div>

                {(withYouList.length > 0 || vsYouList.length > 0) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {withYouList.length > 0 && (
                            <div>
                                <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-2">Your team · Prior teammates</div>
                                <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-slate-300">
                                    {withYouList.map(({ name, g, wr }) => (
                                        <span key={name}><span className="text-cyan-400 font-medium">{name}</span> {g}g {wr != null ? `${wr}%` : ''}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                        {vsYouList.length > 0 && (
                            <div>
                                <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">Enemy team · Prior opponents</div>
                                <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-slate-300">
                                    {vsYouList.map(({ name, g, yourWins, theirWins }) => (
                                        <span key={name}><span className="text-red-400 font-medium">{name}</span> {g}g you {yourWins}-{theirWins}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {hasBriefList.length > 0 && (
                    <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">
                        Neural briefs: <span className="text-slate-400 font-normal">{hasBriefList.join(', ')}</span>
                    </div>
                )}

                {empty && (
                    <span className="text-slate-500 text-sm">No prior encounter data. Open Social Intelligence to build briefs.</span>
                )}
            </div>

            {/* Roster: Your team | Enemy team */}
            <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-2">Your team</div>
                        <div className="rounded-lg border border-white/10 overflow-hidden bg-black/20 divide-y divide-white/5">
                            {yourTeam.map((player, idx) => (
                                <RosterRow
                                    key={idx}
                                    player={player}
                                    isYou={player.name === userPlayer?.name || player.hero === match.hero}
                                    intel={byName[player.name]}
                                    didDC={player.disconnected === 1 || player.disconnected === true}
                                    dcTime={player.dc_timestamp != null ? fmtTime(player.dc_timestamp) : null}
                                />
                            ))}
                        </div>
                    </div>
                    <div>
                        <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">Enemy team</div>
                        <div className="rounded-lg border border-white/10 overflow-hidden bg-black/20 divide-y divide-white/5">
                            {enemyTeam.map((player, idx) => (
                                <RosterRow
                                    key={idx}
                                    player={player}
                                    isYou={false}
                                    intel={byName[player.name]}
                                    didDC={player.disconnected === 1 || player.disconnected === true}
                                    dcTime={player.dc_timestamp != null ? fmtTime(player.dc_timestamp) : null}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function TalentGrid({ match, players, talentMap, onDiscuss, playerProfile }) {
    const [sortBy, setSortBy] = useState('hero')
    const [sortDir, setSortDir] = useState('asc')
    // const [playerProfile, setPlayerProfile] = useState(null) // Removed

    // Talent tier to level mapping (tier 1-7 -> levels 1, 4, 7, 10, 13, 16, 20)
    const levelToTier = {
        1: 1, 4: 2, 7: 3, 10: 4, 13: 5, 16: 6, 20: 7
    }
    const levels = [1, 4, 7, 10, 13, 16, 20]

    const playerInteractions = useEncounteredPlayers()

    // Identify user
    const userPlayer = players.find(p =>
        p.name === 'Discerning' ||
        p.name === 'CerebrateUser' ||
        (p.name && p.name.includes('CerebrateUser')) ||
        p.hero === match.hero
    );
    const userTeamId = userPlayer ? userPlayer.team : 0

    // Sort players
    const sortedPlayers = [...players].sort((a, b) => {
        if (sortBy === 'hero') {
            return sortDir === 'asc'
                ? a.hero.localeCompare(b.hero)
                : b.hero.localeCompare(a.hero)
        }
        return 0
    })

    const handleSort = (column) => {
        if (sortBy === column) {
            setSortDir(sortDir === 'desc' ? 'asc' : 'desc')
        } else {
            setSortBy(column)
            setSortDir('asc')
        }
    }

    // Helper to find highest talent tier picked
    const getHighestTalentTier = (player) => {
        for (let tier = 7; tier >= 1; tier--) {
            if (player.stats?.[`Tier${tier}Talent`]) {
                return tier
            }
        }
        return 0
    }

    return (
        <div className="w-full flex justify-center mt-4">
            <div className="w-full border-[3px] border-[#4c3b7f] bg-[#0c0518] shadow-2xl relative">

                {/* HEADERS */}
                <div className="grid grid-cols-[180px_repeat(7,minmax(0,1fr))_120px] bg-[#1a1033] border-b border-[#2e2158] h-10 select-none border-l-[6px] border-l-transparent">
                    <div
                        className="pl-6 flex items-center text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-[#2a2640] transition-colors"
                        onClick={() => handleSort('hero')}
                    >
                        Hero {sortBy === 'hero' && (sortDir === 'desc' ? '↓' : '↑')}
                    </div>
                    {levels.map(lvl => (
                        <div key={lvl} className="flex items-center justify-center border-l border-[#2e2158] h-full bg-[#1e1b30] p-2">
                            <span className="text-xs font-bold text-gray-200 uppercase">Lvl {lvl}</span>
                        </div>
                    ))}
                    <div className="flex items-center justify-center border-l border-[#2e2158] h-full bg-[#1e1b30] p-2">
                        <span className="text-xs font-bold text-gray-200 uppercase whitespace-nowrap">Build WR</span>
                    </div>
                </div>

                {/* PLAYER ROWS */}
                <div>
                    {sortedPlayers.map((p, i) => {
                        const isUserTeam = p.team === userTeamId
                        const isUser = p === userPlayer
                        const highestTier = getHighestTalentTier(p)
                        const stats = playerInteractions[p.name]

                        // Row styling
                        const rowClass = isUser
                            ? 'bg-[#1e3a8a]/50 border-l-cyan-400 shadow-lg shadow-cyan-900/20'
                            : isUserTeam
                                ? 'bg-[#172554]/30 border-l-blue-500/60 hover:bg-[#172554]/40'
                                : 'bg-[#450a0a]/20 border-l-red-500/60 hover:bg-[#450a0a]/30'

                        // Build key: no separator (matches player_profile.talent_builds from calculate_build_stats)
                        const buildKey = [1, 2, 3, 4, 5, 6, 7]
                            .map(tier => p.stats?.[`Tier${tier}Talent`] || 0)
                            .join('')
                        const buildHash = [1, 2, 3, 4, 5, 6, 7]
                            .map(tier => p.stats?.[`Tier${tier}Talent`] || 0)
                            .join('-')

                        const buildStats = playerProfile?.talent_builds?.[p.hero]?.[buildKey]
                        const realBuildWR = buildStats?.wr
                        const realBuildGames = buildStats?.games

                        return (
                            <div key={i} className={`grid grid-cols-[180px_repeat(7,minmax(0,1fr))_120px] min-h-[60px] py-0.5 border-b border-[#2e2158] items-center transition-colors hover:brightness-110 border-l-[6px] ${rowClass}`}>
                                {/* Hero Info */}
                                <div className="pl-6 flex items-center gap-3 h-full">
                                    <div className={`w-10 h-10 rounded border-2 overflow-hidden ${isUser ? 'border-cyan-400' : isUserTeam ? 'border-blue-500/50' : 'border-red-500/50'}`}>
                                        <HeroPortrait heroName={p.hero} size="full" />
                                    </div>
                                    <div className="flex flex-col justify-center min-w-0">
                                        <div className={`text-[11px] font-bold truncate leading-tight ${isUser ? 'text-white' : isUserTeam ? 'text-blue-200' : 'text-red-200'}`}>
                                            {p.hero}
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <div className={`text-[9px] truncate font-medium ${isUser ? 'text-cyan-300' : 'text-gray-500'}`}>
                                                {p.name}
                                            </div>
                                            {stats && !isUser && <EncounterBadge stats={stats} mini />}
                                        </div>
                                    </div>
                                </div>

                                {/* Talent Cells */}
                                {levels.map((lvl) => {
                                    const realTier = levelToTier[lvl]
                                    let tIdx = p.stats?.[`Tier${realTier}Talent`]
                                    let tName = null

                                    // Fallback to talents array if Tier stat is missing
                                    if (!tIdx && p.talents && p.talents.length >= realTier) {
                                        const tObj = p.talents[realTier - 1]
                                        if (tObj) {
                                            tName = tObj.talent_name
                                            // Extract index if it's "Talent Index X" or "Talent Name #X"
                                            const match = tName?.match(/(?:Index|#)\s*(\d+)/i)
                                            if (match) tIdx = parseInt(match[1]) + (tName.includes('Index') ? 1 : 0)
                                        }
                                    }

                                    const talentInfo = talentData[p.hero]?.[realTier]?.[tIdx]
                                    const displayTName = tName || talentInfo?.name || (tIdx ? `Talent ${tIdx}` : null)

                                    // Fetch real per-talent WR from player_profile.json
                                    const talentStats = playerProfile?.talent_stats?.[p.hero]?.[realTier]?.[tIdx]
                                    const realWR = talentStats?.wr
                                    const realPR = talentStats?.pr

                                    // Use real data strictly
                                    const displayWR = realWR
                                    const displayPR = realPR

                                    return (
                                        <div key={`${i}-${lvl}`} className="flex flex-col items-center justify-center border-l border-[#2e2158] self-stretch pt-1.5 pb-1.5 px-0.5 group hover:bg-white/5 transition-colors relative">
                                            {tIdx ? (
                                                <div className="relative group/tooltip">
                                                    <Questionable
                                                        title={`${p.hero} Lvl ${lvl}`}
                                                        value={displayTName || `Lvl ${lvl}`}
                                                        context={talentInfo?.description}
                                                        onDiscuss={onDiscuss}
                                                    >
                                                        <div className="flex flex-col items-center gap-1 cursor-help">
                                                            {/* Talent Image */}
                                                            <div className="hover:scale-110 transition-transform">
                                                                <TalentImage
                                                                    hero={p.hero}
                                                                    tier={realTier}
                                                                    talentIndex={tIdx}
                                                                    talentName={tName || talentInfo?.tooltipId}
                                                                    talentMap={talentMap}
                                                                    size="md"
                                                                />
                                                            </div>

                                                            {/* Talent Name */}
                                                            <div className="text-[10px] text-slate-300 text-center leading-tight w-full break-words">
                                                                {displayTName}
                                                            </div>
                                                        </div>
                                                    </Questionable>

                                                    {/* RICH DATA TOOLTIP */}
                                                    <div className="absolute z-[100] bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 bg-[#0f172a] border border-[#334155] rounded shadow-xl p-3 opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none">
                                                        <div className="text-xs font-bold text-white mb-2 border-b border-white/10 pb-1">{tName}</div>

                                                        <div className="space-y-2">
                                                            {/* Personal WR */}
                                                            {isUser && (
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-[10px] text-cyan-400 font-bold uppercase">Your WR</span>
                                                                    {(() => {
                                                                        const pWR = playerProfile?.personal_talent_stats?.[p.hero]?.season_3?.[realTier]?.[tIdx]?.wr
                                                                            ?? playerProfile?.personal_talent_stats?.[p.hero]?.lifetime?.[realTier]?.[tIdx]?.wr;

                                                                        const pGames = playerProfile?.personal_talent_stats?.[p.hero]?.season_3?.[realTier]?.[tIdx]?.games
                                                                            ?? playerProfile?.personal_talent_stats?.[p.hero]?.lifetime?.[realTier]?.[tIdx]?.games;

                                                                        if (pWR !== undefined) {
                                                                            const delta = realWR ? pWR - realWR : 0;
                                                                            return (
                                                                                <div className="flex flex-col items-end">
                                                                                    <span className={`text-xs font-bold ${pWR >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                                                        {pWR.toFixed(1)}%
                                                                                    </span>
                                                                                    <div className="flex gap-1 items-center">
                                                                                        <span className="text-[8px] text-slate-500">{pGames} g</span>
                                                                                        {realWR && (
                                                                                            <span className={`text-[8px] ${delta > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                                                                ({delta > 0 ? '+' : ''}{delta.toFixed(1)}%)
                                                                                            </span>
                                                                                        )}
                                                                                    </div>
                                                                                </div>
                                                                            )
                                                                        }
                                                                        return <span className="text-[10px] text-slate-600">No Data</span>
                                                                    })()}
                                                                </div>
                                                            )}

                                                            {/* Meta WR: only show when we have data */}
                                                            {realWR !== undefined && (
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-[10px] text-slate-400 font-bold uppercase">Meta WR</span>
                                                                    <div className="flex flex-col items-end">
                                                                        <span className={`text-xs font-bold ${realWR >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                                            {realWR.toFixed(1)}%
                                                                        </span>
                                                                        {displayPR != null && (
                                                                            <span className="text-[8px] text-slate-500">PR: {displayPR.toFixed(1)}%</span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>

                                                        <div className="mt-2 flex items-center justify-between gap-2 border-t border-white/5 pt-1">
                                                            <span className="text-[9px] text-slate-500 italic flex-1 min-w-0 truncate" title={talentInfo?.description}>
                                                                {talentInfo?.description?.slice(0, 50) ?? ''}{(talentInfo?.description?.length ?? 0) > 50 ? '…' : ''}
                                                            </span>
                                                            <a href={`https://www.heroesprofile.com/Global/Talents/${(p.hero || '').replace(/\s+/g, '')}`} target="_blank" rel="noopener noreferrer" className="text-[8px] text-blue-400 hover:text-blue-300 whitespace-nowrap">HP</a>
                                                        </div>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="w-10 h-10 bg-white/5 rounded border border-white/10 flex items-center justify-center">
                                                    <span className="text-[8px] text-gray-600">N/A</span>
                                                </div>
                                            )}
                                        </div>
                                    )
                                })}

                                {/* Build Win Rate Column */}
                                <div className="flex flex-col items-center justify-center border-l border-[#2e2158] h-full p-2 gap-1.5 overflow-hidden">
                                    {highestTier > 0 ? (
                                        <>
                                            {/* Copy Build Button */}
                                            <button
                                                onClick={() => {
                                                    const buildString = [1, 2, 3, 4, 5, 6, 7]
                                                        .map(tier => p.stats?.[`Tier${tier}Talent`] || 0)
                                                        .join('-')
                                                    navigator.clipboard.writeText(buildString)
                                                }}
                                                className="text-[8px] px-2 py-0.5 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 rounded border border-purple-500/30 transition-colors"
                                                title="Copy build to clipboard"
                                            >
                                                Copy Build
                                            </button>

                                            {/* Compact Stats Display */}
                                            <div className="flex flex-col gap-0.5 w-full items-center">
                                                {/* My spec WR - only for the player; flag when missing */}
                                                {(p.name?.toLowerCase() === 'discerning' || p.name === playerProfile?.battletag?.split('#')[0]) && (
                                                    (() => {
                                                        const specStats = buildKey ? playerProfile?.talent_builds?.[p.hero]?.[buildKey] : null;

                                                        if (specStats != null && specStats.wr != null) {
                                                            return (
                                                                <div className="flex items-center gap-1">
                                                                    <span className="text-[8px] text-orange-400 uppercase font-bold">SPEC</span>
                                                                    <span className={`text-[9px] font-bold ${specStats.wr >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                                        {Number(specStats.wr).toFixed(1)}%
                                                                    </span>
                                                                    <span className="text-[7px] text-slate-500">({specStats.games ?? 0}g)</span>
                                                                </div>
                                                            );
                                                        }

                                                        const s3Stats = playerProfile?.personal_talent_stats?.[p.hero]?.overall?.season_3;
                                                        const lifetimeStats = playerProfile?.personal_talent_stats?.[p.hero]?.overall?.lifetime;
                                                        const pWR = s3Stats?.wr ?? lifetimeStats?.wr;
                                                        const isS3 = s3Stats?.wr !== undefined;

                                                        if (pWR !== undefined) {
                                                            return (
                                                                <div className="flex items-center gap-1">
                                                                    <span className="text-[8px] text-cyan-400 uppercase font-bold">{isS3 ? 'S3' : 'YOU'}</span>
                                                                    <span className={`text-[9px] font-bold ${pWR >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                                        {Number(pWR).toFixed(1)}%
                                                                    </span>
                                                                </div>
                                                            );
                                                        }

                                                        return (
                                                            <div className="flex items-center gap-1" title="Spec WR not in profile — verify stats to populate">
                                                                <span className="text-[8px] text-amber-400 uppercase font-bold">SPEC</span>
                                                                <span className="text-[8px] text-amber-500/90">Missing</span>
                                                            </div>
                                                        );
                                                    })()
                                                )}

                                                {/* META = global build WR (e.g. Heroes Profile). Only show when different from SPEC so we don't duplicate. */}
                                                {realBuildWR != null && realBuildGames != null && (() => {
                                                    const specWR = (p.name?.toLowerCase() === 'discerning' || p.name === playerProfile?.battletag?.split('#')[0])
                                                        ? (playerProfile?.talent_builds?.[p.hero]?.[buildKey]?.wr ?? null) : null;
                                                    if (specWR !== null && Math.abs(Number(realBuildWR) - Number(specWR)) < 0.01) return null;
                                                    return (
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-[8px] text-slate-400 uppercase font-bold">META</span>
                                                            <span className={`text-[9px] font-bold ${realBuildWR >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                                {Number(realBuildWR).toFixed(1)}%
                                                            </span>
                                                            <span className="text-[7px] text-slate-500">({realBuildGames}g)</span>
                                                        </div>
                                                    );
                                                })()}
                                            </div>

                                            {/* SPEC = your build WR (parsed). META = global build WR → Heroes Profile */}
                                            <a
                                                href={`https://www.heroesprofile.com/Global/Talents/${(p.hero || '').replace(/\s+/g, '')}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-[7px] text-blue-400 hover:text-blue-300 underline"
                                                title="SPEC = your WR with this build. META = global build WR on Heroes Profile"
                                            >
                                                HP (META)
                                            </a>
                                        </>
                                    ) : (
                                        <div className="text-xs text-gray-600">No data</div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>

            </div>
        </div>
    )
}


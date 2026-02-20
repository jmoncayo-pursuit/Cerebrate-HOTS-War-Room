import React, { useState, useEffect, useMemo } from 'react';
import { normalizeHeroName } from '../utils/heroUtils';
import { ChevronRight, Activity, Users, Target, Sword, Swords, AlertTriangle, Search, Info, BarChart3, Shield, Zap, TrendingUp, History, BrainCircuit, ShieldCheck, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import HeroText from './HeroText';
import SelfHealingErrorBoundary from './SelfHealingErrorBoundary';
import VerificationModal from './VerificationModal';
import './PlayerNetwork.css';

// StrategyContent now uses HeroText component
// AuditBadge component for social briefs
const AuditBadge = ({ audit }) => {
    const [expanded, setExpanded] = useState(false);
    if (!audit) return null;

    const { scores, reasoning, hallucinations_identified, verdict } = audit;
    const isPass = verdict === 'PASS';

    const getScoreColor = (score) => {
        if (score >= 4) return 'text-green-400';
        if (score >= 3) return 'text-yellow-400';
        return 'text-red-400';
    };

    return (
        <div className={`mt-3 border rounded-lg overflow-hidden transition-all duration-300 ${isPass ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
            <div
                className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-2">
                    {isPass ? (
                        <ShieldCheck size={16} className="text-emerald-400" />
                    ) : (
                        <AlertCircle size={16} className="text-amber-400" />
                    )}
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${isPass ? 'text-emerald-300' : 'text-amber-300'}`}>
                        Neural Audit: {verdict}
                    </span>
                    <div className="flex gap-2 ml-4">
                        <div className="flex items-center gap-1">
                            <span className="text-[9px] text-gray-500 font-medium">Grounding:</span>
                            <span className={`text-[9px] font-bold ${getScoreColor(scores.grounding)}`}>{scores.grounding}/5</span>
                        </div>
                    </div>
                </div>
                {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
            </div>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-white/5 p-3 space-y-3"
                    >
                        <div>
                            <div className="flex items-center gap-1.5 mb-1">
                                <Info size={12} className="text-gray-400" />
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Auditor Reasoning</span>
                            </div>
                            <p className="text-xs text-gray-300 italic leading-relaxed">"{reasoning}"</p>
                        </div>

                        {hallucinations_identified && hallucinations_identified.length > 0 && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded p-2">
                                <div className="text-[10px] font-bold text-red-400 uppercase tracking-tighter mb-1">Hallucinations Detected</div>
                                <ul className="list-disc pl-4 space-y-1">
                                    {hallucinations_identified.map((h, i) => (
                                        <li key={i} className="text-[10px] text-red-300 italic">{h}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// StrategyContent now handles audits
const StrategyContent = ({ player, heroData }) => {
    if (!player.aiStrategy) return null;
    return (
        <div className="strategy-wrapper">
            <div className="strategy-content text-slate-300 leading-relaxed whitespace-pre-wrap">
                <HeroText text={player.aiStrategy} heroData={heroData} />
            </div>
            {player.audit && <AuditBadge audit={player.audit} />}
        </div>
    );
};

const PlayerNetworkContent = () => {
    const [players, setPlayers] = useState([]);
    const [heroData, setHeroData] = useState(null);
    const [filter, setFilter] = useState('all');
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: 'total', direction: 'desc' });
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);
    const [expandedPlayer, setExpandedPlayer] = useState(null);
    const [generatingStrategy, setGeneratingStrategy] = useState(null);

    const loadData = () => {
        setLoading(true);
        Promise.all([
            fetch('/api/player_interactions').then(res => res.json()),
            fetch('/api/data/hero_data.json').then(res => res.json())
        ])
            .then(([interactionsData, heroDataRes]) => {
                setHeroData(heroDataRes);
                const data = interactionsData;
                // Optimized single-pass processing
                const playerList = Object.values(data).map(p => {
                    const matches = p.matches || [];

                    // Use backend-calculated values if available (faster)
                    let winsWith = p.wins_with;
                    let totalWith = p.total_with;
                    let winsAgainst = p.wins_against;
                    let totalAgainst = p.total_against;

                    // Only recalculate if backend values are missing (single pass through matches)
                    if (winsWith === undefined || totalWith === undefined) {
                        let ww = 0, tw = 0;
                        for (const m of matches) {
                            if (m.team === 'WITH') {
                                tw++;
                                if (m.result === 'WIN') ww++;
                            }
                        }
                        winsWith = ww;
                        totalWith = tw;
                    }

                    if (winsAgainst === undefined || totalAgainst === undefined) {
                        let wa = 0, ta = 0;
                        for (const m of matches) {
                            if (m.team === 'AGAINST') {
                                ta++;
                                if (m.result === 'WIN') wa++;
                            }
                        }
                        winsAgainst = wa;
                        totalAgainst = ta;
                    }

                    return {
                        ...p,
                        matches: matches,
                        wins_with: winsWith,
                        total_with: totalWith,
                        wins_against: winsAgainst,
                        total_against: totalAgainst,
                        winrate_with: totalWith > 0 ? (winsWith / totalWith * 100) : 0,
                        winrate_against: totalAgainst > 0 ? (winsAgainst / totalAgainst * 100) : 0,
                        total_games: totalWith + totalAgainst,
                        last_played: matches.length > 0 ? matches[matches.length - 1].date : null
                    };
                });
                setPlayers(playerList);
                setLoading(false);
            })
            .catch(err => {
                console.error('Failed to load player interactions:', err);
                setLoading(false);
            });
    };

    useEffect(() => { loadData(); }, []);

    useEffect(() => {
        const onProfileRefreshed = () => loadData();
        window.addEventListener('profileRefreshed', onProfileRefreshed);
        return () => window.removeEventListener('profileRefreshed', onProfileRefreshed);
    }, []);

    // Load saved strategies from database (already loaded via API, but check localStorage as fallback)
    useEffect(() => {
        if (players.length > 0) {
            // Strategies should already be loaded from API, but check localStorage as fallback
            const savedStrategies = localStorage.getItem('playerStrategies');
            if (savedStrategies) {
                try {
                    const strategies = JSON.parse(savedStrategies);
                    setPlayers(prev => prev.map(p => {
                        // Prefer API-loaded strategy, fallback to localStorage
                        const strategy = p.aiStrategy || strategies[p.id] || strategies[p.name];
                        return { ...p, aiStrategy: strategy };
                    }));
                } catch (error) {
                    console.error('Failed to load saved strategies:', error);
                }
            }
        }
    }, [players.length]);

    const getHeroPortrait = (heroName) => {
        return `/images/heroes/${normalizeHeroName(heroName)}.png`;
    };

    const generateStrategy = async (player) => {
        setGeneratingStrategy(player.id);

        const isAlly = player.total_with > player.total_against;

        // Analyze hero matchups
        const heroStats = {};
        player.matches.forEach(m => {
            const key = `${m.hero} vs ${m.my_hero}`;
            if (!heroStats[key]) {
                heroStats[key] = { wins: 0, games: 0, hero: m.hero, myHero: m.my_hero };
            }
            heroStats[key].games += 1;
            if (m.result === 'WIN') heroStats[key].wins += 1;
        });

        const matchups = Object.values(heroStats)
            .filter(s => s.games >= 2)
            .sort((a, b) => b.games - a.games)
            .slice(0, 3)
            .map(s => `${s.hero} (${s.wins}W-${s.games - s.wins}L)`)
            .join(', ');

        const recentHeroes = [...new Set(player.matches.slice(-10).map(m => m.hero))].slice(0, 5);
        const yourHeroes = [...new Set(player.matches.slice(-10).map(m => m.my_hero))].slice(0, 3);
        const recentMaps = [...new Set(player.matches.slice(-10).map(m => m.map))].filter(Boolean).slice(0, 3);

        const prompt = isAlly
            ? `You are a HOTS tactical analyst. Generate a concise synergy strategy for playing WITH ${player.name}.

PLAYER DATA:
- Name: ${player.name}
- Games together: ${player.total_with}
- Win rate: ${player.winrate_with.toFixed(1)}%
- Their hero pool: ${recentHeroes.join(', ')}
- Your hero pool: ${yourHeroes.join(', ')}
- Common matchups: ${matchups || 'Limited data'}
- Recent maps: ${recentMaps.join(', ') || 'Various'}

INSTRUCTIONS:
Write a tactical brief in plain text (no markdown, no asterisks, no formatting). Use numbered sections:

1. SYNERGY PICKS - Which of your heroes complement their pool best and why
2. COMMUNICATION - Specific callouts and timing windows to coordinate
3. WIN CONDITION - How to leverage your combined strengths to close games

Keep it under 200 words. Be specific with hero names and tactical details.`
            : `You are a HOTS tactical analyst. Generate a concise counter strategy for playing AGAINST ${player.name}.

PLAYER DATA:
- Name: ${player.name}
- Games against: ${player.total_against}
- Win rate vs them: ${player.winrate_against.toFixed(1)}%
- Their hero pool: ${recentHeroes.join(', ')}
- Your hero pool: ${yourHeroes.join(', ')}
- Common matchups: ${matchups || 'Limited data'}
- Recent maps: ${recentMaps.join(', ') || 'Various'}

INSTRUCTIONS:
Write a tactical brief in plain text (no markdown, no asterisks, no formatting). Use numbered sections:

1. COUNTER PICKS - Which heroes shut down their pool and specific matchup advantages
2. EXPLOIT WEAKNESSES - Their predictable patterns, positioning mistakes, or hero-specific vulnerabilities
3. WIN CONDITION - How to punish their mistakes and secure the win

Keep it under 200 words. Be specific with hero names and tactical details.`;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: prompt })
            });
            const data = await response.json();

            // Update player with strategy
            setPlayers(prev => {
                const updated = prev.map(p =>
                    p.id === player.id
                        ? { ...p, aiStrategy: data.response, audit: data.audit }
                        : p
                );

                // Save to database
                try {
                    fetch(`/api/player_interactions/${player.id}/neural_brief`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ brief: data.response })
                    }).catch(err => console.error('Failed to save to database:', err));
                } catch (error) {
                    console.error('Failed to save neural brief:', error);
                }

                // Also save to localStorage as backup
                const strategies = {};
                updated.forEach(p => {
                    if (p.aiStrategy) {
                        strategies[p.id] = p.aiStrategy;
                    }
                });
                localStorage.setItem('playerStrategies', JSON.stringify(strategies));

                return updated;
            });
        } catch (error) {
            console.error('Failed to generate strategy:', error);
        } finally {
            setGeneratingStrategy(null);
        }
    };

    const handleSort = (key) => {
        setSortConfig(prev => {
            if (prev.key !== key) {
                return { key, direction: 'desc' };
            }
            if (prev.direction === 'desc') {
                return { key, direction: 'asc' };
            }
            return { key: 'total', direction: 'desc' }; // Default sort
        });
    };

    const sortedPlayers = useMemo(() => {
        let filtered = [...players];

        // Apply Search
        if (searchTerm) {
            const lowSearch = searchTerm.toLowerCase();
            filtered = filtered.filter(p =>
                p.name.toLowerCase().includes(lowSearch) ||
                p.matches.some(m => m.hero.toLowerCase().includes(lowSearch))
            );
        }

        if (filter === 'allies') {
            filtered = filtered.filter(p => p.total_with > p.total_against || (p.total_with > 0 && p.total_against === 0));
        } else if (filter === 'enemies') {
            filtered = filtered.filter(p => p.total_against > p.total_with || (p.total_against > 0 && p.total_with === 0));
        } else if (filter === 'frequent') {
            filtered = filtered.filter(p => p.total_games >= 2);
        }

        return filtered.sort((a, b) => {
            let comparison = 0;
            const { key } = sortConfig;

            switch (key) {
                case 'name':
                    comparison = a.name.localeCompare(b.name);
                    break;
                case 'total':
                    comparison = a.total_games - b.total_games;
                    break;
                case 'winrate':
                    // Sort by highest winrate (with or against)
                    const aWR = a.total_with > 0 ? a.winrate_with : a.winrate_against;
                    const bWR = b.total_with > 0 ? b.winrate_with : b.winrate_against;
                    comparison = aWR - bWR;
                    break;
                case 'recent':
                    comparison = new Date(a.last_played) - new Date(b.last_played);
                    break;
                case 'affinity':
                    // Custom sort for affinity (Ally > Mixed > Enemy)
                    const getScore = (p) => {
                        if (p.total_with > p.total_against) return 3;
                        if (p.total_against > p.total_with) return 1;
                        return 2;
                    };
                    comparison = getScore(a) - getScore(b);
                    break;
                default:
                    comparison = 0;
            }

            return sortConfig.direction === 'asc' ? comparison : -comparison;
        });
    }, [players, filter, sortConfig, searchTerm]);

    const getRelationshipColor = (player) => {
        if (player.total_with > player.total_against) {
            return player.winrate_with >= 50 ? '#10b981' : '#f59e0b';
        } else if (player.total_against > player.total_with) {
            return player.winrate_against >= 50 ? '#ef4444' : '#8b5cf6';
        }
        return '#6b7280';
    };

    const getRelationshipLabel = (player) => {
        if (player.total_with > player.total_against) {
            return player.winrate_with >= 60 ? 'Strong Ally' :
                player.winrate_with >= 40 ? 'Teammate' : 'Weak Link';
        } else if (player.total_against > player.total_with) {
            return player.winrate_against >= 60 ? 'Nemesis' :
                player.winrate_against >= 40 ? 'Rival' : 'Easy Opponent';
        }
        return 'Mixed';
    };

    const getRelationshipIcon = (player) => {
        if (player.total_with > player.total_against) {
            if (player.winrate_with >= 60) return <Users size={14} />;
            if (player.winrate_with >= 40) return <Users size={14} className="opacity-70" />;
            return <AlertTriangle size={14} />;
        } else if (player.total_against > player.total_with) {
            if (player.winrate_against >= 60) return <Target size={14} />;
            if (player.winrate_against >= 40) return <Sword size={14} />;
            return <Zap size={14} />;
        }
        return <Activity size={14} />;
    };



    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
        return `${Math.floor(diffDays / 30)}mo ago`;
    };

    // Calculate summary stats with confidence threshold - memoized for performance
    const MIN_GAMES_THRESHOLD = 3;
    const summaryStats = useMemo(() => {
        const strongAlliesList = [];
        const weakLinksList = [];
        const nemesesList = [];
        const easyOpponentsList = [];
        const frequentRivalsList = [];
        const topAlliesList = [];
        const topNemesesList = [];

        // Single pass through players to calculate all stats
        players.forEach(p => {
            if (p.total_with >= MIN_GAMES_THRESHOLD) {
                if (p.winrate_with >= 60) strongAlliesList.push(p);
                else if (p.winrate_with < 40) weakLinksList.push(p);
            }
            if (p.total_against >= MIN_GAMES_THRESHOLD) {
                if (p.winrate_against < 40) nemesesList.push(p);
                else if (p.winrate_against >= 60) easyOpponentsList.push(p);
            }
            if (p.total_with >= 3 && p.total_against >= 3) {
                frequentRivalsList.push(p);
            }
            if (p.total_with >= 3 && p.total_against < 3) {
                topAlliesList.push(p);
            }
            if (p.total_against >= 3 && p.total_with < 3) {
                topNemesesList.push(p);
            }
        });

        // Sort arrays once
        frequentRivalsList.sort((a, b) => b.total_games - a.total_games);
        topAlliesList.sort((a, b) => (b.winrate_with * b.total_with) - (a.winrate_with * a.total_with));
        topNemesesList.sort((a, b) => (a.winrate_against * a.total_against) - (b.winrate_against * b.total_against));

        return {
            strongAllies: strongAlliesList.length,
            weakLinks: weakLinksList.length,
            nemeses: nemesesList.length,
            easyOpponents: easyOpponentsList.length,
            frequentRival: frequentRivalsList[0] || null,
            topAlly: topAlliesList[0] || null,
            topNemesis: topNemesesList[0] || null
        };
    }, [players]);

    if (loading) {
        return <div className="player-network-loading">Loading player network...</div>;
    }


    return (
        <div className="player-network-container">
            <div className="cinematic-overlay" />

            <div className="network-header-card">
                <div className="flex items-center">
                    <div className="header-icon-box" style={{ background: 'rgba(168, 85, 247, 0.1)', borderColor: 'rgba(168, 85, 247, 0.2)', color: '#a855f7' }}>
                        <Users size={28} />
                    </div>
                    <div>
                        <h1 className="header-title hots-text-glow">Social Intelligence</h1>
                        <p className="header-subtitle uppercase tracking-widest text-[10px] opacity-70">Strategic Network Matrix · {players.length} Tracked Commanders</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setShowVerificationModal(true)}
                        className="px-4 py-1.5 bg-purple-500/10 border border-purple-500/30 rounded-full text-[10px] font-bold uppercase tracking-widest text-purple-400 hover:bg-purple-500/20 transition-all flex items-center gap-2"
                    >
                        📸 Verify Stats
                    </button>
                    <div className="network-search-container !max-w-[300px]">
                        <div className="search-input-wrapper">
                            <Search className="search-icon" />
                            <input
                                id="player-network-search"
                                name="player-network-search"
                                type="text"
                                placeholder="Identify DNA..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="search-input !py-1.5 !text-xs"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <VerificationModal
                isOpen={showVerificationModal}
                onClose={() => setShowVerificationModal(false)}
                onSuccess={() => {
                    window.dispatchEvent(new CustomEvent('profileRefreshed'));
                    loadData();
                    setShowVerificationModal(false);
                }}
            />

            {/* Top Intelligence Section - Unified "Perfect Rectangle" Grid */}
            <div className="intelligence-summary-wrapper">
                <div className="intelligence-grid">
                    {/* Row 1 & 2 Left Half: Counters (1x1 each) */}
                    <div className="insight-card ally span-1">
                        <div className="card-icon"><Users size={20} /></div>
                        <div className="card-identity">
                            <div className="label-main">Strong Allies</div>
                            <div className="label-sub">60%+ Win Rate</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-xl">{summaryStats.strongAllies}</div>
                        </div>
                    </div>

                    <div className="insight-card enemy span-1">
                        <div className="card-icon"><Target size={20} /></div>
                        <div className="card-identity">
                            <div className="label-main">Nemeses</div>
                            <div className="label-sub">&lt;40% Win Rate</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-xl">{summaryStats.nemeses}</div>
                        </div>
                    </div>

                    {/* Row 1 & 2 Right Half: Primary Rival (2x2) */}
                    <div className="insight-card enemy span-2 row-span-2 primary-rival">
                        <div className="card-icon"><Swords size={24} /></div>
                        <div className="card-identity">
                            <div className="label-main text-red-400">Primary Rival</div>
                            <div className="identity-name-anchor">{summaryStats.frequentRival ? summaryStats.frequentRival.name : 'Analyzing...'}</div>
                            <div className="identity-badge-neural">Captured in Replay Analysis</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-huge text-red-400">{summaryStats.frequentRival ? summaryStats.frequentRival.total_games : '--'}</div>
                            <div className="stat-unit">Engages</div>
                        </div>
                    </div>

                    {/* Row 2 Left Half: Remaining Counters */}
                    <div className="insight-card warning span-1">
                        <div className="card-icon"><AlertTriangle size={20} /></div>
                        <div className="card-identity">
                            <div className="label-main">Weak Links</div>
                            <div className="label-sub">&lt;40% Win Rate</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-xl">{summaryStats.weakLinks}</div>
                        </div>
                    </div>

                    <div className="insight-card easy span-1">
                        <div className="card-icon"><Zap size={20} /></div>
                        <div className="card-identity">
                            <div className="label-main">Easy Prey</div>
                            <div className="label-sub">60%+ Win Rate</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-xl">{summaryStats.easyOpponents}</div>
                        </div>
                    </div>

                    {/* Row 3 & 4: Complex Wide Tiles (2x2 each) */}
                    <div className="insight-card easy span-2 row-span-2 optimized-synergy">
                        <div className="card-icon"><TrendingUp size={24} /></div>
                        <div className="card-identity">
                            <div className="label-main text-blue-400">Optimized Synergy</div>
                            <div className="identity-name-anchor">{summaryStats.topAlly ? summaryStats.topAlly.name : 'Calculating...'}</div>
                            <div className="identity-badge-neural">{summaryStats.topAlly ? `${summaryStats.topAlly.total_with} Games Linked` : 'Scanning Network...'}</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-huge text-blue-400">{summaryStats.topAlly ? `${(summaryStats.topAlly.winrate_with).toFixed(0)}%` : '--'}</div>
                            <div className="stat-unit">Win Prob</div>
                        </div>
                    </div>

                    <div className="insight-card warning span-2 row-span-2 critical-threat">
                        <div className="card-icon"><AlertTriangle size={24} /></div>
                        <div className="card-identity">
                            <div className="label-main text-amber-500">Critical Threat</div>
                            <div className="identity-name-anchor">{summaryStats.topNemesis ? summaryStats.topNemesis.name : 'Monitoring...'}</div>
                            <div className="identity-badge-neural">{summaryStats.topNemesis ? `${summaryStats.topNemesis.total_against} Engages Detected` : 'No Critical Risks'}</div>
                        </div>
                        <div className="card-stats">
                            <div className="value-huge text-amber-400">{summaryStats.topNemesis ? `${(summaryStats.topNemesis.winrate_against).toFixed(0)}%` : '--'}</div>
                            <div className="stat-unit">Loss Prob</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="network-controls">
                <div className="filter-group">
                    <label>Filter:</label>
                    <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>
                        All Players
                    </button>
                    <button className={filter === 'allies' ? 'active' : ''} onClick={() => setFilter('allies')}>
                        🤝 Allies
                    </button>
                    <button className={filter === 'enemies' ? 'active' : ''} onClick={() => setFilter('enemies')}>
                        ⚔️ Enemies
                    </button>
                    <button className={filter === 'frequent' ? 'active' : ''} onClick={() => setFilter('frequent')}>
                        🔁 Frequent
                    </button>
                </div>

                <div className="sort-group hidden">
                    {/* Replaced by column headers */}
                </div>
            </div>

            {/* Tactical Ledger (Condensed List) */}
            <div className="player-ledger">
                <div className="ledger-header">
                    <div className="col-name flex items-center gap-1 hover:text-white transition-colors" onClick={() => handleSort('name')}>
                        Commander
                        {sortConfig.key === 'name' && (sortConfig.direction === 'asc' ? <span className="text-purple-400">↑</span> : <span className="text-purple-400">↓</span>)}
                    </div>
                    <div className="col-relation flex items-center gap-1 hover:text-white transition-colors" onClick={() => handleSort('affinity')}>
                        Affinity
                        {sortConfig.key === 'affinity' && (sortConfig.direction === 'asc' ? <span className="text-purple-400">↑</span> : <span className="text-purple-400">↓</span>)}
                    </div>
                    <div className="col-stats flex items-center gap-1 hover:text-white transition-colors" onClick={() => handleSort('winrate')}>
                        With (WR)
                        {sortConfig.key === 'winrate' && (sortConfig.direction === 'asc' ? <span className="text-purple-400">↑</span> : <span className="text-purple-400">↓</span>)}
                    </div>
                    <div className="col-stats flex items-center gap-1 hover:text-white transition-colors" onClick={() => handleSort('winrate')}>
                        Vs (WR)
                    </div>
                    <div className="col-total flex items-center gap-1 hover:text-white transition-colors" onClick={() => handleSort('total')}>
                        Total
                        {sortConfig.key === 'total' && (sortConfig.direction === 'asc' ? <span className="text-purple-400">↑</span> : <span className="text-purple-400">↓</span>)}
                    </div>
                    <div className="col-action"></div>
                </div>

                <div className="ledger-body">
                    {sortedPlayers.map(player => {
                        const relationColor = getRelationshipColor(player);
                        const relationLabel = getRelationshipLabel(player);
                        const isExpanded = expandedPlayer === player.id;
                        const isAlly = player.total_with > player.total_against;

                        return (
                            <div
                                key={player.id}
                                className={`ledger-row-group ${isExpanded ? 'active' : ''}`}
                            >
                                <div
                                    className="ledger-row"
                                    onClick={() => setExpandedPlayer(isExpanded ? null : player.id)}
                                    style={{ borderLeftColor: relationColor }}
                                >
                                    <div className="col-name">
                                        <div className="flex items-center gap-3">
                                            <div className="relative">
                                                <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                                                <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping opacity-30" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="font-black text-slate-100 leading-tight">{player.name}</span>
                                                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-tighter">
                                                    Captured in Replay Analysis
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="col-relation">
                                        <div className="flex flex-col gap-1">
                                            <span
                                                className="relation-chip"
                                                style={{
                                                    color: relationColor,
                                                    backgroundColor: `${relationColor}15`,
                                                    borderColor: `${relationColor}30`
                                                }}
                                            >
                                                <span className="flex items-center gap-1.5">
                                                    {getRelationshipIcon(player)}
                                                    {relationLabel}
                                                </span>
                                            </span>
                                            <div className="flex items-center gap-1 px-1">
                                                <div className="flex gap-1 items-end h-3">
                                                    {[1, 2, 3, 4, 5].map(i => {
                                                        const active = i <= Math.min(5, Math.ceil(player.total_games / 2));
                                                        return (
                                                            <div
                                                                key={i}
                                                                className={`w-1 rounded-t-sm transition-all duration-500 ${active
                                                                    ? 'bg-gradient-to-t from-cyan-600 to-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.4)]'
                                                                    : 'bg-slate-800 h-1'
                                                                    }`}
                                                                style={{
                                                                    height: active ? `${i * 2 + 4}px` : '4px',
                                                                    opacity: active ? 1 : 0.3
                                                                }}
                                                            />
                                                        );
                                                    })}
                                                </div>
                                                <span className="text-[7px] font-bold uppercase text-slate-500 tracking-[0.2em] ml-1">Data Confidence</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="col-stats font-mono">
                                        {player.total_with > 0 ? (
                                            <span className={player.winrate_with >= 50 ? 'text-green-400' : 'text-orange-400'}>
                                                {player.total_with}g ({player.winrate_with.toFixed(0)}%)
                                            </span>
                                        ) : '—'}
                                    </div>
                                    <div className="col-stats font-mono">
                                        {player.total_against > 0 ? (
                                            <span className={player.winrate_against >= 50 ? 'text-green-400' : 'text-red-400'}>
                                                {player.total_against}g ({player.winrate_against.toFixed(0)}%)
                                            </span>
                                        ) : '—'}
                                    </div>
                                    <div className="col-total font-black text-slate-400">
                                        {player.total_games}
                                    </div>
                                    <div className="col-action">
                                        <ChevronRight
                                            size={16}
                                            className={`transition-transform duration-300 ${isExpanded ? 'rotate-90 text-cyan-400' : 'text-slate-600'}`}
                                        />
                                    </div>
                                </div>

                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="ledger-expansion"
                                        >
                                            <div className="expansion-content">
                                                <div className="player-details">
                                                    <div className="detail-section">
                                                        <div className="detail-header">
                                                            <span>Signal History</span>
                                                            <button
                                                                className="strategy-btn"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    generateStrategy(player);
                                                                }}
                                                                disabled={generatingStrategy === player.id}
                                                            >
                                                                {generatingStrategy === player.id ? '⏳ Processing...' : (player.aiStrategy ? '📡 Refresh Dossier' : '🧠 Extract Intelligence')}
                                                            </button>
                                                        </div>
                                                        <div className="matches-list">
                                                            {player.matches.slice(-5).reverse().map((match, idx) => (
                                                                <div key={idx} className={`match-item ${match.team.toLowerCase()}`}>
                                                                    <img
                                                                        src={getHeroPortrait(match.hero)}
                                                                        alt={match.hero}
                                                                        className="match-hero-portrait shadow-md cursor-pointer hover:ring-2 hover:ring-cyan-500/50 transition-all"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            window.dispatchEvent(new CustomEvent('nav_to_dossier', { detail: match.hero }));
                                                                        }}
                                                                        onError={(e) => e.target.style.display = 'none'}
                                                                    />
                                                                    <span className="match-hero cursor-pointer hover:text-cyan-400"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            window.dispatchEvent(new CustomEvent('nav_to_dossier', { detail: match.hero }));
                                                                        }}>{match.hero}</span>
                                                                    <span className="match-vs text-[10px] font-black opacity-30 tracking-widest">VS</span>
                                                                    <img
                                                                        src={getHeroPortrait(match.my_hero)}
                                                                        alt={match.my_hero}
                                                                        className="match-hero-portrait shadow-md cursor-pointer hover:ring-2 hover:ring-cyan-500/50 transition-all"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            window.dispatchEvent(new CustomEvent('nav_to_dossier', { detail: match.my_hero }));
                                                                        }}
                                                                        onError={(e) => e.target.style.display = 'none'}
                                                                    />
                                                                    <span className="match-your-hero cursor-pointer hover:text-cyan-400"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            window.dispatchEvent(new CustomEvent('nav_to_dossier', { detail: match.my_hero }));
                                                                        }}>{match.my_hero}</span>
                                                                    <div className={`match-result-badge ${match.result.toLowerCase()}`}>
                                                                        {match.result === 'WIN' ? <Shield size={10} /> : <AlertTriangle size={10} />}
                                                                        <span>{match.result}</span>
                                                                    </div>
                                                                    <span className="match-date font-mono text-[9px] opacity-40">{formatDate(match.date)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    <div className="strategy-section">
                                                        <div className="strategy-header">
                                                            <div className="flex items-center gap-2">
                                                                <BrainCircuit size={16} className="text-purple-400" />
                                                                <span className="text-purple-100">Neural Intelligence Brief</span>
                                                            </div>
                                                            <div className="h-px flex-1 bg-gradient-to-r from-purple-500/20 to-transparent ml-4" />
                                                        </div>
                                                        {player.aiStrategy ? (
                                                            <StrategyContent player={player} heroData={heroData} />
                                                        ) : (
                                                            <div className="text-slate-600 italic text-[11px] p-4 text-center border border-dashed border-white/5 rounded-lg">
                                                                No dossier extracted for {player.name}. Initiate Intelligence Extraction to generate a tactical brief.
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        );
                    })}
                </div>
            </div>

            {sortedPlayers.length === 0 && (
                <div className="no-players">
                    No players match the current filter
                </div>
            )}
        </div>
    );
};

const PlayerNetwork = () => (
    <SelfHealingErrorBoundary>
        <PlayerNetworkContent />
    </SelfHealingErrorBoundary>
);

export default PlayerNetwork;

import React, { useState, useEffect } from 'react';
import { ArrowUpCircle, Shield, Swords, Target, Activity, Clock, Users } from 'lucide-react';
import './MatchTimeline.css';
import { normalizeHeroName } from '../utils/heroUtils';

const getHeroPortrait = (heroName) => {
    if (!heroName) return '';
    return `/images/heroes/${normalizeHeroName(heroName)}.png`;
};

const MatchTimeline = ({ matchId, match: matchProp, userPlayer }) => {
    const [timelineData, setTimelineData] = useState(null);
    const [loading, setLoading] = useState(!matchProp);
    const [activeSection, setActiveSection] = useState('match'); // 'match' or 'draft'

    useEffect(() => {
        if (matchProp) {
            setTimelineData(processTimeline(matchProp));
            setLoading(false);
            return;
        }

        if (!matchId) return;

        // Load match data
        fetch(`/api/match_history?limit=50`)
            .then(res => res.json())
            .then(data => {
                const match = data.find(m => m.id === matchId);
                if (match) {
                    setTimelineData(processTimeline(match));
                }
                setLoading(false);
            })
            .catch(err => {
                console.error('Failed to load timeline:', err);
                setLoading(false);
            });
    }, [matchId, matchProp]);

    const processTimeline = (match) => {
        const events = [];
        const advancedStats = match.advanced_stats || {};

        // Add Level Milestones
        const levelMilestones = advancedStats.level_milestones || {};
        Object.entries(levelMilestones).forEach(([team, levels]) => {
            Object.entries(levels).forEach(([level, timestamp]) => {
                if (timestamp) {
                    events.push({
                        timestamp,
                        type: 'level',
                        team: parseInt(team),
                        description: `Team ${team} hit Level ${level}`,
                        icon: ArrowUpCircle,
                        level: parseInt(level)
                    });
                }
            });
        });

        // Add Structure Destructions
        const structures = advancedStats.structure_destructions || [];
        structures.forEach(s => {
            const structureName = s.structure_type
                .replace('TownTownHall', 'Fort')
                .replace('L3', '')
                .replace('L2', '')
                .replace('Mid', '(Mid)')
                .replace('Top', '(Top)')
                .replace('Bot', '(Bot)');

            events.push({
                timestamp: s.timestamp,
                type: 'structure',
                team: s.destroyed_by_team,
                description: `${structureName} destroyed`,
                icon: Shield
            });
        });

        // Add Merc Captures
        const mercs = advancedStats.merc_captures || [];
        mercs.forEach(m => {
            events.push({
                timestamp: m.timestamp,
                type: 'merc',
                team: m.captured_by_team,
                description: `Merc camp captured`,
                icon: Swords
            });
        });

        // Add Talent Picks (from players)
        match.players?.forEach(player => {
            player.talents?.forEach(talent => {
                if (talent.timestamp > 0) {
                    events.push({
                        timestamp: talent.timestamp,
                        type: 'talent',
                        team: player.team,
                        description: `${player.name} picked ${talent.talent_name.replace(/([A-Z])/g, ' $1').trim()}`,
                        icon: Target,
                        player: player.name
                    });
                }
            });
        });

        // Sort by timestamp
        events.sort((a, b) => a.timestamp - b.timestamp);

        return {
            events,
            gameLength: match.game_length || 1200,
            result: match.result,
            originalMatch: match
        };
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (loading) {
        return <div className="timeline-loading">Loading neural history...</div>;
    }

    if (!timelineData) {
        return <div className="timeline-error">Neural history link severed.</div>;
    }

    const { events, gameLength, originalMatch } = timelineData;

    return (
        <div className="match-timeline bg-[#0c0518]/60 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Neural Subtabs */}
            <div className="flex bg-black/40 border-b border-white/5">
                {[
                    { id: 'match', label: 'Match Events', icon: Activity },
                    { id: 'draft', label: 'Draft sequence', icon: Swords }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveSection(tab.id)}
                        className={`flex items-center gap-2 px-8 py-4 text-xs font-black uppercase tracking-[0.2em] transition-all relative ${activeSection === tab.id
                            ? 'text-cyan-400 bg-cyan-500/5'
                            : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                            }`}
                    >
                        <tab.icon size={14} />
                        {tab.label}
                        {activeSection === tab.id && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-500 shadow-[0_0_10px_#22d3ee]" />
                        )}
                    </button>
                ))}
            </div>

            <div className="p-8">
                {activeSection === 'match' ? (
                    <>
                        <div className="timeline-header">
                            <div className="flex items-center gap-3 mb-6">
                                <Clock className="text-cyan-400" size={24} />
                                <h2 className="text-xl font-black uppercase tracking-wider text-white m-0">Temporal Audit</h2>
                            </div>
                            <div className="timeline-legend bg-black/20 p-4 rounded-lg border border-white/5 mb-8">
                                <span><ArrowUpCircle size={14} className="inline mr-1 text-purple-400" /> Milestone</span>
                                <span><Shield size={14} className="inline mr-1 text-blue-400" /> Structure</span>
                                <span><Swords size={14} className="inline mr-1 text-red-400" /> Mercenary</span>
                                <span><Target size={14} className="inline mr-1 text-yellow-400" /> Talent Pick</span>
                            </div>
                        </div>

                        <div className="timeline-container">
                            <div className="timeline-track bg-black/30 border border-white/5 relative">
                                {/* Time markers */}
                                <div className="time-markers border-b border-white/10">
                                    {[0, 5, 10, 15, 20, 25].map(min => (
                                        <div
                                            key={min}
                                            className="time-marker text-[10px] font-bold text-gray-600"
                                            style={{ left: `${(min * 60 / gameLength) * 100}%` }}
                                        >
                                            {min}:00
                                        </div>
                                    ))}
                                </div>

                                {/* Events */}
                                <div className="timeline-events h-48">
                                    {events.map((event, idx) => {
                                        const position = (event.timestamp / gameLength) * 100;
                                        const teamClass = event.team === 0 ? 'team-enemy' : 'team-ally';

                                        return (
                                            <div
                                                key={idx}
                                                className={`timeline-event ${event.type} ${teamClass}`}
                                                style={{ left: `${position}%` }}
                                            >
                                                <div className="event-icon p-1.5 bg-black/80 rounded-full border border-white/10 backdrop-blur-xl hover:border-cyan-500/50 transition-all cursor-crosshair">
                                                    <event.icon
                                                        size={18}
                                                        className={event.team === 1 ? 'text-blue-400' : 'text-red-400'}
                                                    />
                                                </div>
                                                <div className="event-tooltip z-50">
                                                    <div className="event-time font-mono text-cyan-400">{formatTime(event.timestamp)}</div>
                                                    <div className="event-desc font-bold text-white">{event.description}</div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Event List */}
                            <div className="timeline-list bg-black/40 border border-white/5 h-[500px]">
                                <h3 className="text-xs font-black uppercase tracking-widest text-cyan-400 mb-6 flex items-center gap-2">
                                    <Activity size={14} /> Chronological Log
                                </h3>
                                <div className="event-list-container space-y-2">
                                    {events.map((event, idx) => {
                                        const teamClass = event.team === 0 ? 'team-enemy' : 'team-ally';
                                        return (
                                            <div key={idx} className={`event-list-item bg-white/5 border-l-2 ${teamClass === 'team-ally' ? 'border-blue-500' : 'border-red-500'} p-3 rounded hover:bg-white/10 transition-colors`}>
                                                <span className="event-time-badge font-mono text-[10px] text-gray-500">{formatTime(event.timestamp)}</span>
                                                <span className="event-icon">
                                                    <event.icon
                                                        size={14}
                                                        className={event.team === 1 ? 'text-blue-400' : 'text-red-400'}
                                                    />
                                                </span>
                                                <span className="event-description text-sm text-gray-300 font-medium">{event.description}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="draft-sequence-tab animate-in fade-in zoom-in-95 duration-300">
                        <div className="flex items-center gap-3 mb-8">
                            <Swords className="text-purple-400" size={24} />
                            <h2 className="text-xl font-black uppercase tracking-wider text-white m-0">Draft Composition</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Bans Section */}
                            {originalMatch.advanced_stats?.bans?.length > 0 && (
                                <div className="col-span-full bg-black/20 p-6 rounded-xl border border-white/5">
                                    <div className="text-[10px] text-gray-500 uppercase font-black mb-4 tracking-[0.2em]">Banned Protocols (Sequential)</div>
                                    <div className="flex flex-wrap gap-4">
                                        {originalMatch.advanced_stats?.bans?.map((ban, i) => (
                                            <div key={i} className="relative group">
                                                <div className="w-14 h-14 bg-black/40 rounded-lg border border-red-500/20 grayscale group-hover:grayscale-0 transition-all overflow-hidden shadow-2xl">
                                                    <img
                                                        src={getHeroPortrait(ban.hero)}
                                                        alt={ban.hero}
                                                        className="w-full h-full object-cover opacity-60 group-hover:opacity-100"
                                                        onError={(e) => { e.target.style.display = 'none'; }}
                                                    />
                                                    <div className="absolute inset-0 border-2 border-red-500/50 rotate-45 scale-150 pointer-events-none" />
                                                </div>
                                                <div className="absolute -top-2 -left-2 bg-gray-900/90 text-[8px] font-black w-5 h-5 flex items-center justify-center rounded-full border border-white/10 text-gray-400">
                                                    {i + 1}
                                                </div>
                                                <div className="absolute -bottom-2 -right-2 bg-red-600 text-[9px] font-black px-1.5 py-0.5 rounded border border-white/20 shadow-lg">BAN</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Allied Picks */}
                            <div className="bg-cyan-500/5 p-6 rounded-xl border border-cyan-500/20">
                                <div className="text-[10px] text-cyan-400 font-black mb-6 uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Users size={12} /> Allied Deployment
                                </div>
                                <div className="grid grid-cols-5 gap-3">
                                    {originalMatch.players?.filter(p => p.team === userPlayer?.team).map((p, i) => (
                                        <div key={i} className="flex flex-col items-center gap-2">
                                            <div className="w-full aspect-square rounded-lg border-2 border-cyan-500/30 overflow-hidden shadow-lg group relative bg-black/40" title={p.hero}>
                                                <img src={getHeroPortrait(p.hero)} alt={p.hero} className="w-full h-full object-cover group-hover:scale-110 transition-transform" />
                                                <div className="absolute inset-x-0 bottom-0 h-1 bg-cyan-500 shadow-[0_0_10px_#22d3ee]" />
                                            </div>
                                            <div className="text-[9px] font-bold text-cyan-200 truncate w-full text-center">{p.hero}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Hostile Picks */}
                            <div className="bg-red-500/5 p-6 rounded-xl border border-red-500/20">
                                <div className="text-[10px] text-red-400 font-black mb-6 uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Swords size={12} /> Hostile Manifest
                                </div>
                                <div className="grid grid-cols-5 gap-3">
                                    {originalMatch.players?.filter(p => p.team !== userPlayer?.team).map((p, i) => (
                                        <div key={i} className="flex flex-col items-center gap-2">
                                            <div className="w-full aspect-square rounded-lg border-2 border-red-500/30 overflow-hidden shadow-lg group relative bg-black/40" title={p.hero}>
                                                <img src={getHeroPortrait(p.hero)} alt={p.hero} className="w-full h-full object-cover group-hover:scale-110 transition-transform" />
                                                <div className="absolute inset-x-0 bottom-0 h-1 bg-red-500 shadow-[0_0_10px_#ef4444]" />
                                            </div>
                                            <div className="text-[9px] font-bold text-red-200 truncate w-full text-center">{p.hero}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MatchTimeline;

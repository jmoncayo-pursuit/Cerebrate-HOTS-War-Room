import React, { useState, useEffect } from 'react';
import { ArrowUpCircle, Shield, Swords, Target, Activity, Clock, Users } from 'lucide-react';
import './MatchTimeline.css';
import { normalizeHeroName } from '../utils/heroUtils';

const getHeroPortrait = (heroName) => {
    if (!heroName) return '';
    return `/images/heroes/${normalizeHeroName(heroName)}.png`;
};

const EVENT_TYPES = ['level', 'structure', 'merc', 'talent'];

const MatchTimeline = ({ matchId, match: matchProp, userPlayer }) => {
    const [timelineData, setTimelineData] = useState(null);
    const [loading, setLoading] = useState(!matchProp);
    const [activeSection, setActiveSection] = useState('match');
    const [eventFilter, setEventFilter] = useState(new Set(EVENT_TYPES)); // show all by default
    const [logMode, setLogMode] = useState('chrono'); // chrono | team
    const [myEventsOnly, setMyEventsOnly] = useState(false);

    const yourTeamID = userPlayer?.team ?? (matchProp?.players?.find(p => p.hero === matchProp?.hero)?.team ?? 0);
    const userName = userPlayer?.name || matchProp?.user_name || matchProp?.players?.find(p => p.hero === matchProp?.hero)?.name;

    useEffect(() => {
        const fetchWithDetails = (mid) => {
            if (!mid) return;
            setLoading(true);
            fetch(`/api/match_history?id=${encodeURIComponent(mid)}&limit=1&details=true`)
                .then(res => res.json())
                .then(data => {
                    const m = Array.isArray(data) ? data[0] : data?.matches?.[0];
                    if (m) setTimelineData(processTimeline(m));
                    setLoading(false);
                })
                .catch(() => setLoading(false));
        };

        if (matchProp?.id) {
            const hasDetails = !!(matchProp.raw_stats || matchProp.advanced_stats);
            setTimelineData(processTimeline(matchProp));
            setLoading(false);
            if (!hasDetails) {
                fetchWithDetails(matchProp.id);
            }
            return;
        }

        if (matchId) fetchWithDetails(matchId);
    }, [matchId, matchProp?.id]);

    const processTimeline = (match) => {
        const events = [];
        const advancedStats = match.advanced_stats || match.raw_stats || {};
        const yourTeamId = match.players?.find(p => p.hero === match.hero)?.team ?? 0;
        const yourLabel = 'Your team';
        const enemyLabel = 'Enemy team';

        // Level Milestones: when each team hit Level 10 and Level 20 (from replay talent timestamps)
        const levelMilestones = advancedStats.level_milestones || {};
        Object.entries(levelMilestones).forEach(([team, levels]) => {
            const teamId = parseInt(team);
            const side = teamId === yourTeamId ? yourLabel : enemyLabel;
            Object.entries(levels).forEach(([level, timestamp]) => {
                if (timestamp) {
                    events.push({
                        timestamp,
                        type: 'level',
                        team: teamId,
                        description: `${side} hit Level ${level}`,
                        icon: ArrowUpCircle,
                        level: parseInt(level)
                    });
                }
            });
        });

        // Add Structure Destructions (from advanced_stats or raw_stats)
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
                credit: s.destroyed_by_player ? `credit: ${s.destroyed_by_player}` : undefined,
                icon: Shield
            });
        });

        // Add Merc Captures (key from parser: merc_captures)
        const mercs = advancedStats.merc_captures || [];
        mercs.forEach(m => {
            events.push({
                timestamp: m.timestamp,
                type: 'merc',
                team: m.captured_by_team,
                description: `Merc camp captured`,
                credit: m.captured_by_player ? `credit: ${m.captured_by_player}` : undefined,
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
        return <div className="timeline-loading">Loading timeline...</div>;
    }

    if (!timelineData) {
        return <div className="timeline-error">Timeline data unavailable.</div>;
    }

    const { events, gameLength, originalMatch } = timelineData;
    const filteredEvents = events.filter(e => eventFilter.has(e.type));
    const displayEvents = myEventsOnly ? filteredEvents.filter(e => e.team === yourTeamID) : filteredEvents;
    const toggleFilter = (type) => {
        setEventFilter(prev => {
            const next = new Set(prev);
            if (next.has(type)) next.delete(type);
            else next.add(type);
            return next;
        });
    };

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
                            <div className="timeline-legend bg-black/20 p-4 rounded-lg border border-white/5 mb-4 flex flex-wrap items-center gap-4">
                                {[
                                    { type: 'level', label: 'Milestone (L10/L20)', Icon: ArrowUpCircle, color: 'text-purple-400', title: 'When each team hit Level 10 and Level 20' },
                                    { type: 'structure', label: 'Structure', Icon: Shield, color: 'text-cyan-400' },
                                    { type: 'merc', label: 'Mercenary', Icon: Swords, color: 'text-red-400' },
                                    { type: 'talent', label: 'Talent', Icon: Target, color: 'text-yellow-400' }
                                ].map(({ type, label, Icon, color, title }) => (
                                    <button
                                        key={type}
                                        type="button"
                                        onClick={() => toggleFilter(type)}
                                        title={title}
                                        className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-bold transition-opacity ${eventFilter.has(type) ? 'opacity-100' : 'opacity-40 hover:opacity-70'}`}
                                    >
                                        <Icon size={14} className={color} />
                                        {label}
                                    </button>
                                ))}
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider ml-2 flex items-center gap-2">
                                    <span className="w-3 h-3 rounded-sm bg-cyan-500/80" /> Your team
                                    <span className="w-3 h-3 rounded-sm bg-red-500/80" /> Enemy team
                                </span>
                                <button
                                    type="button"
                                    onClick={() => setMyEventsOnly(prev => !prev)}
                                    className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded border ${myEventsOnly ? 'text-cyan-300 border-cyan-500/40 bg-cyan-500/10' : 'text-slate-500 border-white/10 hover:text-slate-300 hover:bg-white/5'}`}
                                    title="Show only your team's events"
                                >
                                    My events only
                                </button>
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider ml-auto">
                                    Showing {displayEvents.length}/{events.length}{myEventsOnly ? ' (yours)' : ''}
                                </span>
                            </div>
                        </div>

                        <div className="timeline-container">
                            <div className="timeline-track bg-black/30 border border-white/5 relative overflow-hidden rounded-lg min-w-0 max-w-full">
                                {/* Time markers */}
                                <div className="time-markers border-b border-white/10 relative">
                                    {[0, 5, 10, 15, 20, 25].filter(min => min * 60 <= gameLength).map(min => (
                                        <div
                                            key={min}
                                            className="time-marker text-[10px] font-bold text-gray-600 absolute"
                                            style={{ left: `${(min * 60 / gameLength) * 100}%`, transform: 'translateX(-50%)' }}
                                        >
                                            {min}:00
                                        </div>
                                    ))}
                                </div>

                                {/* Events: stagger by type row to avoid overlap; position % clamped by track */}
                                <div className="timeline-events relative h-40">
                                    {displayEvents.map((event, idx) => {
                                        const position = Math.min(98, Math.max(2, (event.timestamp / gameLength) * 100));
                                        const isYourTeam = event.team === yourTeamID;
                                        const teamClass = isYourTeam ? 'team-ally' : 'team-enemy';
                                        const rowY = { level: 8, structure: 48, merc: 88, talent: 128 }[event.type] ?? 8;

                                        return (
                                            <div
                                                key={idx}
                                                className={`timeline-event ${event.type} ${teamClass} absolute`}
                                                style={{ left: `${position}%`, top: rowY, transform: 'translate(-50%, 0)' }}
                                            >
                                                <div className="event-icon p-1.5 bg-black/80 rounded-full border border-white/10 backdrop-blur-xl hover:border-cyan-500/50 transition-all cursor-crosshair">
                                                    <event.icon
                                                        size={18}
                                                        className={isYourTeam ? 'text-cyan-400' : 'text-red-400'}
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

                            <div className="timeline-list bg-black/40 border border-white/5 rounded-lg flex flex-col min-h-[320px] max-h-[420px]">
                                <div className="flex items-center justify-between gap-2 shrink-0 px-4 pt-4 pb-2 bg-[#0c0518]/95 border-b border-white/5">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-cyan-400 flex items-center gap-2 m-0">
                                        <Activity size={14} /> Chronological Log
                                    </h3>
                                    <div className="flex items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setLogMode('chrono')}
                                            className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded border ${logMode === 'chrono' ? 'text-cyan-300 border-cyan-500/40 bg-cyan-500/10' : 'text-slate-500 border-white/10 hover:text-slate-300 hover:bg-white/5'}`}
                                        >
                                            Time
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setLogMode('team')}
                                            className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded border ${logMode === 'team' ? 'text-cyan-300 border-cyan-500/40 bg-cyan-500/10' : 'text-slate-500 border-white/10 hover:text-slate-300 hover:bg-white/5'}`}
                                        >
                                            Team
                                        </button>
                                    </div>
                                </div>
                                <div className="event-list-container space-y-2 p-4 pb-4 overflow-y-auto flex-1">
                                    {(() => {
                                        const renderRow = (event, idx) => {
                                            const isYourTeam = event.team === yourTeamID;
                                            const credit = event.credit ? ` · ${event.credit}` : '';
                                            return (
                                                <div key={idx} className={`event-list-item bg-white/5 border-l-2 ${isYourTeam ? 'border-cyan-500' : 'border-red-500'} p-3 rounded hover:bg-white/10 transition-colors`}>
                                                    <span className="event-time-badge font-mono text-[10px] text-gray-500">{formatTime(event.timestamp)}</span>
                                                    <span className="event-icon">
                                                        <event.icon size={14} className={isYourTeam ? 'text-cyan-400' : 'text-red-400'} />
                                                    </span>
                                                    <span className="event-description text-sm text-gray-300 font-medium">{event.description}{credit}</span>
                                                </div>
                                            );
                                        };
                                        if (logMode === 'team') {
                                            const yourEvents = displayEvents.filter(e => e.team === yourTeamID);
                                            const enemyEvents = displayEvents.filter(e => e.team !== yourTeamID);
                                            return (
                                                <div className="space-y-4">
                                                    <div>
                                                        <div className="text-[10px] font-black uppercase tracking-widest text-cyan-400 mb-2">Your team</div>
                                                        <div className="space-y-2">{yourEvents.map(renderRow)}</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-[10px] font-black uppercase tracking-widest text-red-400 mb-2">Enemy team</div>
                                                        <div className="space-y-2">{enemyEvents.map(renderRow)}</div>
                                                    </div>
                                                </div>
                                            );
                                        }
                                        return displayEvents.map(renderRow);
                                    })()}
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="draft-sequence-tab animate-in fade-in zoom-in-95 duration-300">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <Swords className="text-purple-400" size={24} />
                                <h2 className="text-xl font-black uppercase tracking-wider text-white m-0">Draft sequence</h2>
                            </div>
                            {originalMatch.advanced_stats?.user_was_banner && (
                                <div className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/40 rounded text-[10px] text-cyan-400 font-bold uppercase tracking-widest animate-pulse">
                                    You were the team banner
                                </div>
                            )}
                        </div>

                        {/* Unified Draft Flow Section */}
                        {(() => {
                            const bans = (originalMatch.advanced_stats?.bans || originalMatch.raw_stats?.bans || []).map(b => ({ ...b, type: 'BAN' }));
                            const picks = (originalMatch.advanced_stats?.picks || originalMatch.raw_stats?.picks || []).map(p => ({ ...p, type: 'PICK' }));

                            // Combine and sort by gameloop
                            const draftFlow = [...bans, ...picks].sort((a, b) => (a.gameloop || 0) - (b.gameloop || 0));

                            if (draftFlow.length === 0) return <div className="text-gray-500 text-xs italic">No draft data available for this match.</div>;

                            return (
                                <div className="mb-12">
                                    <div className="text-[10px] text-gray-400 uppercase font-black mb-6 tracking-[0.3em] flex items-center gap-4">
                                        <div className="h-px bg-white/10 flex-1"></div>
                                        Chronological Draft Flow
                                        <div className="h-px bg-white/10 flex-1"></div>
                                    </div>

                                    <div className="flex flex-wrap gap-4 items-center justify-center">
                                        {draftFlow.map((item, i) => {
                                            const isAlly = item.team === yourTeamID;
                                            const isBan = item.type === 'BAN';
                                            const isBanner = (item.name === userName && originalMatch.advanced_stats?.user_was_banner) ||
                                                (item.name === originalMatch.advanced_stats?.enemy_banner_name);

                                            return (
                                                <div key={i} className="flex flex-col items-center gap-2 group relative">
                                                    {/* Event Label (1st, 2nd, etc) */}
                                                    <span className={`text-[8px] font-mono ${isAlly ? 'text-cyan-500' : 'text-red-500'} font-bold`}>
                                                        {i + 1}
                                                    </span>

                                                    {/* Portrait Box */}
                                                    <div className={`
                                                        w-14 h-14 rounded-lg border-2 
                                                        ${isAlly ? (isBan ? 'border-cyan-500/30' : 'border-cyan-400') : (isBan ? 'border-red-500/30' : 'border-red-400')} 
                                                        ${isBan ? 'bg-black/60 grayscale' : 'bg-black/20'} 
                                                        overflow-hidden relative transition-all group-hover:scale-110 shadow-2xl
                                                        ${isBanner ? 'ring-2 ring-amber-500 ring-offset-2 ring-offset-[#0c0518]' : ''}
                                                    `}>
                                                        <img
                                                            src={getHeroPortrait(item.hero)}
                                                            alt={item.hero}
                                                            className={`w-full h-full object-cover ${isBan ? 'opacity-40' : 'opacity-100'}`}
                                                            onError={(e) => { e.target.style.display = 'none'; }}
                                                        />

                                                        {/* Type Overlay */}
                                                        <div className={`absolute bottom-0 inset-x-0 text-[7px] font-black text-center py-0.5 ${isAlly ? 'bg-cyan-500' : 'bg-red-500'} text-black uppercase`}>
                                                            {isBan ? 'BAN' : 'PICK'}
                                                        </div>

                                                        {isBanner && (
                                                            <div className="absolute top-0 right-0 p-0.5">
                                                                <div className="w-2 h-2 bg-amber-500 rounded-full shadow-[0_0_8px_#f59e0b]" title="Drafted by Team Banner" />
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Hero Name / Player Name Tooltip-style */}
                                                    <div className="flex flex-col items-center">
                                                        <span className="text-[10px] font-black text-white uppercase tracking-tighter truncate max-w-[60px]">{item.hero}</span>
                                                        {item.name && !isBan && (
                                                            <span className={`text-[8px] font-bold ${isAlly ? 'text-cyan-600' : 'text-red-600'} truncate max-w-[60px]`}>{item.name}</span>
                                                        )}
                                                        {item.banned_by && isBan && (
                                                            <span className={`text-[8px] font-bold ${isAlly ? 'text-cyan-700' : 'text-red-700'} truncate max-w-[60px]`}>{item.banned_by}</span>
                                                        )}
                                                    </div>

                                                    {/* Arrow indicator for next in sequence */}
                                                    {i < draftFlow.length - 1 && (
                                                        <div className="absolute -right-3 top-1/2 -translate-y-1/2 opacity-20 group-hover:opacity-100 transition-opacity">
                                                            <div className="w-1.5 h-1.5 border-t-2 border-r-2 border-white rotate-45" />
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Traditional Team View (Summary) */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-white/5">
                            <div className="bg-cyan-500/5 p-5 rounded-xl border border-cyan-500/20">
                                <div className="text-[10px] text-cyan-400 font-black mb-1 uppercase tracking-widest">Your team Summary</div>
                                <div className="flex flex-wrap gap-2">
                                    {(originalMatch.advanced_stats?.picks?.filter(p => p.team === yourTeamID) || originalMatch.players?.filter(p => p.team === yourTeamID) || []).map((p, i) => {
                                        const isBanner = (p.name === userName && originalMatch.advanced_stats?.user_was_banner);
                                        return (
                                            <div key={i} className="flex flex-col items-center gap-1">
                                                <div className={`w-12 h-12 rounded-lg border-2 ${isBanner ? 'border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]' : 'border-cyan-500/30'} overflow-hidden bg-black/40 relative`}>
                                                    <img src={getHeroPortrait(p.hero)} alt={p.hero} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                                                    {isBanner && (
                                                        <div className="absolute top-0 right-0 bg-amber-500 text-black text-[7px] font-black px-1 rounded-bl">BANNER</div>
                                                    )}
                                                </div>
                                                <span className={`text-[9px] font-bold truncate max-w-[60px] text-center ${isBanner ? 'text-amber-200' : 'text-cyan-200'}`}>{p.hero}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                            <div className="bg-red-500/5 p-5 rounded-xl border border-red-500/20">
                                <div className="text-[10px] text-red-400 font-black mb-1 uppercase tracking-widest">Enemy team Summary</div>
                                <div className="flex flex-wrap gap-2">
                                    {(originalMatch.advanced_stats?.picks?.filter(p => p.team !== yourTeamID) || originalMatch.players?.filter(p => p.team !== yourTeamID) || []).map((p, i) => {
                                        const isBanner = (p.name === originalMatch.advanced_stats?.enemy_banner_name);
                                        return (
                                            <div key={i} className="flex flex-col items-center gap-1">
                                                <div className={`w-12 h-12 rounded-lg border-2 ${isBanner ? 'border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]' : 'border-red-500/30'} overflow-hidden bg-black/40 relative`}>
                                                    <img src={getHeroPortrait(p.hero)} alt={p.hero} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                                                    {isBanner && (
                                                        <div className="absolute top-0 right-0 bg-amber-500 text-black text-[7px] font-black px-1 rounded-bl">BANNER</div>
                                                    )}
                                                </div>
                                                <span className={`text-[9px] font-bold truncate max-w-[60px] text-center ${isBanner ? 'text-amber-200' : 'text-red-200'}`}>{p.hero}</span>
                                            </div>
                                        );
                                    })}
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

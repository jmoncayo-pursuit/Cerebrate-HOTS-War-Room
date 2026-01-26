import React, { useState, useEffect } from 'react';
import { ArrowUpCircle, Shield, Swords, Target, Activity, Clock } from 'lucide-react';
import './MatchTimeline.css';

const MatchTimeline = ({ matchId }) => {
    const [timelineData, setTimelineData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
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
    }, [matchId]);

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
            result: match.result
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
        return <div className="timeline-error">No timeline data available</div>;
    }

    const { events, gameLength } = timelineData;

    return (
        <div className="match-timeline">
            <div className="timeline-header">
                <div className="flex items-center gap-3 mb-2">
                    <Activity className="text-cyan-400" size={24} />
                    <h2>Match Timeline</h2>
                </div>
                <div className="timeline-legend">
                    <span><ArrowUpCircle size={14} className="inline mr-1 text-gray-400" /> Level Milestone</span>
                    <span><Shield size={14} className="inline mr-1 text-gray-400" /> Structure</span>
                    <span><Swords size={14} className="inline mr-1 text-gray-400" /> Merc Camp</span>
                    <span><Target size={14} className="inline mr-1 text-gray-400" /> Talent Pick</span>
                </div>
            </div>

            <div className="timeline-container">
                <div className="timeline-track">
                    {/* Time markers */}
                    <div className="time-markers">
                        {[0, 5, 10, 15, 20, 25].map(min => (
                            <div
                                key={min}
                                className="time-marker"
                                style={{ left: `${(min * 60 / gameLength) * 100}%` }}
                            >
                                {min}:00
                            </div>
                        ))}
                    </div>

                    {/* Events */}
                    <div className="timeline-events">
                        {events.map((event, idx) => {
                            const position = (event.timestamp / gameLength) * 100;
                            const teamClass = event.team === 0 ? 'team-enemy' : 'team-ally';

                            return (
                                <div
                                    key={idx}
                                    className={`timeline-event ${event.type} ${teamClass}`}
                                    style={{ left: `${position}%` }}
                                    title={`${formatTime(event.timestamp)} - ${event.description}`}
                                >
                                    <div className="event-icon p-1 bg-black/60 rounded-full border border-white/10 backdrop-blur-sm">
                                        <event.icon
                                            size={20}
                                            className={event.team === 1 ? 'text-blue-400' : 'text-red-400'}
                                        />
                                    </div>
                                    <div className="event-tooltip">
                                        <div className="event-time">{formatTime(event.timestamp)}</div>
                                        <div className="event-desc">{event.description}</div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Event List */}
                <div className="timeline-list">
                    <h3>Event Log</h3>
                    <div className="event-list-container">
                        {events.map((event, idx) => {
                            const teamClass = event.team === 0 ? 'team-enemy' : 'team-ally';
                            return (
                                <div key={idx} className={`event-list-item ${teamClass}`}>
                                    <span className="event-time-badge">{formatTime(event.timestamp)}</span>
                                    <span className="event-icon">
                                        <event.icon
                                            size={16}
                                            className={event.team === 1 ? 'text-blue-400' : 'text-red-400'}
                                        />
                                    </span>
                                    <span className="event-description">{event.description}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MatchTimeline;

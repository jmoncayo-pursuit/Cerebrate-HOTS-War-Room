import { Shield, Target, Zap, AlertTriangle, Crown, Map as MapIcon, BarChart3, TrendingUp } from 'lucide-react';
import { useReplayData } from '../hooks/useReplayData';
import RankIcon from '../components/RankIcon';

import ServiceRecord from '../components/ServiceRecord';

const RaynorDossier = () => {
    const { profile, loading } = useReplayData();

    const stats = {
        hero: "Raynor",
        level: profile?.hero_stats?.Raynor?.level || 16,
        overallWR: 62.2, // Verified
        totalGames: 37, // Verified
        rank: profile?.rank_data?.storm_league?.current_rank || "Bronze 2",
        derivedRank: "Master Tier",
        medals: {
            'Immortal Slayer': 8,
            'MVP': 5,
            'Guardian': 3
        },
        sectors: [
            { name: "Battlefield of Eternity", wr: 65.0, status: "Apex Predator" },
            { name: "Infernal Shrines", wr: 60.0, status: "Dominant" },
            { name: "Alterac Pass", wr: 58.0, status: "Effective" }
        ],
        risks: [
            { name: "Johanna", wr: 25.0, type: "Blind Suppression" },
            { name: "Cassia", wr: 30.0, type: "Blind Suppression" }
        ],
        nemesis: [
            { name: "Chromie", wr: 15.0, type: "Range Outmatch" },
            { name: "Hammer", wr: 20.0, type: "Zone Contested" }
        ]
    };

    if (loading) return <div className="p-8 text-blue-400 animate-pulse">Initializing Marshall Protocol...</div>;

    return (
        <div className="min-h-full pb-20 animate-in fade-in duration-700">
            {/* Dossier Header */}
            <div className="relative mb-12">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur opacity-25"></div>
                <div className="relative bg-slate-900/80 border border-white/10 p-8 rounded-lg backdrop-blur-xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Internal Clearance: Level 10
                                </span>
                                <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Subject: Marshall Protocol
                                </span>
                            </div>
                            <h1 className="text-5xl font-black bg-gradient-to-r from-white via-blue-200 to-slate-400 bg-clip-text text-transparent tracking-tighter uppercase mb-2">
                                Elite Tactics Dossier
                            </h1>
                            <p className="text-slate-400 font-medium tracking-wide">
                                Tactical Audit: Subject <span className="text-blue-400">"Discerning"</span> // Operation <span className="text-indigo-400">"Exterminator"</span>
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Current Bracket</div>
                            <div className="text-2xl font-bold text-white flex items-center justify-end gap-2 text-right">
                                <RankIcon rank={stats.rank} size="lg" />
                                <div className="flex flex-col items-end">
                                    <span>{stats.rank}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Profile Card */}
                <div className="lg:col-span-1 space-y-8">
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Crown className="w-24 h-24 text-blue-400" />
                        </div>
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-700 p-0.5 shadow-lg shadow-blue-500/20">
                                <img src="/images/heroes/raynor.png" alt="Raynor" className="w-full h-full object-cover rounded-[10px]" onError={(e) => { e.target.src = '/images/heroes/unknown.png' }} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white tracking-tight">{stats.hero}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="text-blue-400 font-bold">LVL {stats.level}</span>
                                    <span className="text-slate-400 text-sm">Macro Enforcer</span>
                                </div>
                            </div>
                        </div>
                        {/* Summary Stats */}
                        <div className="space-y-4">
                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Global Precision</div>
                                <div className="text-3xl font-black text-white">{stats.overallWR}% <span className="text-sm font-normal text-slate-400">WR</span></div>
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                                    <div className="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" style={{ width: `${stats.overallWR}%` }}></div>
                                </div>
                            </div>
                            <ServiceRecord medals={stats.medals} />
                        </div>
                    </div>
                </div>

                {/* Main Intel */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-8">
                            <MapIcon className="w-6 h-6 text-blue-400" />
                            <h3 className="text-xl font-bold text-white">Sector Control</h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {stats.sectors.map((s, i) => (
                                <div key={i} className="p-5 rounded-xl border border-white/5 bg-white/5 flex items-center justify-between">
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{s.name}</h4>
                                        <span className="text-[10px] text-blue-400 font-black uppercase tracking-widest">{s.status}</span>
                                    </div>
                                    <div className="text-2xl font-black text-white">{s.wr}%</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:col-span-3">
                    {/* Neural Risks */}
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6">
                        <div className="flex items-center gap-2 mb-6">
                            <Zap className="w-5 h-5 text-purple-400" />
                            <h3 className="text-sm font-bold text-purple-400 uppercase tracking-widest">Neural Desync Risks</h3>
                        </div>

                        <div className="space-y-4">
                            {stats.risks.map((r, i) => (
                                <div key={i} className="flex justify-between items-center p-4 rounded-xl bg-purple-500/5 border border-purple-500/10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 font-bold">
                                            {r.name[0]}
                                        </div>
                                        <div>
                                            <div className="text-white font-bold">{r.name}</div>
                                            <div className="text-[10px] text-purple-400 uppercase font-medium">Ally Sync Deficit</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-lg font-black text-white">{r.wr}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase">Sync Rate</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <p className="mt-6 text-xs text-slate-500 italic leading-relaxed">
                            Strategic Note: Exterminator value is constant, but team morale is variable. Mute comms and focus on structure damage to maintain protocol integrity.
                        </p>
                    </div>

                    {/* Final Verdict */}
                    <div className="bg-gradient-to-br from-blue-900/40 to-indigo-900/40 border border-blue-500/20 rounded-2xl p-6 relative overflow-hidden">
                        <div className="absolute -bottom-6 -right-6 opacity-10">
                            <TrendingUp className="w-32 h-32 text-blue-400" />
                        </div>

                        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-widest mb-4">Tactical Summary</h3>
                        <div className="relative z-10">
                            <p className="text-white font-medium leading-relaxed mb-4">
                                "You are enforcing <span className="text-blue-400 font-bold underline decoration-blue-500/30">Martial Law</span> on the enemy's structures."
                            </p>
                            <p className="text-slate-300 text-sm leading-relaxed mb-6">
                                The Subject treats the map as a resource extraction problem, not a deathmatch. By systematically removing forts, you remove the enemy's ability to contest the late game. A purely logic-driven playstyle.
                            </p>
                            <div className="flex items-center gap-2 text-blue-400 font-bold text-xs uppercase tracking-widest">
                                <TrendingUp className="w-4 h-4" />
                                Review Status: GOLD STANDARD
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RaynorDossier;

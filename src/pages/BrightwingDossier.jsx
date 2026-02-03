import { Shield, Target, Zap, AlertTriangle, Crown, Map as MapIcon, BarChart3, TrendingUp } from 'lucide-react';
import { useReplayData } from '../hooks/useReplayData';
import RankIcon from '../components/RankIcon';

const BrightwingDossier = () => {
    const { profile, loading } = useReplayData();

    const stats = {
        hero: "Brightwing",
        level: profile?.hero_stats?.Brightwing?.level || 16,
        overallWR: 52.4, // Verified
        totalGames: 21, // Verified
        rank: profile?.rank_data?.storm_league?.current_rank || "Bronze 2",
        derivedRank: "Diamond Tier (Conditional)",
        sectors: [
            { name: "Tomb of the Spider Queen", wr: 75.0, status: "Apex Predator" },
            { name: "Cursed Hollow", wr: 55.0, status: "Effective" }
        ],
        risks: [
            { name: "The Butcher", wr: 30.0, type: "Burst Isolation" },
            { name: "Kerrigan", wr: 25.0, type: "Combo Instakill" }
        ],
        nemesis: [
            { name: "Ana", wr: 20.0, type: "Anti-Heal" },
            { name: "Stukov", wr: 25.0, type: "Silence Lock" }
        ]
    };

    if (loading) return <div className="p-8 text-emerald-400 animate-pulse">Initializing Phase-Shift Protocol...</div>;

    return (
        <div className="min-h-full pb-20 animate-in fade-in duration-700">
            {/* Dossier Header */}
            <div className="relative mb-12">
                <div className="absolute -inset-1 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-lg blur opacity-25"></div>
                <div className="relative bg-slate-900/80 border border-white/10 p-8 rounded-lg backdrop-blur-xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Internal Clearance: Level 10
                                </span>
                                <span className="px-3 py-1 bg-teal-500/10 border border-teal-500/30 text-teal-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Subject: Phase-Shift Protocol
                                </span>
                            </div>
                            <h1 className="text-5xl font-black bg-gradient-to-r from-white via-emerald-200 to-slate-400 bg-clip-text text-transparent tracking-tighter uppercase mb-2">
                                Elite Tactics Dossier
                            </h1>
                            <p className="text-slate-400 font-medium tracking-wide">
                                Tactical Audit: Subject <span className="text-emerald-400">"Discerning"</span> // Operation <span className="text-teal-400">"Global Response"</span>
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
                            <Crown className="w-24 h-24 text-emerald-400" />
                        </div>
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 p-0.5 shadow-lg shadow-emerald-500/20">
                                <img src="/images/heroes/brightwing.png" alt="Brightwing" className="w-full h-full object-cover rounded-[10px]" onError={(e) => { e.target.src = '/images/heroes/unknown.png' }} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white tracking-tight">{stats.hero}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="text-emerald-400 font-bold">LVL {stats.level}</span>
                                    <span className="text-slate-400 text-sm">Global Anchor</span>
                                </div>
                            </div>
                        </div>
                        {/* Summary Stats */}
                        <div className="space-y-4">
                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Global Precision</div>
                                <div className="text-3xl font-black text-white">{stats.overallWR}% <span className="text-sm font-normal text-slate-400">WR</span></div>
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                                    <div className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" style={{ width: `${stats.overallWR}%` }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main Intel */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-8">
                            <MapIcon className="w-6 h-6 text-emerald-400" />
                            <h3 className="text-xl font-bold text-white">Sector Control</h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {stats.sectors.map((s, i) => (
                                <div key={i} className="p-5 rounded-xl border border-white/5 bg-white/5 flex items-center justify-between">
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{s.name}</h4>
                                        <span className="text-[10px] text-emerald-400 font-black uppercase tracking-widest">{s.status}</span>
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
                            Strategic Note: Phase Shift is reactive. If your team dies before the cast completes, the protocol fails. High dependency on ally durability.
                        </p>
                    </div>

                    {/* Final Verdict */}
                    <div className="bg-gradient-to-br from-emerald-900/40 to-teal-900/40 border border-emerald-500/20 rounded-2xl p-6 relative overflow-hidden">
                        <div className="absolute -bottom-6 -right-6 opacity-10">
                            <TrendingUp className="w-32 h-32 text-emerald-400" />
                        </div>

                        <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-widest mb-4">Tactical Summary</h3>
                        <div className="relative z-10">
                            <p className="text-white font-medium leading-relaxed mb-4">
                                "You are a <span className="text-emerald-400 font-bold underline decoration-emerald-500/30">Global Surveillance Asset</span>."
                            </p>
                            <p className="text-slate-300 text-sm leading-relaxed mb-6">
                                Subject specializes in turning 1v1 duels into 2v1 executions. The Phase-Shift Protocol is not about healing; it is about arriving with overwhelming force the moment an enemy commits to a kill.
                            </p>
                            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-widest">
                                <TrendingUp className="w-4 h-4" />
                                Review Status: OPERATIONAL
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BrightwingDossier;

import { Shield, Target, Zap, AlertTriangle, Crown, Map as MapIcon, BarChart3, TrendingUp } from 'lucide-react';
import { useReplayData } from '../hooks/useReplayData';
import RankIcon from '../components/RankIcon';
import ServiceRecord from '../components/ServiceRecord';

const AlphaSpec = () => {
    const { profile, loading } = useReplayData();

    // Data derived from Match Forensics Audit
    const stats = {
        hero: "Gazlowe",
        level: profile?.hero_stats?.Gazlowe?.verified_season_2025_3?.level || 194,
        overallWR: profile?.hero_stats?.Gazlowe?.verified_season_2025_3?.wr || 58.2,
        totalGames: profile?.hero_stats?.Gazlowe?.verified_season_2025_3?.games || 79,
        rank: profile?.rank_data?.storm_league?.current_rank || "Bronze 2",
        derivedRank: "Platinum Tier",
        sectors: [
            { name: "Sky Temple", wr: 71.4, status: "DOMINANT" },
            { name: "Infernal Shrines", wr: 70.0, status: "DOMINANT" },
            { name: "Tomb of the Spider Queen", wr: 66.7, status: "ELITE" },
            { name: "Alterac Pass", wr: 66.7, status: "ELITE" },
            { name: "Garden of Terror", wr: 60.0, status: "STRONG" },
            { name: "Blackheart's Bay", wr: 52.9, status: "THE PIRATE KING" } // Verified 17 games
        ],
        medals: {
            'Cannoneer': 6,
            'Bosun Medals': 10, // Combined Coins + Bosun
            'MVP': 12
        },
        risks: [
            { name: "Diablo", wr: 30.4, type: "Neural Desync" },
            { name: "Illidan", wr: 36.4, type: "Neural Desync" }
        ],
        nemesis: [
            { name: "Rexxar", wr: 10.0, type: "Apex Threat" },
            { name: "Alarak", wr: 28.6, type: "Critical Counter" },
            { name: "Sonya", wr: 33.3, type: "Recurring Threat" }
        ]
    };

    if (loading) return <div className="p-8 text-cyan-400 animate-pulse">Neural Synchronization in Progress...</div>;

    return (
        <div className="min-h-full pb-20 animate-in fade-in duration-700">
            {/* Dossier Header */}
            <div className="relative mb-12">
                <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg blur opacity-25"></div>
                <div className="relative bg-slate-900/80 border border-white/10 p-8 rounded-lg backdrop-blur-xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Internal Clearance: Level 10
                                </span>
                                <span className="px-3 py-1 bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded">
                                    Subject: Alpha Spec
                                </span>
                            </div>
                            <h1 className="text-5xl font-black bg-gradient-to-r from-white via-cyan-200 to-slate-400 bg-clip-text text-transparent tracking-tighter uppercase mb-2">
                                Elite Tactics Dossier
                            </h1>
                            <p className="text-slate-400 font-medium tracking-wide">
                                Tactical Audit: Subject <span className="text-cyan-400">"Discerning"</span> // Operation <span className="text-purple-400">"Gazlowe Dominance"</span>
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Current Bracket</div>
                            <div className="text-2xl font-bold text-white flex items-center justify-end gap-2 text-right">
                                <RankIcon rank={stats.rank} size="lg" />
                                <div className="flex flex-col items-end">
                                    <span>{stats.rank}</span>
                                    {profile?.rank_data?.storm_league?.rank_points !== undefined && (
                                        <span className="text-[10px] text-slate-400 font-mono tracking-tighter uppercase">
                                            {profile.rank_data.storm_league.rank_points} PTS // {profile.rank_data.storm_league.points_required_for_promotion} TO PROMOTE
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="text-[10px] text-cyan-500 font-bold uppercase mt-1 tracking-tighter">
                                Predicted Neural Peak: {stats.derivedRank}
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
                            <Crown className="w-24 h-24 text-cyan-400" />
                        </div>

                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-700 p-0.5 shadow-lg shadow-cyan-500/20">
                                <img
                                    src="/images/heroes/gazlowe.png"
                                    alt="Gazlowe"
                                    className="w-full h-full object-cover rounded-[10px]"
                                />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white tracking-tight">{stats.hero}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="text-cyan-400 font-bold">LVL {stats.level}</span>
                                    <span className="w-1 h-1 bg-slate-600 rounded-full"></span>
                                    <span className="text-slate-400 text-sm">Systemic Outlier</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Global Precision</div>
                                <div className="text-3xl font-black text-white">{stats.overallWR}% <span className="text-sm font-normal text-slate-400">WR</span></div>
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                                    <div className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" style={{ width: `${stats.overallWR}%` }}></div>
                                </div>
                            </div>

                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">Engagement Volume</div>
                                <div className="text-2xl font-bold text-white">{stats.totalGames} <span className="text-sm font-normal text-slate-400 text-xs">Verified Samples</span></div>
                            </div>
                        </div>
                        {/* Service Record */}
                        <ServiceRecord medals={stats.medals} />
                    </div>

                    <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-6 relative overflow-hidden">
                        <div className="flex items-center gap-2 mb-6">
                            <AlertTriangle className="w-5 h-5 text-red-400" />
                            <h3 className="text-sm font-bold text-red-400 uppercase tracking-widest">Apex Threats Identified</h3>
                        </div>

                        <div className="space-y-4">
                            {stats.nemesis.map((n, i) => (
                                <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-red-500/10 border border-red-500/10 group hover:bg-red-500/20 transition-all">
                                    <div>
                                        <div className="text-white font-bold">{n.name}</div>
                                        <div className="text-[10px] text-red-400/70 uppercase font-black">{n.type}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-red-400 font-black">{n.wr}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase">Victory Rate</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Main Intelligence */}
                <div className="lg:col-span-2 space-y-8">

                    {/* Sector Dominance */}
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-3">
                                <MapIcon className="w-6 h-6 text-cyan-400" />
                                <h3 className="text-xl font-bold text-white">Top Sector Performance</h3>
                            </div>
                            <BarChart3 className="w-5 h-5 text-slate-600" />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {stats.sectors.map((s, i) => (
                                <div key={i} className="p-5 rounded-xl border border-white/5 bg-white/5 flex items-center justify-between hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all cursor-default">
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{s.name}</h4>
                                        <span className={`text-[10px] font-black uppercase tracking-widest ${s.wr >= 70 ? 'text-cyan-400' : 'text-emerald-400'}`}>
                                            {s.status}
                                        </span>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-2xl font-black text-white">{s.wr}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Control Ratio</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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
                                Strategic Note: High-mastery performance often conflicts with ally engage patterns in this bracket. Manual synchronization required.
                            </p>
                        </div>

                        {/* Final Verdict */}
                        <div className="bg-gradient-to-br from-cyan-900/40 to-blue-900/40 border border-cyan-500/20 rounded-2xl p-6 relative overflow-hidden">
                            <div className="absolute -bottom-6 -right-6 opacity-10">
                                <TrendingUp className="w-32 h-32 text-cyan-400" />
                            </div>

                            <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-widest mb-4">Tactical Summary</h3>
                            <div className="relative z-10">
                                <p className="text-white font-medium leading-relaxed mb-4">
                                    "You are effectively a <span className="text-cyan-400 font-bold underline decoration-cyan-500/30">Platinum-grade Gazlowe pilot</span> operating in a {stats.rank} ecosystem."
                                </p>
                                <p className="text-slate-300 text-sm leading-relaxed mb-6">
                                    Subject demonstrates advanced Macro Superiority doctrines that the bracket has no automated response for. Primary challenge is not mechanical, but synchronization with volatile teammate variables.
                                </p>
                                <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs uppercase tracking-widest">
                                    <TrendingUp className="w-4 h-4" />
                                    Evolving to Gold // ETA: Immediate
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default AlphaSpec;

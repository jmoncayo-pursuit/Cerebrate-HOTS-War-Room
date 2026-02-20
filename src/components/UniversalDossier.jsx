
import React, { useState } from 'react';
import { Shield, Target, Zap, AlertTriangle, Crown, Map as MapIcon, BarChart3, TrendingUp, RefreshCw, ShieldCheck, AlertCircle, Info, ChevronDown, ChevronUp, Swords } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import RankIcon from './RankIcon';
import ServiceRecord from './ServiceRecord';
import HeroPortrait from './HeroPortrait';
import ConfidenceScore from './ConfidenceScore';
import { formatFullDateTime } from '../utils/dateUtils';

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

const TruthBadge = ({ source }) => {
    const isSecure = source === 'SECURE_DATALINK';
    const isMechanical = source === 'MECHANICAL_AUDIT';

    let colors = 'bg-purple-500/10 border-purple-500/30 text-purple-400';
    if (isSecure) colors = 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
    if (isMechanical) colors = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';

    return (
        <span className={`ml-2 px-1.5 py-0.5 rounded-[2px] text-[8px] font-black uppercase tracking-tighter border ${colors}`}
            title={isSecure ? 'Verified Match Data' : isMechanical ? 'Heuristic Mechanical Analysis' : 'AI Strategic Synthesis'}>
            {isSecure ? 'TRUTH' : isMechanical ? 'CORE' : 'NEURAL'}
        </span>
    );
};

const UniversalDossier = ({ stats, loading, onGenerate }) => {
    if (loading) {
        return (
            <div className="min-h-full flex items-center justify-center p-8">
                <div className="text-cyan-400 animate-pulse text-xl font-mono tracking-widest flex flex-col items-center gap-4">
                    <RefreshCw className="w-12 h-12 animate-spin" />
                    Initializing Neural Link...
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="min-h-full flex flex-col items-center justify-center p-8 text-center space-y-6">
                <div className="text-slate-500 uppercase tracking-widest font-bold">No Dossier Found</div>
                <button
                    onClick={onGenerate}
                    className="px-6 py-3 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded-lg text-cyan-400 font-bold uppercase tracking-widest transition-all flex items-center gap-2"
                >
                    <Zap className="w-5 h-5" />
                    Generate Elite Dossier
                </button>
            </div>
        );
    }

    const theme = {
        primary: (stats.theme && stats.theme.primary) || 'cyan',
        secondary: (stats.theme && stats.theme.secondary) || 'blue',
        gradient: (stats.theme && stats.theme.gradient) || 'from-cyan-600 to-blue-600',
    };

    return (
        <div className="min-h-full pb-20 animate-in fade-in duration-700">
            {/* Dossier Header */}
            <div className="relative mb-12">
                <div className={`absolute -inset-1 bg-gradient-to-r ${theme.gradient} rounded-lg blur opacity-25`}></div>
                <div className="relative bg-slate-900/80 border border-white/10 p-8 rounded-lg backdrop-blur-xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className={`px-3 py-1 bg-${theme.primary}-500/10 border border-${theme.primary}-500/30 text-${theme.primary}-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded`}>
                                    Internal Clearance: Level {stats.clearanceLevel || 1}
                                </span>
                                {stats.codename && (
                                    <span className={`px-3 py-1 bg-${theme.secondary}-500/10 border border-${theme.secondary}-500/30 text-${theme.secondary}-400 text-[10px] uppercase tracking-[0.2em] font-bold rounded`}>
                                        Subject: {stats.codename}
                                    </span>
                                )}
                            </div>
                            <h1 className={`text-5xl font-black bg-gradient-to-r from-white via-${theme.primary}-200 to-slate-400 bg-clip-text text-transparent tracking-tighter uppercase mb-2`}>
                                Elite Tactics Dossier
                            </h1>
                            <p className="text-slate-400 font-medium tracking-wide">
                                Tactical Audit: Subject <span className={`text-${theme.primary}-400`}>"Discerning"</span> // Operation <span className={`text-${theme.secondary}-400`}>"{stats.operationName || stats.hero}"</span>
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
                            {stats.derivedRank && (
                                <div className={`text-[10px] text-${theme.primary}-500 font-bold uppercase mt-1 tracking-tighter`}>
                                    Predicted Neural Peak: {stats.derivedRank}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Profile Card */}
                <div className="lg:col-span-1 space-y-8">
                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Crown className={`w-24 h-24 text-${theme.primary}-400`} />
                        </div>
                        <div className="flex items-center gap-4 mb-8">
                            <div className={`w-20 h-20 rounded-xl bg-gradient-to-br from-${theme.primary}-500 to-${theme.secondary}-700 p-0.5 shadow-lg shadow-${theme.primary}-500/20`}>
                                <img src={`/images/heroes/${stats.hero.toLowerCase().replace(/[^a-z0-9]/g, '')}.png`} alt={stats.hero} className="w-full h-full object-cover rounded-[10px]" onError={(e) => { e.target.src = '/images/heroes/unknown.png' }} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-white tracking-tight">{stats.hero}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className={`text-${theme.primary}-400 font-bold`}>LVL {stats.level}</span>
                                    <span className="text-slate-400 text-sm">{stats.roleDescription || "Field Operative"}</span>
                                </div>
                            </div>
                        </div>

                        {/* Summary Stats */}
                        <div className="space-y-4">
                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1 flex items-center">
                                    Global Precision
                                    <TruthBadge source={stats.statSources && stats.statSources.overallWR} />
                                </div>
                                <ConfidenceScore value={stats.overallWR} n={stats.totalGames} />
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                                    <div className={`h-full bg-${theme.primary}-500 shadow-[0_0_10px_rgba(0,0,0,0.5)]`} style={{ width: `${stats.overallWR}%` }}></div>
                                </div>
                            </div>
                            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1 flex items-center">
                                    Engagement Volume
                                    <TruthBadge source={stats.statSources && stats.statSources.totalGames} />
                                </div>
                                <div className="text-2xl font-bold text-white">{stats.totalGames} <span className="text-sm font-normal text-slate-400 text-xs">Verified Samples</span></div>
                            </div>

                            {/* Service Record Module */}
                            {stats.medals && <ServiceRecord medals={stats.medals} />}
                        </div>
                    </div>

                    {/* Nemesis / Apex Threats */}
                    {stats.nemesis && stats.nemesis.length > 0 && (
                        <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-6 relative overflow-hidden">
                            <div className="flex items-center gap-2 mb-6">
                                <AlertTriangle className="w-5 h-5 text-red-400" />
                                <h3 className="text-sm font-bold text-red-400 uppercase tracking-widest">Apex Threats Identified</h3>
                            </div>
                            <div className="space-y-4">
                                {(stats.nemesis || []).map((n, i) => (
                                    <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-red-500/10 border border-red-500/10 group hover:bg-red-500/20 transition-all">
                                        <div>
                                            <div className="text-white font-bold">{n.name}</div>
                                            <div className="text-[10px] text-red-400/70 uppercase font-black">{n.type}</div>
                                        </div>
                                        <div className="text-right">
                                            <ConfidenceScore value={n.wr} n={n.games} className="scale-75 origin-right" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Main Intel */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Lethality Breakthrough */}
                    {stats.lethality && stats.lethality.high.games > 0 && (
                        <div className="bg-gradient-to-br from-red-900/20 via-black to-cyan-900/20 border border-white/10 rounded-2xl p-8 backdrop-blur-md relative overflow-hidden group">
                            <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                <Zap className="w-40 h-40 text-cyan-400" />
                            </div>

                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-cyan-500/20 rounded-lg">
                                        <Zap className="w-6 h-6 text-cyan-400" />
                                    </div>
                                    <h3 className="text-xl font-black text-white uppercase tracking-tighter">Lethality Breakthrough</h3>
                                    <TruthBadge source="MECHANICAL_AUDIT" />
                                </div>
                                {stats.lethality.jump > 15 && (
                                    <span className="px-3 py-1 bg-cyan-500 text-black text-[10px] font-black uppercase rounded animate-pulse">
                                        Victory Condition Identified
                                    </span>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                                <div className="space-y-6">
                                    <div className="relative">
                                        <div className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-2">Agency Shift (Win Rate Jump)</div>
                                        <div className="text-5xl font-black text-white flex items-baseline gap-2">
                                            +{stats.lethality.jump}%
                                            <span className="text-sm font-bold text-cyan-500/70 tracking-normal uppercase">Agency Premium</span>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex justify-between items-end">
                                            <div className="text-xs text-slate-400 font-bold uppercase tracking-tighter">Under {stats.lethality.threshold} Kills</div>
                                            <div className="text-xs text-red-400 font-mono">{stats.lethality.low.wr}% WR</div>
                                        </div>
                                        <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-red-500/40" style={{ width: `${stats.lethality.low.wr}%` }}></div>
                                        </div>

                                        <div className="flex justify-between items-end mt-4">
                                            <div className="text-xs text-cyan-400 font-bold uppercase tracking-tighter">{stats.lethality.threshold}+ Kills (Power Zone)</div>
                                            <div className="text-xs text-cyan-400 font-mono font-bold">{stats.lethality.high.wr}% WR</div>
                                        </div>
                                        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden shadow-[0_0_15px_rgba(6,182,212,0.2)]">
                                            <div className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" style={{ width: `${stats.lethality.high.wr}%` }}></div>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-black/40 border border-white/5 p-6 rounded-xl space-y-4">
                                    <div className="flex items-start gap-3">
                                        <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center shrink-0 border border-cyan-500/20">
                                            <Target size={14} className="text-cyan-400" />
                                        </div>
                                        <p className="text-[11px] text-slate-300 leading-relaxed uppercase tracking-tight">
                                            <span className="text-white font-bold">Lethal Threshold found at {stats.lethality.threshold} Kills.</span> Securing this count shift individual agency from passive to dominant.
                                        </p>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <div className="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center shrink-0 border border-red-500/20">
                                            <Shield size={14} className="text-red-400" />
                                        </div>
                                        <p className="text-[11px] text-slate-300 leading-relaxed uppercase tracking-tight">
                                            Current sample shows <span className="text-white font-bold">{stats.lethality.high.games} matches</span> hitting the zone with a <span className="text-cyan-400 font-bold">{stats.lethality.high.wr}% Success Rate</span>.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Tactical Forensics */}
                    {stats.forensics && (
                        <div className="bg-slate-900/50 border border-cyan-500/20 rounded-2xl p-8 backdrop-blur-sm">
                            <div className="flex flex-col gap-6">
                                {/* The Good */}
                                <div>
                                    <div className="flex items-center gap-3 mb-6">
                                        <Zap className="w-6 h-6 text-cyan-400" />
                                        <h3 className="text-xl font-bold text-white">Tactical Forensics</h3>
                                        <TruthBadge source="MECHANICAL_AUDIT" />
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {(stats.forensics.summary_stats || []).map((s, i) => (
                                            <div key={i} className="p-5 rounded-xl border border-white/5 bg-white/5 group hover:border-cyan-500/30 transition-all">
                                                <div className="text-[10px] text-cyan-500/70 uppercase tracking-widest mb-1 font-bold">{s.label}</div>
                                                <div className="text-2xl font-black text-white">{s.value}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* The Bad */}
                                {stats.forensics.mortality_stats && stats.forensics.mortality_stats.length > 0 && (
                                    <div className="pt-6 border-t border-white/5">
                                        <div className="flex items-center gap-3 mb-6">
                                            <AlertTriangle className="w-5 h-5 text-red-400" />
                                            <h3 className="text-lg font-bold text-white">Mortality Audit</h3>
                                            <TruthBadge source="SECURE_DATALINK" />
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            {(stats.forensics.mortality_stats || []).map((s, i) => (
                                                <div key={i} className="p-5 rounded-xl border border-red-500/10 bg-red-900/10 group hover:border-red-500/30 transition-all">
                                                    <div className="text-[10px] text-red-400/70 uppercase tracking-widest mb-1 font-bold">{s.label}</div>
                                                    <div className="text-2xl font-black text-red-100">{s.value}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Specific Targets */}
                                {stats.forensics.top_victims && stats.forensics.top_victims.length > 0 && (
                                    <div className="pt-6 border-t border-white/5">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Target className="w-4 h-4 text-cyan-400" />
                                            <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-widest">High Value Targets (Most Hooked)</h4>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {stats.forensics.top_victims.map((v, i) => (
                                                <div key={i} className="p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/10 flex items-center justify-between">
                                                    <div className="text-white font-bold">{v.name}</div>
                                                    <div className="text-xs text-cyan-400 uppercase font-black tracking-widest">{v.count} Confirmed Hooks</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-8">
                            <MapIcon className={`w-6 h-6 text-${theme.primary}-400`} />
                            <h3 className="text-xl font-bold text-white">Sector Control</h3>
                            <TruthBadge source={stats.statSources && stats.statSources.sectors} />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {(stats.sectors || []).map((s, i) => (
                                <div key={i} className="p-5 rounded-xl border border-white/5 bg-white/5 flex items-center justify-between">
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{s.name}</h4>
                                        <span className={`text-[10px] text-${theme.primary}-400 font-black uppercase tracking-widest`}>{s.status}</span>
                                    </div>
                                    <ConfidenceScore value={s.wr} n={s.games_played || 0} className="scale-90 origin-right" />
                                </div>
                            ))}
                        </div>

                        {stats.trainingSectors && stats.trainingSectors.length > 0 && (
                            <div className="mt-8 pt-8 border-t border-white/5">
                                <div className="flex items-center gap-2 mb-4">
                                    <Swords className="w-4 h-4 text-cyan-400" />
                                    <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-widest">Targeted Training Sectors</h4>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {(stats.trainingSectors || []).map((s, i) => (
                                        <div key={i} className="p-4 rounded-lg bg-cyan-900/10 border border-cyan-500/20 flex items-center justify-between opacity-80">
                                            <div className="text-white font-medium">{s.name}</div>
                                            <ConfidenceScore value={s.wr} n={s.games_played || 0} className="scale-75 origin-right" />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:col-span-2">
                        {/* Neural Risks */}
                        {stats.risks && stats.risks.length > 0 && (
                            <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6">
                                <div className="flex items-center gap-2 mb-6">
                                    <Zap className="w-5 h-5 text-purple-400" />
                                    <h3 className="text-sm font-bold text-purple-400 uppercase tracking-widest">Neural Desync Risks</h3>
                                </div>
                                <div className="space-y-4">
                                    {(stats.risks || []).map((r, i) => (
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
                                                <ConfidenceScore value={r.wr} n={r.games} className="scale-75 origin-right" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                {stats.riskNote && (
                                    <p className="mt-6 text-xs text-slate-500 italic leading-relaxed">
                                        Strategic Note: {stats.riskNote}
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Tactical Summary */}
                        {stats.tacticalSummary && (
                            <div className={`bg-gradient-to-br from-${theme.primary}-900/40 to-${theme.secondary}-900/40 border border-${theme.primary}-500/20 rounded-2xl p-6 relative overflow-hidden`}>
                                <div className="absolute -top-1 -right-1">
                                    <TruthBadge source={stats.statSources && stats.statSources.tacticalSummary} />
                                </div>
                                <div className="absolute -bottom-6 -right-6 opacity-10">
                                    <TrendingUp className={`w-32 h-32 text-${theme.primary}-400`} />
                                </div>
                                <h3 className={`text-sm font-bold text-${theme.primary}-400 uppercase tracking-widest mb-4`}>Tactical Summary</h3>
                                <div className="relative z-10">
                                    {stats.tacticalSummary.verdict && (
                                        <p className="text-white font-medium leading-relaxed mb-4" dangerouslySetInnerHTML={{ __html: stats.tacticalSummary.verdict }}></p>
                                    )}
                                    {stats.tacticalSummary.analysis && (
                                        <p className="text-slate-300 text-sm leading-relaxed mb-6">
                                            {stats.tacticalSummary.analysis}
                                        </p>
                                    )}
                                    <div className={`flex items-center gap-2 text-${theme.primary}-400 font-bold text-xs uppercase tracking-widest`}>
                                        <TrendingUp className="w-4 h-4" />
                                        Review Status: {stats.tacticalSummary.status || "OPERATIONAL"}
                                    </div>

                                    {/* Audit Badge for AI Verdict */}
                                    {stats.audit && (
                                        <AuditBadge audit={stats.audit} />
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Mission History */}
                    {stats.recentPerformance && stats.recentPerformance.length > 0 && (
                        <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 backdrop-blur-sm">
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-3">
                                    <BarChart3 className={`w-6 h-6 text-${theme.primary}-400`} />
                                    <h3 className="text-xl font-bold text-white">Mission History</h3>
                                    <TruthBadge source="SECURE_DATALINK" />
                                </div>
                                <span className="text-[10px] text-slate-500 uppercase font-mono italic">Verified Match Records</span>
                            </div>
                            <div className="space-y-3">
                                {(stats.recentPerformance || []).map((match, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all cursor-pointer group"
                                        onClick={() => window.dispatchEvent(new CustomEvent('nav_to_replay', { detail: match.id }))}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`w-10 h-10 rounded border flex items-center justify-center font-black ${match.result === 'WIN' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-red-500/10 border-red-500/30 text-red-400'
                                                }`}>
                                                {match.result[0]}
                                            </div>
                                            <div>
                                                <div className="text-white font-bold text-sm tracking-tight">{match.map}</div>
                                                <div className="text-[10px] text-slate-500 uppercase">{formatFullDateTime(match.date)}</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-6">
                                            <div className="flex gap-4">
                                                <div className="text-center">
                                                    <div className="text-[10px] text-slate-500 uppercase">K</div>
                                                    <div className="text-xs font-bold text-white">{match.kills}</div>
                                                </div>
                                                <div className="text-center">
                                                    <div className="text-[10px] text-slate-500 uppercase">D</div>
                                                    <div className="text-xs font-bold text-white">{match.deaths}</div>
                                                </div>
                                                <div className="text-center">
                                                    <div className="text-[10px] text-slate-500 uppercase">A</div>
                                                    <div className="text-xs font-bold text-white">{match.assists}</div>
                                                </div>
                                            </div>
                                            <div className="text-slate-600 group-hover:text-cyan-400 transition-colors">
                                                <Zap className="w-4 h-4" />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UniversalDossier;

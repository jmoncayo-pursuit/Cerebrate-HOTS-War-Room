import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Skull, Sword, Zap, AlertTriangle, Crosshair, Users } from 'lucide-react';

const CompositionMatrix = () => {
    const [selectedRole, setSelectedRole] = useState('TANK');

    // Matrix Logic: "Standard" vs "Asymmetric_Warfare"
    // Based on User Reality: Bronze 3 / High Variance
    const compositions = {
        TANK: {
            standard: {
                name: "The 'Standard' Trap",
                desc: "Traditional Tanking (Peel/Engage). Relies on team follow-up.",
                winRate: "20-33%",
                heroes: ["Stitches", "Tyrael", "Johanna"],
                verdict: "CRITICAL FAILURE",
                risk: "High (Dependency)",
                color: "text-red-500"
            },
            asymmetric: {
                name: "The 'Macro-Enforcer'",
                desc: "Zone Control & Waveclear. Forces enemy to respond to YOU.",
                winRate: "52%+",
                heroes: ["Gazlowe", "Dehaka", "Blaze"],
                verdict: "OPTIMAL PATH",
                risk: "Low (Independence)",
                color: "text-green-400"
            }
        },
        HEALER: {
            standard: {
                name: "The 'Passenger' Healer",
                desc: "Sustained Healing. Only delays the inevitable if team fails to kill.",
                winRate: "45%",
                heroes: ["Lt. Morales", "Li Li", "Whitemane"],
                verdict: "INEFFECTIVE",
                risk: "High (Passive)",
                color: "text-orange-400"
            },
            asymmetric: {
                name: "The 'Gladiator' Support",
                desc: "Serves kills & XP. Heals are secondary to finishing the fight.",
                winRate: "60%+",
                heroes: ["Rehgar", "Kharazim", "Brightwing"],
                verdict: "FORCE MULTIPLIER",
                risk: "Medium (Requires Aggression)",
                color: "text-cyan-400"
            }
        },
        DPS: {
            standard: {
                name: "The 'Poker'",
                desc: "High Hero Damage, Low Siege. Fluffs stats but doesn't end games.",
                winRate: "40%",
                heroes: ["Li-Ming (Orb)", "Hanzo", "Chromie"],
                verdict: "STAT TRAP",
                risk: "Medium",
                color: "text-yellow-400"
            },
            asymmetric: {
                name: "The 'Siege-Breaker'",
                desc: "Structure deletion. Turns one won fight into a game-over.",
                winRate: "60-64%",
                heroes: ["Sylvanas", "Raynor (Exterm)", "Azmodan"],
                verdict: "WIN CONDITION",
                risk: "Low (Macro Pressure)",
                color: "text-purple-400"
            }
        }
    };

    const currentComp = compositions[selectedRole];

    return (
        <div className="p-6 bg-slate-900 min-h-screen text-slate-100 font-sans">
            <h1 className="text-3xl font-black text-white mb-2 uppercase tracking-tight flex items-center gap-3">
                <Crosshair className="text-cyan-400" />
                Tactical Composition Matrix
            </h1>
            <p className="text-slate-400 mb-8 max-w-2xl text-sm border-l-2 border-cyan-500 pl-4 py-1">
                Forensic Analysis of "Standard" (Meta) vs "Asymmetric" (Bronze 3 Reality).
                <br /><span className="text-cyan-400 font-bold">Objective:</span> Identify why "Filling" with standard picks results in equity loss.
            </p>

            {/* Role Selector */}
            <div className="flex gap-2 mb-8">
                {['TANK', 'HEALER', 'DPS'].map(role => (
                    <button
                        key={role}
                        onClick={() => setSelectedRole(role)}
                        className={`px-6 py-3 rounded-lg font-black uppercase tracking-widest text-sm transition-all duration-300 ${selectedRole === role
                                ? 'bg-cyan-600 text-white shadow-[0_0_15px_rgba(8,145,178,0.5)]'
                                : 'bg-slate-800 text-slate-500 hover:bg-slate-700 hover:text-slate-300'
                            }`}
                    >
                        {role}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl">

                {/* Standard Trap Card */}
                <motion.div
                    key={`${selectedRole}-standard`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="relative bg-slate-800/50 border border-slate-700 rounded-2xl p-6 overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Users size={120} />
                    </div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="bg-slate-700/50 text-slate-400 px-2 py-1 rounded text-[10px] uppercase font-bold tracking-widest">
                                The "Fill" Option
                            </span>
                        </div>
                        <h2 className={`text-2xl font-black mb-2 ${currentComp.standard.color}`}>
                            {currentComp.standard.name}
                        </h2>
                        <p className="text-sm text-slate-300 mb-6 italic border-l-2 border-slate-600 pl-3">
                            "{currentComp.standard.desc}"
                        </p>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-black/30 p-3 rounded-lg text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Win Probability</div>
                                <div className={`text-2xl font-mono font-bold ${currentComp.standard.color}`}>
                                    {currentComp.standard.winRate}
                                </div>
                            </div>
                            <div className="bg-black/30 p-3 rounded-lg text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Risk Profile</div>
                                <div className="text-xl font-mono font-bold text-slate-200">
                                    {currentComp.standard.risk}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="text-xs uppercase text-slate-500 font-bold tracking-wider">Example Assets</div>
                            <div className="flex flex-wrap gap-2">
                                {currentComp.standard.heroes.map(h => (
                                    <span key={h} className="px-3 py-1 bg-red-900/20 border border-red-500/30 text-red-200 text-xs font-mono rounded">
                                        {h}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="mt-8 pt-4 border-t border-white/5">
                            <div className="flex items-center gap-2 text-red-400 font-bold text-sm uppercase">
                                <AlertTriangle size={16} />
                                Verdict: {currentComp.standard.verdict}
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Asymmetric Solution Card */}
                <motion.div
                    key={`${selectedRole}-asymmetric`}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="relative bg-gradient-to-br from-cyan-900/20 to-slate-900 border border-cyan-500/30 rounded-2xl p-6 overflow-hidden shadow-[0_0_30px_rgba(8,145,178,0.1)]"
                >
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Crosshair size={120} className="text-cyan-400" />
                    </div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="bg-cyan-500/20 text-cyan-300 px-2 py-1 rounded text-[10px] uppercase font-bold tracking-widest border border-cyan-500/30">
                                The "Smurf" Option
                            </span>
                        </div>
                        <h2 className={`text-2xl font-black mb-2 ${currentComp.asymmetric.color}`}>
                            {currentComp.asymmetric.name}
                        </h2>
                        <p className="text-sm text-cyan-100/80 mb-6 italic border-l-2 border-cyan-500 pl-3">
                            "{currentComp.asymmetric.desc}"
                        </p>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-cyan-950/40 border border-cyan-500/20 p-3 rounded-lg text-center">
                                <div className="text-[10px] text-cyan-400/70 uppercase">Win Probability</div>
                                <div className={`text-2xl font-mono font-bold ${currentComp.asymmetric.color}`}>
                                    {currentComp.asymmetric.winRate}
                                </div>
                            </div>
                            <div className="bg-cyan-950/40 border border-cyan-500/20 p-3 rounded-lg text-center">
                                <div className="text-[10px] text-cyan-400/70 uppercase">Risk Profile</div>
                                <div className="text-xl font-mono font-bold text-white">
                                    {currentComp.asymmetric.risk}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="text-xs uppercase text-cyan-500 font-bold tracking-wider">Recommended Assets</div>
                            <div className="flex flex-wrap gap-2">
                                {currentComp.asymmetric.heroes.map(h => (
                                    <span key={h} className="px-3 py-1 bg-cyan-500/20 border border-cyan-400/50 text-cyan-100 text-xs font-mono rounded shadow-[0_0_10px_rgba(34,211,238,0.2)]">
                                        {h}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="mt-8 pt-4 border-t border-cyan-500/20">
                            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm uppercase animate-pulse">
                                <Shield size={16} />
                                Verdict: {currentComp.asymmetric.verdict}
                            </div>
                        </div>
                    </div>
                </motion.div>

            </div>
        </div>
    );
};

export default CompositionMatrix;

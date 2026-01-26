import { useState, useEffect } from 'react';
import { Shield, Sword, Eye, Terminal, ChevronRight, Zap } from 'lucide-react';
import './DraftSimulation.css';

export default function DraftSimulation() {
    const [isScanning, setIsScanning] = useState(false);
    const [showInsights, setShowInsights] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);

    const launchAnalysis = () => {
        setIsScanning(true);
        setScanProgress(0);
        setShowInsights(false);

        // Simulate neural scanning progress
        const interval = setInterval(() => {
            setScanProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setTimeout(() => {
                        setIsScanning(false);
                        setShowInsights(true);
                    }, 500);
                    return 100;
                }
                return prev + 5;
            });
        }, 100);
    };

    return (
        <div className="draft-simulation animate-fadeIn">
            {/* Simulation Header */}
            <div className="draft-header">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold text-white uppercase tracking-tight">Strategic Vision</h2>
                        <div className="status-dot active"></div>
                        <span className="text-[10px] font-mono text-cyan-500 uppercase">Live Nexus Polling</span>
                    </div>
                    <p className="text-slate-400 text-xs">Simulated Lobby Injection · Real-time Scout Analysis</p>
                </div>

                <button
                    onClick={launchAnalysis}
                    disabled={isScanning}
                    className={`launch-btn ${isScanning ? 'scanning' : ''}`}
                >
                    {isScanning ? (
                        <>
                            <Terminal size={18} className="animate-pulse" />
                            Scout Polling... {scanProgress}%
                        </>
                    ) : (
                        <>
                            <Eye size={18} />
                            Launch Live Draft Analysis
                        </>
                    )}
                </button>
            </div>

            {/* Lobby Simulation */}
            <div className="lobby-grid">
                <div className="team-container">
                    <h3 className="team-title">Your Team (Blue)</h3>
                    <div className="hero-slot filled">
                        <div className="hero-portrait">
                            <img src="/images/heroes/johanna.png" alt="Johanna" className="w-full h-full object-cover" />
                        </div>
                        <div className="hero-info">
                            <span className="hero-name">Johanna</span>
                            <span className="hero-role">Tank</span>
                        </div>
                    </div>
                    <div className="hero-slot filled">
                        <div className="hero-portrait">
                            <img src="/images/heroes/valla.png" alt="Valla" className="w-full h-full object-cover" />
                        </div>
                        <div className="hero-info">
                            <span className="hero-name">Valla</span>
                            <span className="hero-role">Ranged Assassin</span>
                        </div>
                    </div>
                    <div className="hero-slot filled border-cyan-500/50 bg-cyan-500/5 ring-1 ring-cyan-500/20">
                        <div className="hero-portrait border-cyan-500/50">
                            <div className="flex items-center justify-center h-full text-cyan-500/30">
                                <Zap size={24} />
                            </div>
                        </div>
                        <div className="hero-info">
                            <span className="hero-name text-cyan-400 italic">Target Insight Area</span>
                            <span className="hero-role">Flex Pick Needed</span>
                        </div>
                    </div>
                    <div className="hero-slot"></div>
                    <div className="hero-slot"></div>
                </div>

                <div className="vs-badge">VS</div>

                <div className="team-container">
                    <h3 className="team-title">Opponents (Red)</h3>
                    <div className="hero-slot filled border-red-500/30">
                        <div className="hero-portrait border-red-500/20">
                            <img src="/images/heroes/diablo.png" alt="Diablo" className="w-full h-full object-cover" />
                        </div>
                        <div className="hero-info">
                            <span className="hero-name">Diablo</span>
                            <span className="hero-role">Tank</span>
                        </div>
                    </div>
                    <div className="hero-slot filled border-red-500/30">
                        <div className="hero-portrait border-red-500/20">
                            <img src="/images/heroes/uther.png" alt="Uther" className="w-full h-full object-cover" />
                        </div>
                        <div className="hero-info">
                            <span className="hero-name">Uther</span>
                            <span className="hero-role">Healer</span>
                        </div>
                    </div>
                    <div className="hero-slot"></div>
                    <div className="hero-slot"></div>
                    <div className="hero-slot"></div>
                </div>
            </div>

            {/* Intelligence Result */}
            {isScanning && (
                <div className="scanning-overlay">
                    <div className="scanner-ring"></div>
                    <div className="scanning-text">Neural Scout Scanning Lobby Patterns...</div>
                    <div className="flex gap-2 max-w-xs w-full">
                        <div className="h-1 bg-cyan-950 flex-1 rounded-full overflow-hidden">
                            <div className="h-full bg-cyan-500 transition-all duration-300" style={{ width: `${scanProgress}%` }}></div>
                        </div>
                    </div>
                </div>
            )}

            {showInsights && (
                <div className="insight-panel">
                    <div className="insight-title">
                        <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/20 insight-icon">
                            <Zap size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white uppercase tracking-tight">Live Strategic Insights</h3>
                            <p className="text-cyan-400/70 text-xs font-mono">SCOUT AGENT · OPTIMAL PATHWAY FOUND</p>
                        </div>
                    </div>

                    <div className="recommendations-grid">
                        <div className="rec-card border-l-4 border-l-amber-500">
                            <div className="rec-header">
                                <div className="w-12 h-12 bg-slate-800 rounded-lg overflow-hidden border border-white/10">
                                    <img src="/images/heroes/tychus.png" alt="Tychus" className="w-full h-full object-cover" />
                                </div>
                                <div className="hero-info">
                                    <span className="hero-name">Tychus</span>
                                    <span className="text-[10px] text-amber-500 font-bold uppercase">Meta Counter</span>
                                </div>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed italic">
                                \"Minigun will shred their Diablo/Uther frontline. High lethality against their current composition.\"
                            </p>
                            <div className="rec-stats">
                                <div className="stat-item">
                                    <span className="stat-label">Win Rate vs Composition</span>
                                    <span className="stat-value positive">58.4%</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Synergy with Valla</span>
                                    <span className="stat-value positive">+4.2%</span>
                                </div>
                            </div>
                        </div>

                        <div className="rec-card border-l-4 border-l-indigo-500">
                            <div className="rec-header">
                                <div className="w-12 h-12 bg-slate-800 rounded-lg overflow-hidden border border-white/10">
                                    <img src="/images/heroes/stitches.png" alt="Stitches" className="w-full h-full object-cover" />
                                </div>
                                <div className="hero-info">
                                    <span className="hero-name">Stitches</span>
                                    <span className="text-[10px] text-indigo-400 font-bold uppercase">Displacement Strat</span>
                                </div>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed italic">
                                \"Uther has limited mobility to save hooked targets. Gorge creates 5v4 opportunities early.\"
                            </p>
                            <div className="rec-stats">
                                <div className="stat-item">
                                    <span className="stat-label">Win Rate vs Composition</span>
                                    <span className="stat-value positive">53.1%</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Map Preference</span>
                                    <span className="stat-value positive">High</span>
                                </div>
                            </div>
                        </div>

                        <div className="rec-card border-l-4 border-l-emerald-500">
                            <div className="rec-header">
                                <div className="w-12 h-12 bg-slate-800 rounded-lg overflow-hidden border border-white/10">
                                    <img src="/images/heroes/lucio.png" alt="Lucio" className="w-full h-full object-cover" />
                                </div>
                                <div className="hero-info">
                                    <span className="hero-name">Lúcio</span>
                                    <span className="text-[10px] text-emerald-500 font-bold uppercase">Efficiency Pick</span>
                                </div>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed italic">
                                \"Speed Boost helps Valla kite Diablo's engage. Sound Barrier counters Diablo's Apocalypse combo.\"
                            </p>
                            <div className="rec-stats">
                                <div className="stat-item">
                                    <span className="stat-label">Win Rate vs Composition</span>
                                    <span className="stat-value positive">52.8%</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Personal Skill</span>
                                    <span className="stat-value positive">92%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-white/5 flex justify-between items-center text-[10px]">
                        <div className="flex gap-4">
                            <span className="text-slate-500 font-mono"><span className="text-cyan-500">MAP:</span> INFERNAL SHRINES</span>
                            <span className="text-slate-500 font-mono"><span className="text-cyan-500">CONFIDENCE:</span> 94.2%</span>
                        </div>
                        <span className="text-slate-600 italic">Neural Network provided by Cerebrate Scout v2.1</span>
                    </div>
                </div>
            )}
        </div>
    );
}

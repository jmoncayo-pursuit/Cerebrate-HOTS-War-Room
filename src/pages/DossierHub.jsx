
import React, { useState, useEffect } from 'react';
import { Shield, ChevronRight, RefreshCw, PlusCircle, Search } from 'lucide-react';
import { useReplayData } from '../hooks/useReplayData';
import UniversalDossier from '../components/UniversalDossier';
import ConfidenceScore from '../components/ConfidenceScore';

const DossierHub = () => {
    const { heroes, matches, loading } = useReplayData();
    const [selectedHero, setSelectedHero] = useState(null);
    const [generatedDossiers, setGeneratedDossiers] = useState({});
    const [filter, setFilter] = useState('');
    const [manifest, setManifest] = useState(new Set());

    useEffect(() => {
        const fetchManifest = async () => {
            try {
                const res = await fetch('/api/hero_dossier/manifest');
                if (res.ok) {
                    const data = await res.json();
                    setManifest(new Set(data.manifest));
                }
            } catch (e) {
                console.error("Failed to load archive manifest", e);
            }
        };
        fetchManifest();

        // Listen for external navigation requests
        const handleNav = (e) => {
            if (e.detail) {
                fetchDossier(e.detail);
            }
        };
        window.addEventListener('nav_to_dossier', handleNav);
        return () => window.removeEventListener('nav_to_dossier', handleNav);
    }, []);

    const fetchDossier = async (heroName) => {
        // Check local state first
        if (generatedDossiers[heroName]) {
            setSelectedHero(generatedDossiers[heroName]);
            return;
        }

        // Set loading state
        setSelectedHero({ hero: heroName, loading: true });

        try {
            const res = await fetch(`/api/hero_dossier?hero=${encodeURIComponent(heroName)}`);
            if (!res.ok) throw new Error("Failed to retrieve dossier");

            const data = await res.json();

            setGeneratedDossiers(prev => ({
                ...prev,
                [heroName]: data
            }));
            setSelectedHero(data);

            // Add to manifest if successful
            setManifest(prev => new Set(prev).add(heroName));

        } catch (error) {
            console.error("Dossier generation failed:", error);
            // Fallback
            const mockGenerated = {
                hero: heroName,
                level: 0,
                overallWR: 0,
                totalGames: 0,
                tacticalSummary: {
                    verdict: "Neural Uplink Offline.",
                    analysis: "Unable to contact Cerebrate High Command. Check connection.",
                    status: "OFFLINE"
                }
            };
            setSelectedHero(mockGenerated);
        }
    };

    const sortedHeroes = [...heroes]
        .filter(h => h.games_played > 5) // Filter out noise
        .filter(h => h.hero.toLowerCase().includes(filter.toLowerCase()))
        .sort((a, b) => b.games_played - a.games_played);

    if (loading) return <div className="p-8 text-cyan-400 animate-pulse">Accessing War Room Archives...</div>;

    if (selectedHero) {
        return (
            <div className="relative">
                <button
                    onClick={() => setSelectedHero(null)}
                    className="absolute top-4 left-4 z-10 px-4 py-2 bg-black/50 hover:bg-black/80 text-cyan-400 text-xs font-bold uppercase tracking-widest border border-cyan-500/30 rounded flex items-center gap-2 backdrop-blur-md"
                >
                    <ChevronRight className="w-4 h-4 rotate-180" />
                    Return to Hub
                </button>
                <div className="pt-12 min-h-screen">
                    <UniversalDossier
                        stats={selectedHero.loading ? null : selectedHero}
                        loading={selectedHero.loading}
                        onGenerate={() => { }}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-full pb-20 animate-in fade-in duration-700 p-8">
            <div className="mb-12">
                <div className="flex items-center gap-3 mb-2">
                    <Shield className="w-6 h-6 text-cyan-400" />
                    <span className="text-cyan-400 text-xs uppercase tracking-[0.3em] font-bold">
                        Cerebrate // Archives
                    </span>
                </div>
                <h1 className="text-4xl font-black text-white tracking-tighter uppercase mb-6">
                    Hero Dossier Hub
                </h1>

                <div className="relative max-w-md">
                    <input
                        type="text"
                        placeholder="Search Protocols..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="w-full bg-slate-900/50 border border-white/10 rounded-lg py-3 pl-12 pr-4 text-white focus:outline-none focus:border-cyan-500/50 transition-all font-mono text-sm"
                    />
                    <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-500" />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {sortedHeroes.map((h, i) => {
                    const isArchived = manifest.has(h.hero);

                    return (
                        <div
                            key={i}
                            onClick={() => fetchDossier(h.hero)}
                            className={`group relative bg-slate-900/40 border border-white/5 rounded-xl p-4 cursor-pointer hover:bg-slate-800/60 hover:border-cyan-500/30 transition-all ${!isArchived ? 'opacity-70 hover:opacity-100' : ''}`}
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-lg bg-black/50 overflow-hidden border border-white/10 relative">
                                    <img
                                        src={`/images/heroes/${h.hero.toLowerCase().replace(/[^a-z0-9]/g, '')}.png`}
                                        alt={h.hero}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                        onError={(e) => { e.target.src = '/images/heroes/unknown.png' }}
                                    />
                                    {!isArchived && (
                                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                            <RefreshCw className="w-6 h-6 text-cyan-400" />
                                        </div>
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start">
                                        <h3 className="text-lg font-bold text-white truncate group-hover:text-cyan-400 transition-colors uppercase tracking-tight">{h.hero}</h3>
                                        {isArchived && <Shield className="w-3 h-3 text-cyan-500" />}
                                    </div>
                                    <div className="flex items-end justify-between mt-2">
                                        <div className="flex flex-col items-end">
                                            <ConfidenceScore
                                                value={h.win_rate}
                                                n={h.games_played}
                                                className="scale-90 origin-right"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default DossierHub;

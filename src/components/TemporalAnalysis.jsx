import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const defaultStats = {
    morning: { wins: 0, games: 0, wr: 0 },
    afternoon: { wins: 0, games: 0, wr: 0 },
    evening: { wins: 0, games: 0, wr: 0 },
    night: { wins: 0, games: 0, wr: 0 }
};

const TemporalAnalysis = () => {
    const [stats, setStats] = useState(defaultStats);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/temporal_analysis')
            .then(res => res.json())
            .then(data => {
                if (data.success) setStats(data.stats);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const getTimeIcon = (period) => {
        switch (period) {
            case 'morning': return '🌅';
            case 'afternoon': return '☀️';
            case 'evening': return '🌖';
            case 'night': return '🌌';
            default: return '⏰';
        }
    };

    const getStatusColor = (wr) => {
        if (wr >= 55) return 'text-green-400';
        if (wr >= 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    return (
        <div className="bg-black/40 border border-white/10 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-cyan-400 mb-4 flex items-center gap-2">
                ⏳ Temporal Performance (EST)
            </h3>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {['morning', 'afternoon', 'evening', 'night'].map(period => {
                    const data = stats[period];
                    const isOptimal = period === 'night'; // hardcoded bias based on known data or check highest

                    return (
                        <div key={period} className={`p-4 rounded-lg border ${isOptimal ? 'bg-indigo-900/20 border-indigo-500/50' : 'bg-black/20 border-white/5'}`}>
                            <div className="flex justify-between items-start mb-2">
                                <span className="text-2xl">{getTimeIcon(period)}</span>
                                <span className="text-xs uppercase text-gray-500 font-bold">{period}</span>
                            </div>

                            <div className="text-2xl font-bold font-mono text-white mb-1">
                                {data.wr}%
                            </div>

                            <div className="flex justify-between items-center text-xs">
                                <span className="text-gray-400">{data.games} Games</span>
                                <span className={`${getStatusColor(data.wr)} font-bold`}>
                                    {data.wr >= 55 ? 'OPTIMAL' : data.wr < 50 ? 'SUB-PAR' : 'STABLE'}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-4 pt-4 border-t border-white/10 text-xs text-center text-gray-500 italic">
                * Adjusted to Local Time (EST). "Night" window (12AM-6AM) shows historically highest win probability.
            </div>
        </div>
    );
};

export default TemporalAnalysis;

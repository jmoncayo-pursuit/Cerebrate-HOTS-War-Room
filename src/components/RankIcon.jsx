
import React, { useState } from 'react';
import { Shield } from 'lucide-react';

const RankIcon = ({ rank, className = "w-8 h-8", showLabel = false }) => {
    const [error, setError] = useState(false);

    // Normalize rank name for URL
    // e.g., "Silver 5" -> "silver", "Bronze 2" -> "bronze"
    const league = rank?.split(' ')[0]?.toLowerCase() || 'unranked';

    // Local assets are prioritized to ensure 100% uptime
    const sources = [
        `/images/ranks/${league}.png`
    ];

    const fallbackColors = {
        bronze: 'from-orange-700 to-orange-900 text-orange-400',
        silver: 'from-slate-400 to-slate-600 text-slate-200',
        gold: 'from-yellow-400 to-yellow-600 text-yellow-100',
        platinum: 'from-cyan-400 to-cyan-600 text-cyan-100',
        diamond: 'from-blue-400 to-blue-600 text-blue-100',
        master: 'from-purple-500 to-purple-700 text-purple-100',
        grandmaster: 'from-red-500 to-red-700 text-red-100',
        unranked: 'from-slate-700 to-slate-800 text-slate-500'
    };

    const colorClass = fallbackColors[league] || fallbackColors.unranked;

    if (error || !league || league === 'unranked') {
        return (
            <div className={`flex flex-col items-center gap-1 ${className}`}>
                <div className={`relative p-1.5 rounded-lg bg-gradient-to-br ${colorClass} border border-white/10 shadow-lg`}>
                    <Shield size={20} fill="currentColor" fillOpacity={0.2} />
                    {rank?.includes(' ') && (
                        <span className="absolute inset-0 flex items-center justify-center text-[10px] font-black text-white drop-shadow-md">
                            {rank.split(' ')[1]}
                        </span>
                    )}
                </div>
                {showLabel && <span className="text-[10px] font-bold uppercase tracking-tighter opacity-70">{rank}</span>}
            </div>
        );
    }

    return (
        <div className={`flex flex-col items-center gap-1 ${className}`}>
            <img
                src={sources[0]}
                alt={rank}
                className="w-full h-full object-contain filter drop-shadow-md"
                onError={() => setError(true)}
            />
            {showLabel && <span className="text-[10px] font-bold uppercase tracking-tighter opacity-70">{rank}</span>}
        </div>
    );
};

export default RankIcon;

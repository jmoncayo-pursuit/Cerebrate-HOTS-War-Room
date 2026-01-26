
import React from 'react';
import { Shield, Award, Trophy, Star, Crown, Diamond, Zap } from 'lucide-react';

const RankIcon = ({ rank, size = "md", showLabel = false, className = "" }) => {
    // Normalize rank name
    const rankParts = rank?.split(' ') || ['Unranked'];
    const league = rankParts[0]?.toLowerCase() || 'unranked';
    const tier = rankParts[1] || '';

    const sizes = {
        xs: { container: 'p-1 rounded-md', icon: 12, tier: 'text-[7px] -bottom-0.5 -right-0.5 px-0.5', tierMinW: 'min-w-[10px]' },
        sm: { container: 'p-1.5 rounded-lg', icon: 16, tier: 'text-[8px] -bottom-1 -right-1 px-1', tierMinW: 'min-w-[12px]' },
        md: { container: 'p-2 rounded-xl', icon: 24, tier: 'text-[9px] -bottom-1 -right-1 px-1', tierMinW: 'min-w-[14px]' },
        lg: { container: 'p-3 rounded-2xl', icon: 32, tier: 'text-[11px] -bottom-1.5 -right-1.5 px-1.5', tierMinW: 'min-w-[18px]' }
    };

    const s = sizes[size] || sizes.md;

    const rankConfigs = {
        bronze: {
            icon: Shield,
            color: 'from-orange-700/80 via-orange-600 to-orange-900',
            glow: 'shadow-[0_0_15px_rgba(194,65,12,0.4)]',
            text: 'text-orange-200',
            border: 'border-orange-500/30'
        },
        silver: {
            icon: Shield,
            color: 'from-slate-400 via-slate-300 to-slate-500',
            glow: 'shadow-[0_0_15px_rgba(148,163,184,0.4)]',
            text: 'text-slate-100',
            border: 'border-slate-400/30'
        },
        gold: {
            icon: Shield,
            color: 'from-yellow-500 via-amber-400 to-yellow-700',
            glow: 'shadow-[0_0_15px_rgba(245,158,11,0.4)]',
            text: 'text-yellow-50',
            border: 'border-yellow-400/30'
        },
        platinum: {
            icon: Award,
            color: 'from-cyan-500 via-teal-400 to-cyan-700',
            glow: 'shadow-[0_0_15px_rgba(6,182,212,0.4)]',
            text: 'text-cyan-50',
            border: 'border-cyan-400/30'
        },
        diamond: {
            icon: Diamond,
            color: 'from-blue-500 via-indigo-400 to-blue-700',
            glow: 'shadow-[0_0_15px_rgba(59,130,246,0.5)]',
            text: 'text-blue-50',
            border: 'border-blue-400/30'
        },
        master: {
            icon: Trophy,
            color: 'from-purple-600 via-fuchsia-500 to-purple-900',
            glow: 'shadow-[0_0_20px_rgba(168,85,247,0.6)]',
            text: 'text-purple-50',
            border: 'border-purple-400/30'
        },
        grandmaster: {
            icon: Crown,
            color: 'from-red-600 via-rose-500 to-red-900',
            glow: 'shadow-[0_0_25px_rgba(239,68,68,0.7)]',
            text: 'text-red-50',
            border: 'border-red-500/30'
        },
        unranked: {
            icon: Zap,
            color: 'from-slate-700 via-slate-800 to-slate-900',
            glow: 'shadow-none',
            text: 'text-slate-500',
            border: 'border-slate-700/50'
        }
    };

    const config = rankConfigs[league] || rankConfigs.unranked;
    const IconComponent = config.icon;

    return (
        <div className={`flex flex-col items-center gap-1.5 shrink-0 ${className}`}>
            <div className={`
                relative ${s.container} bg-gradient-to-br ${config.color} 
                border ${config.border} ${size !== 'xs' ? config.glow : ''}
                transition-transform hover:scale-110 duration-300
            `}>
                <IconComponent
                    size={s.icon}
                    className={`${config.text} drop-shadow-[0_0_3px_rgba(255,255,255,0.3)]`}
                    strokeWidth={size === 'xs' ? 3 : 2.5}
                />

                {tier && (
                    <div className={`absolute ${s.tier} bg-slate-950/90 border border-white/10 rounded-md py-0.5 ${s.tierMinW} flex items-center justify-center shadow-lg z-10`}>
                        <span className={`font-black text-white leading-none tracking-tighter`}>
                            {tier}
                        </span>
                    </div>
                )}
            </div>
            {showLabel && (
                <span className={`${size === 'sm' || size === 'xs' ? 'text-[8px]' : 'text-[10px]'} font-black uppercase tracking-widest text-slate-400 whitespace-nowrap`}>
                    {rank}
                </span>
            )}
        </div>
    );
};

export default RankIcon;

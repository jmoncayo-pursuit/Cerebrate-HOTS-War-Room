import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { normalizeHeroName } from '../utils/heroUtils';
import { Zap } from 'lucide-react';

const SOURCE_COLORS = {
    RECENT: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10',
    LIFETIME: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
    META: 'text-amber-400 border-amber-500/30 bg-amber-500/10'
};

const BuildDisplay = ({ hero, buildStr, stats, source = 'META', talentMap = {}, talentData = {}, heroData = {}, compact = false }) => {
    const [copied, setCopied] = useState(false);

    if (!buildStr || !hero) return null;

    const heroKey = normalizeHeroName(hero);
    const tiers = [1, 4, 7, 10, 13, 16, 20];

    let buildArray = [];
    let isNamedBuild = false;

    if (Array.isArray(buildStr)) {
        buildArray = buildStr;
    } else {
        const str = buildStr.toString();
        if (str.includes('-') && str.length > 10) {
            buildArray = str.split('-').slice(0, 7);
            isNamedBuild = true;
        } else {
            buildArray = str.replace(/[^0-9]/g, '').split('');
        }
    }

    const colorClass = SOURCE_COLORS[source] || SOURCE_COLORS.META;

    const handleCopy = (e) => {
        e.stopPropagation();
        let codeStr = '';

        if (isNamedBuild) {
            try {
                const hData = heroData[heroKey];
                if (hData && hData.talents) {
                    const indices = buildArray.map((tName, i) => {
                        const tier = tiers[i];
                        const tierTalents = hData.talents[tier] || [];
                        const normalizedTarget = tName.toLowerCase().replace(/[^a-z0-9]/g, '');
                        if (tName.includes('Talent Index')) return '?';
                        const match = tierTalents.find(t => {
                            const nName = t.tooltipId?.toLowerCase().replace(/[^a-z0-9]/g, '') || '';
                            const nText = t.name?.toLowerCase().replace(/[^a-z0-9]/g, '') || '';
                            return nName.includes(normalizedTarget) || normalizedTarget.includes(nName) || nText === normalizedTarget || normalizedTarget.includes(nText);
                        });
                        return match ? match.sort : '?';
                    });
                    codeStr = indices.join('').replace(/\?/g, '1');
                } else {
                    codeStr = '0000000';
                }
            } catch (err) {
                codeStr = '0000000';
            }
        } else {
            codeStr = buildArray.join('');
        }

        const code = `[T${codeStr},${hero}]`;
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="space-y-1.5 w-fit">
            {!compact && (
                <div className="flex justify-between items-center px-0.5 min-w-[150px]">
                    <div className={`text-[8px] font-black uppercase tracking-[0.15em] px-1.5 py-0.5 rounded border ${colorClass}`}>
                        {source} GUIDANCE {stats?.isComplete === false ? '(Partial)' : ''}
                    </div>
                    {stats && (
                        <span className="text-[9px] text-slate-500 font-mono">
                            {Number.isFinite(stats.wr) ? stats.wr.toFixed(1) : 0}% WR ({stats.games}{typeof stats.games === 'number' ? 'g' : ''})
                        </span>
                    )}
                </div>
            )}

            <div className="flex items-center gap-2 group/build bg-black/40 p-1.5 rounded border border-white/5 w-fit shadow-lg shadow-black/20">
                <div className="flex gap-1 flex-shrink-0">
                    {tiers.map((tier, i) => {
                        const item = buildArray[i];
                        if (item === undefined) return null;

                        let finalIcon = null;
                        const isMissing = item === '0' || item === 0 || item === '?';

                        if (!isMissing) {
                            if (isNamedBuild) {
                                const cleanItem = item.trim();
                                if (talentMap[cleanItem]) {
                                    finalIcon = talentMap[cleanItem];
                                } else {
                                    const potentialKey = Object.keys(talentMap).find(k => k.startsWith(cleanItem) || cleanItem.startsWith(k));
                                    if (potentialKey) finalIcon = talentMap[potentialKey];
                                }
                            } else {
                                const index = item.toString();
                                const iconKey = `${heroKey}-${tier}-${index}`;
                                finalIcon = talentMap[iconKey];
                                // Silently fall back to placeholder if icon is missing
                            }
                        }

                        // Lookup talent data for tooltip
                        const hData = talentData[hero] || talentData[heroKey] || {};
                        const TIER_MAPPING = { 1: '1', 4: '2', 7: '3', 10: '4', 13: '5', 16: '6', 20: '7' };
                        const tTier = hData[tier] || hData[tier.toString()] || hData[TIER_MAPPING[tier]] || {};
                        const detail = tTier[item] || null;

                        return (
                            <TalentIcon
                                key={tier}
                                index={item}
                                tier={tier}
                                selection={item}
                                icon={finalIcon}
                                detail={detail}
                                isMissing={isMissing}
                            />
                        );
                    })}
                </div>
                <button
                    onClick={handleCopy}
                    className={`text-[9px] px-2 py-1.5 rounded border transition-all cursor-pointer whitespace-nowrap flex-shrink-0 font-bold uppercase tracking-wider ${copied
                        ? 'text-green-400 border-green-500/30 bg-green-500/10 scale-95'
                        : 'text-cyan-400 opacity-60 group-hover/build:opacity-100 hover:text-cyan-300 border-cyan-500/20 hover:bg-cyan-500/10'
                        }`}
                >
                    {copied ? 'Copied' : 'Copy'}
                </button>
            </div>
        </div>
    );
};

function TalentIcon({ index, tier, selection, icon, detail, isMissing = false }) {
    const [isHovered, setIsHovered] = useState(false);
    const [imgError, setImgError] = useState(false);
    const iconRef = useRef(null);

    return (
        <div
            ref={iconRef}
            className={`w-[21px] h-[21px] rounded border flex items-center justify-center overflow-hidden flex-shrink-0 shadow-inner relative group/icon transition-all ${isMissing
                ? 'bg-slate-900/50 border-slate-800/50 opacity-40'
                : 'bg-slate-800 border-slate-700 hover:border-cyan-500/50'
                }`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {isMissing ? (
                <span className="text-[10px] font-bold text-slate-700">—</span>
            ) : (
                icon && !imgError ? (
                    <img
                        src={`/images/talents/${icon}`}
                        className="w-full h-full object-cover transition-transform group-hover/icon:scale-110"
                        alt={`T${tier}`}
                        onError={() => setImgError(true)}
                    />
                ) : (
                    <div className="flex items-center justify-center w-full h-full bg-slate-800 relative">
                        <Zap size={12} className="text-slate-600 opacity-50" />
                        <span className="absolute text-[8px] font-bold text-slate-500/50 bottom-0.5 right-0.5 leading-none">{selection}</span>
                    </div>
                )
            )}

            {isHovered && (
                <TooltipPortal
                    targetRef={iconRef}
                    tier={tier}
                    selection={selection}
                    detail={detail || (isMissing ? { name: "Talent Not Selected", description: "This talent tier was not reached in this game." } : null)}
                />
            )}
        </div>
    );
}

function TooltipPortal({ targetRef, tier, selection, detail }) {
    const [coords, setCoords] = useState(null);

    useEffect(() => {
        if (targetRef.current) {
            const rect = targetRef.current.getBoundingClientRect();
            const scrollY = window.scrollY;
            const tooltipWidth = 320;

            let top = rect.bottom + 8 + scrollY;
            let left = rect.left + rect.width / 2;
            let isTop = false;

            // Vertical Flip if too close to bottom
            if (rect.bottom + 150 > window.innerHeight) {
                top = rect.top - 8 + scrollY;
                isTop = true;
            }

            // Horizontal Clamping
            const halfWidth = tooltipWidth / 2;
            const padding = 10; // min distance from edge

            if (left - halfWidth < padding) {
                left = halfWidth + padding;
            } else if (left + halfWidth > window.innerWidth - padding) {
                left = window.innerWidth - padding - halfWidth;
            }

            setCoords({ top, left, isTop });
        }
    }, [targetRef]);

    if (!coords) return null;

    return createPortal(
        <div
            className="fixed z-[9999] pointer-events-none"
            style={{
                top: coords.top,
                left: coords.left,
                transform: `translateX(-50%) ${coords.isTop ? 'translateY(-100%)' : ''}`
            }}
        >
            <div className="bg-slate-900/95 backdrop-blur-md border border-slate-700 p-3 rounded-lg shadow-2xl max-w-[320px] animate-fadeIn">
                <div className="flex justify-between items-start gap-4 mb-2">
                    <div>
                        <div className="text-[10px] font-black text-cyan-500 uppercase tracking-widest mb-0.5">Level {tier} Talent</div>
                        <h4 className="text-sm font-bold text-white leading-tight">
                            {detail?.name || `Talent Option ${selection}`}
                        </h4>
                    </div>
                </div>
                {detail?.description && (
                    <p className="text-xs text-slate-400 leading-relaxed italic">
                        "{detail.description}"
                    </p>
                )}
                {!detail && !selection.toString().includes('Selected') && (
                    <p className="text-[10px] text-slate-500 mt-2">
                        Detailed intelligence for this asset is currently being indexed.
                    </p>
                )}
            </div>
        </div>,
        document.body
    );
}

export default BuildDisplay;

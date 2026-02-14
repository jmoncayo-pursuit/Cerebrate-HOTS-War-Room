import React from 'react';

/**
 * Honest UI ConfidenceScore Wrapper
 * Standards:
 * 1. Data Transparency: Always pairs win-rate with games played (n).
 * 2. Statistical Significance: n < 3 is 'Volatile'.
 * 3. Neural Fog: Volatile states apply pulse, low opacity, and specific labeling.
 */
const ConfidenceScore = ({ value, n, label, className = "" }) => {
    const isVolatile = n < 3;
    const isNValid = typeof n === 'number' && !isNaN(n);
    const displayN = isNValid ? n : '0';

    // Base styles
    const baseStyles = "inline-flex items-center gap-2 transition-all duration-300";
    const volatileStyles = isVolatile ? "animate-pulse opacity-60 cursor-help" : "";

    return (
        <div
            className={`${baseStyles} ${volatileStyles} ${className}`}
            data-confidence={isVolatile ? "volatile" : "stable"}
            title={isVolatile ? "INSUFFICIENT MISSION DATA" : "Statistical Confidence: Verified"}
        >
            <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                    <span className={`text-2xl font-black ${isVolatile ? 'text-slate-400 font-mono italic' : 'text-white'}`}>
                        {value}%
                    </span>
                    {label && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</span>}
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-tighter">
                        Sample Size: <span className={isVolatile ? 'text-amber-500' : 'text-cyan-500'}>n={displayN}</span>
                    </span>
                    {isVolatile && (
                        <span className="text-[9px] font-black text-amber-500/80 bg-amber-500/5 px-1.5 rounded border border-amber-500/20 uppercase tracking-widest">
                            Neural Fog
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ConfidenceScore;

import React, { useState, useEffect } from 'react';
import { normalizeHeroName } from '../utils/heroUtils';

// Global cache for hero data to avoid multiple fetches and layout jumps
let globalHeroData = null;
let globalHeroDataPromise = null;

export default function HeroText({ text, className = '', iconSize = 'w-5 h-5', compact = false, heroData: propHeroData }) {
    const [heroData, setHeroData] = useState(propHeroData || globalHeroData);

    useEffect(() => {
        if (propHeroData) {
            setHeroData(propHeroData);
            return;
        }

        if (globalHeroData) {
            setHeroData(globalHeroData);
            return;
        }

        if (!globalHeroDataPromise) {
            globalHeroDataPromise = fetch('/api/data/hero_data.json')
                .then(res => res.json())
                .then(data => {
                    globalHeroData = data;
                    return data;
                })
                .catch(err => {
                    console.error("HeroText failed to load hero data:", err);
                    globalHeroDataPromise = null;
                    throw err;
                });
        }

        globalHeroDataPromise.then(data => setHeroData(data));
    }, [propHeroData]);

    if (!text) return null;
    if (!heroData) return <span className={className}>{text}</span>;

    // Create a list of { key, name } objects for matching
    // We match against the display name (e.g. "Li Li"), but load image using the key/shortname (e.g. "lili")
    const heroes = Object.entries(heroData)
        .map(([key, data]) => ({ key, name: data?.name }))
        .filter(h => h.name)
        .sort((a, b) => b.name.length - a.name.length);

    let parts = [text];
    let heroMatchCounter = 0;

    heroes.forEach(({ key, name }) => {
        if (!name) return;

        let newParts = [];

        parts.forEach((part, partIndex) => {
            if (typeof part !== 'string') {
                newParts.push(part);
                return;
            }

            const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            let pattern;
            if (name.endsWith('.')) {
                pattern = `\\b(${escapedName})('s)?`; // No trailing \b for dots
            } else {
                pattern = `\\b(${escapedName})('s)?\\b`;
            }

            const regex = new RegExp(pattern, 'gi');
            const split = part.split(regex);

            // split results in [non-match, hero, 's, non-match, hero, 's, ...]
            for (let i = 0; i < split.length; i += 3) {
                // The non-matching part
                if (split[i]) newParts.push(split[i]);

                // If we have a hero match at this position
                if (i + 1 < split.length && split[i + 1]) {
                    const heroMatch = split[i + 1];
                    const possessiveMatch = split[i + 2] || '';
                    const uniqueKey = `${key}-${partIndex}-${i}-${heroMatchCounter++}`;

                    newParts.push(
                        <span
                            key={uniqueKey}
                            className={`inline-flex items-center gap-1 ${compact ? 'px-1 py-0' : 'px-2 py-0.5'} bg-slate-800/80 rounded border border-slate-700/50 mx-0.5 my-0.5 align-middle shadow-sm break-inside-avoid min-h-[24px]`}
                        >
                            <img
                                src={`/images/heroes/${normalizeHeroName(name)}.png`}
                                alt={name}
                                width="20"
                                height="20"
                                className={`${iconSize} rounded shadow-inner border border-white/5 flex-shrink-0 object-cover`}
                                loading="eager"
                                decoding="async"
                                onError={(e) => {
                                    e.target.onerror = null; // Prevent infinite loop
                                    e.target.src = '/images/heroes/unknown.png';
                                }}
                            />
                            <span className={`font-bold text-cyan-300 ${compact ? 'text-[10px]' : 'text-[11px]'} leading-none tracking-tight whitespace-nowrap`}>
                                {heroMatch}{possessiveMatch}
                            </span>
                        </span>
                    );
                }
            }
        });
        parts = newParts;
    });

    return <span className={className}>{parts}</span>;
}

/**
 * Utility function to process text and return React elements with hero icons
 * Useful for markdown rendering where we need to process the text first
 */
export function processHeroIcons(text, heroData) {
    if (!text || !heroData) return [text];

    // Create a list of { key, name } objects
    const heroes = Object.entries(heroData)
        .map(([key, data]) => ({ key, name: data?.name }))
        .filter(h => h.name)
        .sort((a, b) => b.name.length - a.name.length);

    let parts = [text];

    heroes.forEach(({ key, name }) => {
        if (!name) return;

        let newParts = [];
        parts.forEach(part => {
            if (typeof part !== 'string') {
                newParts.push(part);
                return;
            }

            // Match Name
            const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            let pattern;
            if (name.endsWith('.')) {
                pattern = `\\b(${escapedName})`;
            } else {
                pattern = `\\b(${escapedName})\\b`;
            }

            const regex = new RegExp(pattern, 'gi');
            const split = part.split(regex);

            split.forEach((sub, i) => {
                if (sub && sub.toLowerCase() === name.toLowerCase()) {
                    newParts.push(
                        <span
                            key={`${key}-${i}`}
                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800/80 rounded border border-slate-700/50 mx-0.5 align-middle shadow-sm min-h-[24px]"
                        >
                            <img
                                src={`/images/heroes/${normalizeHeroName(name)}.png`}
                                alt={name}
                                width="20"
                                height="20"
                                className="w-5 h-5 rounded shadow-inner border border-white/5 object-cover"
                                onError={(e) => {
                                    e.target.onerror = null;
                                    e.target.src = '/images/heroes/unknown.png';
                                }}
                            />
                            <span className="font-bold text-cyan-300 text-[11px] leading-none tracking-tight">{sub}</span>
                        </span>
                    );
                } else if (sub) {
                    newParts.push(sub);
                }
            });
        });
        parts = newParts;
    });

    return parts;
}

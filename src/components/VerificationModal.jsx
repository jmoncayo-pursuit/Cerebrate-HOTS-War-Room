import { useState, useEffect } from 'react';
import './VerificationModal.css';

export default function VerificationModal({ isOpen, onClose, onSuccess }) {
    const [screenshots, setScreenshots] = useState([]); // Array of files
    const [currentScreenshotIndex, setCurrentScreenshotIndex] = useState(0);
    const [extractionProgress, setExtractionProgress] = useState(0);
    const [extractionPhase, setExtractionPhase] = useState('');
    const [screenshotPreview, setScreenshotPreview] = useState(null);

    // Bucket State: Separates Lifetime and Season data
    const [statType, setStatType] = useState('season'); // Active view
    const [buckets, setBuckets] = useState({
        lifetime: { stats: { total_games: '', wins: '', losses: '', player_level: '', rank: '', roles: null, takedowns: '', mvp_awards: '', kda: '', avg_takedowns: '' }, heroes: [], maps: [] },
        season: { stats: { total_games: '', wins: '', losses: '', player_level: '', rank: '', roles: null, takedowns: '', mvp_awards: '', kda: '', avg_takedowns: '' }, heroes: [], maps: [] }
    });

    const [isExtracting, setIsExtracting] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState('');
    const [detectedHeroes, setDetectedHeroes] = useState([]);
    const [syncSuccess, setSyncSuccess] = useState(false);
    const HERO_ALIASES = {
        "Crusader": "Johanna", "FaerieDragon": "Brightwing", "DemonHunter": "Valla",
        "Monk": "Kharazim", "Medic": "Lt. Morales", "Firebat": "Blaze",
        "Amazon": "Cassia", "Necromancer": "Xul", "WitchDoctor": "Nazeebo",
        "Barbarian": "Sonya", "Wizard": "Li-Ming", "L90ETC": "E.T.C.",
        "Tinker": "Gazlowe", "Dryad": "Lunara", "Dreadlord": "Mal'Ganis", "LiLi": "Li Li"
    };

    const INITIAL_BUCKETS = {
        lifetime: { stats: { total_games: '', wins: '', losses: '', player_level: '', rank: '', roles: null, takedowns: '', mvp_awards: '', kda: '', avg_takedowns: '' }, heroes: [], maps: [] },
        season: { stats: { total_games: '', wins: '', losses: '', player_level: '', rank: '', roles: null, takedowns: '', mvp_awards: '', kda: '', avg_takedowns: '' }, heroes: [], maps: [] }
    };

    useEffect(() => {
        if (isOpen) {
            loadCurrentVerifiedStats();
        }
    }, [isOpen]);

    const loadCurrentVerifiedStats = async () => {
        try {
            const res = await fetch('/api/player_profile');
            const profile = await res.json();
            const sl = profile.rank_data?.storm_league || {};

            // Load Heroes
            const hs = profile.hero_stats || {};
            const heroListLifetime = Object.entries(hs).map(([name, data]) => ({
                hero: name,
                games: data.verified_lifetime?.games || data.verified?.games || '',
                wr: data.verified_lifetime?.wr || data.verified?.wr || '',
                level: data.verified_lifetime?.level || data.verified?.level || ''
            })).filter(h => h.games || h.wr);

            const heroListSeason = Object.entries(hs).map(([name, data]) => ({
                hero: name,
                games: data.verified_season_2025_3?.games || '',
                wr: data.verified_season_2025_3?.wr || '',
                level: data.verified_season_2025_3?.level || ''
            })).filter(h => h.games || h.wr);

            // Load Maps
            const ms = profile.map_records_verified || {};
            const mapList = Object.entries(ms).map(([name, data]) => ({
                map: name,
                wins: data.wins,
                losses: data.losses,
                wr: data.win_rate
            }));

            setBuckets(prev => ({
                ...prev,
                lifetime: {
                    ...prev.lifetime,
                    stats: {
                        ...prev.lifetime.stats,
                        total_games: sl.verified_lifetime?.total_games || '',
                        wins: sl.verified_lifetime?.wins || '',
                        losses: sl.verified_lifetime?.losses || '',
                        win_rate: sl.verified_lifetime?.win_rate || ''
                    },
                    heroes: heroListLifetime,
                    maps: mapList
                },
                season: {
                    ...prev.season,
                    stats: {
                        ...prev.season.stats,
                        total_games: sl.verified_season_2025_3?.total_games || '',
                        wins: sl.verified_season_2025_3?.wins || '',
                        losses: sl.verified_season_2025_3?.losses || '',
                        win_rate: sl.verified_season_2025_3?.win_rate || ''
                    },
                    heroes: heroListSeason,
                    maps: mapList
                }
            }));
        } catch (err) {
            console.error('Failed to pre-load verified stats:', err);
        }
    };

    const resetMatrix = () => {
        setBuckets(JSON.parse(JSON.stringify(INITIAL_BUCKETS)));
        loadCurrentVerifiedStats();
        setScreenshots([]);
        setScreenshotPreview(null);
        setCurrentScreenshotIndex(0);
        setDetectedHeroes([]);
        setError('');
        setExtractionPhase('');
        setExtractionProgress(0);
    };

    if (!isOpen) return null;

    // Helper to get active bucket
    const getActiveBucket = () => buckets[statType];

    const handleFileUpload = (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            setScreenshots(files);
            setCurrentScreenshotIndex(0);

            const reader = new FileReader();
            reader.onloadend = () => {
                setScreenshotPreview(reader.result);
            };
            reader.readAsDataURL(files[0]);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (files.length > 0) {
            setScreenshots(files);
            setCurrentScreenshotIndex(0);

            const reader = new FileReader();
            reader.onloadend = () => {
                setScreenshotPreview(reader.result);
            };
            reader.readAsDataURL(files[0]);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const autoExtractStats = async () => {
        if (screenshots.length === 0) {
            setError('Please upload at least one screenshot first');
            return;
        }

        setIsExtracting(true);
        setError('');

        const simulateProgress = (start, end, duration, phase) => {
            setExtractionPhase(phase);
            return new Promise(resolve => {
                const startTime = Date.now();
                const interval = setInterval(() => {
                    const elapsed = Date.now() - startTime;
                    const pct = Math.min(1, elapsed / duration);
                    setExtractionProgress(start + (end - start) * pct);
                    if (pct === 1) {
                        clearInterval(interval);
                        resolve();
                    }
                }, 50);
            });
        };

        try {
            for (let i = 0; i < screenshots.length; i++) {
                setCurrentScreenshotIndex(i);
                const currentFile = screenshots[i];

                if (i > 0) {
                    const reader = new FileReader();
                    reader.onloadend = () => setScreenshotPreview(reader.result);
                    reader.readAsDataURL(currentFile);
                }

                await simulateProgress(0, 20, 800, "📡 SIGNAL ACQUISITION");
                setExtractionPhase("🌐 CEREBRATE UPLINK");
                setExtractionProgress(30);

                const getBase64 = (file) => {
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = (error) => reject(error);
                        reader.readAsDataURL(file);
                    });
                };

                const base64Image = await getBase64(currentFile);
                setExtractionPhase("🧠 NEURAL PATTERN RECOGNITION");
                const progressInterval = setInterval(() => {
                    setExtractionProgress(prev => (prev < 85 ? prev + 0.5 : prev));
                }, 200);

                const response = await fetch('/api/extract_stats_from_screenshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: base64Image })
                });

                clearInterval(progressInterval);

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to extract stats');
                }

                const data = await response.json();

                if (data.success) {
                    setExtractionPhase("🔳 DATA MATRIX RECONSTRUCTION");
                    setExtractionProgress(90);
                    await new Promise(r => setTimeout(r, 600));

                    const s = data.stats;
                    const typeFound = s.stat_type || 'season';
                    const screenType = s.screen_type || 'profile_page';

                    const normalizeHero = (name) => {
                        if (!name) return null;
                        const trimmed = name.trim();
                        if (!trimmed) return null;

                        // Check for exact alias first
                        if (HERO_ALIASES[trimmed]) return HERO_ALIASES[trimmed];

                        // Common misparsings
                        const misparsings = {
                            "Jalna": "Jaina",
                            "Jaina Proudmoore": "Jaina",
                            "The Butcher": "The Butcher",
                            "Butcher": "The Butcher",
                            "Medic": "Lt. Morales",
                            "Faerie Dragon": "Brightwing",
                            "Demon Hunter": "Valla",
                            "Dryad": "Lunara",
                            "Dreadlord": "Mal'Ganis"
                        };
                        if (misparsings[trimmed]) return misparsings[trimmed];

                        // Try Title Case
                        const titleCase = trimmed.charAt(0).toUpperCase() + trimmed.slice(1).toLowerCase();
                        if (HERO_ALIASES[titleCase]) return HERO_ALIASES[titleCase];
                        if (misparsings[titleCase]) return misparsings[titleCase];

                        if (titleCase === "Jalna") return "Jaina";

                        return titleCase;
                    };

                    const rawHeroes = s.heroes || s.hero_stats || [];
                    const allFound = [...new Set([
                        ...(s.viewed_hero ? [s.viewed_hero] : []),
                        ...rawHeroes.map(h => h.hero)
                    ].map(normalizeHero).filter(Boolean))];

                    if (allFound.length > 0) {
                        // Self-healing dedup: Normalize PREV state as well to catch legacy 'Jalna's
                        setDetectedHeroes(prev => {
                            const combined = [...prev, ...allFound];
                            const reNormalized = combined.map(normalizeHero).filter(Boolean);
                            return [...new Set(reNormalized)];
                        });

                        const heroLabel = allFound.length > 1 ? `${allFound.length} HEROES` : allFound[0].toUpperCase();
                        setExtractionPhase(`🔳 SYNCHRONIZING ${heroLabel} TELEMETRY`);
                    } else {
                        setExtractionPhase("🔳 DATA MATRIX RECONSTRUCTION");
                    }

                    let heroName = normalizeHero(s.viewed_hero);
                    if (!heroName && rawHeroes.length > 0) {
                        heroName = normalizeHero(rawHeroes[0].hero);
                    }

                    setExtractionProgress(95);
                    await new Promise(r => setTimeout(r, 600));

                    // Normalize Core Totals (with Backwards Extrapolation)
                    let tg = s.total_games || s.totalGames || '';
                    let w = s.wins || s.Wins || '';
                    let l = s.losses || s.Losses || '';
                    let wr = s.win_rate || s.winRate || s.WinRate || '';

                    const tgNum = parseInt(tg) || 0;
                    const wNum = parseInt(w) || 0;
                    const lNum = parseInt(l) || 0;
                    const wrNum = parseFloat(wr) || 0;

                    // If we have Total and Win Rate but no Wins/Losses (Common in Hero views)
                    if (tgNum > 0 && wrNum > 0 && !w && !l) {
                        w = Math.round((wrNum / 100) * tgNum);
                        l = tgNum - w;
                    }
                    // If we have Total and Wins but no Losses
                    else if (tgNum > 0 && wNum >= 0 && !l) {
                        l = tgNum - wNum;
                    }
                    // If everything is present but inconsistent, trust Total and Wins
                    else if (tgNum > 0 && wNum >= 0 && lNum >= 0 && (wNum + lNum !== tgNum)) {
                        l = tgNum - wNum;
                    }

                    setBuckets(prev => {
                        const b = prev[typeFound];

                        // 1. Update Core Stats (Protect Account Totals during Hero Views)
                        const newStats = {
                            ...b.stats,
                            total_games: (!s.is_hero_view && tg) ? tg : b.stats.total_games,
                            wins: (!s.is_hero_view && w) ? w : b.stats.wins,
                            losses: (!s.is_hero_view && l) ? l : b.stats.losses,
                            win_rate: (!s.is_hero_view && wr) ? wr : b.stats.win_rate,
                            player_level: s.player_level || b.stats.player_level,
                            rank: s.rank || b.stats.rank,
                            roles: s.roles || b.stats.roles,
                            takedowns: s.takedowns || b.stats.takedowns,
                            mvp_awards: s.mvp_awards || b.stats.mvp_awards,
                            kda: s.kda_ratio || s.kda || b.stats.kda,
                            avg_takedowns: s.avg_takedowns || b.stats.avg_takedowns
                        };

                        // 2. Merge Maps
                        const newMaps = s.maps ? [...(b.maps || []), ...s.maps].reduce((acc, curr) => {
                            const existing = acc.find(m => m.map === curr.map);
                            if (existing) { Object.assign(existing, curr); return acc; }
                            acc.push(curr); return acc;
                        }, []) : (b.maps || []);

                        // 3. Merge Heroes & Extrapolate
                        let incomingHeroes = s.heroes || s.hero_stats || [];

                        // If it's a hero view, ensure hero object exists or update it
                        if (s.is_hero_view && heroName) {
                            // Priority: if s.total_games is 0/null, check if s.heroes has a better count for this hero
                            let heroEntry = (s.heroes || []).find(h => h.hero?.toLowerCase() === heroName.toLowerCase());
                            const effectiveGames = (parseInt(s.total_games) || parseInt(s.games_played) || (heroEntry ? parseInt(heroEntry.games) : 0));
                            const effectiveWR = (parseFloat(s.win_rate) || (heroEntry ? parseFloat(heroEntry.wr) : 0));

                            const heroStats = {
                                hero: heroName,
                                games: effectiveGames || '',
                                wins: s.wins || (heroEntry ? heroEntry.wins : ''),
                                wr: effectiveWR || '',
                                level: s.hero_level || (heroEntry ? heroEntry.level : '')
                            };

                            const existingIdx = incomingHeroes.findIndex(h => h.hero?.toLowerCase() === heroName.toLowerCase());
                            if (existingIdx >= 0) {
                                incomingHeroes[existingIdx] = { ...incomingHeroes[existingIdx], ...heroStats };
                            } else {
                                incomingHeroes.push(heroStats);
                            }
                        }

                        const newHeroes = [...(b.heroes || [])];
                        incomingHeroes.forEach(rawHero => {
                            const name = normalizeHero(rawHero.hero);
                            if (!name) return;

                            // Sanitize incoming data (Ignore header titles captured as data)
                            const rawG = String(rawHero.games || '');
                            const rawW = String(rawHero.wins || '');
                            const rawWR = String(rawHero.wr || '');

                            const g_val = (rawG.toLowerCase().includes('game') || isNaN(parseInt(rawG))) ? 0 : parseInt(rawG);
                            const w_val = (rawW.toLowerCase().includes('win') || isNaN(parseInt(rawW))) ? 0 : parseInt(rawW);
                            const wr_val = (rawWR.toLowerCase().includes('wr') || isNaN(parseFloat(rawWR))) ? 0 : parseFloat(rawWR);

                            const newHero = {
                                hero: name,
                                games: g_val || '',
                                wins: w_val || '',
                                wr: wr_val || '',
                                level: rawHero.level || ''
                            };

                            const existingIdx = newHeroes.findIndex(h => h.hero?.toLowerCase() === name.toLowerCase());
                            let combined = existingIdx >= 0 ? { ...newHeroes[existingIdx], ...newHero } : { ...newHero };

                            // Extrapolation Math (Ensure we use sanitized values)
                            let final_g = parseFloat(combined.games) || 0;
                            let final_w = parseFloat(combined.wins) || 0;
                            let final_wr = parseFloat(combined.wr) || 0;

                            if (final_g > 0 && final_wr > 0 && !final_w) combined.wins = Math.round((final_wr / 100) * final_g);
                            else if (final_g > 0 && final_w > 0 && (!final_wr)) combined.wr = parseFloat(((final_w / final_g) * 100).toFixed(1));
                            else if (final_w > 0 && final_wr > 0 && !final_g) combined.games = Math.round((final_w * 100) / final_wr);

                            if (existingIdx >= 0) newHeroes[existingIdx] = combined;
                            else newHeroes.push(combined);
                        });

                        return {
                            ...prev,
                            [typeFound]: { stats: newStats, heroes: newHeroes, maps: newMaps }
                        };
                    });

                    setStatType(typeFound);
                    const label = (screenType === 'heroes_profile' || screenType === 'talent_builds')
                        ? `🎯 EXTERNAL INTELLIGENCE (${screenType.replace('_', ' ').toUpperCase()})`
                        : (heroName ? `🎯 ${heroName.toUpperCase()} SYNCHRONIZED` : "🎯 PROFILES SYNCHRONIZED");

                    setExtractionPhase(label);
                    setExtractionProgress(100);
                    await new Promise(r => setTimeout(r, 500));
                }
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsExtracting(false);
            setExtractionProgress(0);
        }
    };

    const calculateWinRate = () => {
        const b = getActiveBucket();
        const total = parseInt(b.stats.total_games) || 0;
        const wins = parseInt(b.stats.wins) || 0;
        if (total === 0) return 0;
        return ((wins / total) * 100).toFixed(1);
    };

    const handleSave = async () => {
        try {
            setIsSaving(true);
            setError('');
            setIsExtracting(true);
            setExtractionProgress(10);
            setExtractionPhase("🔳 NEURAL LINK HANDSHAKE");

            const types = ['lifetime', 'season'];
            for (let i = 0; i < types.length; i++) {
                const type = types[i];
                const b = buckets[type];

                // Update progress per bucket type
                setExtractionProgress(20 + (i * 30));
                setExtractionPhase(`🔳 SYNCING ${type.toUpperCase()} DATA`);
                await new Promise(r => setTimeout(r, 600));

                const hasGames = parseInt(b.stats.total_games) > 0;
                const hasHeroes = b.heroes.length > 0;
                const hasMaps = b.maps.length > 0;

                if (!hasGames && !hasHeroes && !hasMaps) continue;

                // Simple validation for the bucket (Strict Parity Check)
                const tg = parseInt(b.stats.total_games) || 0;
                const w = parseInt(b.stats.wins) || 0;
                const l = parseInt(b.stats.losses) || 0;

                // Allow save if no data, but if there is data, it must be consistent
                if (tg > 0 && (w + l !== tg)) {
                    throw new Error(`${type === 'lifetime' ? 'Lifetime' : 'Season'} stats are logically inconsistent: Total(${tg}) ≠ Wins(${w}) + Losses(${l}). Please manually adjust the counts.`);
                }

                const response = await fetch('/api/verify_stats', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stats: {
                            ...b.stats,
                            total_games: tg,
                            wins: w,
                            losses: l,
                            win_rate: tg > 0 ? parseFloat(((w / tg) * 100).toFixed(1)) : (parseFloat(b.stats.win_rate) || 0),
                            maps: b.maps
                        },
                        stat_type: type,
                        hero_stats: b.heroes
                    })
                });

                if (!response.ok) throw new Error(`Failed to save ${type} data`);
            }

            setExtractionProgress(100);
            setExtractionPhase("🔳 AUDIT SYNCHRONIZATION FINALIZED");
            setSyncSuccess(true);
            await new Promise(r => setTimeout(r, 1500));

            setSyncSuccess(false);

            // Clear state after successful save
            resetMatrix();
            onSuccess();
            onClose();
        } catch (err) {
            setError(err.message);
            setIsSaving(false);
            setIsExtracting(false);
        } finally {
            setIsSaving(false);
            setIsExtracting(false);
        }
    };

    const updateActiveStat = (field, value) => {
        setBuckets(prev => ({
            ...prev,
            [statType]: {
                ...prev[statType],
                stats: { ...prev[statType].stats, [field]: value }
            }
        }));
    };

    const addHeroStat = () => {
        setBuckets(prev => ({
            ...prev,
            [statType]: {
                ...prev[statType],
                heroes: [...prev[statType].heroes, { hero: '', games: '', wr: '' }]
            }
        }));
    };

    const updateHeroStat = (index, field, value) => {
        setBuckets(prev => {
            const newHeroes = [...prev[statType].heroes];
            newHeroes[index] = { ...newHeroes[index], [field]: value };
            return {
                ...prev,
                [statType]: { ...prev[statType], heroes: newHeroes }
            };
        });
    };

    const removeHeroStat = (index) => {
        setBuckets(prev => ({
            ...prev,
            [statType]: {
                ...prev[statType],
                heroes: prev[statType].heroes.filter((_, i) => i !== index)
            }
        }));
    };

    const currentStats = getActiveBucket().stats;
    const currentHeroes = getActiveBucket().heroes;
    const currentMaps = getActiveBucket().maps;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="verification-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>📸 Verify Blizzard Stats</h2>
                    {syncSuccess && <div className="sync-success-toast">📡 NEURAL LINK SYNCHRONIZED</div>}
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="modal-body">
                    <div className="modal-content-wrapper">
                        {/* Left Panel: Visual Intelligence */}
                        <div className="left-panel">
                            <div className="upload-section">
                                <label>Visual Intelligence Feed</label>
                                <div
                                    className="upload-zone"
                                    onDrop={handleDrop}
                                    onDragOver={handleDragOver}
                                    onClick={() => document.getElementById('screenshot-input').click()}
                                >
                                    {screenshotPreview && (
                                        <div className={`preview-container ${isExtracting ? 'extracting' : ''}`}>
                                            <img src={screenshotPreview} alt="Screenshot preview" />
                                            {isExtracting && (
                                                <div className="extraction-overlay">
                                                    <div className="scan-line"></div>
                                                    <div className="lightning-grid">
                                                        {[...Array(8)].map((_, i) => (
                                                            <div key={i} className="lightning-spark"></div>
                                                        ))}
                                                    </div>
                                                    <div className="digital-glimmer"></div>
                                                    <div className="neural-shimmer"></div>

                                                    <div className="progress-hud">
                                                        <div className="phase-label">
                                                            {extractionPhase}
                                                            {screenshots.length > 1 && ` [BATCH: ${currentScreenshotIndex + 1}/${screenshots.length}]`}
                                                        </div>
                                                        <div className="progress-bar-container">
                                                            <div
                                                                className="progress-bar-fill"
                                                                style={{ width: `${extractionProgress}%` }}
                                                            ></div>
                                                        </div>
                                                        <div className="progress-pct">{Math.round(extractionProgress)}%</div>
                                                        {detectedHeroes.length > 0 && (
                                                            <div className="detected-signals">
                                                                <div className="signals-label">📡 SIGNALS IDENTIFIED:</div>
                                                                <div className="signals-list">
                                                                    {detectedHeroes.map((h, idx) => (
                                                                        <span key={idx} className="signal-tag">{h}</span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            <button
                                                className="extract-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    autoExtractStats();
                                                }}
                                                disabled={isExtracting}
                                            >
                                                {isExtracting ? '⚡ ENERGIZING...' : '🤖 Auto-Extract Batch'}
                                            </button>
                                            {!isExtracting && (
                                                <button
                                                    className="clear-matrix-secondary-btn"
                                                    onClick={(e) => { e.stopPropagation(); resetMatrix(); }}
                                                    title="Clear session and start fresh"
                                                >
                                                    🧹 Clear
                                                </button>
                                            )}
                                        </div>
                                    )}

                                    {!screenshotPreview && isExtracting && (
                                        <div className="extraction-overlay standalone">
                                            <div className="scan-line"></div>
                                            <div className="lightning-grid">
                                                {[...Array(8)].map((_, i) => (
                                                    <div key={i} className="lightning-spark"></div>
                                                ))}
                                            </div>
                                            <div className="digital-glimmer"></div>
                                            <div className="neural-shimmer"></div>

                                            <div className="progress-hud">
                                                <div className="phase-label">
                                                    {extractionPhase}
                                                </div>
                                                <div className="progress-bar-container">
                                                    <div
                                                        className="progress-bar-fill"
                                                        style={{ width: `${extractionProgress}%` }}
                                                    ></div>
                                                </div>
                                                <div className="progress-pct">{Math.round(extractionProgress)}%</div>
                                            </div>
                                        </div>
                                    )}

                                    {!screenshotPreview && !isExtracting && (
                                        <div className="upload-placeholder">
                                            <span className="upload-icon">📷</span>
                                            <p>Drag & Drop or Click to Upload</p>
                                            <p className="upload-hint">Upload Full Profile & Detailed Stats Mixed</p>
                                        </div>
                                    )}
                                </div>
                                <input
                                    id="screenshot-input"
                                    type="file"
                                    accept="image/*"
                                    multiple
                                    onChange={handleFileUpload}
                                    style={{ display: 'none' }}
                                />
                            </div>

                            {error && (
                                <div className="error-message">
                                    ⚠️ {error}
                                </div>
                            )}
                        </div>

                        {/* Right Panel: Tactical Matrix */}
                        <div className="right-panel">
                            {/* Extracted Context Tabs */}
                            <div className="stat-type-tabs">
                                <button
                                    className={`tab-btn ${statType === 'season' ? 'active' : ''}`}
                                    onClick={() => setStatType('season')}
                                >
                                    📊 SEASON {buckets.season.stats.total_games > 0 && `(READY)`}
                                </button>
                                <button
                                    className={`tab-btn ${statType === 'lifetime' ? 'active' : ''}`}
                                    onClick={() => setStatType('lifetime')}
                                >
                                    🏆 LIFETIME {buckets.lifetime.stats.total_games > 0 && `(READY)`}
                                </button>
                            </div>

                            {/* Stats Entry */}
                            <div className="stats-section">
                                <label>Core Stats ({statType.toUpperCase()}):</label>
                                <div className="stats-grid">
                                    <div className="stat-input">
                                        <label>Total Games</label>
                                        <input
                                            type="number"
                                            value={currentStats.total_games}
                                            onChange={(e) => updateActiveStat('total_games', e.target.value)}
                                            placeholder="0"
                                        />
                                    </div>
                                    <div className="stat-input">
                                        <label>Wins</label>
                                        <input
                                            type="number"
                                            value={currentStats.wins}
                                            onChange={(e) => updateActiveStat('wins', e.target.value)}
                                            placeholder="0"
                                        />
                                    </div>
                                    <div className="stat-input">
                                        <label>Losses</label>
                                        <input
                                            type="number"
                                            value={currentStats.losses}
                                            onChange={(e) => updateActiveStat('losses', e.target.value)}
                                            placeholder="0"
                                        />
                                    </div>
                                </div>
                                {currentStats.total_games && (
                                    <div className="calculated-wr">
                                        Calculated Win Rate: <strong>{calculateWinRate()}%</strong>
                                        {parseInt(currentStats.wins) + parseInt(currentStats.losses) === parseInt(currentStats.total_games) && (
                                            <span className="valid-check"> ✓</span>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Enriched Stats */}
                            {(currentStats.roles || currentStats.player_level || currentStats.rank || currentMaps.length > 0) && (
                                <div className="enriched-stats-section">
                                    <label>Context-Aware Intel ({statType}):</label>

                                    {currentMaps.length > 0 && (
                                        <div className="maps-verified-grid">
                                            <span className="roles-label">Verified Map Intelligence ({currentMaps.length} Detected):</span>
                                            <div className="maps-distribution expanded-grid">
                                                {currentMaps.map(m => (
                                                    <div key={m.map} className="map-stat-item">
                                                        <span className="map-name-sm" title={m.map}>
                                                            {m.map.split('(')[0].trim()}
                                                        </span>
                                                        <span className={`map-wr-sm ${m.wr >= 55 ? 'win' : m.wr < 40 ? 'loss' : ''}`}>
                                                            {m.wr}%
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="profile-badge-grid">
                                        {currentStats.player_level && (
                                            <div className="badge-item">
                                                <span className="badge-label">Level</span>
                                                <span className="badge-value">{currentStats.player_level}</span>
                                            </div>
                                        )}
                                        {currentStats.rank && (
                                            <div className="badge-item">
                                                <span className="badge-label">Rank</span>
                                                <span className="badge-value">{currentStats.rank}</span>
                                            </div>
                                        )}
                                    </div>

                                    {currentStats.roles && (
                                        <div className="roles-distribution">
                                            <span className="roles-label">Role Distribution (Game Counts):</span>
                                            <div className="roles-grid">
                                                {Object.entries(currentStats.roles).map(([role, count]) => (
                                                    <div key={role} className="role-stat">
                                                        <span className="role-name">{role.replace('_', ' ')}</span>
                                                        <span className="role-count">{count}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {(currentStats.takedowns || currentStats.mvp_awards || currentStats.kda || currentStats.avg_takedowns) && (
                                        <div className="career-preview">
                                            {currentStats.takedowns && <span>⚔️ {currentStats.takedowns.toLocaleString()} Takedowns</span>}
                                            {currentStats.avg_takedowns && <span>📉 {currentStats.avg_takedowns} Avg</span>}
                                            {currentStats.kda && <span>📊 {currentStats.kda} KDA</span>}
                                            {currentStats.mvp_awards && <span>🏆 {currentStats.mvp_awards} MVPs</span>}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Hero Stats */}
                            <div className="hero-stats-section">
                                <div className="hero-stats-header">
                                    <label>Detected Heroes ({currentHeroes.length})</label>
                                    <button className="add-hero-btn" onClick={addHeroStat}>
                                        + Add Hero
                                    </button>
                                </div>
                                {currentHeroes.map((hero, index) => (
                                    <div key={index} className="hero-stat-row">
                                        <input
                                            type="text"
                                            placeholder="Hero"
                                            value={hero.hero}
                                            onChange={(e) => updateHeroStat(index, 'hero', e.target.value)}
                                        />
                                        <input
                                            type="number"
                                            placeholder="Games"
                                            value={hero.games}
                                            onChange={(e) => updateHeroStat(index, 'games', e.target.value)}
                                        />
                                        <input
                                            type="number"
                                            step="0.1"
                                            placeholder="WR%"
                                            value={hero.wr}
                                            onChange={(e) => updateHeroStat(index, 'wr', e.target.value)}
                                        />
                                        <button className="remove-btn" onClick={() => removeHeroStat(index)}>
                                            ✕
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="cancel-btn" onClick={onClose}>
                        Cancel
                    </button>
                    <button
                        className="save-btn"
                        onClick={handleSave}
                        disabled={isSaving || (!buckets.season.stats.total_games && buckets.season.heroes.length === 0 && !buckets.lifetime.stats.total_games && buckets.lifetime.heroes.length === 0)}
                    >
                        {isSaving ? 'Synchronizing...' : 'Verify & Synchronize All'}
                    </button>
                </div>
            </div>
        </div>
    );
}

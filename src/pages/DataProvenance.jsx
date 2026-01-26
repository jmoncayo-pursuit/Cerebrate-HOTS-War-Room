import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import './DataProvenance.css';
import VerificationModal from '../components/VerificationModal';

export default function DataProvenance() {
    const [ingestionLog, setIngestionLog] = useState([]);
    const [sourceStatus, setSourceStatus] = useState({});
    const [conflicts, setConflicts] = useState([]);
    const [selectedSource, setSelectedSource] = useState('all');
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        loadIngestionData();
    }, []);

    const loadIngestionData = async () => {
        try {
            // Load ingestion log
            const logRes = await fetch('/api/data/ingestion_log.json');
            const log = await logRes.json();
            setIngestionLog(log.entries || []);

            // Load source status
            const statusRes = await fetch('/api/data_sources/status');
            const status = await statusRes.json();
            setSourceStatus(status);

            // Load conflicts
            const conflictsRes = await fetch('/api/data_sources/conflicts');
            const conflictsData = await conflictsRes.json();
            setConflicts(conflictsData.conflicts || []);
        } catch (error) {
            console.error('Failed to load ingestion data:', error);
        }
    };


    const getSourceIcon = (source) => {
        const icons = {
            'blizzard_verified': '🎮',
            'heroesprofile': '🌐',
            'replay_parser': '📼',
            'manual_entry': '✍️'
        };
        return icons[source] || '📊';
    };

    const getSourceColor = (source) => {
        const colors = {
            'blizzard_verified': 'text-green-400',
            'heroesprofile': 'text-blue-400',
            'replay_parser': 'text-purple-400',
            'manual_entry': 'text-yellow-400'
        };
        return colors[source] || 'text-gray-400';
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const filteredLog = selectedSource === 'all'
        ? ingestionLog
        : ingestionLog.filter(entry => entry.source === selectedSource);

    return (
        <div className="data-provenance-page">
            {/* Premium Page Header */}
            <div className="cerebrate-header-card">
                <div className="flex items-center">
                    <div className="header-icon-box" style={{ background: 'rgba(99, 102, 241, 0.1)', borderColor: 'rgba(99, 102, 241, 0.2)', color: '#6366f1' }}>
                        <BarChart3 size={24} />
                    </div>
                    <div>
                        <h1 className="header-title hots-text-glow">Data Provenance</h1>
                        <p className="header-subtitle">Intelligence Sources & Verification Matrix</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowVerificationModal(true)}
                        className="px-4 py-1.5 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-[10px] font-bold uppercase tracking-widest text-indigo-400 hover:bg-indigo-500/20 transition-all flex items-center gap-2"
                    >
                        📸 Verify Stats
                    </button>
                    <div className="status-indicator" style={{ background: 'rgba(99, 102, 241, 0.1)', borderColor: 'rgba(99, 102, 241, 0.2)', color: '#6366f1' }}>
                        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
                        Links Verified
                    </div>
                </div>
            </div>

            {/* Message Toast */}
            {message && (
                <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg border backdrop-blur-md transition-all ${message.type === 'success'
                    ? 'bg-green-900/80 border-green-500/50 text-green-100'
                    : 'bg-red-900/80 border-red-500/50 text-red-100'
                    }`}>
                    <div className="flex items-center gap-2">
                        <span>{message.type === 'success' ? '✓' : '✗'}</span>
                        <span className="font-medium">{message.text}</span>
                    </div>
                </div>
            )}

            {/* Verification Modal */}
            <VerificationModal
                isOpen={showVerificationModal}
                onClose={() => setShowVerificationModal(false)}
                onSuccess={() => {
                    loadIngestionData();
                    setShowVerificationModal(false);
                }}
            />

            {/* Source Status Cards */}
            <div className="source-status-grid">
                {Object.entries(sourceStatus).map(([source, status]) => (
                    <div key={source} className="source-card">
                        <div className="source-card-header">
                            <span className="text-2xl">{getSourceIcon(source)}</span>
                            <div className="flex-1">
                                <h3 className="font-bold text-white capitalize">
                                    {source.replace('_', ' ')}
                                </h3>
                                <p className="text-xs text-gray-400">
                                    Last updated: {formatTimestamp(status.last_updated)}
                                </p>
                            </div>
                            <div className={`status-badge ${status.healthy ? 'healthy' : 'stale'}`}>
                                {status.healthy ? '✓ Active' : '⚠ Stale'}
                            </div>
                        </div>

                        <div className="source-card-stats">
                            <div className="stat">
                                <span className="stat-label">Records</span>
                                <span className="stat-value">{status.record_count || 0}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Coverage</span>
                                <span className="stat-value">{status.coverage || 0}%</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Confidence</span>
                                <span className={`stat-value confidence-${(status.confidence || 'N/A').toLowerCase()}`}>{status.confidence || 'N/A'}</span>
                            </div>
                        </div>

                    </div>
                ))}
            </div>

            {/* Conflicts Section */}
            {conflicts.length > 0 && (
                <div className="conflicts-section">
                    <h2 className="section-title">⚖️ Synchronization Audit ({conflicts.length})</h2>
                    <div className="conflicts-list">
                        {conflicts.map((conflict, idx) => (
                            <div key={idx} className={`conflict-card ${conflict.field.includes('stale') ? 'stale-warning' : 'intelligence-gap'}`}>
                                <div className="conflict-header">
                                    <span className="conflict-field">
                                        {conflict.field === 'calibration_required' ? '🔍 Calibration Task' :
                                            conflict.field.includes('stale') ? '⚠️ Stale Verification' : conflict.field}
                                    </span>
                                    <span className="conflict-entity">{conflict.entity}</span>
                                </div>
                                <div className="conflict-sources">
                                    {conflict.values.map((val, i) => (
                                        <div key={i} className="conflict-value">
                                            <span className={`source-tag ${getSourceColor(val.source)}`}>
                                                {getSourceIcon(val.source)} {val.source}
                                            </span>
                                            <span className={`value ${val.value === 'Unverified' ? 'text-cyan-400' : val.value === 'Missing' ? 'text-red-500 font-bold' : ''}`}>
                                                {val.value}
                                            </span>
                                            {val.timestamp && <span className="timestamp">{formatTimestamp(val.timestamp)}</span>}
                                        </div>
                                    ))}
                                </div>
                                <div className="conflict-resolution">
                                    <span className="resolution-label">
                                        {(conflict.field === 'calibration_required' || conflict.field.includes('stale')) ? 'Required Action:' : 'Resolved Using:'}
                                    </span>
                                    <span className={`resolution-source ${getSourceColor(conflict.resolved_source)}`}>
                                        {(conflict.field === 'calibration_required' || conflict.field.includes('stale')) ? '📸 Screenshot Upload' : `${getSourceIcon(conflict.resolved_source)} ${conflict.resolved_source}`}
                                    </span>
                                    <span className="resolution-reason">({conflict.reason})</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Ingestion Log */}
            <div className="ingestion-log-section">
                <div className="log-header">
                    <h2 className="section-title">📜 Ingestion History</h2>
                    <select
                        value={selectedSource}
                        onChange={(e) => setSelectedSource(e.target.value)}
                        className="source-filter"
                    >
                        <option value="all">All Sources</option>
                        <option value="blizzard_verified">Blizzard Verified</option>
                        <option value="heroesprofile">HeroesProfile</option>
                        <option value="replay_parser">Replay Parser</option>
                        <option value="manual_entry">Manual Entry</option>
                    </select>
                </div>

                <div className="log-timeline">
                    {filteredLog.map((entry, idx) => (
                        <div key={idx} className="log-entry">
                            <div className="log-timestamp">
                                {formatTimestamp(entry.timestamp)}
                            </div>
                            <div className="log-marker">
                                <div className={`marker-dot ${getSourceColor(entry.source)}`}></div>
                                <div className="marker-line"></div>
                            </div>
                            <div className="log-content">
                                <div className="log-content-header">
                                    <span className={`log-source ${getSourceColor(entry.source)}`}>
                                        {getSourceIcon(entry.source)} {entry.source}
                                    </span>
                                    <span className={`log-status ${entry.status}`}>
                                        {entry.status === 'success' ? '✓' : '✗'} {entry.status}
                                    </span>
                                </div>
                                <p className="log-message">{entry.message}</p>
                                {entry.details && (
                                    <div className="log-details">
                                        <div className="detail-item">
                                            <span className="detail-label">Records:</span>
                                            <span className="detail-value">{entry.details.records_added || 0} added, {entry.details.records_updated || 0} updated</span>
                                        </div>
                                        {entry.details.conflicts && (
                                            <div className="detail-item">
                                                <span className="detail-label">Conflicts:</span>
                                                <span className="detail-value text-yellow-400">{entry.details.conflicts} resolved</span>
                                            </div>
                                        )}
                                        {entry.details.errors && (
                                            <div className="detail-item">
                                                <span className="detail-label">Errors:</span>
                                                <span className="detail-value text-red-400">{entry.details.errors}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Data Lineage Viewer */}
            <div className="lineage-section">
                <h2 className="section-title">🔍 Data Lineage Explorer</h2>
                <p className="text-sm text-gray-400 mb-4">
                    Search for any stat to see where it came from and when
                </p>
                <input
                    type="text"
                    placeholder="Search: 'Raynor win rate' or 'Cursed Hollow games'"
                    className="lineage-search"
                />
                {/* Lineage results would go here */}
            </div>
        </div>
    );
}

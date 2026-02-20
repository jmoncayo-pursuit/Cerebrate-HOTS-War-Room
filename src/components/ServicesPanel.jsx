import { useState, useEffect } from 'react'
import FileProgressBar from './FileProgressBar'
import MCPStatus from './MCPStatus'
import './ServicesPanel.css'

export default function ServicesPanel() {
    const [watcherStatus, setWatcherStatus] = useState('unknown')
    const [apiStatus, setApiStatus] = useState('unknown')
    const [replayCount, setReplayCount] = useState(0)
    const [loading, setLoading] = useState(false)
    const [processingDetails, setProcessingDetails] = useState(null)
    const [activities, setActivities] = useState([])
    const [mcpStatus, setMcpStatus] = useState('DISCONNECTED')

    useEffect(() => {
        checkStatus()
        const interval = setInterval(checkStatus, 2000)
        return () => clearInterval(interval)
    }, [])

    const checkStatus = async () => {
        try {
            // Add cache buster to prevent stale status reports
            const timestamp = Date.now()
            const apiRes = await fetch(`/api/health?t=${timestamp}`)
            const isApiUp = apiRes.ok
            setApiStatus(isApiUp ? 'running' : 'stopped')

            if (isApiUp) {
                const watcherRes = await fetch(`/api/watcher/status?t=${timestamp}`)
                if (watcherRes.ok) {
                    const data = await watcherRes.json()
                    // Only update if not in a loading state to prevent flickering
                    if (!loading) {
                        setWatcherStatus(data.running ? 'running' : 'stopped')
                        setReplayCount(data.replay_count || 0)
                        setProcessingDetails(data.processing || null)
                        setActivities(data.activities || [])
                    }
                }
                const usageRes = await fetch(`/api/usage?t=${timestamp}`)
                if (usageRes.ok) {
                    const usageData = await usageRes.json()
                    if (usageData.services && usageData.services.mcp_bridge) {
                        setMcpStatus(usageData.services.mcp_bridge)
                    }
                }

            } else {
                setWatcherStatus('stopped')
            }
        } catch (error) {
            setApiStatus('stopped')
            setWatcherStatus('stopped')
        }
    }

    const toggleWatcher = async () => {
        if (loading || apiStatus !== 'running') return

        const isCurrentlyRunning = watcherStatus === 'running'
        const action = isCurrentlyRunning ? 'stop' : 'start'

        // PHASE 1: Optimistic Commitment
        // Switch visual state immediately to provide zero-latency feedback
        setWatcherStatus(isCurrentlyRunning ? 'stopped' : 'running')
        setLoading(true)

        try {
            // PHASE 2: Background Synchronization
            const timestamp = Date.now()
            const res = await fetch(`/api/watcher/${action}?t=${timestamp}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })

            const data = await res.json()

            if (res.ok) {
                // PHASE 3: Definitive State Realization
                // We trust the server's forced state more than the scan results
                if (data.running !== undefined) {
                    setWatcherStatus(data.running ? 'running' : 'stopped')
                    if (data.replay_count !== undefined) setReplayCount(data.replay_count)
                    if (data.activities) setActivities(data.activities)
                    if (data.processing) setProcessingDetails(data.processing)
                }
            } else {
                console.warn(`Watcher ${action} rejected:`, data.error)
                // Revert only on definitive rejection
                await checkStatus()
            }
        } catch (error) {
            console.error(`Link command fault:`, error)
            // Revert on network fault
            await checkStatus()
        } finally {
            setLoading(false)
        }
    }

    const getStatusText = (status) => {
        switch (status) {
            case 'running': return 'Active'
            case 'stopped': return 'Offline'
            default: return 'Scanning...'
        }
    }

    return (
        <div className="services-container">
            {/* Scoped Site Overlay */}
            <div className="services-overlay" />

            <div className="cerebrate-header-card">
                <div className="flex items-center">
                    <div className="header-icon-box" style={{ background: 'rgba(234, 88, 12, 0.1)', borderColor: 'rgba(234, 88, 12, 0.2)', color: '#ea580c' }}>
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="header-title hots-text-glow">Tactical Services</h1>
                        <p className="header-subtitle">Background Ingress & Monitoring</p>
                    </div>
                </div>

                <div className="hidden md:flex flex-col items-end gap-2">
                    <div className={`status-indicator ${apiStatus === 'running' ? '' : 'opacity-50 grayscale'}`}
                        style={{
                            background: apiStatus === 'running' ? 'rgba(234, 88, 12, 0.1)' : 'rgba(100, 116, 139, 0.1)',
                            borderColor: apiStatus === 'running' ? 'rgba(234, 88, 12, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                            color: apiStatus === 'running' ? '#ea580c' : '#94a3b8'
                        }}>
                        <span className={`w-1.5 h-1.5 rounded-full ${apiStatus === 'running' ? 'bg-orange-500 animate-pulse' : 'bg-slate-500'}`} />
                        {apiStatus === 'running' ? 'System Link Active' : 'System Link Offline'}
                    </div>
                    <span className="text-[10px] text-slate-600 font-mono tracking-widest opacity-60 uppercase">Node: Cerebrate-v2.7</span>
                </div>
            </div>

            {/* Ops / Token Usage link */}
            <button
                onClick={() => window.dispatchEvent(new CustomEvent('nav_to_healer_ops'))}
                className="w-full py-2 px-3 rounded-lg border border-cyan-500/20 bg-cyan-500/5 hover:bg-cyan-500/10 text-cyan-400 text-xs font-bold uppercase tracking-widest transition-colors mb-4"
            >
                Ops / Token Usage →
            </button>

            {/* Replay Watcher Card */}
            <div className="service-card group">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                        <div className={`service-status-dot ${watcherStatus}`} />
                        <div>
                            <h3 className="text-white font-bold text-lg tracking-tight">Intelligence Watcher</h3>
                            <p className="text-xs text-slate-500 font-mono uppercase">
                                {watcherStatus === 'running'
                                    ? `Synchronized with ${replayCount} matches`
                                    : 'Autonomous detection disabled'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={toggleWatcher}
                        disabled={loading || apiStatus !== 'running'}
                        className={`service-action-btn ${watcherStatus === 'running' ? 'btn-stop' : 'btn-start'} disabled:opacity-30 disabled:cursor-not-allowed`}
                    >
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <div className="animate-spin h-3 w-3 border-2 border-current border-t-transparent rounded-full" />
                                {watcherStatus === 'running' ? 'Linking...' : 'Stopping...'}
                            </span>
                        ) : watcherStatus === 'running' ? (
                            'Disable Link'
                        ) : (
                            'Establish Link'
                        )}
                    </button>
                </div>

                {watcherStatus === 'running' && (
                    <div className="mt-4 pt-4 border-t border-white/5 space-y-4">
                        {processingDetails ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
                                        {processingDetails.status === 'idle' ? (
                                            <span className="text-green-400 animate-pulse flex items-center gap-1.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                                                {processingDetails.message || 'Standby // Monitoring...'}
                                            </span>
                                        ) : (
                                            <span className="text-cyan-400 flex items-center gap-1.5">
                                                <div className="animate-spin h-3 w-3 border-2 border-cyan-400 border-t-transparent rounded-full" />
                                                {processingDetails.message || 'Ingesting Telemetry...'}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {processingDetails.current_file && (
                                    <div className="text-[10px] text-slate-400 font-mono p-2 bg-black/30 rounded border border-white/5 truncate">
                                        <span className="opacity-40">RAW:</span> {processingDetails.current_file}
                                    </div>
                                )}

                                {processingDetails.total > 0 && processingDetails.processed !== undefined && (
                                    <div className="space-y-4">
                                        {/* Dual-Track Visualization */}
                                        <div className="space-y-3">
                                            {/* Scan Track (Fast) */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[9px] font-mono text-cyan-400 uppercase tracking-wider">
                                                    <span className="flex items-center gap-1.5">
                                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                                        </svg>
                                                        Scan Progress (Fast)
                                                    </span>
                                                    <span>{processingDetails.processed} / {processingDetails.total}</span>
                                                </div>
                                                <div className="w-full bg-slate-900/50 rounded-full h-2 overflow-hidden border border-cyan-500/20">
                                                    <div
                                                        className="bg-gradient-to-r from-cyan-500 to-cyan-600 h-full transition-all duration-300 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.4)]"
                                                        style={{ width: `${(processingDetails.processed / processingDetails.total) * 100}%` }}
                                                    />
                                                </div>
                                                <div className="text-[8px] text-slate-500 font-mono">
                                                    Most files skip instantly (analysis complete)
                                                </div>
                                            </div>

                                            {/* Processing Queue (Slow) */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[9px] font-mono text-orange-400 uppercase tracking-wider">
                                                    <span className="flex items-center gap-1.5">
                                                        <svg className="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                        </svg>
                                                        Processing Queue (5s each)
                                                    </span>
                                                    <span className="text-orange-300">
                                                        {activities.filter(a => a.status === 'success' || a.status === 'duplicate').length} analyzed
                                                    </span>
                                                </div>
                                                <div className="w-full bg-slate-900/50 rounded-full h-2 overflow-hidden border border-orange-500/20">
                                                    <div
                                                        className="bg-gradient-to-r from-orange-500 to-amber-600 h-full transition-all duration-500 rounded-full shadow-[0_0_10px_rgba(249,115,22,0.4)] animate-pulse"
                                                        style={{ width: `${Math.min(100, (activities.filter(a => a.status === 'success' || a.status === 'duplicate').length / Math.max(1, activities.length)) * 100)}%` }}
                                                    />
                                                </div>
                                                <div className="text-[8px] text-slate-500 font-mono">
                                                    Only new sessions need neural-link analysis
                                                </div>
                                            </div>
                                        </div>

                                        {/* Stats Summary */}
                                        <div className="grid grid-cols-3 gap-2 text-center">
                                            <div className="p-2 bg-slate-900/30 rounded border border-white/5">
                                                <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Total</div>
                                                <div className="text-lg font-bold text-white font-mono">{processingDetails.total}</div>
                                            </div>
                                            <div className="p-2 bg-green-500/10 rounded border border-green-500/20">
                                                <div className="text-[10px] text-green-400 uppercase tracking-wider mb-1">Complete</div>
                                                <div className="text-lg font-bold text-green-300 font-mono">
                                                    {processingDetails.total - activities.filter(a => a.status !== 'skipped').length}
                                                </div>
                                            </div>
                                            <div className="p-2 bg-orange-500/10 rounded border border-orange-500/20">
                                                <div className="text-[10px] text-orange-400 uppercase tracking-wider mb-1">Processing</div>
                                                <div className="text-lg font-bold text-orange-300 font-mono">
                                                    {activities.filter(a => a.status !== 'skipped').length}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
                                <span>Replay Watcher Active</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Browser Neural Link (MCP) */}
            <div className="mt-4">
                <MCPStatus status={mcpStatus} />
            </div>

            {/* Activity Log - Cinematic View */}
            <div className="activity-log">
                <div className="activity-log-header">
                    <span>Telemetry Log</span>
                    <span className="opacity-50 font-mono">ACTIVE SESSIONS: {activities.length}</span>
                </div>

                {activities.length === 0 ? (
                    <div className="p-8 text-center text-slate-500 font-mono text-xs border border-white/5 rounded-lg bg-white/5">
                        NO TELEMETRY SIGNATURES DETECTED
                        <br />
                        <span className="opacity-50">Provide replay files to initiate scan sequence.</span>
                    </div>
                ) : (
                    <div className="space-y-3 h-[400px] overflow-y-auto custom-scrollbar pr-2">
                        {activities.map((activity) => (
                            <div key={activity.filename || Math.random()} className="p-2 bg-white/5 rounded-lg border border-white/5 hover:border-cyan-500/30 transition-colors min-h-[120px]">
                                <FileProgressBar
                                    activity={activity}
                                    isWatcherRunning={watcherStatus === 'running'}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Info Box - Premium Style */}
            <div className="info-box-enhanced">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center border border-blue-400/30 shadow-[0_0_10px_rgba(59,130,246,0.1)] shrink-0">
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div className="text-sm">
                    <p className="text-blue-400 font-bold uppercase tracking-widest text-[10px] mb-1 hots-text-glow">Operational Doctrine</p>
                    <p className="text-xs text-slate-300 leading-relaxed font-medium opacity-90">
                        Watcher systems synchronize with your local Hots Replay archives. New telemetry is automatically captured, parsed via neural-link, and persisted to your central match history without commander intervention.
                    </p>
                </div>
            </div>
        </div>
    )
}

import React from 'react';
import {
    FileSearch,
    History,
    Database,
    CloudUpload,
    CheckCircle2,
    AlertCircle,
    XCircle,
    PlayCircle,
    Clock,
    ShieldCheck
} from 'lucide-react';
import './FileProgressBar.css';

/**
 * Elegant Pipeline Progress component for file validation.
 * Replaces simple colors with descriptive stages and status icons.
 * Upgraded with Cerebrate Neural Scanner treatment.
 */
export default function FileProgressBar({ activity, isWatcherRunning }) {
    const stages = activity.stages || {};
    const details = activity.details || {};

    const getStageStatus = (stageStatus) => {
        if (stageStatus === 'complete') return 'complete';
        if (stageStatus === 'active') return 'active';
        if (stageStatus === 'error') return 'error';
        if (stageStatus === 'skipped') return 'skipped';
        return 'pending';
    };

    const Stage = ({ label, status, detail, Icon }) => {
        const stageStatus = getStageStatus(status);
        return (
            <div className={`pipeline-stage ${stageStatus}`}>
                <div className="stage-icon-wrap">
                    <Icon size={14} className={stageStatus === 'active' ? 'animate-pulse' : ''} />
                </div>
                <div className="flex flex-col items-center leading-tight overflow-hidden w-full">
                    <span className="stage-label">
                        {label}
                    </span>
                    <span className="stage-detail">
                        {detail || '---'}
                    </span>
                </div>
            </div>
        );
    };

    const getStatusClass = () => {
        if (activity.status === 'success') return 'status-success';
        if (activity.status === 'error') return 'status-error';
        if (activity.status === 'duplicate') return 'status-duplicate';
        if (activity.status === 'checking' || activity.status === 'uploading' || activity.status === 'pending') return 'status-active';
        return '';
    };

    return (
        <div className={`file-progress-item ${getStatusClass()}`}>
            {/* Header: Filename + Status + Meta */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3 min-w-0">
                    <div className="p-1.5 bg-cyan-500/10 rounded-md border border-cyan-500/20 text-cyan-400">
                        <FileSearch size={14} />
                    </div>
                    <div className="flex flex-col min-w-0">
                        <span className="text-[11px] font-bold text-slate-200 truncate font-mono" title={activity.filename}>
                            {activity.filename}
                        </span>
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] text-slate-500 uppercase tracking-tighter">
                                {new Date(activity.timestamp * 1000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </span>
                            {activity.status === 'checking' && (
                                <div className="neural-activity-indicator">
                                    <div className="neural-bar" />
                                    <div className="neural-bar" />
                                    <div className="neural-bar" />
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 ml-4">
                    <div className="file-meta-badge">
                        <div className={`w-1.5 h-1.5 rounded-full ${activity.status === 'error' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' :
                            activity.status === 'success' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' :
                                activity.status === 'duplicate' ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.4)]' :
                                    activity.status === 'stopped' ? 'bg-slate-600' :
                                        'bg-cyan-500 animate-pulse shadow-[0_0_8px_rgba(0,242,255,0.5)]'
                            }`} />
                        <span className={`text-[9px] uppercase font-black tracking-widest ${activity.status === 'error' ? 'text-red-400' :
                            activity.status === 'success' ? 'text-green-400' :
                                activity.status === 'duplicate' ? 'text-yellow-400' :
                                    'text-cyan-400'
                            }`}>
                            {activity.message}
                            {!isWatcherRunning && (activity.status === 'checking' || activity.status === 'uploading' || activity.status === 'pending') && (
                                <span className="ml-1 text-[8px] text-slate-500 font-bold italic opacity-60">
                                    (LINK PAUSED)
                                </span>
                            )}
                        </span>
                    </div>
                </div>
            </div>

            {/* Pipeline Stepper */}
            <div className="pipeline-stepper">
                <Stage label="Ingress" status={stages.file_check} detail={details.file_check} Icon={FileSearch} />
                <Stage label="Neural Match" status={stages.history_match} detail={details.history_match} Icon={History} />
                <Stage label="Telemetry" status={stages.completeness} detail={details.completeness} Icon={Database} />
                <Stage label="Forensic" status={stages.forensic} detail={details.forensic} Icon={ShieldCheck} />
                <Stage label="Synchronize" status={stages.upload} detail={details.upload} Icon={CloudUpload} />
                <Stage label="Persisted" status={stages.done} detail={details.done} Icon={CheckCircle2} />
            </div>
        </div>
    );
}

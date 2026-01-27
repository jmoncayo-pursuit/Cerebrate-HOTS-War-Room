import React from 'react';
import { Monitor, Link, Link2Off } from 'lucide-react';

const MCPStatus = ({ status }) => {
    const isConnected = status === 'ACTIVE';

    return (
        <div className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${isConnected
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-slate-500/5 border-white/5 text-slate-500'
            }`}>
            <div className={`p-2 rounded-lg ${isConnected ? 'bg-emerald-500/20' : 'bg-slate-500/10'}`}>
                {isConnected ? <Link size={18} /> : <Link2Off size={18} />}
            </div>
            <div className="flex-1">
                <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase tracking-widest font-bold">Neural Link (Browser)</span>
                    <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold ${isConnected ? 'bg-emerald-500/20' : 'bg-slate-500/20'
                        }`}>
                        {isConnected ? 'STABLE' : 'OFFLINE'}
                    </span>
                </div>
                <div className="text-[9px] opacity-70 mt-0.5">
                    {isConnected
                        ? 'Eyes on the DOM: Intelligence Swarm Synced'
                        : 'Browser Bridge Disconnected: Open DevTools'}
                </div>
            </div>
        </div>
    );
};

export default MCPStatus;

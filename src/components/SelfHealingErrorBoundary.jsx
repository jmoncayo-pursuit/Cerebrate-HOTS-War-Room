import React, { Component } from 'react';
import { Activity, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

class SelfHealingErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            healing: false,
            healed: false
        };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
        // In a real agentic loop, this would trigger an external repair mission
        this.initiateSelfHealing();
    }

    initiateSelfHealing = () => {
        this.setState({ healing: true });

        // Simulate complex analysis and repair protocol
        setTimeout(() => {
            this.setState({ healing: false, healed: true, hasError: false });
        }, 2000);
    };

    handleManualRetry = () => {
        this.setState({ hasError: false, healing: false, healed: false });
        window.location.reload();
    };

    render() {
        if (this.state.hasError || this.state.healing) {
            return (
                <div className="flex flex-col items-center justify-center p-8 h-full min-h-[400px] w-full bg-slate-900/50 backdrop-blur-md rounded-2xl border border-white/5">
                    <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="flex flex-col items-center text-center space-y-6 max-w-md"
                    >
                        <div className="relative">
                            <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full" />
                            <div className="relative w-20 h-20 bg-slate-900 border border-purple-500/30 rounded-2xl flex items-center justify-center shadow-2xl">
                                {this.state.healing ? (
                                    <RefreshCw className="w-10 h-10 text-purple-400 animate-spin" />
                                ) : (
                                    <Activity className="w-10 h-10 text-red-400" />
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h2 className="text-xl font-bold tracking-wider text-white uppercase">
                                {this.state.healing ? "Self-Healing Protocol Engaged" : "System Anomaly Detected"}
                            </h2>
                            <p className="text-slate-400 text-sm font-medium leading-relaxed">
                                {this.state.healing
                                    ? "Analyst Agent is attempting to reconstruct the interface state..."
                                    : "Components have destabilized. Initiating automated recovery sequence."}
                            </p>
                        </div>

                        {!this.state.healing && (
                            <button
                                onClick={this.handleManualRetry}
                                className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold uppercase tracking-widest rounded-lg transition-all shadow-lg hover:shadow-purple-500/25 border border-white/10"
                            >
                                <RefreshCw size={14} />
                                Manual Override
                            </button>
                        )}

                        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-600 pt-4 border-t border-white/5 w-full">
                            Automated Error Correction v2.0
                        </div>
                    </motion.div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default SelfHealingErrorBoundary;

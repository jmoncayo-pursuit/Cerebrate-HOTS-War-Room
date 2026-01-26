import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ProgressLog({ logs, isProcessing }) {
    const logEndRef = useRef(null)

    useEffect(() => {
        // Auto-scroll to bottom when new logs appear
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    if (logs.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 bg-black/40 border border-cyan-500/30 rounded-lg overflow-hidden"
        >
            <div className="bg-cyan-900/20 border-b border-cyan-500/30 px-4 py-2 flex items-center justify-between">
                <span className="text-sm font-bold text-cyan-300">Processing Log</span>
                {isProcessing && (
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                        <span className="text-xs text-cyan-400">Processing...</span>
                    </div>
                )}
            </div>

            <div className="max-h-64 overflow-y-auto p-4 space-y-1 font-mono text-xs">
                <AnimatePresence>
                    {logs.map((log, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={`flex items-start gap-2 ${log.type === 'error' ? 'text-red-400' :
                                    log.type === 'success' ? 'text-green-400' :
                                        'text-gray-300'
                                }`}
                        >
                            <span className="text-gray-500 shrink-0">[{log.timestamp}]</span>
                            <span className="break-all">{log.message}</span>
                        </motion.div>
                    ))}
                </AnimatePresence>
                <div ref={logEndRef} />
            </div>
        </motion.div>
    )
}

import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw } from 'lucide-react'

export default function DataUpdateNotification({ show, lastUpdated }) {
    if (!show) return null

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.9 }}
                className="fixed top-4 right-4 z-50 bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-6 py-3 rounded-lg shadow-2xl border border-cyan-300/30 flex items-center gap-3"
            >
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                    <RefreshCw size={20} />
                </motion.div>
                <div>
                    <div className="font-bold text-sm">Data Updated!</div>
                    <div className="text-xs opacity-90">
                        {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Just now'}
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    )
}

import { TrendingUp, TrendingDown, Award, AlertTriangle } from 'lucide-react'
import { motion } from 'framer-motion'
import HeroText from './HeroText'

/**
 * MatchStatsCard - Visual data display for replay analysis
 * Shows key stats, team comparison, and performance metrics
 */
export default function MatchStatsCard({ match }) {
    if (!match) return null

    const { map, hero, result, analysis, advanced_stats } = match

    // Find user's stats from the match data (if available in future)
    // For now, we'll use the analysis data
    const isWin = result?.toUpperCase() === 'WIN'

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-md-surface-container border border-md-outline-variant rounded-xl overflow-hidden shadow-lg mb-4"
        >
            {/* Header */}
            <div className={`p-4 border-b border-md-outline-variant ${isWin ? 'bg-green-900/20' : 'bg-red-900/20'
                }`}>
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-lg text-white">{map}</h3>
                        <p className="text-sm text-gray-400">Playing {hero}</p>
                    </div>
                    <div className={`px-4 py-2 rounded-lg font-bold ${isWin
                        ? 'bg-green-600/30 text-green-300 border border-green-500/50'
                        : 'bg-red-600/30 text-red-300 border border-red-500/50'
                        }`}>
                        {result}
                    </div>
                </div>
            </div>

            {/* Verdict & Key Stat */}
            {analysis && (
                <div className="p-4 space-y-4">
                    {/* Verdict */}
                    <div className="flex items-center gap-3">
                        <Award className="text-cyan-400" size={20} />
                        <div>
                            <p className="text-xs text-gray-400 uppercase tracking-wide">Verdict</p>
                            <p className="text-white font-bold">{analysis.verdict}</p>
                        </div>
                    </div>



                    {/* Summary */}
                    {analysis.summary && (
                        <div className="text-sm text-gray-300 leading-relaxed">
                            <HeroText text={analysis.summary} />
                        </div>
                    )}

                    {/* Tactical Breakdown */}
                    {(analysis.tactical_breakdown || analysis.areas_for_improvement) && (
                        <div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-3 flex gap-3">
                            <AlertTriangle className="text-orange-400 shrink-0 mt-0.5" size={18} />
                            <div>
                                <p className="text-xs text-orange-400 uppercase tracking-wide mb-1">Tactical Breakdown</p>
                                <p className="text-sm text-orange-200">
                                    <HeroText text={analysis.tactical_breakdown || analysis.areas_for_improvement} />
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Win Condition */}
                    {(analysis.win_condition || analysis.win_condition_analysis) && (
                        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3">
                            <p className="text-xs text-purple-400 uppercase tracking-wide mb-1">Win Condition</p>
                            <p className="text-sm text-purple-200">
                                <HeroText text={analysis.win_condition || analysis.win_condition_analysis} />
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Bans (if available) */}
            {advanced_stats?.bans && advanced_stats.bans.length > 0 && (
                <div className="p-4 border-t border-md-outline-variant bg-black/20">
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Draft Bans</p>
                    <div className="flex flex-wrap gap-2">
                        {advanced_stats.bans.map((ban, idx) => (
                            <span
                                key={idx}
                                className="px-2 py-1 bg-red-900/30 text-red-300 text-xs rounded border border-red-500/30"
                            >
                                {ban.hero}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    )
}

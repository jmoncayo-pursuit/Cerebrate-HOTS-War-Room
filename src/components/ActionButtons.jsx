import { useState } from 'react'
import { Check, X, MessageSquare, Star, AlertTriangle, Send } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

/**
 * ActionButtons - Clickable buttons for AI recommendations
 * Allows users to interact with AI suggestions via API calls
 */
export default function ActionButtons({ message, matchId, onAction }) {
    const [loading, setLoading] = useState(false)
    const [feedback, setFeedback] = useState(null)
    const [activeInput, setActiveInput] = useState(null) // 'challenge', 'note', 'hero_note'
    const [inputValue, setInputValue] = useState('')

    const handleAction = async (actionType, data) => {
        setLoading(true)
        try {
            let endpoint = ''
            let payload = {}

            switch (actionType) {
                case 'challenge':
                    endpoint = '/api/update_match'
                    payload = {
                        match_id: matchId,
                        type: 'challenge',
                        data: { challenge: data.reason, original_verdict: message.content }
                    }
                    break

                case 'add_note':
                    endpoint = '/api/update_match'
                    payload = {
                        match_id: matchId,
                        type: 'player_note',
                        data: { note: data.note }
                    }
                    break

                case 'mark_learned':
                    endpoint = '/api/update_match'
                    payload = {
                        match_id: matchId,
                        type: 'learned',
                        data: { learned: true, timestamp: new Date().toISOString() }
                    }
                    break

                case 'update_hero_note':
                    endpoint = '/api/update_profile'
                    payload = {
                        type: 'hero_note',
                        data: { hero: data.hero, note: data.note }
                    }
                    break

                case 'update_map_preference':
                    endpoint = '/api/update_profile'
                    payload = {
                        type: 'map_preference',
                        data: { map: data.map, preference: data.preference }
                    }
                    break

                default:
                    throw new Error('Unknown action type')
            }

            const response = await fetch(`${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const result = await response.json()

            if (result.success) {
                setFeedback({ type: 'success', message: result.message || 'Updated successfully!' })
                if (onAction) onAction(actionType, data)
            } else {
                setFeedback({ type: 'error', message: result.error || 'Update failed' })
            }
        } catch (error) {
            setFeedback({ type: 'error', message: error.message })
        } finally {
            setLoading(false)
            setActiveInput(null) // Close input on success/fail
            setInputValue('')
            setTimeout(() => setFeedback(null), 3000)
        }
    }

    // Extract hero/map from message content if present
    const extractContext = () => {
        const content = message.content || ''
        const heroMatch = content.match(/(?:Play|Pick|Recommend)\s+(\w+)/i)

        // Try strict map pattern first (from backend response format)
        let mapMatch = content.match(/\[MISSION-CODE-REDACTED\]:\s*([\w\s']+(?:\(.*\))?)/i);

        // Fallback to looser "on Map" pattern but restricted to title case or known map structures
        if (!mapMatch) {
            mapMatch = content.match(/(?:on|for)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)/);
        }

        return {
            hero: heroMatch ? heroMatch[1] : null,
            map: mapMatch ? mapMatch[1].trim() : null
        }
    }

    const context = extractContext()

    const toggleInput = (type) => {
        if (activeInput === type) {
            setActiveInput(null)
            setInputValue('')
        } else {
            setActiveInput(type)
            setInputValue('')
        }
    }

    const handleSubmitInput = () => {
        const value = inputValue.trim()

        if (activeInput === 'challenge') {
            handleAction('challenge', { reason: value || 'User disagreed with recommendation' })
        } else if (activeInput === 'note' && value) {
            handleAction('add_note', { note: value })
        } else if (activeInput === 'hero_note' && value) {
            handleAction('update_hero_note', { hero: context.hero, note: value })
        }
    }

    const getInputPlaceholder = () => {
        switch (activeInput) {
            case 'challenge': return 'Why do you disagree? (Optional)'
            case 'note': return 'Add your note about this match...'
            case 'hero_note': return `Add note for ${context.hero}...`
            default: return 'Type here...'
        }
    }

    return (
        <div className="flex flex-col gap-2 mt-2">
            {/* Action Buttons Row */}
            <div className="flex gap-2 flex-wrap">

            </div>

            {/* Inline Input Area - Only show for hero_note */}
            <AnimatePresence>
                {activeInput === 'hero_note' && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="flex gap-2 items-center bg-black/20 p-2 rounded-lg border border-white/5">
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSubmitInput()}
                                placeholder={getInputPlaceholder()}
                                autoFocus
                                className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder-gray-500"
                            />
                            <button
                                onClick={handleSubmitInput}
                                disabled={loading}
                                className="p-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded transition-colors"
                            >
                                <Send size={14} />
                            </button>
                            <button
                                onClick={() => setActiveInput(null)}
                                className="p-1.5 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white rounded transition-colors"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Feedback Message */}
            {feedback && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`text-xs px-3 py-1.5 rounded-lg ${feedback.type === 'success'
                        ? 'bg-green-900/30 text-green-300 border border-green-500/30'
                        : 'bg-red-900/30 text-red-300 border border-red-500/30'
                        }`}
                >
                    {feedback.message}
                </motion.div>
            )}
        </div>
    )
}

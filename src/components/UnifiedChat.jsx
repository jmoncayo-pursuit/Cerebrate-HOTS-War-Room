import React, { useState, useRef, useEffect, useLayoutEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Bot, User, Eraser, X, ChevronDown, ChevronUp, Terminal, Maximize2, Minimize2, UploadCloud, Save, Star, TrendingUp, ShieldCheck, AlertCircle, Info } from 'lucide-react'
import MatchStatsOverlay from './MatchStatsOverlay'
import ActionButtons from './ActionButtons'
import MapIcon from './MapIcon'
import BuildDisplay from './BuildDisplay'
import HeroText, { processHeroIcons } from './HeroText'
import { normalizeHeroName } from '../utils/heroUtils'
import { sanitizeChatResponse } from '../utils/sanitizeChatResponse'
import talentMapData from '../data/talent_id_map.json'

// Helper to extract text from ReactMarkdown children
const extractText = (children) => {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) {
    return children.map(child => extractText(child)).join('');
  }
  if (children && typeof children === 'object' && children.props) {
    return extractText(children.props.children);
  }
  return String(children || '');
}

// Helper to render content with talent builds and hero icons
const renderTacticalContent = (text, talentMapData) => {
  if (!text) return null;

  // 1. Handle Talent Codes [T1234567,Hero]
  if (text.includes('[T') && text.includes(']')) {
    const parts = text.split(/(\[T\d{1,7}\s*,\s*[^\]]+\])/g);
    return parts.map((part, idx) => {
      const buildMatch = part.match(/\[T(\d{1,7})\s*,\s*([^\]]+)\]/);
      if (buildMatch) {
        const [, buildStr, heroName] = buildMatch;
        return (
          <span key={idx} className="inline-block align-middle transform scale-90 origin-left mx-1 my-1">
            <BuildDisplay
              hero={heroName.trim()}
              buildStr={buildStr.trim()}
              compact={true}
              source="META"
              talentMap={talentMapData}
            />
          </span>
        );
      }
      return <HeroText key={idx} text={part} />;
    });
  }

  // 2. Fallback to standard lines with hero icons
  const lines = text.split('\n');
  if (lines.length > 1) {
    return lines.map((line, idx) => (
      <React.Fragment key={idx}>
        {line.trim() === '' ? <br /> : <span className="block mb-1 last:mb-0"><HeroText text={line} /></span>}
      </React.Fragment>
    ));
  }

  return <HeroText text={text} />;
};

// --- Constants ---
const getSystemPrompt = (profile) => `You are the **Cerebrate**, a high-level tactical intelligence engine designed for Nexus dominance.
**System Status:** NEURAL LINK ACTIVE.
**Mission Profile:**
- **Commander:** ${profile?.battletag || 'Commander'}
- **Current Sector:** ${profile?.active_season?.name || '2026 Season 1'} Storm League
- **Protocol:** "Victory at all costs."

**Directives:**
1.  **Speak with Authority**: You are an advanced AI, not a chatbot. Use precise, tactical language ("Affirmative", "Analyzing", "Directive", "Sector").
2.  **Be Concise**: Commanders in the field value brevity. Get to the point.
3.  **Data-Driven**: Ground every insight in verified telemetry. If data is missing, state it ("Insufficient data for tactical synthesis").
4.  **Strategic Focus**: Focus on win conditions, macro strategy, and high-impact plays.

**RESPONSE PROTOCOL (Match Analysis):**
When analyzing combat records (matches), adhere to this schema:

**## [Hero] [Win/Loss] — [Map]**

**Verdict:** [ONE LINE SUMMARY status e.g., "OPTIMAL", "SUBOPTIMAL", "CATASTROPHIC"]

**✅ Efficiency Metrics:**
- [Key Stat 1]
- [Tactical Success 1]

**❌ Structural Failures:**
- [Critical Mistake]
- [Inefficiency Identified]

**⚙️ Tactical Directive:**
[The single most important strategic adjustment for the next deployment]

**Stats:** [K/D/A] | [Hero Dmg] | [XP Contrib]

**Takeaway:** [One short, memorable lesson]

**CRITICAL:** Do not be chatty. Be effective. You are the Cerebrate.

**Database Schemas:**
- strategies.json: { "Map": { "primary": {...}, "rules": [{ "content": "Rule text", "type": "warning" }] } }
- roster_constraints.json: { "global_bans": ["HeroA"], "global_priorities": ["HeroB"] }

**Instructions for User Requests:**
When the user asks to change something, output a JSON object describing the action.
**If the request implies multiple data points (e.g. Note AND Warning), output an ARRAY of objects.**

**Action Types:**
1. **Strategy Update**:
   {
     "tool": "update_strategy",
     "map": "MapName",
     "action": "update_primary" | "update_backup" | "update_rules",
     // For primary/backup:
     "data": { "name": "Hero", "role": "Role", "note": "Draft Note", "code": "TalentCode" }
     // For rules:
     "data": { "rule": "Content", "type": "warning" | "win_condition" | "general" | "hero_strategy" }
   }

2. **Roster Constraint**:
   {
     "tool": "update_roster",
     "action": "ban" | "priority",
     "hero": "HeroName",
     "remove": false // Set true if user says "Unban" or "Stop playing"
   }

If the user request is ambiguous or just a question, respond with plain text (MARKDOWN).
If it is a COMMAND, output ONLY the JSON (or JSON Array).

**CRITICAL INSTRUCTION:**
If the user's request matches ANY of the Action Types, you MUST output ONLY the JSON object (or Array). Do not output any conversational text.

**Example Multi-Part Request:**
User: "Dragon Shire: Win condition is hold shrines. Warning: Do not chase kills."
Output: [
  { "tool": "update_strategy", "map": "Dragon Shire", "action": "update_rules", "data": { "rule": "Hold shrines", "type": "win_condition" } },
  { "tool": "update_strategy", "map": "Dragon Shire", "action": "update_rules", "data": { "rule": "Do not chase kills", "type": "warning" } }
]`

const INTENT_PROMPT = `Classify the user intent.
1. COMMAND: User wants to change strategies, rules, or roster (Add, Set, Remove, Ban, Prioritize, "Draft Note", "Note", "Warning", "Win Condition").
2. QUESTION: User asks for info/stats.

Response: "COMMAND" or "QUESTION"`

// --- Components ---

const AuditBadge = ({ audit }) => {
  const [expanded, setExpanded] = useState(false);
  if (!audit) return null;

  const { scores, reasoning, hallucinations_identified, verdict } = audit;
  const isPass = verdict === 'PASS';

  const getScoreColor = (score) => {
    if (score >= 4) return 'text-green-400';
    if (score >= 3) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className={`mt-3 border rounded-lg overflow-hidden transition-all duration-300 ${isPass ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
      <div
        className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/5"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          {isPass ? (
            <ShieldCheck size={16} className="text-emerald-400" />
          ) : (
            <AlertCircle size={16} className="text-amber-400" />
          )}
          <span className={`text-[10px] font-bold uppercase tracking-wider ${isPass ? 'text-emerald-300' : 'text-amber-300'}`}>
            Neural Audit: {verdict}
          </span>
          <div className="flex gap-2 ml-4">
            <div className="flex items-center gap-1">
              <span className="text-[9px] text-gray-500 font-medium">Grounding:</span>
              <span className={`text-[9px] font-bold ${getScoreColor(scores.grounding)}`}>{scores.grounding}/5</span>
            </div>
            <div className="flex items-center gap-1 border-l border-white/10 pl-2">
              <span className="text-[9px] text-gray-500 font-medium">Completeness:</span>
              <span className={`text-[9px] font-bold ${getScoreColor(scores.completeness)}`}>{scores.completeness}/5</span>
            </div>
          </div>
        </div>
        {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/5 p-3 space-y-3"
          >
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <Info size={12} className="text-gray-400" />
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Auditor Reasoning</span>
              </div>
              <p className="text-xs text-gray-300 italic leading-relaxed">"{reasoning}"</p>
            </div>

            {hallucinations_identified && hallucinations_identified.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/20 rounded p-2">
                <div className="text-[10px] font-bold text-red-400 uppercase tracking-tighter mb-1">Hallucinations Detected</div>
                <ul className="list-disc pl-4 space-y-1">
                  {hallucinations_identified.map((h, i) => (
                    <li key={i} className="text-[10px] text-red-300 italic">{h}</li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const StarRating = ({ rating, onRate, readonly = false }) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          onClick={() => !readonly && onRate(star)}
          disabled={readonly}
          className={`transition-all ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'}`}
        >
          <Star
            size={20}
            className={star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-600'}
          />
        </button>
      ))}
    </div>
  )
}

const MessageBubble = ({ message, onSaveAdvice, showSaveButton, matchContext }) => {
  const isUser = message.role === 'user'
  const hasRecommendation = !isUser && (message.content.includes('Recommended:') || message.content.includes('🎯') || message.content.includes('**Recommended') || /\*\*[A-Z][a-z]+\*\*.*-.*Strategic Insight/i.test(message.content))

  // Heroes of the Storm style: player name followed by message
  const playerName = isUser ? 'You' : (message.model || 'Nexus Intelligence')
  const playerNameColor = isUser ? 'text-blue-300' : 'text-cyan-300'
  const playerNameGlow = isUser ? 'drop-shadow-[0_0_4px_rgba(96,165,250,0.6)]' : 'drop-shadow-[0_0_4px_rgba(34,211,238,0.6)]'

  // Don't animate static messages - only animate on first mount
  // Use a ref-like approach: check if message timestamp is recent (within last 2 seconds)
  const isNewMessage = message.timestamp && (Date.now() - new Date(message.timestamp).getTime() < 2000)

  // Agent badge helper
  const getAgentIcon = (agentName) => {
    const icons = {
      'ANALYST': '🔍',
      'SCOUT': '🎯',
      'COACH': '📈',
      'TACTICIAN': '⚔️',
      'SOCIAL': '🤝'
    }
    return icons[agentName] || '🤖'
  }

  return (
    <div className="mb-2 text-sm leading-relaxed relative group">
      {/* Subtle glow effect on hover */}
      <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/0 via-blue-500/0 to-purple-500/0 group-hover:from-cyan-500/10 group-hover:via-blue-500/10 group-hover:to-purple-500/10 rounded-lg blur-xl transition-all duration-300 -z-10"></div>

      {/* Agent Badge */}
      {!isUser && message.agent && (
        <div className="mb-2 flex items-center gap-2 text-xs">
          <span className="flex items-center gap-1.5 px-2 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-md">
            <span>{getAgentIcon(message.agent.name || message.agent)}</span>
            <span className="text-cyan-300 font-medium">{message.agent.name || message.agent}</span>
            {message.agent.role && <span className="text-gray-400">• {message.agent.role}</span>}
          </span>
          {message.orchestrator?.capable_agents?.length > 1 && (
            <span className="text-gray-500 text-[10px]">
              (Also capable: {message.orchestrator.capable_agents.filter(a => a !== message.orchestrator.selected_agent).join(', ')})
            </span>
          )}
        </div>
      )}

      {/* Hide flex gap if no player name is shown (map-only messages) */}
      <div className={`flex items-start ${(message.content || isUser) ? 'gap-2' : ''}`}>
        {/* Hide player name for map-only messages */}
        {(message.content || isUser) && (
          <span className={`${playerNameColor} ${playerNameGlow} font-semibold shrink-0 relative`}>
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12 animate-[shimmer_2s_ease-in-out_infinite] opacity-0 group-hover:opacity-100 transition-opacity"></span>
            <span className="relative">{playerName}:</span>
          </span>
        )}
        <div className="flex-1 text-gray-200 break-words relative">
          {/* Subtle text glow */}
          {(message.content || isUser) && (
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm -z-10"></div>
          )}
          {isUser && message.image && (
            <div className="mb-1">
              <img src={message.image} alt="User Attachment" className="max-h-48 rounded border border-blue-800/50 shadow-lg" />
            </div>
          )}

          {isUser ? (
            <div className="whitespace-pre-wrap select-text">{message.content}</div>
          ) : message.content ? (
            <div className="markdown-content prose prose-sm prose-invert prose-cyan max-w-none font-mono text-sm bg-black/20 py-1.5 px-2.5 rounded-lg border-l-2 border-cyan-500/30 space-y-0.5 select-text">
              <ReactMarkdown
                remarkPlugins={[]}
                rehypePlugins={[]}
                components={{
                  h1: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <div className="text-sm font-semibold mt-2 first:mt-0 mb-1 text-cyan-400"><HeroText text={text} /></div>;
                  },
                  h2: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <div className="text-sm font-semibold mt-1.5 mb-0.5 text-purple-300"><HeroText text={text} /></div>;
                  },
                  h3: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <div className="text-sm font-medium mt-1 mb-0.5 text-purple-200"><HeroText text={text} /></div>;
                  },
                  ul: ({ node, ...props }) => <ul className="list-disc pl-4 my-1 space-y-0.5" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal pl-4 my-1 space-y-0.5" {...props} />,
                  li: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <li className="leading-snug">{renderTacticalContent(text, talentMapData)}</li>;
                  },
                  code: ({ node, inline, className, children, ...props }) => {
                    // Extract text content from ReactMarkdown children
                    let content = '';
                    if (typeof children === 'string') {
                      content = children;
                    } else if (Array.isArray(children)) {
                      content = children.map(c => {
                        if (typeof c === 'string') return c;
                        if (c && typeof c === 'object' && c.props && c.props.children) {
                          return extractText(c.props.children);
                        }
                        return String(c || '');
                      }).join('');
                    } else if (children && typeof children === 'object' && children.props) {
                      content = extractText(children.props.children);
                    } else {
                      content = String(children || '');
                    }

                    // Clean up content - remove any extra whitespace/newlines
                    content = content.trim();

                    // Match standard talent code format: [T1234567,HeroName]
                    // Handle various formats: [T1234567,HeroName], `[T1234567,HeroName]`, etc.
                    // More flexible regex to handle whitespace and different formats
                    const buildCodeMatch = content.match(/\[T(\d{1,7})\s*,\s*([^\]]+)\]/);

                    if (buildCodeMatch) {
                      const [, buildStr, heroName] = buildCodeMatch;
                      const cleanHeroName = heroName.trim().replace(/`/g, ''); // Remove any backticks
                      const cleanBuildStr = buildStr.trim();

                      return (
                        <div className={`${inline ? 'inline-block' : 'my-1 inline-block'} align-middle transform scale-90 origin-left`}>
                          <BuildDisplay
                            hero={cleanHeroName}
                            buildStr={cleanBuildStr}
                            compact={true}
                            source="META"
                            talentMap={talentMapData}
                          />
                        </div>
                      );
                    }

                    return inline
                      ? <code className="bg-black/30 px-1 py-0.5 rounded text-cyan-300 font-mono text-sm" {...props}><HeroText text={content} compact={true} iconSize="w-4 h-4" /></code>
                      : <div className="bg-black/40 rounded-lg p-2 my-1.5 border border-white/10 overflow-x-auto"><code className="text-sm font-mono text-gray-300 block whitespace-pre-wrap break-words" {...props}>{children}</code></div>
                  },
                  p: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <div className="mb-1.5 last:mb-0 leading-snug whitespace-pre-wrap">{renderTacticalContent(text, talentMapData)}</div>;
                  },
                  strong: ({ node, children, ...props }) => {
                    const text = extractText(children);
                    return <strong className="font-bold text-cyan-200"><HeroText text={text} /></strong>;
                  },
                  text: ({ node, children, ...props }) => {
                    // Process text nodes to add hero icons
                    const text = typeof children === 'string' ? children : String(children || '');
                    return <HeroText text={text} />;
                  },
                }}
                skipHtml={false}
              >
                {String(message.content || '').trim()}
              </ReactMarkdown>
            </div>
          ) : null}


          {!isUser && message.showExamples && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {/* Current Map Rotation */}
              {['Alterac Pass', 'Battlefield of Eternity', "Blackheart's Bay", 'Braxis Holdout', 'Cursed Hollow', 'Dragon Shire', 'Garden of Terror', 'Hanamura Temple', 'Infernal Shrines', 'Sky Temple', 'Tomb of the Spider Queen', 'Towers of Doom', 'Volskaya Foundry', 'Warhead Junction'].map(map => (
                <button
                  key={map}
                  onClick={() => message.onExampleClick?.(map)}
                  className="px-2 py-1 bg-blue-900/30 hover:bg-blue-800/40 border border-blue-800/50 hover:border-blue-700/50 rounded text-blue-200 hover:text-blue-100 text-[10px] font-medium transition-all flex items-center gap-1.5"
                >
                  <MapIcon mapName={map} size="xs" className="rounded-sm" />
                  {map}
                </button>
              ))}
            </div>
          )}

          {/* Action Buttons for Recommendations */}
          {hasRecommendation && matchContext && (
            <div className="mt-2 text-right">
              <ActionButtons
                message={message}
                matchId={matchContext.matchId}
                onAction={(actionType, data) => {
                  console.log('Action taken:', actionType, data)
                }}
              />
            </div>
          )}

          {/* Audit Badge for Strategic Insights */}
          {!isUser && message.audit && (
            <AuditBadge audit={message.audit} />
          )}

        </div>
      </div>
    </div>
  )
}

const PendingUpdateCard = ({ update, onConfirm, onReject }) => (
  <motion.div
    initial={{ opacity: 0, y: 20, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    transition={{ duration: 0.3, ease: "easeOut" }}
    className="mx-auto max-w-2xl w-full bg-gradient-to-r from-blue-900/40 via-purple-900/30 to-blue-900/40 border border-cyan-500/50 rounded-xl overflow-hidden shadow-xl shadow-cyan-900/30 mb-6 relative group"
  >
    {/* Animated shimmer background */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-[shimmer_3s_ease-in-out_infinite]"></div>

    {/* Glowing border effect */}
    <div className="absolute inset-0 rounded-xl border-2 border-cyan-400/0 group-hover:border-cyan-400/40 transition-all duration-500 pointer-events-none"></div>

    <div className="bg-gradient-to-r from-cyan-900/30 via-blue-900/20 to-purple-900/30 p-3 border-b border-cyan-500/40 flex items-center gap-2 relative z-10">
      <Sparkles size={16} className="text-cyan-300 drop-shadow-[0_0_4px_rgba(34,211,238,0.8)] animate-pulse" />
      <span className="text-sm font-bold text-cyan-200 drop-shadow-[0_0_4px_rgba(34,211,238,0.5)]">Database Update Request</span>
    </div>
    <div className="p-5">
      <div className="text-lg font-bold text-white mb-1">
        {update.action === 'update_rules'
          ? (update.data.type === 'warning' ? 'Add Pre-Game Warning' : (update.data.type === 'win_condition' ? 'Set Win Condition' : 'Add Strategic Note'))
          : (update.action === 'update_primary' ? 'Set Primary Hero' : 'Add Backup Hero')}
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
        on <span className="text-cyan-300 bg-cyan-900/30 px-2 py-0.5 rounded">{update.map}</span>
      </div>

      {update.action === 'update_rules' ? (
        <div className={`bg-black/20 p-3 rounded-lg border mb-6 ${update.data.type === 'warning' ? 'border-red-500/30' : 'border-white/5'}`}>
          <div className={`text-xs uppercase tracking-wider mb-1 ${update.data.type === 'warning' ? 'text-red-400' : 'text-gray-500'}`}>
            {update.data.type === 'warning' ? '⚠️ WARNING' : (update.data.type === 'win_condition' ? '🏆 WIN CONDITION' : 'NOTE')}
          </div>
          <div className="font-medium text-white italic">"{update.data.rule}"</div>
        </div>
      ) : (
        <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm mb-6 bg-black/20 p-3 rounded-lg border border-white/5">
          <div className="text-gray-500">Hero:</div>
          <div className="font-medium text-white">{update.data.name}</div>

          <div className="text-gray-500">Role:</div>
          <div className="font-medium text-purple-300">{update.data.role}</div>

          <div className="text-gray-500">Note:</div>
          <div className="italic text-gray-300">{update.data.note || 'Not specified'}</div>
        </div>
      )}

      <div className="flex gap-3 relative z-10">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onReject}
          className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-gray-800/40 to-gray-900/40 hover:from-red-900/40 hover:to-red-800/40 text-gray-300 hover:text-red-300 font-medium transition-all border border-gray-700/50 hover:border-red-500/50 shadow-md hover:shadow-lg"
        >
          Cancel
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onConfirm}
          className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 hover:from-cyan-500 hover:via-blue-500 hover:to-purple-500 text-white font-bold transition-all shadow-lg shadow-cyan-900/40 hover:shadow-xl hover:shadow-cyan-900/60 relative overflow-hidden group"
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12 opacity-0 group-hover:opacity-100 group-hover:animate-[shimmer_1.5s_ease-in-out_infinite]"></div>
          <span className="relative z-10 drop-shadow-[0_0_4px_rgba(0,0,0,0.5)]">Confirm Update</span>
        </motion.button>
      </div>
    </div>
  </motion.div>
)

const LoadingIndicator = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="flex items-center gap-3 mb-6 ml-3 p-3 rounded-lg bg-black/20 w-fit border border-white/5"
  >
    <div className="flex gap-1 h-3 items-end">
      <motion.div
        className="w-1 bg-cyan-500 animate-process-wave"
        style={{ height: '100%', animationDelay: '0s' }}
      />
      <motion.div
        className="w-1 bg-cyan-400 animate-process-wave"
        style={{ height: '80%', animationDelay: '0.1s' }}
      />
      <motion.div
        className="w-1 bg-cyan-300 animate-process-wave"
        style={{ height: '60%', animationDelay: '0.2s' }}
      />
      <motion.div
        className="w-1 bg-purple-500 animate-process-wave"
        style={{ height: '80%', animationDelay: '0.3s' }}
      />
      <motion.div
        className="w-1 bg-blue-500 animate-process-wave"
        style={{ height: '100%', animationDelay: '0.4s' }}
      />
    </div>
    <span className="text-xs font-bold text-cyan-300 animate-pulse tracking-widest uppercase">Processing Tactical Data...</span>
  </motion.div>
)

// --- Main Component ---

export default function UnifiedChat({
  matches = [],
  heroes = [],
  strategies = {},
  onStrategyUpdate,
  selectedHeroes = [],
  onExcludeHeroes,
  queryContext,
  onQueryContextClear,
  isMaximized,
  onToggleMaximize,
  showMaximizeControl = true,
  onShowMatchStats,
  profile,
  // Site Context Props
  viewMode,
  activeMatch
}) {
  // Debug Props
  useEffect(() => {
    // console.log('UnifiedChat mounted with:', { matches: matches?.length, heroes: heroes?.length, strategies })
  }, [matches, heroes, strategies])

  const SYSTEM_PROMPT = getSystemPrompt(profile);

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzingImage, setAnalyzingImage] = useState(false)
  const [pendingUpdate, setPendingUpdate] = useState(null)
  const [pendingFile, setPendingFile] = useState(null)
  const [inputImage, setInputImage] = useState(null)
  const [isInputExpanded, setIsInputExpanded] = useState(false)
  const [savedAdviceId, setSavedAdviceId] = useState(null)
  const [showFeedbackUI, setShowFeedbackUI] = useState(false)
  const [feedbackRating, setFeedbackRating] = useState(0)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [adviceStats, setAdviceStats] = useState(null)
  // const [activeMatchStats, setActiveMatchStats] = useState(null) // MOVED TO APP
  const [lastReplayResult, setLastReplayResult] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [matchContext, setMatchContext] = useState({ matchId: null, hero: null, map: null })
  const [linkState, setLinkState] = useState('Nexus Intelligence')
  const [lastUsage, setLastUsage] = useState(null)
  const [globalUsage, setGlobalUsage] = useState(null)
  const [agentMode, setAgentMode] = useState('multi') // 'single' or 'multi'

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  const handleFile = (file) => {
    if (!file) return

    setIsInputExpanded(false) // Collapse if full screen

    // Handle File Preview
    if (file.type.startsWith('image/')) {
      const previewUrl = URL.createObjectURL(file)
      setInputImage(previewUrl)
    } else {
      setInputImage(null)
    }
    setPendingFile(file)

    // Focus the input to encourage typing a prompt
    setTimeout(() => textareaRef.current?.focus(), 100)
  }

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    handleFile(file)
    // Reset file input so same file can be selected again if cancelled
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set to false if we're leaving the actual container
    if (e.relatedTarget === null || !e.currentTarget.contains(e.relatedTarget)) {
      setIsDragging(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (typeof document !== 'undefined' && document.getSelection?.()?.toString?.()) return
    scrollToBottom()
  }, [messages, pendingUpdate, loading])

  // --- Match History Logic ---
  const [showHistory, setShowHistory] = useState(false)
  const [matchHistory, setMatchHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  const fetchMatchHistory = async () => {
    setLoadingHistory(true)
    try {
      const res = await fetch('/api/match_history?limit=20')
      if (res.ok) {
        let history = await res.json()
        setMatchHistory(history.reverse()) // Newest first
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingHistory(false)
    }
  }

  const loadMatchFromHistory = (match) => {
    setShowHistory(false)
    // Synchronize global match context so agents know which match we are discussing
    if (onShowMatchStats) onShowMatchStats(match)

    let replayMarkdown = `### 🎬 Archive Loaded: ${match.map} (${match.result})\n`
    if (match.analysis.verdict) {
      const color = match.analysis.verdict.toUpperCase().includes('WIN') ? 'text-green-400' : 'text-red-400'
      replayMarkdown += `> **VERDICT**: ${match.analysis.verdict}\n\n`
    }
    if (match.analysis.the_good) replayMarkdown += `**✅ The Good**:\n${match.analysis.the_good}\n\n`
    if (match.analysis.the_bad) replayMarkdown += `**❌ The Bad**:\n${match.analysis.the_bad}\n\n`
    if (match.analysis.next_step) replayMarkdown += `**🚀 Next Step**:\n${match.analysis.next_step}\n`

    setMessages(prev => [...prev, { role: 'assistant', content: replayMarkdown }])
  }

  useEffect(() => {
    if (showHistory) fetchMatchHistory()
  }, [showHistory])

  // Initialize chat with map buttons only
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: '', // No welcome text, just map buttons
        showExamples: true
      }])
    }
  }, []) // Run only once on mount


  // --- Auto-resize ---
  useLayoutEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
      textarea.style.overflowY = textarea.scrollHeight > 200 ? 'auto' : 'hidden'
    }
  }, [input])

  // Context Auto-Fill
  useEffect(() => {
    if (queryContext) {
      let contextStr = ''
      if (queryContext.text) {
        contextStr = queryContext.text
      } else if (queryContext.type === 'map') {
        contextStr = `Tell me about ${queryContext.item} strategy`
      } else if (queryContext.type === 'hero') {
        contextStr = queryContext.map
          ? `Tell me about ${queryContext.item} on ${queryContext.map}`
          : `Tell me about ${queryContext.item}`
      } else if (queryContext.type === 'match') {
        const player = queryContext.match?.players?.[0]
        contextStr = `Analyze this match on ${queryContext.map || 'Unknown map'}`
      }
      setInput(contextStr)
      // Focus textarea
      setTimeout(() => textareaRef.current?.focus(), 100)
    }
  }, [queryContext])

  const detectIntent = async (message) => {
    const urlMatch = message.match(/https?:\/\/[^\s]+/i)
    if (urlMatch) return 'SCRAPE_URL'

    const lower = message.toLowerCase().trim()
    const questionPatterns = /\b(what|who|which|how|when|should i|can i|could you|recommend|suggest|advice|tips|best|strategy for|playing as|when playing)\b/i
    const isQuestion = questionPatterns.test(lower)
    if (isQuestion) return 'QUESTION'

    const commandKeywords = ['add', 'set', 'remove', 'update', 'change', 'create', 'rule', 'validation', 'condition', 'prioritize', 'unban', 'stop playing']
    const hasCommandKeyword = commandKeywords.some(k => lower.includes(k))
    const imperativeBan = /^ban\s+\w+|^\s*ban\s+[\w\s]+$/i.test(lower) || /\b(ban|add to ban|put on ban)\s+(me\s+)?[\w\s]+/i.test(lower)
    if (hasCommandKeyword || imperativeBan) return 'COMMAND'
    return 'QUESTION'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getPlaceholder = () => {
    if (pendingFile) {
      return pendingFile.type?.startsWith('image/')
        ? 'Ready to analyze screenshot...'
        : 'Ready to analyze replay...'
    }
    if (queryContext) {
      return `Ask about ${queryContext.item}...`
    }
    return 'Ask for stats or update strategies...'
  }

  const sendMessage = async () => {
    if ((!input.trim() && !pendingFile) || loading) return

    // User Message
    const isImage = pendingFile?.type?.startsWith('image/')
    const defaultText = isImage ? "Analyze this screenshot" : "Analyze this replay"
    const userMessage = { role: 'user', content: input || (pendingFile ? defaultText : "") }
    if (pendingFile) userMessage.image = inputImage

    setMessages(prev => [...prev, userMessage])

    const userInput = input
    const fileToUpload = pendingFile // capture ref

    setInput('')
    setInputImage(null) // Clear image input
    setPendingFile(null)
    setLoading(true)
    setIsInputExpanded(false) // Auto-collapse on send
    setPendingUpdate(null)

    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      // 1. REPLAY ANALYSIS (FILE)
      if (fileToUpload && (fileToUpload.name.endsWith('.StormReplay') || fileToUpload.name.endsWith('.json'))) {

        let response;

        // Legacy/Debug JSON Support
        if (fileToUpload.name.endsWith('.json')) {
          const text = await fileToUpload.text();
          response = await fetch('/api/analyze_replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: text
          });
        } else {
          // BINARY REPLAY UPLOAD
          const formData = new FormData();
          formData.append('file', fileToUpload);

          response = await fetch('/api/analyze_replay', {
            method: 'POST',
            body: formData
          });
        }

        const data = await response.json()
        if (data.error) throw new Error(data.error)

        // Store replay result for Learning Coach
        const gameResult = data.verdict?.toUpperCase().includes('WIN') ? 'WIN' : 'LOSS'
        setLastReplayResult({ result: gameResult, map: data.map, hero: data.hero })

        // Format Replay Analysis
        let replayMarkdown = `### 🎬 Replay Analysis: ${data.map || 'Unknown Map'}\n`

        if (data.verdict) {
          const color = data.verdict.toUpperCase().includes('WIN') ? 'text-green-400' : 'text-red-400'
          replayMarkdown += `> **VERDICT**: ${data.verdict}\n\n`
        }

        if (data.the_good) replayMarkdown += `**✅ The Good**:\n${data.the_good}\n\n`
        if (data.the_bad) replayMarkdown += `**❌ The Bad**:\n${data.the_bad}\n\n`
        if (data.next_step) replayMarkdown += `**🚀 Next Step**:\n${data.next_step}\n`

        if (data.is_duplicate) {
          replayMarkdown = `> 💾 **LOADED FROM LIBRARY**\n\n` + replayMarkdown;
        }

        setMessages(prev => [...prev, {
          role: 'assistant',
          content: replayMarkdown,
          model: data.link_quality || 'Nexus Analysis'
        }])

        // Refresh match history after successful parse
        // Trigger a custom event that App.jsx can listen to
        window.dispatchEvent(new CustomEvent('replayParsed', { detail: { matchId: data.id } }))

        // Show feedback UI if there's saved advice
        if (savedAdviceId) {
          setShowFeedbackUI(true)
        }

        return
      }

      // 2. VISION ANALYSIS (IMAGE)
      else if (fileToUpload) {
        setAnalyzingImage(true)
        const formData = new FormData()
        formData.append('image', fileToUpload)
        if (userInput.trim()) formData.append('prompt', userInput) // Send user prompt if exists

        const response = await fetch('/api/analyze_image', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        setAnalyzingImage(false);

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n");
          buffer = parts.pop(); // Keep last incomplete chunk

          for (const part of parts) {
            if (!part.trim()) continue;
            try {
              const data = JSON.parse(part);
              if (data.error) throw new Error(data.error);

              const analysis = data.analysis || {};
              const directAnswer = analysis.direct_answer;

              if (directAnswer) {
                // Determine if we should append to last assistant message or create new one
                setMessages(prev => {
                  const lastMsg = prev[prev.length - 1];
                  // If last message is from assistant and it was a fast_path, maybe we append?
                  // Better to append to the SAME message if it's the same request
                  // For simplicity, we can just add a new message or update the last one if it's from this stream.

                  // Simple approach: Add to content if it's a follow-up step
                  if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
                    return [...prev.slice(0, -1), {
                      ...lastMsg,
                      content: lastMsg.content + "\n\n---\n\n" + directAnswer,
                      model: data.link_quality || lastMsg.model
                    }];
                  } else {
                    return [...prev, {
                      role: 'assistant',
                      content: directAnswer,
                      model: data.link_quality || (data.step === 'fast_path' ? 'Local Cache' : 'Gemini Vision'),
                      isStreaming: true
                    }];
                  }
                });
              }
            } catch (err) {
              console.error("Error parsing NDJSON chunk:", err, part);
            }
          }
        }

        // Finalize streaming state
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.isStreaming) {
            return [...prev.slice(0, -1), { ...lastMsg, isStreaming: false }];
          }
          return prev;
        });

        return

      }

      // ELSE -> Use Text Chat Endpoint
      const intent = await detectIntent(userInput)

      if (intent === 'COMMAND') {
        await handleCommand(userInput)
      } else {
        await handleQuestion(userInput)
      }

    } catch (error) {
      setAnalyzingImage(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ **System Error**: ${error.message}`
      }])
    } finally {
      setLoading(false)
      if (onQueryContextClear) onQueryContextClear()
    }
  }

  const [updateQueue, setUpdateQueue] = useState([])

  // Queue Processor
  useEffect(() => {
    if (!pendingUpdate && updateQueue.length > 0) {
      // Pop the next update from queue
      const [nextUpdate, ...remaining] = updateQueue
      setPendingUpdate(nextUpdate)
      setUpdateQueue(remaining)
    }
  }, [pendingUpdate, updateQueue])

  const handleCommand = async (userInput) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `${SYSTEM_PROMPT}\n\nUser request: ${userInput}\n\nOutput ONLY the JSON object (or Array of objects), no other text:`,
        context: {
          strategies: Object.keys(strategies || {}),
          viewMode,
          selectedMatch: activeMatch
        }
      })
    })
    const data = await response.json()
    if (data.link_quality) setLinkState(data.link_quality)
    const jsonMatch = data.response.match(/\[\s*\{[\s\S]*\}\s*\]|\{\s*[\s\S]*\}/) // Match Object OR Array

    if (jsonMatch) {
      let parsedData
      try {
        parsedData = JSON.parse(jsonMatch[0])
      } catch (e) {
        throw new Error('Failed to parse (Invalid JSON)')
      }

      // Normalize to array
      const updates = Array.isArray(parsedData) ? parsedData : [parsedData]

      const validUpdates = []

      for (const updateData of updates) {
        // Handle new tool schema (Roster) - direct execute
        if (updateData.tool === 'update_roster') {
          await handleRosterUpdate(updateData)
          continue
        }

        // Handle Strategy Updates - Queue them
        if ((updateData.tool === 'update_strategy' || updateData.action) && updateData.map && updateData.data) {
          validUpdates.push(updateData)
        }
      }

      if (validUpdates.length > 0) {
        setUpdateQueue(prev => [...prev, ...validUpdates])
      }

    } else {
      // ... error logging ...
      try {
        await fetch('/api/logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'COMMAND_PARSE_ERROR',
            message: "Failed to parse JSON from AI response",
            context: { userInput, aiResponse: data.response }
          })
        })
      } catch (e) { }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "⚠️ **Processing Error.** Unrecognized command syntax. Refine parameters.",
        model: 'Nexus Intelligence'
      }])
    }
  }

  const handleRosterUpdate = async (updateData) => {
    try {
      await fetch('/api/roster-constraints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ **Roster Protocol Updated**: ${updateData.action === 'ban' ? 'NEUTRALIZE' : 'PRIORITIZE'} Directive set for ${updateData.hero}`
      }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Roster update failed: ${e.message}` }])
    }
  }

  const handleAgentQuery = async (userInput) => {
    // Route query to multi-agent system
    try {
      const response = await fetch('/api/cerebrate/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userInput,
          context: {
            viewMode,
            selectedMatch: activeMatch
          }
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ API Error (${response.status}): ${errorText.substring(0, 200)}`
        }])
        return
      }

      const data = await response.json()
      if (data.link_quality) setLinkState(data.link_quality)
      if (data.usage) setLastUsage(data.usage)
      if (data.global_usage) setGlobalUsage(data.global_usage)

      // Format agent response
      let content = data.response || data.error || data.message;

      // Try to extract a formatted response if no direct 'response' field exists
      if (!content && data.analysis_type) {
        content = formatAgentResponse(data)
      } else if (!content) {
        content = JSON.stringify(data, null, 2);
      }

      // Sanitize: jargon → plain language, collapse duplicate hero names
      const sanitized = typeof content === 'string' ? sanitizeChatResponse(content) : content
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: sanitized,
        agent: data.agent,
        orchestrator: data.orchestrator,
        model: data.agent?.name || 'Cerebrate',
        audit: data.audit
      }])
    } catch (error) {
      console.error('Agent Query Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Error: ${error.message}`
      }])
    }
  }

  const formatAgentResponse = (data) => {
    // If agent already provided a formatted response, use it
    if (data.response) return data.response;

    // Format different agent response types
    if (data.analysis_type === 'hero_improvement' || data.analysis_type === 'overall_improvement') {
      const { hero, weaknesses, strengths, roadmap, current_stats, improvement_areas, common_mistakes, trend } = data;
      const title = hero ? `${hero} Development Roadmap` : 'Strategic Improvement Roadmap';
      let content = `## ${title}\n\n`;

      if (trend) {
        const direction = trend.direction === 'improving' ? '📈' : trend.direction === 'declining' ? '📉' : '📊';
        content += `**Performance Trend**: ${direction} ${trend.direction.toUpperCase()} (${trend.change > 0 ? '+' : ''}${trend.change?.toFixed(1)}% WR Change)\n\n`;
      }

      if (current_stats) {
        content += `**Vitals:**\n- Lifetime WR: **${current_stats.lifetime_wr?.toFixed(1)}%**\n- Season WR: **${current_stats.season_wr?.toFixed(1)}%**\n- Combat Records: ${current_stats.games_played} games\n\n`;
      }

      const mistakes = weaknesses || common_mistakes;
      if (mistakes?.length > 0) {
        content += `**Critical Weaknesses / Common Mistakes:**\n`;
        mistakes.forEach(m => {
          content += `- **${m.area || m.mistake}**: ${m.description}\n  → *Action*: ${m.action}\n`;
        });
        content += '\n';
      }

      const areas = strengths || improvement_areas;
      if (areas?.length > 0) {
        content += `**High-Value Strengths / Focus Areas:**\n`;
        areas.forEach(a => {
          content += `- **${a.area}**: ${a.description}\n`;
        });
        content += '\n';
      }

      if (roadmap?.length > 0) {
        content += `### 🚀 Actionable Roadmap\n`;
        roadmap.forEach(r => {
          const priority = r.priority === 'high' || r.priority === 'critical' ? '🔴' : r.priority === 'medium' ? '🟡' : '🟢';
          content += `${priority} **${r.task}**\n   *Area: ${r.area} | Timeline: ${r.timeline}*\n\n`;
        });
      }
      return content;
    }

    if (data.analysis_type === 'draft_recommendation') {
      const { map, role, context, recommendations } = data;
      const title = map ? `Draft Intel: ${map}` : 'Strategic Draft Recommendations';
      let content = `## ${title} ${role ? `(${role})` : ''}\n`;
      content += `*Link Status: ${context}*\n\n`;

      if (recommendations?.length > 0) {
        content += `### 🎯 Optimal Deployments\n`;
        recommendations.forEach(r => {
          if (r.role && r.heroes) {
            // Map-specific recommendations (grouped by role)
            content += `**${r.role}**:\n`;
            r.heroes.forEach(h => content += `- ${h}\n`);
          } else {
            // Hero-specific recommendations
            const heroName = r.hero || r;
            const stats = r.wr ? ` (${r.wr}% WR, ${r.games}g)` : '';
            content += `- **${heroName}**${stats}${r.role ? ` [${r.role}]` : ''}\n`;
          }
        });
      }
      return content;
    }

    if (data.analysis_type === 'match_analysis') {
      const { hero, map, result, analysis } = data;
      const emoji = result === 'WIN' ? '🏆' : '💀';
      let content = `## ${emoji} ${hero} ${result} — ${map}\n\n`;

      if (analysis) {
        content += `**Verdict:** ${analysis.verdict}\n\n`;
        if (analysis.summary) content += `**Neural Summary:** ${analysis.summary}\n\n`;
        if (analysis.critical_mistake) content += `**🔴 Critical Mistake:** ${analysis.critical_mistake}\n\n`;
        if (analysis.win_condition) content += `**🏆 Win Condition:** ${analysis.win_condition}\n\n`;
        if (analysis.tactical_breakdown) content += `**⚙️ Tactical Breakdown:**\n${analysis.tactical_breakdown}\n\n`;

        if (analysis.follow_up_questions?.length > 0) {
          content += `**Follow-up Directives:**\n${analysis.follow_up_questions.map(q => `- ${q}`).join('\n')}`;
        }
      }
      return content;
    }

    if (data.analysis_type === 'map_specific_analysis') {
      const { map, analysis } = data;
      let content = `## 🗺️ ${map} Strategic Intelligence\n\n`;

      if (analysis) {
        if (analysis.map_specific_metrics) {
          content += `**Diagnostic Matrices (Map Specific):**\n`;
          Object.entries(analysis.map_specific_metrics).forEach(([key, value]) => {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            content += `- **${label}**: ${value}\n`;
          });
          content += '\n';
        }

        if (analysis.summary) content += `**Neural Summary:** ${analysis.summary}\n\n`;
        if (analysis.critical_mistake) content += `**🔴 Critical Mistake:** ${analysis.critical_mistake}\n\n`;
        if (analysis.win_condition) content += `**🏆 Win Condition:** ${analysis.win_condition}\n\n`;

        if (analysis.tactical_advice?.length > 0) {
          content += `**⚙️ Tactical Directives:**\n${analysis.tactical_advice.map(q => `- ${q}`).join('\n')}\n\n`;
        }
      }
      return content;
    }

    if (data.analysis_type === 'social_network' || data.analysis_type === 'player_analysis') {
      const { strong_allies, nemeses, recommendations, player_name, relationship, stats, recommendation, ai_strategy } = data;
      const title = player_name ? `Combat Profile: ${player_name}` : 'Social Network Analytics';
      let content = `## ${title}\n\n`;

      if (relationship) {
        const relEmoji = relationship.includes('ally') ? '🤝' : relationship.includes('nemesis') ? '☢️' : '👤';
        content += `**Intelligence Status**: ${relEmoji} ${relationship.replace('_', ' ').toUpperCase()}\n`;
        if (stats) {
          content += `- Performance With: **${stats.with.win_rate.toFixed(1)}% WR** (${stats.with.total} games)\n`;
          content += `- Performance Against: **${stats.against.win_rate.toFixed(1)}% WR** (${stats.against.total} games)\n\n`;
        }
        if (recommendation) content += `**Neural Directive**: ${recommendation}\n\n`;
        if (ai_strategy) content += `**Tactical Counter**: ${ai_strategy}\n\n`;
      }

      if (strong_allies?.length > 0) {
        content += `### 🤝 High-Synergy Assets (Allies)\n`;
        content += strong_allies.map(a => `- **${a.name}**: ${a.win_rate.toFixed(1)}% WR (${a.games} games)`).join('\n') + '\n\n';
      }
      if (nemeses?.length > 0) {
        content += `### ☢️ High-Threat Identification (Nemeses)\n`;
        content += nemeses.map(n => `- **${n.name}**: ${n.win_rate.toFixed(1)}% WR against (${n.games} games)`).join('\n') + '\n\n';
      }
      if (recommendations?.length > 0) {
        content += `### 💡 Strategic Advice\n`;
        content += recommendations.map(r => `- ${r}`).join('\n');
      }
      return content;
    }

    if (data.analysis_type === 'quick_strategy_summary') {
      const { map, analysis } = data;
      let content = `## ${map} Tactical Overview\n`;
      content += `*Directives from STATIC_VERIFIED intelligence.*\n\n`;

      if (analysis) {
        if (analysis.win_condition) content += `**🏆 Win Condition:** ${analysis.win_condition}\n\n`;
        if (analysis.critical_objective) content += `**🎯 Critical Objective:** ${analysis.critical_objective}\n`;
        if (analysis.key_timings) content += `**🕒 Key Timings:** ${analysis.key_timings}\n`;
        if (analysis.macro_priority) content += `**⚙️ Macro Priority:** ${analysis.macro_priority}\n`;
        if (analysis.draft_focus) content += `**👥 Draft Focus:** ${analysis.draft_focus}\n`;
      }
      return content;
    }

    // Fallback to JSON if no specific formatter
    return "```json\n" + JSON.stringify(data, null, 2) + "\n```";
  }

  const handleQuestion = async (userInput) => {
    // Use multi-agent system if in agent mode
    if (agentMode === 'multi') {
      await handleAgentQuery(userInput)
      return
    }

    // Check exclusion logic first
    const exclusionKeywords = ["don't play", "dont play", "never play", "exclude"]
    if (exclusionKeywords.some(k => userInput.toLowerCase().includes(k))) {
      // ... (Reuse exclusion logic from before or simplify)
      // For speed, let's just do a simple pass-through to AI for now, or assume this is handled
      // Simplifying for this rewrite to focus on UI
    }

    // Load recent match history from backend with summary analysis
    let recentMatches = []
    let latestMatch = null
    try {
      const historyRes = await fetch('/api/match_history?limit=10')
      if (historyRes.ok) {
        const history = await historyRes.json()
        recentMatches = history.slice(-5).map(m => ({
          map: m.map,
          hero: m.hero,
          result: m.result,
          date: m.date || m.timestamp_iso,
          // Include full analysis for detailed coaching responses
          analysis: m.analysis ? {
            verdict: m.analysis.verdict,
            summary: m.analysis.summary,
            key_insights: m.analysis.key_insights,
            critical_mistake: m.analysis.critical_mistake,
            win_condition: m.analysis.win_condition || m.analysis.win_condition_analysis,
            tactical_breakdown: m.analysis.tactical_breakdown || m.analysis.areas_for_improvement
          } : null,
          // Include player stats for detailed breakdowns
          players: m.players || []
        }))
        latestMatch = recentMatches[0] || null
      }
    } catch (e) {
      console.warn('Could not load match history:', e)
    }

    // Detect if user is asking about a specific match (including casual phrases)
    const lowerInput = userInput.toLowerCase()
    const matchKeywords = [
      'brightwing', 'tomb', 'game', 'match', 'replay', 'crushed', 'lost', 'won',
      'how did i do', 'how did i play', 'analyze', 'breakdown', 'stats',
      'performance', 'that match', 'last match', 'recent match'
    ]
    const isMatchQuery = matchKeywords.some(k => lowerInput.includes(k))

    if (isMatchQuery && recentMatches.length > 0) {
      // Find the most relevant match
      const relevantMatch = recentMatches.find(m =>
        lowerInput.includes(m.hero?.toLowerCase()) ||
        lowerInput.includes(normalizeHeroName(m.hero)) ||
        lowerInput.includes(m.map?.toLowerCase())
      ) || recentMatches[0] // Default to most recent

      // Fetch specific match data via ID for precision
      try {
        const matchId = relevantMatch.id;
        const fullHistoryRes = await fetch(`/api/match_history?limit=1&offset=0&id=${matchId}`)
        if (fullHistoryRes.ok) {
          const matchData = await fullHistoryRes.json()
          const matched = matchData[0]
          if (matched) {
            recentMatches = [matched] // Focus context on this specific match
            if (onShowMatchStats) onShowMatchStats(matched)
          }
        }
      } catch (e) {
        console.warn('Could not load full match data:', e)
      }
    }


    const context = {
      totalMatches: matches?.length || 0,
      heroes: heroes?.slice(0, 10).map(h => ({ name: h.hero, winRate: h.win_rate })) || [],
      strategies: Object.keys(strategies || {}),
      recentMatches,
      query: queryContext,
      viewMode,
      selectedMatch: activeMatch,
      map: matchContext.map // Add map from matchContext for map expert routing
    }

    // Enhance prompt for match analysis queries
    let enhancedMessage = userInput
    if (isMatchQuery && latestMatch) {
      const match = latestMatch
      const userPlayer = match.players?.find(p =>
        p.name === 'Discerning' ||
        p.name === 'CerebrateUser' ||
        p.name?.toLowerCase().includes('cerebrate') ||
        p.name?.toLowerCase().includes('player') ||
        p.is_user ||
        p.hero === match.hero
      ) || match.players?.[0]

      const stats = userPlayer?.stats || {}
      enhancedMessage = `**MATCH ANALYSIS REQUEST**

User Query: "${userInput}"

**Latest Match Context:**
- Hero: ${match.hero || 'Unknown'}
- Map: ${match.map || 'Unknown'}
- Result: ${match.result || 'Unknown'}
- Date: ${match.date || match.timestamp_iso || 'Unknown'}

**Your Stats:**
- K/D/A: ${stats.Kills || 0}/${stats.Deaths || 0}/${stats.Assists || 0}
- Hero Damage: ${stats.HeroDamage?.toLocaleString() || 0}
- Siege Damage: ${stats.SiegeDamage?.toLocaleString() || 0}
- XP Contribution: ${stats.ExperienceContribution?.toLocaleString() || 0}
- Minion XP: ${stats.MinionXP?.toLocaleString() || 'N/A'}

**Match Analysis:**
${match.analysis ? `
- Verdict: ${match.analysis.verdict || 'N/A'}
- Summary: ${match.analysis.summary || 'N/A'}
- Critical Mistake: ${match.analysis.critical_mistake || 'N/A'}
- Win Condition: ${match.analysis.win_condition || 'N/A'}
- Key Insights: ${JSON.stringify(match.analysis.key_insights || {})}
` : 'No analysis available yet.'}

**INSTRUCTION:** Provide a DETAILED analytical breakdown following the format specified in your system prompt. Include:
1. Verdict and overall assessment
2. What went well (with specific stats/metrics)
3. What went wrong (if loss, with context)
4. Strategic analysis (why decisions worked/failed)
5. Key stats breakdown
6. Actionable takeaways

${queryContext ? `\n[Additional Context: ${JSON.stringify(queryContext)}]` : ''}`
    } else {
      enhancedMessage = queryContext ? `[Context: ${JSON.stringify(queryContext)}]\n\n${userInput}` : userInput
    }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: enhancedMessage,
          context: { ...context, latestMatch }
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Chat API Error:', response.status, errorText)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ API Error (${response.status}): ${errorText.substring(0, 200)}`
        }])
        return
      }

      const data = await response.json()
      if (data.link_quality) setLinkState(data.link_quality)
      if (data.usage) setLastUsage(data.usage)
      if (data.global_usage) setGlobalUsage(data.global_usage)

      if (!data.response || !data.response.trim()) {
        setMessages(prev => [...prev, { role: 'assistant', content: "⚠️ **Telemetry Interrupted.** Signal loss detected. Please restate directive." }])
      } else {
        const sanitized = sanitizeChatResponse(data.response)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: sanitized,
          model: data.link_quality || 'Cerebrate'
        }])
      }
    } catch (error) {
      console.error('Chat Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Error: ${error.message}`
      }])
    }
  }

  // Learning Coach Functions
  const saveAdvice = async (message) => {
    try {
      const response = await fetch('/api/save_advice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context: { map: queryContext?.item || 'Unknown' },
          advice_given: { content: message.content }
        })
      })
      const data = await response.json()
      if (data.advice_id) {
        setSavedAdviceId(data.advice_id)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ **Directive Cached.** Tracking outcome efficiency. Connect replay to validate.`
        }])
      }
    } catch (error) {
      console.error('Failed to save advice:', error)
    }
  }

  const linkReplayToAdvice = async (followed) => {
    if (!savedAdviceId || !lastReplayResult) return

    try {
      await fetch('/api/link_replay_to_advice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          advice_id: savedAdviceId,
          followed,
          result: lastReplayResult.result,
          hero: lastReplayResult.hero,
          map: lastReplayResult.map
        })
      })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `📊 **Outcome Logged.** ${followed ? 'Directive followed.' : 'Deviation recorded.'} Analyzing impact on win rate.`
      }])
    } catch (error) {
      console.error('Failed to link replay:', error)
    }
  }

  const submitFeedback = async () => {
    if (!savedAdviceId || feedbackRating === 0) return

    try {
      await fetch('/api/submit_feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          advice_id: savedAdviceId,
          rating: feedbackRating,
          comment: feedbackComment
        })
      })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⭐ **Feedback Integrated.** (${feedbackRating}/5) Neural weights adjusted for future synthesis.`
      }])
      // Reset feedback state
      setShowFeedbackUI(false)
      setSavedAdviceId(null)
      setFeedbackRating(0)
      setFeedbackComment('')
      setLastReplayResult(null)
      // Fetch updated stats
      fetchAdviceStats()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  const fetchAdviceStats = async () => {
    try {
      const response = await fetch('/api/advice_stats')
      const data = await response.json()
      setAdviceStats(data)
    } catch (error) {
      console.error('Failed to fetch advice stats:', error)
    }
  }

  const confirmUpdate = async () => {
    try {
      const response = await fetch('/api/strategies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pendingUpdate)
      })
      if (!response.ok) throw new Error('API Error')

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ **Database Update Confirmed**: ${pendingUpdate.action === 'update_rules' ? 'Tactical note logged' : 'Strategy matrix updated'} for ${pendingUpdate.map}.`
      }])
      setPendingUpdate(null)
      if (onStrategyUpdate) await onStrategyUpdate()
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Update failed: ${e.message}` }])
    }
  }

  // Handler for map button clicks
  const handleMapClick = (mapName) => {
    setMatchContext(prev => ({ ...prev, map: mapName }))
    setInput(`What should I pick for ${mapName}?`)
    setTimeout(() => textareaRef.current?.focus(), 100)
  }

  return (
    <div
      className="h-full bg-slate-950/50 backdrop-blur-sm flex flex-col relative overflow-hidden"
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag and Drop Overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-md-primary/20 backdrop-blur-sm border-4 border-dashed border-md-primary flex items-center justify-center pointer-events-none"
          >
            <div className="bg-md-surface-container p-8 rounded-2xl shadow-2xl flex flex-col items-center gap-4">
              <UploadCloud size={64} className="text-md-primary animate-bounce" />
              <div className="text-xl font-bold text-md-on-surface">Drop Tactical Intel Here</div>
              <div className="text-sm text-md-on-surface-variant">Screenshots or StormReplay files</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="p-4 border-b border-cyan-500/20 flex justify-between items-center bg-slate-900/80 backdrop-blur-md shadow-lg shadow-cyan-900/10 sticky top-0 z-10 select-none">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${linkState.includes('Nexus') ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : linkState.includes('Neural') ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]' : 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]'} animate-pulse`} />
            <h2 className="font-bold text-xs tracking-widest text-md-on-surface-variant flex items-center gap-2 uppercase">
              {linkState.toUpperCase()}
              {loading && <span className="text-[10px] animate-pulse">(PROCESSING...)</span>}
            </h2>
          </div>
          <div className="flex items-center gap-2 border-l border-md-outline-variant/30 pl-4">
            <span className="text-xs text-md-on-surface-variant">Mode:</span>
            <button
              onClick={() => setAgentMode(agentMode === 'multi' ? 'single' : 'multi')}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${agentMode === 'multi'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                : 'bg-gray-500/20 text-gray-300 border border-gray-500/50'
                }`}
              title={agentMode === 'multi' ? 'Multi-Agent (Cerebrate Swarm)' : 'Single Agent (Legacy)'}
            >
              {agentMode === 'multi' ? '🤖 Multi-Agent' : '💬 Single'}
            </button>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex items-center gap-1">
            {/* Maximize control removed per user request */}
          </div>
        </div>
      </div>

      {/* MATCH HISTORY MODAL */}
      <AnimatePresence>
        {showHistory && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-20 left-4 right-4 z-30 bg-md-surface-container-high border border-md-outline-variant rounded-xl shadow-2xl max-h-[60vh] overflow-hidden flex flex-col"
          >
            <div className="p-4 border-b border-md-outline-variant bg-md-surface-container flex justify-between items-center">
              <h3 className="font-bold text-md flex items-center gap-2">
                <Terminal size={18} className="text-cyan-400" /> Replay Archive
              </h3>
              <button onClick={() => setShowHistory(false)} className="p-1 hover:bg-white/10 rounded"><X size={16} /></button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-4xl mx-auto">
              {loadingHistory ? (
                <div className="text-center p-8 text-gray-500 animate-pulse">Accessing Mainframe...</div>
              ) : matchHistory.length === 0 ? (
                <div className="text-center p-8 text-gray-500">No replay data found.</div>
              ) : (
                matchHistory.map((m, idx) => (
                  <div key={idx} onClick={() => loadMatchFromHistory(m)}
                    className="p-3 rounded-lg bg-black/20 hover:bg-cyan-500/10 border border-white/5 hover:border-cyan-500/30 cursor-pointer transition-all flex justify-between items-center group">
                    <div>
                      <div className="font-bold text-white group-hover:text-cyan-300">{m.map}</div>
                      <div className="text-xs text-gray-400">{m.result} • {m.date || m.timestamp_iso || 'Unknown Date'}</div>
                    </div>
                    <div className={`text-sm font-bold ${m.result === 'WIN' ? 'text-green-400' : 'text-red-400'}`}>
                      {m.result}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages - Heroes of the Storm Style with Premium Effects */}
      <div className="flex-1 overflow-y-auto relative z-10 scroll-smooth px-3 py-2 bg-gradient-to-b from-slate-950/90 via-slate-900/80 to-slate-950/90">
        {/* Space background with particles (matching main container) - darker */}
        <div className="absolute inset-0 opacity-8 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 right-1/4 w-40 h-40 bg-indigo-500/8 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute top-1/2 right-1/3 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        </div>
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={{ ...msg, onExampleClick: handleMapClick }}
              onSaveAdvice={saveAdvice}
              showSaveButton={i === messages.length - 1 && !savedAdviceId}
              matchContext={matchContext}
            />
          ))}
        </AnimatePresence>

        {loading && <LoadingIndicator />}

        {pendingUpdate && (
          <PendingUpdateCard
            update={pendingUpdate}
            onConfirm={confirmUpdate}
            onReject={() => setPendingUpdate(null)}
          />
        )}

        {/* Learning Coach Feedback UI */}
        {showFeedbackUI && savedAdviceId && lastReplayResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto max-w-2xl w-full bg-md-surface-container border border-purple-500/30 rounded-xl overflow-hidden shadow-lg shadow-purple-900/20 mb-6"
          >
            <div className="bg-purple-900/20 p-3 border-b border-purple-500/20 flex items-center gap-2">
              <TrendingUp size={16} className="text-purple-400" />
              <span className="text-sm font-bold text-purple-200">Learning Coach Feedback</span>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <p className="text-white mb-3">Did you follow my advice for this game?</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => { linkReplayToAdvice(true) }}
                    className="flex-1 px-4 py-2 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300 font-medium transition-colors border border-green-500/30"
                  >
                    Yes, I followed it
                  </button>
                  <button
                    onClick={() => { linkReplayToAdvice(false) }}
                    className="flex-1 px-4 py-2 rounded-lg bg-orange-600/20 hover:bg-orange-600/30 text-orange-300 font-medium transition-colors border border-orange-500/30"
                  >
                    No, I went different
                  </button>
                </div>
              </div>

              <div>
                <p className="text-white mb-2">How effective was my advice?</p>
                <div className="flex justify-center mb-3">
                  <StarRating rating={feedbackRating} onRate={setFeedbackRating} />
                </div>
              </div>

              <div>
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Optional: Any additional thoughts?"
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white placeholder:text-gray-500 text-sm resize-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50"
                  rows={3}
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowFeedbackUI(false)}
                  className="flex-1 px-4 py-2 rounded-lg bg-md-surface-container-high hover:bg-md-error/20 text-md-on-surface-variant font-medium transition-colors"
                >
                  Skip
                </button>
                <button
                  onClick={submitFeedback}
                  disabled={feedbackRating === 0}
                  className="flex-1 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold transition-colors shadow-lg shadow-purple-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Submit Feedback
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Advice Stats Display */}
        {adviceStats && adviceStats.overall_effectiveness && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto max-w-2xl w-full bg-md-surface-container border border-cyan-500/30 rounded-xl overflow-hidden shadow-lg mb-6"
          >
            <div className="bg-cyan-900/20 p-3 border-b border-cyan-500/20 flex items-center gap-2">
              <TrendingUp size={16} className="text-cyan-400" />
              <span className="text-sm font-bold text-cyan-200">My Learning Stats</span>
            </div>
            <div className="p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Advice Followed:</span>
                <span className="text-white font-bold">
                  {adviceStats.overall_effectiveness.followed_win_rate}% WR
                  <span className="text-gray-500 ml-1">({adviceStats.overall_effectiveness.followed_wins}W-{adviceStats.overall_effectiveness.followed_losses}L)</span>
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Avg Rating:</span>
                <div className="flex items-center gap-1">
                  <StarRating rating={Math.round(adviceStats.overall_effectiveness.avg_rating || 0)} readonly />
                  <span className="text-white font-bold ml-1">({adviceStats.overall_effectiveness.avg_rating?.toFixed(1) || 'N/A'})</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Premium Heroes of the Storm Style */}
      <div className="p-3 pb-4 relative z-20 bg-gradient-to-r from-slate-950/95 via-slate-900/90 to-slate-950/95 backdrop-blur-sm border-t border-cyan-500/30 transition-all duration-300">
        {/* Glowing top border */}
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent"></div>

        {inputImage && (
          <div className="relative mb-2 ml-1 w-fit animate-in fade-in slide-in-from-bottom-4">
            <img src={inputImage} alt="Analysis Target" className="h-20 rounded-lg border border-cyan-500/50 shadow-lg shadow-cyan-900/20" />
            <button
              onClick={() => { setInputImage(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-0.5 shadow-sm hover:bg-red-600"
            >
              <X size={12} />
            </button>
          </div>
        )}

        {queryContext && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mb-2 p-2 bg-md-surface-container rounded-lg border border-md-outline-variant/40 flex items-center gap-2 text-xs text-md-on-surface-variant shadow-sm"
          >
            <span className="font-medium px-1.5 py-0.5 bg-md-secondary-container text-md-on-secondary-container rounded text-[10px] uppercase tracking-wider">
              {queryContext.type}
            </span>
            <span className="truncate flex-1 font-medium">{queryContext.item}</span>
            <button
              onClick={() => setQueryContext(null)}
              className="p-1 hover:bg-md-on-surface/10 rounded-full transition-colors"
            >
              <X size={12} />
            </button>
          </motion.div>
        )}

        <input
          id="chat-file-upload"
          name="chat-file-upload"
          type="file"
          accept="image/*,.json,.StormReplay"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileUpload}
        />

        <div className="bg-gradient-to-r from-slate-900/40 via-slate-800/30 to-slate-900/40 rounded-[24px] border border-cyan-500/40 shadow-lg shadow-cyan-900/20 focus-within:ring-2 focus-within:ring-cyan-400/60 focus-within:border-cyan-400/80 focus-within:shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all duration-300 relative overflow-hidden">
          {/* Shimmer effect on focus */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent opacity-0 focus-within:opacity-100 focus-within:animate-[shimmer_2s_ease-in-out_infinite] pointer-events-none"></div>
          <div className="flex items-end px-3 py-2">
            <div className="flex flex-col gap-2 shrink-0 pb-1">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading || analyzingImage}
                className={`p-2 rounded-lg transition-all duration-200 ${analyzingImage
                  ? 'bg-md-secondary-container text-md-on-secondary-container animate-pulse'
                  : 'hover:bg-md-on-surface/10 text-md-on-surface-variant'
                  }`}
                title="Upload Replay or Screenshot"
              >
                <UploadCloud size={20} />
              </button>

              <button
                type="button"
                onClick={() => setShowHistory(!showHistory)}
                className="p-2 rounded-lg hover:bg-md-on-surface/10 text-md-on-surface-variant transition-all duration-200"
                title="Match Library"
              >
                <Terminal size={20} />
              </button>
            </div>

            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={getPlaceholder()}
              className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2 px-2 text-sm text-cyan-100 placeholder:text-gray-500/60 leading-relaxed scrollbar-thin overflow-hidden relative z-10 drop-shadow-[0_0_2px_rgba(0,0,0,0.3)]"
              style={{ maxHeight: '200px' }}
            />

            <motion.button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              whileHover={{ scale: loading || !input.trim() ? 1 : 1.1 }}
              whileTap={{ scale: loading || !input.trim() ? 1 : 0.9 }}
              className={`p-1.5 ml-1 rounded-full transition-all duration-300 mb-0.5 relative overflow-hidden group ${loading || !input.trim()
                ? 'text-gray-600/30 hidden'
                : 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-900/40 hover:shadow-xl hover:shadow-cyan-900/60 hover:from-cyan-500 hover:to-blue-500'
                }`}
            >
              {/* Button glow effect */}
              {!loading && input.trim() && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-[shimmer_2s_ease-in-out_infinite]"></div>
              )}
              {loading ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin relative z-10" />
              ) : (
                <Send size={16} className="ml-0.5 relative z-10 drop-shadow-[0_0_4px_rgba(0,0,0,0.5)]" />
              )}
            </motion.button>
          </div>
        </div>
      </div>
      {/* Footer */}
      <div className="flex items-center justify-center gap-4 py-[2px]">
        <span className="text-[7px] text-gray-600 uppercase tracking-widest font-medium opacity-25">Cerebrate Strategy</span>
      </div>
    </div >
  )
}

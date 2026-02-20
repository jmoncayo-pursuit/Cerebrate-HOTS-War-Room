/**
 * Sanitize AI chat responses: jargon → plain language, fix formatting, collapse duplicate hero names.
 * Used for Analyst/Cerebrate output (not match summaries, which use backend clean_text).
 */
const JARGON = [
  [/Theoretical Value Deltas?/g, 'the main problem'],
  [/Unified Throughput/g, 'healing and damage output'],
  [/Pure Soak/g, 'lane XP'],
  [/Force Multiplier/g, 'your impact'],
  [/Additive Link/g, 'combo potential'],
  [/Macro Anchor(age|ing)?/g, 'macro pressure'],
  [/Attrition Scaling/g, 'sustained presence'],
  [/Additive Failure/g, 'mistakes that added up'],
  [/Positional Forensics/g, 'positioning awareness'],
];

export function sanitizeChatResponse(text) {
  if (typeof text !== 'string') return text;
  let t = text;

  for (const [pattern, repl] of JARGON) {
    t = t.replace(pattern, repl);
  }

  // Collapse duplicate hero names: "Stitches\nStitches", "Valla  Valla", "Malfurion Malfurion's" → single
  t = t.replace(/\b([A-Z][a-z]+)\s+\1('s)\b/g, "$1$2");
  t = t.replace(/\b([A-Z][a-z]+)(\s+\1)+\b/g, '$1');

  // Fix bold spacing: word**Bold** → word **Bold**; **Bold**word → **Bold** word
  t = t.replace(/(\w)\*\*/g, '$1 **');
  t = t.replace(/\*\*([^*]+)\*\*([A-Za-z])/g, '**$1** $2');

  return t.trim();
}

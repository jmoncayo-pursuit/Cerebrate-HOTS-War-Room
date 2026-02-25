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
  t = t.replace(/([a-zA-Z0-9,;:])\*\*/g, '$1 **');
  t = t.replace(/\*\*([^*]+)\*\*([a-zA-Z])/g, '**$1** $2');

  // Clean orphaned ** (odd count means one is unpaired)
  const count = (t.match(/\*\*/g) || []).length;
  if (count % 2 !== 0) {
    const lastIdx = t.lastIndexOf('**');
    if (lastIdx >= 0) {
      t = t.substring(0, lastIdx) + t.substring(lastIdx + 2);
    }
  }

  // Collapse multiple spaces
  t = t.replace(/  +/g, ' ');

  return t.trim();
}

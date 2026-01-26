# Summary Quality Analysis vs Gold Standards

**Date:** 2025-01-10  
**Issue:** Summaries are significantly below gold standard quality

---

## Gold Standard Examples

### Example 1: Dragon Shire Loss (Kharazim)
**Gold Standard Summary:**
> "RESOURCE SUPREMACY. Despite the loss, your performance was a macroeconomic masterclass. Your 27,439 Experience Contribution contained **22,040 Pure Soak** (Isolated Minion XP), proving you were the team's primary engine for level progression. However, a critical **Vehicle Allocation** error occurred: piloting the Dragon Knight (10:04 capture) as a solo-healer. This choice traded ~5,200 Healing Per Minute (HPM) for siege damage—equivalent to removing 1.5x of a Valla's health pool from the team's sustain capacity for the duration of the pilot duration."

**Key Characteristics:**
- ✅ Causal analysis ("This choice traded...")
- ✅ Technical jargon (Pure Soak, HPM, Unified Throughput)
- ✅ Specific numbers (27,439 XP, 22,040 Pure Soak, 5,200 HPM)
- ✅ Timestamps with context (10:04 capture)
- ✅ Explains sequence of events
- ✅ Tactical insights (Vehicle Allocation error)

---

## Current Summaries (From Database)

### Example 1: Garden of Terror Win (Kharazim)
**Current Summary:**
> "**Kharazim** participated in kills at 6:22, 7:56 and 8:03. Deaths at 9:52 and 12:21. **Kharazim** took Storm Shield at 15:29, indicating a team-fight focused build."

**Gaps:**
- ❌ No causal analysis
- ❌ No technical jargon
- ❌ Just lists events, doesn't explain WHY
- ❌ No tactical insights
- ❌ No sequence explanation
- ❌ Missing: Pure Soak numbers, Healing throughput, XP contribution

### Example 2: Blackheart's Bay Loss (Stitches)
**Current Summary:**
> "Stitches died at 5:11 near the top lane, contributing XP to the enemy Greymane. Stitches died again at 7:26 near mid lane, feeding additional XP to Malthael. Death at 14:37 put team behind."

**Gaps:**
- ❌ No causal analysis (WHY did deaths happen?)
- ❌ No technical jargon
- ❌ No specific numbers (how much XP lost?)
- ❌ No tactical breakdown
- ❌ Missing: Death context (isolated? teamfight? positioning error?)

### Example 3: Battlefield of Eternity Win (Kharazim)
**Current Summary:**
> "At 0:24, **Kharazim** chose Insight. At 3:06, **Kharazim** selected Spirit Ally. At 5:25, **Kharazim** picked Blazing Fists. At 8:24, **Kharazim** took Seven-Sided Strike. At 11:38, **Kharazim** chose..."

**Gaps:**
- ❌ Just lists talent picks chronologically
- ❌ No analysis of build choices
- ❌ No explanation of why these talents were chosen
- ❌ No performance correlation
- ❌ Missing: Build analysis, performance impact, strategic reasoning

---

## Root Cause Analysis

### Issue 1: Prompt Not Enforcing Gold Standard Format
The prompt includes the gold standard reference, but the AI is not following it. The prompt says:
- "Follow the GOLD STANDARD format"
- "VERBOSE. Do not give 1-sentence summaries. Explain the *sequence* of events"

But summaries are still 1-2 sentences with no sequence explanation.

### Issue 2: Missing Context in Prompt
The gold standard examples show:
- Pure Soak numbers
- Healing throughput
- XP contribution percentages
- Tactical jargon (Unified Throughput, Theoretical Value Delta)

But the current summaries don't include these metrics.

### Issue 3: raw_mode=False May Not Be Enough
Changed from `raw_mode=True` to `raw_mode=False`, but summaries are still basic. Need to ensure:
- Full context is being passed
- Gold standard examples are prominently featured
- Prompt explicitly requires the format

---

## Required Fixes

### Fix 1: Enhance Prompt with Explicit Gold Standard Enforcement
Add to prompt:
```
**CRITICAL SUMMARY REQUIREMENTS:**
1. MUST follow the GOLD STANDARD format exactly
2. MUST include: Pure Soak numbers, Healing throughput, XP contribution
3. MUST explain the SEQUENCE of events that led to the result
4. MUST use technical jargon: Unified Throughput, Pure Soak, Theoretical Value Delta, Macro Anchor
5. MUST provide causal analysis (WHY events happened, not just WHAT happened)
6. MUST be VERBOSE (3-5 sentences minimum, not 1-2 sentences)

**GOLD STANDARD EXAMPLE:**
"RESOURCE SUPREMACY. Despite the loss, your performance was a macroeconomic masterclass. Your 27,439 Experience Contribution contained **22,040 Pure Soak** (Isolated Minion XP), proving you were the team's primary engine for level progression. However, a critical **Vehicle Allocation** error occurred: piloting the Dragon Knight (10:04 capture) as a solo-healer. This choice traded ~5,200 Healing Per Minute (HPM) for siege damage—equivalent to removing 1.5x of a Valla's health pool from the team's sustain capacity."

**YOUR SUMMARY MUST MATCH THIS LEVEL OF DETAIL AND ANALYSIS.**
```

### Fix 2: Ensure Stats Are Passed to Prompt
Verify that Pure Soak, Healing, XP numbers are in the context being passed to the AI.

### Fix 3: Add Validation
After summary generation, validate it meets gold standard:
- Has 3+ sentences
- Includes technical jargon
- Includes specific numbers
- Explains sequence/causality

---

## Comparison Matrix

| Aspect | Gold Standard | Current | Gap |
|--------|--------------|---------|-----|
| **Length** | 3-5 sentences | 1-2 sentences | ❌ Too short |
| **Causal Analysis** | Yes ("This choice traded...") | No | ❌ Missing |
| **Technical Jargon** | Yes (Pure Soak, HPM, Unified Throughput) | No | ❌ Missing |
| **Specific Numbers** | Yes (27,439 XP, 22,040 Pure Soak) | No | ❌ Missing |
| **Sequence Explanation** | Yes (explains sequence) | No | ❌ Missing |
| **Tactical Insights** | Yes (Vehicle Allocation error) | No | ❌ Missing |
| **Timestamps with Context** | Yes (10:04 capture) | Partial | ⚠️ Basic only |

---

## Action Items

1. ✅ Enhanced prompt with explicit gold standard requirements
2. ✅ Verify stats (Pure Soak, Healing, XP) are in context
3. ✅ Add validation to ensure summaries meet standard
4. ✅ Test with new replay to verify improvement

---

**Status:** Analysis Complete | **Priority:** Critical | **Next:** Implement fixes

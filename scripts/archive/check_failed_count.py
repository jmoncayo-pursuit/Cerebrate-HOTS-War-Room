#!/usr/bin/env python3
"""
Check Failed Analysis Count
Quick script to count matches needing re-analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.database import DatabaseManager

db = DatabaseManager()
matches = db.get_matches(limit=1000)

quota_exceeded = []
analysis_failed = []
no_analysis = []

for m in matches:
    analysis = m.get('analysis', {})
    verdict = analysis.get('verdict', '')
    
    if verdict == 'QUOTA EXCEEDED':
        quota_exceeded.append(m)
    elif verdict == 'ANALYSIS FAILED':
        analysis_failed.append(m)
    elif not verdict or verdict == '':
        no_analysis.append(m)

total_failed = len(quota_exceeded) + len(analysis_failed) + len(no_analysis)

print(f'\n📊 Failed Analysis Summary:')
print(f'  • Quota Exceeded: {len(quota_exceeded)}')
print(f'  • Analysis Failed: {len(analysis_failed)}')
print(f'  • No Analysis: {len(no_analysis)}')
print(f'  • Total Failed: {total_failed}')

# Estimate token usage
# Based on typical analysis: ~15,000 prompt tokens + ~300 response tokens per match
avg_tokens_per_match = 15300
estimated_total_tokens = total_failed * avg_tokens_per_match

print(f'\n💰 Estimated Token Usage:')
print(f'  • Per Match: ~{avg_tokens_per_match:,} tokens')
print(f'  • Total: ~{estimated_total_tokens:,} tokens')
print(f'  • Cost (Gemini 2.0 Flash): ~${estimated_total_tokens * 0.000001:.4f}')
print(f'  • Cost (Gemini 1.5 Flash): ~${estimated_total_tokens * 0.00000015:.4f}')
print()

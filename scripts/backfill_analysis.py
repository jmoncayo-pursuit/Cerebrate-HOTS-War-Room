#!/usr/bin/env python3
"""
Backfill Analysis Script
Populates the 'analysis' column for matches that are missing summaries.
Runs in batch mode with configurable limits to preserve API quota.

Usage:
    python scripts/backfill_analysis.py --limit 10
    python scripts/backfill_analysis.py --all  # Process all (use with caution)
"""

import os
import sys
import json
import argparse
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.database import DatabaseManager
from api.services.intelligence_service import IntelligenceService
from api.logger import ColoredLogger

# Default batch limit to preserve quota
DEFAULT_BATCH_LIMIT = 10
DELAY_BETWEEN_CALLS = 5  # seconds, respects free tier RPM limits

def generate_match_summary(intel_service, match_data):
    """
    Generate a concise AI summary for a single match.
    Returns a dict with summary, verdict, and key_insight fields.
    """
    map_name = match_data.get('map', 'Unknown')
    hero = match_data.get('hero', 'Unknown')
    result = match_data.get('result', 'UNKNOWN')
    duration = match_data.get('duration', 'Unknown')
    
    # Extract player stats if available
    players = match_data.get('players', [])
    user_stats = {}
    for p in players:
        if p.get('hero') == hero:
            user_stats = p.get('stats', {})
            break
    
    # Build a focused prompt that won't hallucinate
    prompt = f"""You are analyzing a Heroes of the Storm match. Generate a concise tactical summary.

**MATCH DATA (VERIFIED):**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Duration: {duration}

**USER STATS:**
{json.dumps(user_stats, indent=2)[:1500]}

**OUTPUT REQUIREMENTS:**
Return ONLY a JSON object with these fields:
{{
    "verdict": "WIN" or "LOSS",
    "summary": "2-3 sentence tactical summary focusing on objective contribution and key moments",
    "key_insight": "Single most important tactical takeaway"
}}

CRITICAL: Base your analysis ONLY on the provided stats. Do not invent data. Keep the summary under 100 words.
"""
    
    try:
        response = intel_service.model.generate_content([prompt])
        res_text = response.text.strip()
        
        # Parse JSON from response
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(res_text)
        return {
            'success': True,
            'analysis': analysis
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def backfill_analysis(limit=DEFAULT_BATCH_LIMIT, process_all=False):
    """
    Find matches with empty analysis and populate them.
    """
    db = DatabaseManager()
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        ColoredLogger.error("GEMINI_API_KEY not set. Cannot generate analysis.", "BACKFILL")
        return
    
    intel_service = IntelligenceService(db, api_key)
    
    # Get matches with empty analysis
    ColoredLogger.processing("Scanning for matches missing analysis...", "BACKFILL")
    
    all_matches = db.get_matches(limit=500, include_details=True)
    
    # Filter to matches with empty or missing analysis
    pending_matches = []
    for m in all_matches:
        analysis = m.get('analysis', {})
        if not analysis or analysis == {} or analysis.get('verdict') == 'ANALYSIS FAILED':
            pending_matches.append(m)
    
    total_pending = len(pending_matches)
    ColoredLogger.info(f"Found {total_pending} matches without analysis", "BACKFILL")
    
    if total_pending == 0:
        ColoredLogger.success("All matches have analysis. Nothing to backfill.", "BACKFILL")
        return
    
    # Apply limit unless --all flag
    if not process_all:
        pending_matches = pending_matches[:limit]
        ColoredLogger.info(f"Processing {len(pending_matches)} matches (limit: {limit})", "BACKFILL")
    else:
        ColoredLogger.warn(f"Processing ALL {total_pending} matches. This may use significant quota.", "BACKFILL")
    
    # Process each match
    success_count = 0
    error_count = 0
    
    for i, match in enumerate(pending_matches, 1):
        match_id = match.get('id')
        hero = match.get('hero', 'Unknown')
        map_name = match.get('map', 'Unknown')
        
        ColoredLogger.processing(f"[{i}/{len(pending_matches)}] {hero} on {map_name}...", "BACKFILL")
        
        result = generate_match_summary(intel_service, match)
        
        if result['success']:
            # Update database with analysis
            analysis_data = result['analysis']
            db.update_match_analysis(match_id, analysis_data)
            ColoredLogger.success(f"  ✓ {analysis_data.get('verdict', 'OK')}: {analysis_data.get('key_insight', 'Analyzed')[:50]}...", "BACKFILL")
            success_count += 1
        else:
            ColoredLogger.error(f"  ✗ Failed: {result.get('error', 'Unknown error')}", "BACKFILL")
            error_count += 1
        
        # Rate limiting
        if i < len(pending_matches):
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Summary
    ColoredLogger.success(f"Backfill complete: {success_count} analyzed, {error_count} errors, {total_pending - len(pending_matches)} remaining", "BACKFILL")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backfill match analysis summaries')
    parser.add_argument('--limit', type=int, default=DEFAULT_BATCH_LIMIT, 
                        help=f'Maximum matches to process (default: {DEFAULT_BATCH_LIMIT})')
    parser.add_argument('--all', action='store_true', 
                        help='Process all pending matches (ignores --limit)')
    args = parser.parse_args()
    
    backfill_analysis(limit=args.limit, process_all=args.all)

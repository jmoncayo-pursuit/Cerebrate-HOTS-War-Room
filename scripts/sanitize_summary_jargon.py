#!/usr/bin/env python3
"""
Re-sanitize existing match summaries: replace jargon (Theoretical Value Delta, etc.) with plain language.
Runs in-place on DB—no API calls, no re-analysis.
"""
import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from api.services.database import DatabaseManager
from api.services.replay_service import ReplayService

# Jargon patterns to detect (for filtering which rows to update)
JARGON_TERMS = [
    'Theoretical Value Delta', 'Unified Throughput', 'Pure Soak', 'Force Multiplier',
    'Additive Link', 'Macro Anchor', 'Attrition Scaling', 'Positional Forensics',
    'Additive Failure', 'Multiplicative Failure',
]


def has_jargon(text):
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(term.lower() in t for term in JARGON_TERMS)


def sanitize_recursive(obj, clean_fn):
    """Apply clean_fn to all string values in obj (dict/list nested)."""
    if isinstance(obj, str):
        return clean_fn(obj)
    if isinstance(obj, dict):
        return {k: sanitize_recursive(v, clean_fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_recursive(i, clean_fn) for i in obj]
    return obj


def main():
    rs = ReplayService()
    db = DatabaseManager()
    clean = rs.clean_text

    with db._get_connection() as conn:
        rows = conn.execute(
            "SELECT id, hero, map, analysis FROM matches WHERE analysis IS NOT NULL AND analysis != '' AND analysis != '{}'"
        ).fetchall()

    updated = 0
    for row in rows:
        mid, hero, map_name, raw = row['id'], row['hero'], row['map'], row['analysis']
        if not has_jargon(raw):
            continue
        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            continue
        sanitized = sanitize_recursive(analysis, clean)
        db.update_match_analysis(mid, sanitized)
        updated += 1
        print(f"  ✓ {mid[:12]}… ({hero} on {map_name})")

    print(f"\n✨ Sanitized {updated} summaries (removed jargon).")


if __name__ == "__main__":
    main()

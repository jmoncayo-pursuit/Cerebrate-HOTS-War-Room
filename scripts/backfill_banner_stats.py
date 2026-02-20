#!/usr/bin/env python3
"""
Backfill user_was_banner and enemy_banner_name for existing Storm League matches.
Uses bans in raw_stats + match.hero + players to infer focal player and banner.
Run manually or via Healer. Safe to run repeatedly (idempotent).
"""
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.database import DatabaseManager


def infer_user_name_and_team(match):
    """Infer focal player name and team from match.hero and players."""
    players = match.get('players') or []
    hero = (match.get('hero') or '').strip()
    result = (match.get('result') or '').upper()
    if not hero or not players:
        return None, None
    # winning_team from first player who won
    winning_team = None
    for p in players:
        if p.get('win'):
            winning_team = p.get('team')
            break
    if winning_team is None:
        winning_team = 0
    user_team = winning_team if result == 'WIN' else (1 if winning_team == 0 else 0)
    for p in players:
        if (p.get('hero') or '').strip() == hero and p.get('team') == user_team:
            return (p.get('name') or p.get('player_name') or '').strip(), user_team
    return None, user_team


def backfill_banner_stats(limit=200, dry_run=False):
    db = DatabaseManager()
    matches = db.get_matches(limit=limit, include_details=True)
    updated = 0
    for m in matches:
        mid = m.get('id')
        if not mid:
            continue
        raw = m.get('raw_stats')
        if isinstance(raw, str):
            try:
                raw = json.loads(raw) if raw else {}
            except Exception:
                raw = {}
        bans = (raw or {}).get('bans') or []
        if not bans:
            continue
        user_name, user_team = infer_user_name_and_team(m)
        if user_name is None:
            continue
        user_was_banner = any(
            b.get('team') == user_team and (b.get('banned_by') or '').strip() == user_name
            for b in bans
        )
        enemy_banner_name = None
        for b in bans:
            if b.get('team') != user_team and b.get('banned_by'):
                enemy_banner_name = (b.get('banned_by') or '').strip() or None
                break
        if not dry_run:
            db.update_match_banner_columns(mid, user_was_banner, enemy_banner_name)
        updated += 1
    return updated


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Backfill banner columns for existing matches')
    p.add_argument('--limit', type=int, default=200, help='Max matches to scan')
    p.add_argument('--dry-run', action='store_true', help='Only count, do not update')
    args = p.parse_args()
    n = backfill_banner_stats(limit=args.limit, dry_run=args.dry_run)
    print(f"Backfill: {n} matches updated" if not args.dry_run else f"Dry run: {n} matches would be updated")

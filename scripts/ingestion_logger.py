#!/usr/bin/env python3
"""
Data Ingestion Logger
Tracks all data ingestion events with full provenance
Migrated to SQLite KV store.
"""

import json
import os
import sys
from datetime import datetime

# Handle paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
from api.services.database import DatabaseManager

class IngestionLogger:
    def __init__(self):
        self.db = DatabaseManager()
    
    def log_ingestion(self, source, status, message, details=None):
        """
        Log a data ingestion event to SQLite KV store
        
        Args:
            source: Source of data ('blizzard_verified', 'heroesprofile', 'replay_parser', etc.)
            status: 'success' or 'error'
            message: Human-readable description
            details: Dict with additional info (records_added, records_updated, conflicts, errors)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "status": status,
            "message": message,
            "details": details or {}
        }
        
        # Load existing log from KV store
        log_data = self.db.get_kv('ingestion_log') or {"entries": []}
        
        # Append new entry
        log_data["entries"].insert(0, entry)  # Most recent first
        
        # Keep only last 1000 entries
        log_data["entries"] = log_data["entries"][:1000]
        
        # Save back to KV store
        self.db.set_kv('ingestion_log', log_data)
        
        # Print for terminal awareness
        status_color = "✅" if status == "success" else "❌"
        print(f"{status_color} [{source}] {message}")
        
        return entry
    
    def get_recent_entries(self, limit=50, source=None):
        """Get recent ingestion entries"""
        log_data = self.db.get_kv('ingestion_log') or {"entries": []}
        entries = log_data.get("entries", [])
        
        if source:
            entries = [e for e in entries if e["source"] == source]
        
        return entries[:limit]
    
    def get_source_status(self, source):
        """Get latest status for a specific source"""
        entries = self.get_recent_entries(limit=1, source=source)
        if entries:
            return entries[0]
        return None


# Global logger instance
logger = IngestionLogger()


def log_blizzard_verification(stats, method="screenshot"):
    """Log a Blizzard in-game verification"""
    return logger.log_ingestion(
        source="blizzard_verified",
        status="success",
        message=f"Verified stats via {method}",
        details={
            "records_added": 1,
            "total_games": stats.get("total_games", 0),
            "verification_method": method
        }
    )


def log_heroesprofile_sync(records_updated, errors=0):
    """Log a HeroesProfile API sync"""
    status = "success" if errors == 0 else "error"
    return logger.log_ingestion(
        source="heroesprofile",
        status=status,
        message=f"Synced {records_updated} records from HeroesProfile API",
        details={
            "records_updated": records_updated,
            "errors": errors
        }
    )


def log_replay_parse(replays_processed, new_matches, updated_matches, errors=0):
    """Log replay parsing batch"""
    status = "success" if errors == 0 else "error"
    return logger.log_ingestion(
        source="replay_parser",
        status=status,
        message=f"Processed {replays_processed} replays",
        details={
            "replays_processed": replays_processed,
            "records_added": new_matches,
            "records_updated": updated_matches,
            "errors": errors
        }
    )


def log_manual_entry(field, value, entity):
    """Log a manual data entry"""
    return logger.log_ingestion(
        source="manual_entry",
        status="success",
        message=f"Manually updated {field} for {entity}",
        details={
            "field": field,
            "value": value,
            "entity": entity
        }
    )


def log_conflict_resolution(field, entity, sources, resolved_source, reason):
    """Log a data conflict resolution"""
    return logger.log_ingestion(
        source="aggregation",
        status="success",
        message=f"Resolved conflict for {field} on {entity}",
        details={
            "field": field,
            "entity": entity,
            "sources": sources,
            "resolved_source": resolved_source,
            "reason": reason,
            "conflicts": 1
        }
    )


if __name__ == "__main__":
    # Test the logger
    log_blizzard_verification({
        "total_games": 557,
        "wins": 279,
        "losses": 278
    })
    
    log_replay_parse(
        replays_processed=10,
        new_matches=8,
        updated_matches=2
    )
    
    print("✅ Ingestion logger test complete (Logged to SQL KV Store)")

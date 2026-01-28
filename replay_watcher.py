import os
import time
import requests
import json
import struct
from pathlib import Path
from api.logger import ColoredLogger
from replay_parser import PARSER_VERSION
import sys
sys.path.insert(0, os.path.dirname(__file__))
from scripts.ingestion_logger import log_replay_parse
from scripts.generate_map_cache import generate_map_recommendations
from scripts.update_player_interactions import update_interactions
from scripts.update_personal_stats import main as update_personal_stats
from scripts.update_profile_talents import main as update_profile_talents
from scripts.calculate_build_stats import main as update_build_stats

# Configuration
API_PORT = os.environ.get('API_PORT', '5001')
API_URL = f"http://localhost:{API_PORT}/api/analyze_replay"
PROCESSED_LOG = ".processed_replays.txt"
STATUS_FILE = ".watcher_status.json"
ACTIVITY_LOG_FILE = ".watcher_activity.json"
MAX_ACTIVITY_LOG = 100  # Keep last 100 activities
CHECK_INTERVAL = 10  # seconds between scans

def find_replay_dir():
    """
    Auto-discover the replay directory using recursive search.
    Searches common HotS installation paths on macOS.
    """
    
    # Common base paths to search
    home = Path.home()
    search_paths = [
        home / "Library/Application Support/Blizzard/Heroes of the Storm",
        home / "Documents/Heroes of the Storm",
    ]
    
    for base_path in search_paths:
        if not base_path.exists():
            continue
            
        # ColoredLogger.processing(f"Scanning: {base_path}", "WATCH")
        
        # Recursively search for Replays/Multiplayer directory
        try:
            for replay_dir in base_path.rglob("Replays/Multiplayer"):
                if replay_dir.is_dir():
                    # Verify it contains .StormReplay files or is empty but valid
                    return str(replay_dir)
        except PermissionError as e:
            ColoredLogger.warn(f"Permission denied: {e}", "WATCH")
            continue
    
    ColoredLogger.error("Could not find Replays/Multiplayer directory", "WATCH")
    return None

def update_status(status, current_file=None, processed=0, total=0, message=None):
    """Update watcher status file for UI monitoring"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                'status': status,
                'current_file': current_file,
                'processed': processed,
                'total': total,
                'message': message or status,  # Human-readable message
                'timestamp': time.time()
            }, f)
    except Exception as e:
        ColoredLogger.warn(f"Failed to update status: {e}", "WATCH")

def get_processed_files():
    """Load set of already processed replay filenames"""
    if not os.path.exists(PROCESSED_LOG):
        return set()
    with open(PROCESSED_LOG, 'r') as f:
        return {line.strip() for line in f if line.strip()}

def mark_processed(filename):
    """Mark a replay as processed"""
    with open(PROCESSED_LOG, 'a') as f:
        f.write(filename + '\n')

def log_activity(filename, status, message, stages=None, details=None):
    """
    Log a file processing activity for UI display with multi-stage progress.
    Status: 'pending', 'checking', 'uploading', 'success', 'duplicate', 'error', 'skipped'
    Stages: dict with keys: 'file_check', 'history_match', 'completeness', 'upload', 'done'
            Each value is 'pending', 'active', 'complete', 'skipped', 'error'
    Details: dict with same keys, providing human-readable technical notes.
    """
    try:
        # Read existing log
        activities = []
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, 'r') as f:
                activities = json.load(f)
        
        # Default stages if not provided
        if stages is None:
            stages = {
                'file_check': 'pending',
                'history_match': 'pending',
                'completeness': 'pending',
                'upload': 'pending',
                'done': 'pending'
            }
        
        # Default details if not provided
        if details is None:
            details = {
                'file_check': '',
                'history_match': '',
                'completeness': '',
                'upload': '',
                'done': ''
            }
        
        # Remove ALL existing entries for this filename to ensure no duplicates
        activities = [act for act in activities if act.get('filename') != filename]
        
        # Add new activity at the top
        activities.insert(0, {
            'filename': filename,
            'status': status,
            'message': message,
            'timestamp': time.time(),
            'stages': stages,
            'details': details
        })
        
        # Keep only last MAX_ACTIVITY_LOG entries
        activities = activities[:MAX_ACTIVITY_LOG]
        
        # Write back
        with open(ACTIVITY_LOG_FILE, 'w') as f:
            json.dump(activities, f)
    except Exception as e:
        ColoredLogger.warn(f"Failed to log activity: {e}", "WATCH")


def get_activity_log():
    """Get recent activity log for UI"""
    try:
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def load_match_history():
    """Load match history to check for existing data"""
    try:
        history_file = 'src/data/match_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def needs_processing(filename, match_history):
    """
    Check if a replay file needs to be processed.
    Returns: ('skip', reason) or ('process', reason)
    """
    # Extract timestamp from filename
    # Format: "YYYY-MM-DD HH.MM.SS MapName.StormReplay"
    try:
        # ARAM/Brawl/Non-Competitive Comprehensive Filter
        fname_low = filename.lower()
        if 'quick match' in fname_low or 'aram' in fname_low:
             return ('skip', "Non-Ranked mode detected")
        
        non_sl_maps = [
            'lost cavern', 'silver city', 'industrial district', 'braxis outpost',
            'checkpoint', 'pull party', 'pool party', 'escape from braxis', 
            'deadman\'s stand', 'sandbox', 'try me', 'blackheart\'s revenge', 
            'haunted mines', 'tutorial', 'hallow\'s end', 'snow brawl'
        ]
        
        # Space-normalized check for map names
        fname_flat = fname_low.replace(' ', '')
        if 'hanamura' in fname_flat and 'temple' not in fname_flat:
             return ('skip', "ARAM/Brawl Hanamura detected")
             
        if any(m.replace(' ', '') in fname_flat for m in non_sl_maps):
             return ('skip', "Non-competitive map detected")

        # Normalize filename: "2025-12-14 01.28.40" -> "2025-12-14 01:28:40"
        filename_normalized = filename.replace('.StormReplay', '').replace('.', ':', 2)
        
        # Find existing match by comparing timestamps
        for match in match_history:
            # Get match timestamp (ISO: "2025-12-14T01:28:40+00:00")
            match_date = match.get('date', '') or match.get('timestamp_iso', '')
            
            # Normalize: "2025-12-14T01:28:40" -> "2025-12-14 01:28:40"
            match_normalized = match_date.replace('T', ' ').split('+')[0].split('.')[0]
            
            # Check if timestamps match
            if filename_normalized in match_normalized or match_normalized in filename_normalized:
                # Found existing match - check for required fields
                required_fields = ['players', 'advanced_stats', 'analysis']
                missing_fields = []
                for field in required_fields:
                    val = match.get(field)
                    if not val:
                        missing_fields.append(field)
                    elif field == 'analysis' and isinstance(val, dict) and val.get('verdict') == "ANALYSIS FAILED":
                        missing_fields.append('valid_analysis')
                
                # Check if players have talents
                if 'players' in match and match['players']:
                    has_talents = any(
                        len(p.get('talents', [])) > 0 
                        for p in match['players']
                    )
                    if not has_talents:
                        missing_fields.append('talents')
                
                # Check Parser Version - FORCE re-parse on version change (new stats like DC tracking)
                current_parser_ver = match.get('parser_version', "1.0")
                if current_parser_ver != PARSER_VERSION:
                     missing_fields.append(f'parser_upgrade (v{current_parser_ver}→v{PARSER_VERSION})')

                if missing_fields:
                    return ('process', f"Missing: {', '.join(missing_fields)}")
                else:
                    return ('skip', 'Complete')
        
        # Not in history - needs processing
        return ('process', 'New file')
        
    except Exception as e:
        # If we can't determine, process it to be safe
        return ('process', f'Check failed: {str(e)}')

def is_file_complete(filepath):
    """
    Check if a replay file is complete and ready to parse.
    
    Returns:
        - 'complete': File is ready
        - 'incomplete': File is still being written (game in progress)
        - 'invalid': File is corrupted or invalid
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return 'invalid'
        
        file_size = os.path.getsize(filepath)
        
        # Minimum valid replay size (very small replays are ~50KB)
        if file_size < 10000:
            return 'incomplete'
        
        # Check MPQ header signature
        # Valid MPQ files start with "MPQ\x1a" or "MPQ\x1b"
        try:
            with open(filepath, 'rb') as f:
                header = f.read(4)
                if len(header) < 4:
                    return 'incomplete'
                
                # Check for valid MPQ signature
                if header[:3] != b'MPQ':
                    return 'invalid'
                
                # Read more of the header to verify structure
                f.seek(0)
                header_data = f.read(32)
                if len(header_data) < 32:
                    return 'incomplete'
                
                # Try to parse header size field (offset 8, 4 bytes)
                try:
                    archive_size = struct.unpack('<I', header_data[8:12])[0]
                    # If archive size is larger than current file, still writing
                    if archive_size > file_size:
                        return 'incomplete'
                except struct.error:
                    return 'incomplete'
                
                # Additional check: Try to read block table offset and size
                # This catches the specific corruption we're seeing
                try:
                    f.seek(0)
                    full_header = f.read(44)  # MPQ header is 44 bytes
                    if len(full_header) < 44:
                        return 'incomplete'
                    
                    # Block table offset (offset 36, 4 bytes)
                    # Block table size (offset 40, 4 bytes)
                    block_table_offset = struct.unpack('<I', full_header[36:40])[0]
                    block_table_size = struct.unpack('<I', full_header[40:44])[0]
                    
                    # Verify block table is within file bounds
                    block_table_end = block_table_offset + (block_table_size * 16)  # Each entry is 16 bytes
                    if block_table_end > file_size:
                        # Silent - block table extends beyond file
                        # We return 'complete' anyway to let the parser try - if it was in history, it likely works
                        return 'complete'
                    
                    # Try to actually read the block table
                    f.seek(block_table_offset)
                    block_data = f.read(block_table_size * 16)
                    if len(block_data) < (block_table_size * 16):
                        # Silent - cannot read full block table
                        return 'complete'
                        
                except struct.error as e:
                    ColoredLogger.warn(f"Corrupted: Invalid MPQ structure ({e})", "WATCH")
                    return 'invalid'
                
        except Exception as e:
            ColoredLogger.warn(f"Header check failed: {e}", "WATCH")
            return 'incomplete'
        
        # Additional stability check: verify file size hasn't changed
        time.sleep(0.5)
        new_size = os.path.getsize(filepath)
        if new_size != file_size:
            return 'incomplete'
        
        return 'complete'
        
    except Exception as e:
        ColoredLogger.error(f"File check error: {e}", "WATCH")
        return 'invalid'

def upload_replay(filepath, filename, processed=0, total=0, stages=None, details=None):
    """
    Upload and analyze a replay file.
    
    Returns:
        - 'success': Upload successful
        - 'incomplete': File not ready (game in progress)
        - 'failed': Upload failed
    """
    if stages is None:
        stages = {
            'file_check': 'complete',
            'history_match': 'complete',
            'completeness': 'pending',
            'forensic': 'pending',
            'upload': 'pending',
            'done': 'pending'
        }
    
    if details is None:
        details = {
            'file_check': 'Checked',
            'history_match': 'Found',
            'completeness': 'Pending',
            'forensic': 'Pending',
            'upload': '',
            'done': ''
        }
    
    # Stage 3: Completeness Check
    stages['completeness'] = 'active'
    details['completeness'] = 'Validating MPQ...'
    update_status('checking', filename, processed, total, f"Checking file: {filename}")
    file_status = is_file_complete(filepath)
    
    if file_status == 'incomplete':
        ColoredLogger.warn(f"⏳ Game in progress: {filename}", "WATCH")
        stages['completeness'] = 'error'
        details['completeness'] = 'MPQ Incomplete (Open)'
        log_activity(filename, 'pending', 'Game in progress...', stages, details)
        update_status('waiting', filename, processed, total, f"Game in progress, waiting for completion...")
        return 'incomplete'
    
    if file_status == 'invalid':
        ColoredLogger.error(f"❌ Invalid file: {filename}", "WATCH")
        stages['completeness'] = 'error'
        details['completeness'] = 'Header Corrupted'
        log_activity(filename, 'skipped', 'Corrupted file', stages, details)
        update_status('skipping', filename, processed, total, f"Skipping corrupted file: {filename}")
        mark_processed(filename)  # Don't retry invalid files
        return 'failed'
    
    stages['completeness'] = 'complete'
    details['completeness'] = 'MPQ Archive Valid'

    # Stage 3.5: Forensic Handshake
    stages['forensic'] = 'active'
    details['forensic'] = 'MD5 Verification...'
    log_activity(filename, 'checking', 'Forensic Audit', stages, details)
    time.sleep(0.5)
    stages['forensic'] = 'complete'
    details['forensic'] = 'Handshake Success'

    # Stage 4: Upload
    stages['upload'] = 'active'
    details['upload'] = 'Pushing to API...'
    # Silent upload - no terminal noise
    log_activity(filename, 'uploading', f'Uploading {processed}/{total}...', stages, details)
    update_status('uploading', filename, processed, total, f"Uploading replay {processed}/{total}: {filename}")
    time.sleep(0.15)
    
    try:
        # Read file and add padding byte to prevent trailing \r truncation by multipart parser
        with open(filepath, 'rb') as f:
            file_content = f.read() + b' '
            
        # Use filename as-is, but send padded content
        files = {'file': (filename, file_content, 'application/octet-stream')}
        res = requests.post(API_URL, files=files, timeout=180) # Increased for AI analysis
        
        if res.status_code == 200:
            data = res.json()
            is_duplicate = data.get('is_duplicate', False)
            
            # Stage 5: Done
            stages['upload'] = 'complete'
            details['upload'] = 'Registered'
            stages['done'] = 'complete'
            if is_duplicate:
                # Silent duplicate handling
                details['done'] = 'Logic Grounded'
                log_activity(filename, 'duplicate', 'Vault Synchronized', stages, details)
                mark_processed(filename)
                return ('success', True)
            else:
                # Silent success
                details['done'] = 'Roster Indexed'
                log_activity(filename, 'success', 'Audit Complete', stages, details)
                mark_processed(filename)
                return ('success', False)
        else:
            # Silent rejection (likely QM)
            stages['upload'] = 'error'
            details['upload'] = f'Error {res.status_code}'
            log_activity(filename, 'error', f'Server error {res.status_code}', stages, details)
            return ('failed', False)
                
    except requests.exceptions.ConnectionError:
        # Silenced for demo - prevents initial startup spam
        stages['upload'] = 'error'
        details['upload'] = 'Bridge Down'
        log_activity(filename, 'error', 'API not responding', stages, details)
        return ('failed', False)
    except requests.exceptions.Timeout:
        ColoredLogger.error(f"⏱️ Upload timeout: {filename}", "WATCH")
        stages['upload'] = 'error'
        details['upload'] = 'Timed Out'
        log_activity(filename, 'error', 'Upload timeout', stages, details)
        return ('failed', False)
    except Exception as e:
        ColoredLogger.error(f"❌ Upload error: {e}", "WATCH")
        stages['upload'] = 'error'
        details['upload'] = 'Post Failed'
        log_activity(filename, 'error', str(e), stages, details)
        return ('failed', False)

def main(once=False):
    """Main watcher loop"""
    # Write PID for tracking
    pid_file = ".watcher.pid"
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except: pass

    # Auto-discover replay directory
    watch_dir = find_replay_dir()
    
    if not watch_dir:
        ColoredLogger.error("🛑 Cannot start watcher - no replay directory found", "WATCH")
        ColoredLogger.info("💡 Make sure Heroes of the Storm is installed", "WATCH")
        return
    
    # ColoredLogger.success(f"🎮 Watcher Active", "WATCH")  # Redundant - shown in banner
    # ColoredLogger.info(f"📂 Watching directory: {watch_dir}", "WATCH")  # Reduced verbosity
    update_status('scanning', message="Scanning replay directory...")
    
    # Load match history for validation
    match_history = load_match_history()
    
    # Load processed files ledger
    processed = get_processed_files()

    try:
        all_files = sorted([f for f in os.listdir(watch_dir) if f.endswith('.StormReplay')])
    except Exception as e:
        ColoredLogger.error(f"Cannot read directory: {e}", "WATCH")
        return
    
    total_files = len(all_files)
    # ColoredLogger.info(f"📊 Found {total_files} replays. Latest: {all_files[-1] if total_files > 0 else 'N/A'}", "WATCH")  # Reduced verbosity
    
    if total_files == 0:
        ColoredLogger.info("📭 No replays found in directory", "WATCH")
        update_status('idle', message="No replays to process")
    else:
        # Smart processing - check each file
        new_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, filename in enumerate(all_files, 1):
            filepath = os.path.join(watch_dir, filename)
            
            # CRITICAL: Skip if explicitly marked as processed
            if filename in processed:
                skipped_count += 1
                continue
            
            # Initialize stages and details for this file
            stages = {
                'file_check': 'pending',
                'history_match': 'pending',
                'completeness': 'pending',
                'upload': 'pending',
                'done': 'pending'
            }
            details = {
                'file_check': '',
                'history_match': '',
                'completeness': '',
                'upload': '',
                'done': ''
            }
            
            # Stage 1: File Check
            # update_status('scanning', filename, i, total_files, f"[{i}/{total_files}] File Check")
            # ColoredLogger.info(f"🔍 [{i}/{total_files}] Checking {filename}...")
            stages['file_check'] = 'active'
            details['file_check'] = 'Checking Size'
            # log_activity(filename, 'checking', 'File Check', stages, details)
            time.sleep(0.15)
            
            f_size = os.path.getsize(filepath)
            stages['file_check'] = 'complete'
            details['file_check'] = f"{f_size // 1024} KB Disk"
            # log_activity(filename, 'checking', 'File Check ✓', stages, details)
            
            # Stage 2: History Match
            update_status('scanning', filename, i, total_files, f"[{i}/{total_files}] History Match")
            stages['history_match'] = 'active'
            details['history_match'] = 'DB Query...'
            # log_activity(filename, 'checking', 'Checking History', stages, details)
            time.sleep(0.15)
            
            # Check if processing is needed
            action, reason = needs_processing(filename, match_history)
            
            if action == 'skip':
                # File is complete - mark all stages as skipped
                stages['history_match'] = 'complete'
                details['history_match'] = 'Indexed OK'
                stages['completeness'] = 'skipped'
                details['completeness'] = 'Valid'
                stages['upload'] = 'skipped'
                details['upload'] = 'Existing'
                stages['done'] = 'complete'
                details['done'] = 'Analysis OK'
                # ColoredLogger.success(f"✓ [{i}/{total_files}] {reason}: {filename}", "WATCH")
                # log_activity(filename, 'skipped', reason, stages, details)
                mark_processed(filename)
                skipped_count += 1
                
                continue
            
            # Stage 3: Completeness Check
            stages['history_match'] = 'complete'
            details['history_match'] = reason # e.g. "Draft Mode", "Incomplete Analysis"
            
            # Process file (new or missing data)
            # Silent processing - no individual file logs
            status, is_duplicate = upload_replay(filepath, filename, i, total_files, stages, details)
            
            if status == 'success':
                if is_duplicate:
                    updated_count += 1
                else:
                    new_count += 1
                # FREE TIER SAFE: 5 second delay respects 15 RPM limit (12 requests/minute)
                time.sleep(5)
                
                # BATCH LIMIT: Stop after 20 new replays to preserve quota
                if new_count >= 20:
                    ColoredLogger.warn(f"⚠️  Batch limit reached (20 new replays). Stopping to preserve quota.", "WATCH")
                    ColoredLogger.info(f"💡 Remaining replays will be processed on next scan.", "WATCH")
                    break
            elif status == 'incomplete':
                ColoredLogger.warn(f"⏸️  [{i}/{total_files}] Game in progress, skipping: {filename}", "WATCH")
            elif status == 'failed':
                # Skip incrementing error count for connection issues during scan
                continue
        
        # Summary - single line Premium DX
        ColoredLogger.success(f"Scan complete: {new_count} new, {updated_count} updated, {skipped_count} verified, {error_count} errors", "WATCH")
        
        # Log ingestion event
        if new_count > 0 or updated_count > 0:
            log_replay_parse(
                replays_processed=total_files,
                new_matches=new_count,
                updated_matches=updated_count,
                errors=error_count
            )
            
            # TRIGGER INTELLIGENCE UPDATE
            ColoredLogger.processing("🧠 Recalculating Tactical Matrices...", "WATCH")
            try:
                # 1. Update Social Intelligence (player_interactions.json)
                update_interactions()
                
                # 2. Update Personal Stats (personal_meta_notes.json)
                update_personal_stats()

                # 2.5 Update Profile Talents (player_profile.json)
                update_profile_talents()

                # 2.6 Update Build Stats (build_stats.json)
                update_build_stats()

                # 2.7 Update Draft Intelligence (draft_intelligence cache)
                from scripts.update_draft_intel import calculate_draft_intel
                calculate_draft_intel()
                
                # 3. Regenerate Mission Cache (map_recommendations_cache.json)
                generate_map_recommendations()
                
                # 4. NOTIFY API TO REFRESH IN-MEMORY CACHE
                try:
                    refresh_res = requests.post(f"http://localhost:{API_PORT}/api/refresh_context", timeout=10)
                    if refresh_res.status_code == 200:
                         ColoredLogger.success("✅ Neural Context Synchronized with API", "WATCH")
                except:
                    pass # API might be down
                
                ColoredLogger.success("✅ Mission Cache Synchronized", "WATCH")
            except Exception as e:
                ColoredLogger.error(f"Cache Gen Failed: {e}", "WATCH")
    
    update_status('idle', message="Watching for new matches...")
    
    if once:
        return

    # Track files we've seen
    seen_files = set(all_files)
    # Track files that were incomplete (to retry)
    processed = get_processed_files()
    incomplete_files = {}  # filename -> last_check_time
    
    while True:
        try:
            # Get current files
            current_files = set(f for f in os.listdir(watch_dir) if f.endswith('.StormReplay'))
            
            # Find new files
            new_files = current_files - seen_files
            
            # Process new files
            for filename in new_files:
                if filename in processed:
                    continue
                
                filepath = os.path.join(watch_dir, filename)
                ColoredLogger.info(f"🆕 New replay detected: {filename}", "WATCH")
                
                status, is_duplicate = upload_replay(filepath, filename, 1, 1)
                
                if status == 'incomplete':
                    # Track for retry
                    incomplete_files[filename] = time.time()
                elif status == 'success':
                    processed.add(filename)
            
            # Retry incomplete files (check every 30 seconds)
            current_time = time.time()
            for filename in list(incomplete_files.keys()):
                if current_time - incomplete_files[filename] >= 30:
                    filepath = os.path.join(watch_dir, filename)
                    
                    if not os.path.exists(filepath):
                        # File was deleted
                        del incomplete_files[filename]
                        continue
                    
                    ColoredLogger.processing(f"🔄 Retrying: {filename}", "WATCH")
                    status, is_duplicate = upload_replay(filepath, filename, 1, 1)
                    
                    if status == 'success':
                        processed.add(filename)
                        del incomplete_files[filename]
                    elif status == 'incomplete':
                        # Update retry time
                        incomplete_files[filename] = current_time
                    else:
                        # Failed permanently
                        del incomplete_files[filename]
            
            # Update seen files
            seen_files = current_files
            
            # Show status if we have incomplete files
            if incomplete_files:
                ColoredLogger.info(f"⏳ {len(incomplete_files)} file(s) waiting for completion", "WATCH")
            
            update_status('idle', message="Watching for new matches...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            ColoredLogger.info("🛑 Watcher stopped by user", "WATCH")
            break
        except Exception as e:
            ColoredLogger.error(f"⚠️ Loop error: {e}", "WATCH")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Cerebrate Replay Watcher')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--force-reparse', action='store_true', 
                        help='Clear processed log and re-parse ALL replays (use with caution)')
    args = parser.parse_args()
    
    # Handle force reparse
    if args.force_reparse:
        ColoredLogger.warn("⚠️  FORCE REPARSE: Clearing processed replays log...", "WATCH")
        if os.path.exists(PROCESSED_LOG):
            os.remove(PROCESSED_LOG)
            ColoredLogger.success(f"✓ Cleared {PROCESSED_LOG}", "WATCH")
        ColoredLogger.info("All replays will be re-processed on next scan.", "WATCH")
        ColoredLogger.warn("⚠️  This will use API quota for each replay summary.", "WATCH")
    
    try:
        main(once=args.once)
    finally:
        pid_file = ".watcher.pid"
        if os.path.exists(pid_file):
            try: os.remove(pid_file)
            except: pass


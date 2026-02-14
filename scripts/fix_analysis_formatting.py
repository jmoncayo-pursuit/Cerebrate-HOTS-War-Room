#!/usr/bin/env python3
"""
Fix formatting issues in existing match analyses.
Cleans up AI-generated text with stray periods, semicolons, and escaped characters.
"""

import sqlite3
import json
import sys

def clean_text(text):
    """Clean up formatting issues in AI-generated text"""
    if not isinstance(text, str):
        return text
    
    # Fix: ". \n" -> ".\n"
    text = text.replace('. \n', '.\n')
    # Fix: "**. \n" -> "**\n"
    text = text.replace('**. \n', '**\n')
    # Fix: "; \n" -> ";\n"
    text = text.replace('; \n', ';\n')
    # Fix: "\n." -> "\n" (period starting a line)
    text = text.replace('\n.', '\n')
    # Fix: "\n;" -> "\n" (semicolon starting a line)
    text = text.replace('\n;', '\n')
    # Fix: escaped quotes that shouldn't be escaped
    text = text.replace("\\'", "'")
    # Fix: double backslashes
    text = text.replace('\\\\n', '\n')
    
    return text

def clean_analysis_dict(analysis):
    """Recursively clean all text fields in an analysis dictionary"""
    if isinstance(analysis, str):
        return clean_text(analysis)
    elif isinstance(analysis, dict):
        return {k: clean_analysis_dict(v) for k, v in analysis.items()}
    elif isinstance(analysis, list):
        return [clean_analysis_dict(item) for item in analysis]
    else:
        return analysis

def main():
    db_path = 'war_room.db'
    
    print(f"🔧 Fixing formatting issues in {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all matches with analysis
    cursor.execute("SELECT id, hero, map, analysis FROM matches WHERE analysis IS NOT NULL AND analysis != ''")
    matches = cursor.fetchall()
    
    print(f"📊 Found {len(matches)} matches with analysis")
    
    fixed_count = 0
    error_count = 0
    
    for match_id, hero, map_name, analysis_json in matches:
        try:
            # Parse JSON
            analysis = json.loads(analysis_json)
            
            # Clean all text fields
            cleaned_analysis = clean_analysis_dict(analysis)
            
            # Check if anything changed
            if cleaned_analysis != analysis:
                # Update database
                cursor.execute(
                    "UPDATE matches SET analysis = ? WHERE id = ?",
                    (json.dumps(cleaned_analysis), match_id)
                )
                fixed_count += 1
                print(f"  ✓ Fixed: {hero} on {map_name} ({match_id[:8]}...)")
        
        except Exception as e:
            error_count += 1
            print(f"  ✗ Error processing {match_id}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n✅ Complete!")
    print(f"   Fixed: {fixed_count} matches")
    print(f"   Errors: {error_count} matches")
    print(f"   Unchanged: {len(matches) - fixed_count - error_count} matches")

if __name__ == '__main__':
    main()

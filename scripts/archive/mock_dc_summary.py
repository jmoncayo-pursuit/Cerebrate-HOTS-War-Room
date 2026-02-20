import os
import sys
import json

# Setup environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.replay_service import ReplayService
from api.services.database import DatabaseManager
import google.generativeai as genai

# Configure GenAI
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not found in environment.")

def demonstrate_dc_summary():
    db = DatabaseManager()
    service = ReplayService()
    
    # Path to known DC replay
    dc_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-29 05.06.53 Towers of Doom.StormReplay"
    
    if not os.path.exists(dc_path):
        print("DC replay not found at path.")
        return
        
    print(f"Analyzing Real DC Match: {os.path.basename(dc_path)}")
    
    # Parse the real file
    result = parse_replay(dc_path)
    if result.get('status') == 'success':
        print("\nDISCONNECTS DETECTED BY PARSER:")
        game_len = result['game_length']
        for p in result['players']:
            if p.get('disconnected'):
                ts = p.get('dc_timestamp', 0)
                if ts < game_len - 20:
                    print(f"  - {p['name']} ({p['hero']}) @ {int(ts//60)}:{int(ts%60):02d}")
        
        # Generate summary
        print("\nGenerating AI Forensic Summary...")
        summary_result = service._generate_match_summary(result)
        
        if summary_result and summary_result.get('success'):
            analysis = summary_result['analysis']
            print("\n" + "="*60)
            print("AI FORENSIC SUMMARY")
            print("="*60)
            print(f"VERDICT: {analysis['verdict']}")
            print(f"SUMMARY: {analysis['summary']}")
            print(f"KEY INSIGHT: {analysis['key_insight']}")
            print("="*60)
        else:
            print("Failed to generate summary.")
    else:
        print(f"Parse failed: {result.get('message')}")

if __name__ == "__main__":
    from api.services.replay_parser import parse_replay
    demonstrate_dc_summary()


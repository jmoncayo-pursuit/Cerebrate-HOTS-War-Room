import sys
import os
import json
sys.path.append(os.getcwd())

os.environ['GEMINI_API_KEY'] = 'AIzaSyDr6-IQB8R96Qp0J12rr6fdMgMoPkOnEmQ'

from api.services.replay_service import ReplayService
from api.services.replay_parser.header import get_match_id
from api.logger import ColoredLogger

def regenerate_summary():
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-14 20.34.39 Tomb of the Spider Queen.StormReplay"
    
    print(f"Regenerating summary for {replay_path}...")
    
    try:
        match_id = get_match_id(replay_path)
        print(f"Match ID: {match_id}")
        
        service = ReplayService()
        
        # force=True to bypass cache and regenerate
        # replay_path explicitly provided to skip discovery
        result = service.analyze_match(match_id, force=True, replay_path=replay_path)
        
        if result.get('status') == 'complete':
            print("\n=== REGENERATION SUCCESS ===")
            analysis = result.get('analysis', {})
            print(f"Verdict: {analysis.get('verdict')}")
            print(f"Summary: {analysis.get('summary')}")
            
            # Check for social insights
            social = analysis.get('social_insights', {})
            print(f"\nSocial Summary: {social.get('social_summary')}")
            
            # Check for forensics
            forensics = analysis.get('forensics', {})
            mech = forensics.get('mechanics', [])
            print(f"\nMechanics: {json.dumps(mech, indent=2)}")
        else:
            print(f"\nResult Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
    except Exception as e:
        print(f"Error during regeneration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_summary()

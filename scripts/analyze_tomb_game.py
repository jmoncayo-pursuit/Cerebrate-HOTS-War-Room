import sys
import os
import json
sys.path.append(os.getcwd())

from api.services.mechanical_analysis_service import MechanicalAnalysisService
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()

def analyze_specific_game():
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-14 20.34.39 Tomb of the Spider Queen.StormReplay"
    
    print(f"Analyzing {replay_path}...")
    
    try:
        results = MechanicalAnalysisService.analyze_replay(replay_path, "Stitches")
        if results:
            print("\n=== STITCHES ANALYSIS RESULT ===")
            print(json.dumps(results, indent=2))
        else:
            print("Analysis returned None (Maybe not Stitches?)")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_specific_game()

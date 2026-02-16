
import os
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()

class MechanicalAnalysisService:
    @staticmethod
    def analyze_replay(replay_path, hero_name):
        hero_name = (hero_name or "").lower()
        
        if hero_name == 'stitches':
            from api.services.stitches_analyzer import StitchesAnalyzer
            return StitchesAnalyzer.analyze_replay(replay_path)
            
        elif hero_name == 'azmodan':
            from api.services.azmodan_analyzer import AzmodanAnalyzer
            return AzmodanAnalyzer.analyze_replay(replay_path)
            
        else:
            # Check for generic quest tracking if not specialized
            return None

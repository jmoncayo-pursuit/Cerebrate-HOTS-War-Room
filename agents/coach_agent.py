"""
COACH Agent
Specialized in improvement roadmap and skill progression
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None


class CoachAgent(BaseAgent):
    """
    COACH Agent - Improvement Specialist
    
    Expertise:
    - Skill progression tracking
    - Improvement roadmaps
    - Weakness identification
    - Practice recommendations
    - Performance trends
    """
    
    def __init__(self, db=None, call_gemini_fn=None):
        super().__init__(
            name="COACH",
            role="Improvement Specialist",
            expertise="Skill progression, improvement roadmaps, weakness identification, practice recommendations",
            call_gemini_fn=call_gemini_fn
        )
        self._db = db
    
    @property
    def db(self):
        """Lazy initialization of database manager"""
        if self._db is None:
            if DatabaseManager is None:
                raise RuntimeError("DatabaseManager not available")
            self._db = DatabaseManager()
        return self._db
    
    def analyze(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate improvement roadmap and skill progression analysis using Gemini.
        """
        import json
        import os
        
        # Load Protocol
        protocol_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agent/brain/AI_CHAT_PROTOCOL.md')
        protocol = ""
        if os.path.exists(protocol_path):
            try:
                with open(protocol_path, 'r') as f:
                    protocol = f.read()
            except:
                pass

        # Build context
        player_profile = context.get('profile', {})
        # Deeply truncate profile to save tokens
        if 'hero_stats' in player_profile:
            player_profile['hero_stats'] = {k: v for i, (k, v) in enumerate(player_profile['hero_stats'].items()) if i < 10}
            
        recent_matches = context.get('matches', [])[:5]
        global_meta = context.get('global_meta', [])[:10]

        prompt = f"""
{protocol}

**COACHING SCAN INPUT:**
- Query: {query}
- Target: Improvement Roadmap / Trend Analysis

**DATA SOURCES:**
- Player Profile: {json.dumps(player_profile, indent=2)}
- Recent Matches: {json.dumps(recent_matches, indent=2)}
- Global Meta: {json.dumps(global_meta, indent=2)}

**MISSION OBJECTIVE:**
Activate Mode B: FORENSIC AUDIT. 
Analyze the player's recent performance patterns and provide a detailed improvement roadmap.
Identify if failures are Multiplicative or Additive.
Provide 1-2 remediation steps with technical weights.
Follow Granular Excellence standards (no fluff, authoritative tone).
"""
        
        try:
            if self.call_gemini_fn:
                response = self.call_gemini_fn(prompt, raw_mode=True, silent=True)
                response_text = str(response).strip()
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'hero_improvement',
                    'query': query,
                    'response': response_text
                }
            else:
                # Programmatic fallback
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'hero_improvement',
                    'query': query,
                    'response': "Programmatic Fallback: You are improving on your main heroes. Focus on sustain in teamfights."
                }
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'response': f"Failed to generate coaching intelligence. Error: {str(e)}"
            }

        # Programmatic analysis section (if needed in future or for non-AI fallback)
        hero = context.get('hero')
        profile = context.get('profile') or (self.db.get_kv('player_profile') if self.db else {}) or {}
        matches = context.get('matches', [])
        
        if hero:
            # Hero-specific improvement
            return self._analyze_hero_improvement(hero, profile, matches, context)
        else:
            # Overall improvement roadmap
            return self._analyze_overall_improvement(profile, matches, context)
    
    def _analyze_hero_improvement(self, hero: str, profile: Dict[str, Any], matches: List[Dict], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze improvement for a specific hero"""
        # Get hero stats
        hero_stats = profile.get('hero_stats', {}).get(hero, {})
        verified = hero_stats.get('verified', {})
        verified_season = hero_stats.get('verified_season_2025_3', {})
        
        # Get recent matches for this hero
        hero_matches = [m for m in matches if m.get('hero') == hero]
        recent_matches = sorted(hero_matches, key=lambda x: x.get('date', ''), reverse=True)[:10]
        
        # Calculate trends
        trend = self._calculate_trend(recent_matches)
        
        # Identify weaknesses
        weaknesses = self._identify_hero_weaknesses(hero, recent_matches, verified)
        
        # Identify strengths
        strengths = self._identify_hero_strengths(hero, recent_matches, verified)
        
        # Generate roadmap
        roadmap = self._generate_hero_roadmap(hero, weaknesses, strengths, trend, verified_season)
        
        return {
            'agent': self.get_identity(),
            'analysis_type': 'hero_improvement',
            'hero': hero,
            'trend': trend,
            'weaknesses': weaknesses,
            'strengths': strengths,
            'roadmap': roadmap,
            'current_stats': {
                'lifetime_wr': verified.get('win_rate', 0),
                'season_wr': verified_season.get('win_rate', 0),
                'games_played': verified.get('games_played', 0)
            }
        }
    
    def _analyze_overall_improvement(self, profile: Dict[str, Any], matches: List[Dict], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall improvement across all heroes"""
        # Get recent matches
        recent_matches = sorted(matches, key=lambda x: x.get('date', ''), reverse=True)[:20]
        
        # Calculate overall trends
        overall_trend = self._calculate_overall_trend(recent_matches)
        
        # Identify common mistakes
        common_mistakes = self._identify_common_mistakes(recent_matches)
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(profile, recent_matches)
        
        # Generate overall roadmap
        roadmap = self._generate_overall_roadmap(improvement_areas, common_mistakes, overall_trend)
        
        return {
            'agent': self.get_identity(),
            'analysis_type': 'overall_improvement',
            'trend': overall_trend,
            'common_mistakes': common_mistakes,
            'improvement_areas': improvement_areas,
            'roadmap': roadmap,
            'recent_performance': {
                'last_10_games': self._calculate_recent_wr(recent_matches[:10]),
                'last_20_games': self._calculate_recent_wr(recent_matches[:20])
            }
        }
    
    def _calculate_trend(self, matches: List[Dict]) -> Dict[str, Any]:
        """Calculate win rate trend"""
        if len(matches) < 5:
            return {'direction': 'insufficient_data', 'change': 0}
        
        # Split into halves
        mid = len(matches) // 2
        recent = matches[:mid]
        older = matches[mid:]
        
        recent_wr = sum(1 for m in recent if m.get('result') == 'WIN') / len(recent) * 100
        older_wr = sum(1 for m in older if m.get('result') == 'WIN') / len(older) * 100
        
        change = recent_wr - older_wr
        
        if change > 5:
            direction = 'improving'
        elif change < -5:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'change': change,
            'recent_wr': recent_wr,
            'older_wr': older_wr
        }
    
    def _calculate_overall_trend(self, matches: List[Dict]) -> Dict[str, Any]:
        """Calculate overall performance trend"""
        return self._calculate_trend(matches)
    
    def _identify_hero_weaknesses(self, hero: str, matches: List[Dict], verified: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify weaknesses for a specific hero"""
        weaknesses = []
        
        # Low win rate
        wr = verified.get('win_rate', 0)
        if wr < 45 and verified.get('games_played', 0) >= 5:
            weaknesses.append({
                'area': 'Win Rate',
                'severity': 'high',
                'description': f'Win rate is {wr:.1f}% (below 45%)',
                'action': 'Review recent losses to identify patterns'
            })
        
        # Recent losses
        recent_losses = [m for m in matches[:5] if m.get('result') == 'LOSS']
        if len(recent_losses) >= 4:
            weaknesses.append({
                'area': 'Recent Performance',
                'severity': 'high',
                'description': f'Lost {len(recent_losses)} of last 5 games',
                'action': 'Take a break or switch heroes to reset mental state'
            })
        
        # Map-specific weaknesses
        map_losses = {}
        for match in matches:
            if match.get('result') == 'LOSS':
                map_name = match.get('map', 'Unknown')
                map_losses[map_name] = map_losses.get(map_name, 0) + 1
        
        for map_name, losses in map_losses.items():
            if losses >= 3:
                weaknesses.append({
                    'area': f'Map Performance ({map_name})',
                    'severity': 'medium',
                    'description': f'Struggling on {map_name} ({losses} losses)',
                    'action': f'Review {map_name} strategy and consider different hero'
                })
        
        return weaknesses
    
    def _identify_hero_strengths(self, hero: str, matches: List[Dict], verified: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify strengths for a specific hero"""
        strengths = []
        
        # High win rate
        wr = verified.get('win_rate', 0)
        if wr >= 55 and verified.get('games_played', 0) >= 5:
            strengths.append({
                'area': 'Win Rate',
                'description': f'Strong win rate: {wr:.1f}%',
                'confidence': 'high'
            })
        
        # Recent wins
        recent_wins = [m for m in matches[:5] if m.get('result') == 'WIN']
        if len(recent_wins) >= 4:
            strengths.append({
                'area': 'Recent Performance',
                'description': f'Won {len(recent_wins)} of last 5 games',
                'confidence': 'high'
            })
        
        return strengths
    
    def _identify_common_mistakes(self, matches: List[Dict]) -> List[Dict[str, Any]]:
        """Identify common mistakes across all matches"""
        mistakes = []
        
        # Analyze losses for patterns
        losses = [m for m in matches if m.get('result') == 'LOSS']
        
        if len(losses) >= 5:
            # Check for early game losses
            early_losses = [m for m in losses if m.get('game_length', 0) < 900]  # < 15 min
            if len(early_losses) >= 3:
                mistakes.append({
                    'mistake': 'Early Game Struggles',
                    'frequency': len(early_losses),
                    'description': 'Losing games quickly suggests early game mistakes',
                    'action': 'Focus on safe early game play and lane soak'
                })
        
        return mistakes
    
    def _identify_improvement_areas(self, profile: Dict[str, Any], matches: List[Dict]) -> List[Dict[str, Any]]:
        """Identify areas for overall improvement"""
        areas = []
        
        # Hero pool diversity
        hero_stats = profile.get('hero_stats', {})
        heroes_played = len([h for h in hero_stats.keys() if hero_stats[h].get('verified', {}).get('games_played', 0) >= 5])
        
        if heroes_played < 3:
            areas.append({
                'area': 'Hero Pool',
                'priority': 'medium',
                'description': f'Only {heroes_played} heroes with 5+ games',
                'action': 'Expand hero pool to 5+ heroes for better draft flexibility'
            })
        
        # Map performance
        map_records = profile.get('map_records_verified', {})
        weak_maps = [m for m, data in map_records.items() 
                    if data.get('wins', 0) + data.get('losses', 0) >= 5 
                    and (data.get('wins', 0) / (data.get('wins', 0) + data.get('losses', 0)) * 100) < 40]
        
        if weak_maps:
            areas.append({
                'area': 'Map Performance',
                'priority': 'high',
                'description': f'Struggling on {len(weak_maps)} maps',
                'action': f'Review strategy for: {", ".join(weak_maps[:3])}'
            })
        
        return areas
    
    def _generate_hero_roadmap(self, hero: str, weaknesses: List[Dict], strengths: List[Dict], 
                              trend: Dict[str, Any], verified_season: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement roadmap for a hero"""
        roadmap = []
        
        # High priority: address weaknesses
        for weakness in weaknesses:
            if weakness['severity'] == 'high':
                roadmap.append({
                    'priority': 'high',
                    'task': weakness['action'],
                    'area': weakness['area'],
                    'timeline': 'Immediate'
                })
        
        # Medium priority: build on strengths
        if strengths:
            roadmap.append({
                'priority': 'medium',
                'task': f'Continue playing {hero} - you\'re performing well',
                'area': 'Consistency',
                'timeline': 'Ongoing'
            })
        
        # Trend-based recommendations
        if trend['direction'] == 'declining':
            roadmap.append({
                'priority': 'high',
                'task': 'Review recent losses to identify what changed',
                'area': 'Trend Analysis',
                'timeline': 'This week'
            })
        elif trend['direction'] == 'improving':
            roadmap.append({
                'priority': 'low',
                'task': 'Keep up the good work - maintain current approach',
                'area': 'Momentum',
                'timeline': 'Ongoing'
            })
        
        return roadmap
    
    def _generate_overall_roadmap(self, improvement_areas: List[Dict], common_mistakes: List[Dict], 
                                  trend: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate overall improvement roadmap"""
        roadmap = []
        
        # Add improvement areas
        for area in improvement_areas:
            roadmap.append({
                'priority': area['priority'],
                'task': area['action'],
                'area': area['area'],
                'timeline': 'This month'
            })
        
        # Add mistake corrections
        for mistake in common_mistakes:
            roadmap.append({
                'priority': 'high',
                'task': mistake['action'],
                'area': mistake['mistake'],
                'timeline': 'This week'
            })
        
        return roadmap
    
    def _calculate_recent_wr(self, matches: List[Dict]) -> float:
        """Calculate win rate for recent matches"""
        if not matches:
            return 0
        wins = sum(1 for m in matches if m.get('result') == 'WIN')
        return (wins / len(matches)) * 100
    
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for improvement analysis"""
        hero = context.get('hero', 'Overall')
        query = context.get('query', '')
        
        return f"""
        COACH Agent Improvement Analysis Request
        
        Query: {query}
        Focus: {hero}
        
        Generate improvement roadmap and skill progression analysis.
        """
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """COACH handles improvement and progression queries"""
        query_lower = query.lower()
        coach_keywords = [
            'improve', 'better', 'progress', 'roadmap', 'weakness', 'strength',
            'practice', 'learn', 'skill', 'coach', 'help me', 'how to get better',
            'what should i work on', 'mistake', 'fix', 'training', 'performance',
            'forensic'
        ]
        return any(keyword in query_lower for keyword in coach_keywords)

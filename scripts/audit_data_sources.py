#!/usr/bin/env python3
"""
Comprehensive Data Source Audit Script
Validates data consistency across database, API, and frontend components.
"""

import sys
import os
import json
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.services.database import DatabaseManager
except ImportError:
    print("❌ Error: Could not import DatabaseManager")
    print("   Make sure database_manager.py is in the root directory")
    sys.exit(1)

class DataAudit:
    def __init__(self):
        self.db = DatabaseManager()
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def run_all_checks(self):
        """Run all audit checks"""
        print("🔍 Starting Comprehensive Data Source Audit...\n")
        
        # Phase 1: Database Integrity
        print("📊 Phase 1: Database Integrity")
        self.check_database_structure()
        self.check_match_data_completeness()
        self.check_kv_store_completeness()
        print()
        
        # Phase 2: Data Consistency
        print("🔄 Phase 2: Data Consistency")
        self.check_win_rate_consistency()
        self.check_stat_calculations()
        self.check_profile_stats_match_database()
        print()
        
        # Phase 3: Source Attribution
        print("📝 Phase 3: Source Attribution")
        self.check_hero_recommendation_sources()
        self.check_summary_source_attribution()
        print()
        
        # Phase 4: Data Quality
        print("✅ Phase 4: Data Quality")
        self.check_for_dummy_data()
        self.check_for_placeholder_text()
        self.check_for_external_blame_language()
        print()
        
        # Phase 5: File Integrity
        print("📁 Phase 5: File Integrity")
        self.check_data_files_valid()
        print()
        
        # Generate Report
        self.generate_report()
        
    def check_database_structure(self):
        """Check database structure and required fields"""
        try:
            matches = self.db.get_matches(limit=10)
            if not matches:
                self.warnings.append("No matches found in database")
                return
            
            required_fields = ['id', 'map', 'hero', 'result', 'date', 'players']
            sample_match = matches[0]
            
            for field in required_fields:
                if field not in sample_match:
                    self.issues.append(f"Missing required field: {field}")
                else:
                    self.passed.append(f"Required field present: {field}")
            
            # Check analysis structure
            if 'analysis' in sample_match:
                analysis = sample_match['analysis']
                analysis_fields = ['verdict', 'summary', 'win_condition_analysis']
                for field in analysis_fields:
                    if field not in analysis:
                        self.warnings.append(f"Analysis missing field: {field}")
                    else:
                        self.passed.append(f"Analysis field present: {field}")
                        
        except Exception as e:
            self.issues.append(f"Database structure check failed: {e}")
    
    def check_match_data_completeness(self):
        """Check all matches have required data"""
        try:
            matches = self.db.get_matches(limit=1000)
            total = len(matches)
            
            if total == 0:
                self.warnings.append("No matches in database")
                return
            
            incomplete = 0
            missing_analysis = 0
            
            for match in matches:
                if not all(k in match for k in ['id', 'map', 'hero', 'result']):
                    incomplete += 1
                if 'analysis' not in match or not match['analysis']:
                    missing_analysis += 1
            
            if incomplete > 0:
                self.issues.append(f"{incomplete}/{total} matches missing required fields")
            else:
                self.passed.append(f"All {total} matches have required fields")
            
            if missing_analysis > 0:
                self.warnings.append(f"{missing_analysis}/{total} matches missing analysis")
            else:
                self.passed.append(f"All {total} matches have analysis")
                
        except Exception as e:
            self.issues.append(f"Match completeness check failed: {e}")
    
    def check_kv_store_completeness(self):
        """Check key-value store has required data"""
        try:
            required_keys = [
                'player_profile',
                'cerebrate_config',
                'hero_roles',
                'map_meta'
            ]
            
            for key in required_keys:
                data = self.db.get_kv(key)
                if data is None:
                    self.warnings.append(f"KV store missing: {key}")
                else:
                    self.passed.append(f"KV store has: {key}")
                    
        except Exception as e:
            self.issues.append(f"KV store check failed: {e}")
    
    def check_win_rate_consistency(self):
        """Check win rates are consistent across different calculations"""
        try:
            matches = self.db.get_matches(limit=1000)
            if not matches:
                return
            
            # Get profile
            profile = self.db.get_kv('player_profile') or {}
            audit = profile.get('storm_league_audit', {})
            heroes = audit.get('heroes', {})
            
            # Calculate win rates from matches for each hero
            hero_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
            
            for match in matches:
                hero = match.get('hero')
                if not hero:
                    continue
                
                hero_stats[hero]['games'] += 1
                if match.get('result') == 'WIN':
                    hero_stats[hero]['wins'] += 1
            
            # Compare with profile audit
            discrepancies = []
            for hero, stats in hero_stats.items():
                if stats['games'] == 0:
                    continue
                    
                calculated_wr = (stats['wins'] / stats['games']) * 100
                
                if hero in heroes:
                    profile_wr = heroes[hero].get('win_rate', 0)
                    diff = abs(calculated_wr - profile_wr)
                    
                    if diff > 1.0:  # More than 1% difference
                        discrepancies.append({
                            'hero': hero,
                            'calculated': round(calculated_wr, 1),
                            'profile': profile_wr,
                            'diff': round(diff, 1),
                            'games': stats['games']
                        })
            
            if discrepancies:
                for disc in discrepancies[:5]:  # Show first 5
                    self.warnings.append(
                        f"Win rate mismatch: {disc['hero']} - "
                        f"Calculated: {disc['calculated']}%, "
                        f"Profile: {disc['profile']}% "
                        f"(diff: {disc['diff']}%)"
                    )
            else:
                self.passed.append(f"Win rates consistent across {len(hero_stats)} heroes")
                
        except Exception as e:
            self.issues.append(f"Win rate consistency check failed: {e}")
    
    def check_stat_calculations(self):
        """Check stat calculations match expected patterns"""
        try:
            matches = self.db.get_matches(limit=100)
            if not matches:
                return
            
            # Sample check: verify result field is valid
            valid_results = {'WIN', 'LOSS'}
            invalid_results = 0
            
            for match in matches:
                result = match.get('result')
                if result not in valid_results:
                    invalid_results += 1
            
            if invalid_results > 0:
                self.issues.append(f"{invalid_results} matches have invalid result field")
            else:
                self.passed.append("All match results are valid")
                
        except Exception as e:
            self.issues.append(f"Stat calculation check failed: {e}")
    
    def check_profile_stats_match_database(self):
        """Check profile stats match aggregated database stats"""
        try:
            profile = self.db.get_kv('player_profile') or {}
            audit = profile.get('storm_league_audit', {})
            
            # Check total games
            total_games = audit.get('total_games', 0)
            matches = self.db.get_matches(limit=10000)
            db_total = len(matches)
            
            if total_games > 0 and abs(total_games - db_total) > 5:
                self.warnings.append(
                    f"Game count mismatch: Profile says {total_games}, "
                    f"Database has {db_total}"
                )
            else:
                self.passed.append(f"Game counts match: {db_total} games")
                
        except Exception as e:
            self.issues.append(f"Profile stats check failed: {e}")
    
    def check_hero_recommendation_sources(self):
        """Check hero recommendations cite their sources"""
        try:
            # This would check frontend components, but since we're in Python,
            # we'll check the data that feeds recommendations
            profile = self.db.get_kv('player_profile') or {}
            audit = profile.get('storm_league_audit', {})
            heroes = audit.get('heroes', {})
            
            # Check heroes have win_rate and games_played
            missing_data = []
            for hero, stats in heroes.items():
                if 'win_rate' not in stats or 'games_played' not in stats:
                    missing_data.append(hero)
            
            if missing_data:
                self.warnings.append(
                    f"{len(missing_data)} heroes missing required stat fields"
                )
            else:
                self.passed.append(f"All {len(heroes)} heroes have complete stats")
                
        except Exception as e:
            self.issues.append(f"Hero recommendation source check failed: {e}")
    
    def check_summary_source_attribution(self):
        """Check summaries don't contain placeholder or dummy text"""
        try:
            matches = self.db.get_matches(limit=1000)
            placeholder_count = 0
            
            for match in matches:
                analysis = match.get('analysis', {})
                summary = analysis.get('summary', '')
                
                if not summary:
                    continue
                
                summary_lower = summary.lower()
                
                # Check for placeholder patterns
                if 'never, never' in summary_lower or 'never,' in summary_lower:
                    placeholder_count += 1
            
            if placeholder_count > 0:
                self.warnings.append(
                    f"{placeholder_count} summaries contain placeholder timestamps"
                )
            else:
                self.passed.append("No placeholder timestamps found")
                
        except Exception as e:
            self.issues.append(f"Summary attribution check failed: {e}")
    
    def check_for_dummy_data(self):
        """Check for emergency baseline or dummy data"""
        try:
            profile = self.db.get_kv('player_profile') or {}
            audit = profile.get('storm_league_audit', {})
            heroes = audit.get('heroes', {})
            
            # Check if all heroes have exactly 50.0% WR (emergency baseline)
            all_50 = all(
                hero.get('win_rate', 0) == 50.0 
                for hero in heroes.values()
            ) if heroes else False
            
            if all_50 and len(heroes) > 0:
                self.issues.append(
                    "Emergency baseline detected: All heroes at 50.0% WR "
                    "(likely using dummy data)"
                )
            else:
                self.passed.append("No emergency baseline detected")
                
        except Exception as e:
            self.issues.append(f"Dummy data check failed: {e}")
    
    def check_for_placeholder_text(self):
        """Check for placeholder text in summaries"""
        try:
            matches = self.db.get_matches(limit=1000)
            placeholder_patterns = ['never', 'n/a', 'unknown', 'tbd', 'placeholder']
            
            placeholder_matches = []
            for match in matches:
                analysis = match.get('analysis', {})
                summary = analysis.get('summary', '') + ' ' + analysis.get('win_condition_analysis', '')
                
                if not summary:
                    continue
                
                summary_lower = summary.lower()
                for pattern in placeholder_patterns:
                    if pattern in summary_lower and match['id'] not in [m['id'] for m in placeholder_matches]:
                        # Check context - "Never" alone might be valid
                        if pattern == 'never' and 'never,' not in summary_lower and 'never, never' not in summary_lower:
                            continue
                        placeholder_matches.append({
                            'id': match['id'][:8],
                            'hero': match.get('hero', 'Unknown'),
                            'pattern': pattern
                        })
                        break
            
            if placeholder_matches:
                self.warnings.append(
                    f"{len(placeholder_matches)} matches contain placeholder text: "
                    f"{', '.join(set(m['pattern'] for m in placeholder_matches[:10]))}"
                )
            else:
                self.passed.append("No placeholder text found")
                
        except Exception as e:
            self.issues.append(f"Placeholder text check failed: {e}")
    
    def check_for_external_blame_language(self):
        """Check for external blame language (accountability violations)"""
        try:
            matches = self.db.get_matches(limit=1000)
            forbidden_phrases = [
                'teammates to', 'team failed', 'allies to peel', 'forcing a 4v5',
                'enabling enemy', 'allowing enemy', 'permits teammates',
                'team suffered', 'team achieved', 'your team underperformed'
            ]
            
            violations = []
            for match in matches:
                analysis = match.get('analysis', {})
                summary = analysis.get('summary', '')
                
                if not summary:
                    continue
                
                summary_lower = summary.lower()
                found_phrases = [p for p in forbidden_phrases if p in summary_lower]
                
                if found_phrases:
                    violations.append({
                        'id': match['id'][:8],
                        'hero': match.get('hero', 'Unknown'),
                        'phrases': found_phrases
                    })
            
            if violations:
                self.issues.append(
                    f"❌ CRITICAL: {len(violations)} summaries contain external blame language "
                    f"(Accountability violations)"
                )
                for v in violations[:5]:
                    self.issues.append(
                        f"   Match {v['id']} ({v['hero']}): {', '.join(v['phrases'])}"
                    )
            else:
                self.passed.append("No external blame language found")
                
        except Exception as e:
            self.issues.append(f"External blame check failed: {e}")
    
    def check_data_files_valid(self):
        """Check data files are valid JSON"""
        try:
            data_files = [
                'src/data/hero_data.json',
                'src/data/talent_id_map.json',
                'src/data/talents.json',
                'src/data/global_hero_stats_stormleague_plus_talents.json'
            ]
            
            valid_files = 0
            for filepath in data_files:
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            json.load(f)
                        self.passed.append(f"Valid JSON: {os.path.basename(filepath)}")
                        valid_files += 1
                    except json.JSONDecodeError as e:
                        self.issues.append(f"Invalid JSON: {os.path.basename(filepath)} - {e}")
                else:
                    self.warnings.append(f"File not found: {os.path.basename(filepath)}")
            
            if valid_files == len(data_files):
                self.passed.append(f"All {valid_files} data files are valid JSON")
                
        except Exception as e:
            self.issues.append(f"Data file validation failed: {e}")
    
    def generate_report(self):
        """Generate final audit report"""
        print("=" * 60)
        print("📊 AUDIT REPORT")
        print("=" * 60)
        print()
        
        # Calculate health score
        total_checks = len(self.passed) + len(self.warnings) + len(self.issues)
        health_score = int((len(self.passed) / total_checks * 100)) if total_checks > 0 else 0
        
        print(f"Health Score: {health_score}%")
        print(f"✅ PASSED: {len(self.passed)} checks")
        print(f"⚠️  WARNINGS: {len(self.warnings)} issues")
        print(f"❌ CRITICAL: {len(self.issues)} issues")
        print()
        
        # Show passed checks (summary)
        if self.passed:
            print("✅ PASSED CHECKS:")
            for check in self.passed[:10]:  # Show first 10
                print(f"   {check}")
            if len(self.passed) > 10:
                print(f"   ... and {len(self.passed) - 10} more")
            print()
        
        # Show warnings
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        # Show critical issues
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   {issue}")
            print()
        
        # Recommendations
        print("📋 RECOMMENDATIONS:")
        if self.issues:
            print("   1. Fix critical issues first (external blame language, dummy data)")
            print("   2. Re-analyze matches with parser v2.9 to fix old summaries")
            print("   3. Run: rm .processed_replays.txt to force full re-analysis")
        elif self.warnings:
            print("   1. Address warnings (placeholder text, missing data)")
            print("   2. Background watcher will fix old summaries automatically")
        else:
            print("   ✅ All checks passed! System is healthy.")
        print()
        
        # Exit code: 0 if clean, 1 if issues found
        exit_code = 1 if self.issues else (0 if not self.warnings else 1)
        
        print(f"Exit Code: {exit_code} (0 = clean, 1 = issues found)")
        sys.exit(exit_code)


if __name__ == "__main__":
    audit = DataAudit()
    audit.run_all_checks()

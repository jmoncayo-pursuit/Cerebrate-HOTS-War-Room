import datetime

class AuditEngine:
    def __init__(self, hp_client):
        self.client = hp_client

    def run_audit(self, season):
        print(f"Starting audit for {season}...")
        
        # 1. Fetch Data
        current_stats = self.client.get_season_stats(season)
        lifetime_stats = self.client.get_lifetime_stats()
        
        # Convert to dict for easier lookup
        lifetime_map = {h['hero']: h for h in lifetime_stats}
        
        # 2. Analyze Deltas
        audit_results = {
            "critical_slump": [],
            "slump": [],
            "on_form": [],
            "improving": [],
            "all_data": []
        }
        
        for hero_stat in current_stats:
            hero_name = hero_stat['hero']
            s3_wr = hero_stat['win_rate']
            s3_games = hero_stat['games']
            
            if s3_games < 10:
                continue # Ignore low sample size per spec
                
            lt_stat = lifetime_map.get(hero_name)
            
            if lt_stat and lt_stat['games'] >= 50:
                lt_wr = lt_stat['win_rate']
                delta = s3_wr - lt_wr
                
                entry = {
                    "hero": hero_name,
                    "s3_wr": s3_wr,
                    "lt_wr": lt_wr,
                    "delta": delta,
                    "games": s3_games
                }
                
                if delta < -10.0:
                    audit_results["critical_slump"].append(entry)
                    entry['status'] = "🔴 CRITICAL"
                elif delta < -5.0:
                    audit_results["slump"].append(entry)
                    entry['status'] = "⚠️ SLUMP"
                elif delta > 5.0:
                    audit_results["improving"].append(entry)
                    entry['status'] = "📈 IMPROVING"
                else:
                    audit_results["on_form"].append(entry)
                    entry['status'] = "✅ ON FORM"
                    
                audit_results["all_data"].append(entry)

        # 3. Generate Report
        report = self._generate_markdown_report(season, audit_results)
        return report

    def _generate_markdown_report(self, season, data):
        date_str = datetime.date.today().strftime("%B %d, %Y")
        
        report = f"""# Storm League Performance Audit - {season}
**Player:** CerebrateUser
**Date:** {date_str}
**Analyst:** Cerebrate AI War Room

---

## Executive Summary

Audit found **{len(data['critical_slump'])} Critical Underperformers** and **{len(data['slump'])} Slumps**.

"""
        # Critical List
        for i, item in enumerate(data['critical_slump'] + data['slump']):
             report += f"{i+1}. **{item['hero']}** ({item['delta']:.2f}%, {item['games']} games)\n"
             
        report += "\n---\n\n## Part 1: Performance Delta Analysis\n\n"
        report += "| Hero | Lifetime WR | Season WR | Delta | Games | Severity |\n"
        report += "|------|-------------|-----------|-------|-------|----------|\n"
        
        # Sort by worst delta first
        sorted_all = sorted(data['all_data'], key=lambda x: x['delta'])
        
        for item in sorted_all:
            report += f"| **{item['hero']}** | {item['lt_wr']:.2f}% | {item['s3_wr']:.2f}% | **{item['delta']:.2f}%** | {item['games']} | {item['status']} |\n"

        report += "\n---\n\n## Part 2: Diagnosis & Action Plan\n\n"
        
        slumps = data['critical_slump'] + data['slump']
        
        if not slumps:
            report += "No major slumps detected. Keep up the good work!\n"
        
        for item in slumps:
            report += f"### {item['hero']}\n"
            report += f"- **Current WR:** {item['s3_wr']:.2f}%\n"
            report += f"- **Lifetime WR:** {item['lt_wr']:.2f}%\n"
            report += f"- **Delta:** {item['delta']:.2f}%\n"
            report += "- **Potential Root Cause:** [To be analyzed - Check Patch Notes]\n"
            report += "- **Recommended Fix:** Review talent builds and meta changes.\n\n"
            
        report += """---

**Report Generated:** {date}
**Analyst:** Cerebrate AI War Room
**Workflow:** `/storm-league-performance-audit`
""".format(date=date_str)

        return report

if __name__ == "__main__":
    # Test stub
    pass

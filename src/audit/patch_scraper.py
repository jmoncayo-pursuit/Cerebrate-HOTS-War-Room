"""
Real Patch Scraper for heroespatchnotes.com

This module scrapes actual patch data from heroespatchnotes.com
and parses talent changes for obsolete build detection.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re


class HeroesPatchNotesScraper:
    """Scrapes patch notes from heroespatchnotes.com."""
    
    def __init__(self):
        self.base_url = "https://heroespatchnotes.com"
        
    def get_hero_patch_history(self, hero_name):
        """
        Scrape full patch history for a hero.
        
        Args:
            hero_name (str): Hero name (e.g., "Gazlowe")
            
        Returns:
            list: List of patch entries with changes
        """
        # Convert hero name to URL slug
        hero_slug = self._hero_name_to_slug(hero_name)
        url = f"{self.base_url}/hero/{hero_slug}"
        
        print(f"Scraping {url}...")
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            patches = []
            
            # Find all patch panels (div.panel.panel-primary)
            patch_panels = soup.find_all('div', class_='panel panel-primary')
            
            if not patch_panels:
                print(f"No patch panels found for {hero_name}")
                return []
            
            print(f"Found {len(patch_panels)} patch panels")
            
            for panel in patch_panels:
                patch_data = self._parse_patch_panel(panel)
                if patch_data and patch_data['changes']:
                    patches.append(patch_data)
            
            return patches
            
        except requests.RequestException as e:
            print(f"Error scraping patch notes: {e}")
            return []
    
    def _hero_name_to_slug(self, hero_name):
        """Convert hero name to URL slug."""
        # Remove special characters, lowercase, remove spaces
        slug = hero_name.lower()
        slug = slug.replace("'", "")
        slug = slug.replace(".", "")
        slug = slug.replace(" ", "")
        return slug
    
    def _parse_patch_panel(self, panel):
        """Parse a single patch panel."""
        try:
            # Extract patch date from header
            header = panel.find('h3')
            if not header:
                return None
            
            header_text = header.get_text()
            
            # Extract date (format: "2023-11-16 Patch Notes")
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', header_text)
            patch_date = date_match.group(1) if date_match else "Unknown"
            
            version_tag = header.find('small')
            version = version_tag.get_text().strip() if version_tag else "Unknown"
            
            # Find panel body
            panel_body = panel.find('div', class_='panel-body')
            if not panel_body:
                return None
            
            changes = []
            
            # Find "Talents" section
            # Can be either <p><strong>Talents</strong></p> or <h4>Talents</h4>
            talents_markers = panel_body.find_all(['p', 'h4'])
            
            for marker in talents_markers:
                marker_text = marker.get_text().strip()
                
                if marker_text in ['Talents', 'Abilities', 'Hero Updates']:
                    # Get the next sibling (should be a <ul>)
                    next_elem = marker.find_next_sibling()
                    
                    if next_elem and next_elem.name == 'ul':
                        # Parse nested talent list
                        talent_changes = self._parse_talent_list(next_elem)
                        changes.extend(talent_changes)
            
            return {
                "date": patch_date,
                "version": version,
                "changes": changes
            }
            
        except Exception as e:
            print(f"Error parsing patch panel: {e}")
            return None
    
    def _parse_talent_list(self, ul_element):
        """
        Parse nested talent list structure.
        
        Structure:
        <ul>
          <li><strong>Level 10</strong>
            <ul>
              <li>Tormented Souls [R1]
                <ul>
                  <li>Cooldown reduced from 80 to 60 seconds.</li>
                </ul>
              </li>
            </ul>
          </li>
        </ul>
        """
        changes = []
        
        for li in ul_element.find_all('li', recursive=False):
            # Check if this is a tier marker (e.g., "Level 10")
            tier_text = li.find(text=True, recursive=False)
            if tier_text:
                tier_text = tier_text.strip()
            
            # Look for nested ul (talent names)
            nested_ul = li.find('ul')
            if nested_ul:
                for talent_li in nested_ul.find_all('li', recursive=False):
                    # Extract talent name (first text node)
                    talent_name_node = talent_li.find(text=True, recursive=False)
                    if talent_name_node:
                        talent_name = talent_name_node.strip()
                        
                        # Remove bracketed suffixes like [R1], [Q], (Trait)
                        talent_name = re.sub(r'\s*\[.*?\]|\s*\(.*?\)', '', talent_name)
                        
                        # Look for change descriptions (innermost ul)
                        change_ul = talent_li.find('ul')
                        if change_ul:
                            for change_li in change_ul.find_all('li', recursive=False):
                                description = change_li.get_text().strip()
                                
                                if description:
                                    # Parse the change
                                    change = self._parse_talent_change_from_desc(
                                        talent_name,
                                        description
                                    )
                                    if change:
                                        changes.append(change)
        
        return changes
    
    def _parse_talent_change_from_desc(self, talent_name, description):
        """Parse talent change from talent name and description."""
        # Determine change type
        change_type = self._classify_change(description)
        
        # Determine severity
        severity = self._classify_severity(description)
        
        return {
            "talent": talent_name,
            "description": description,
            "change_type": change_type,
            "severity": severity
        }
    
    def _classify_change(self, description):
        """Classify if a change is a buff, nerf, or rework."""
        desc_lower = description.lower()
        
        # Special case: "reduced" can be buff or nerf depending on context
        # Buff: "cooldown reduced", "mana cost reduced"
        # Nerf: "damage reduced", "duration reduced"
        if 'reduced' in desc_lower or 'decreased' in desc_lower:
            buff_contexts = ['cooldown', 'mana cost', 'mana', 'cost']
            nerf_contexts = ['damage', 'duration', 'health', 'shield', 'armor', 'range']
            
            if any(context in desc_lower for context in buff_contexts):
                return "buff"
            elif any(context in desc_lower for context in nerf_contexts):
                return "nerf"
        
        # Nerf indicators
        nerf_keywords = ['removed', 'no longer', 'nerfed']
        if any(keyword in desc_lower for keyword in nerf_keywords):
            return "nerf"
        
        # Buff indicators
        buff_keywords = ['increased', 'improved', 'added', 'now', 'buffed', 'bonus']
        if any(keyword in desc_lower for keyword in buff_keywords):
            return "buff"
        
        # Rework indicators
        rework_keywords = ['reworked', 'changed to', 'moved from', 'replaced']
        if any(keyword in desc_lower for keyword in rework_keywords):
            return "rework"
        
        return "unknown"
    
    def _classify_severity(self, description):
        """Classify severity of a change (major/minor)."""
        desc_lower = description.lower()
        
        # Major change indicators
        major_keywords = [
            'removed', 'no longer', 'moved from', 'replaced',
            '50%', '40%', '30%',  # Large percentage changes
            'reworked'
        ]
        
        if any(keyword in desc_lower for keyword in major_keywords):
            return "major"
        
        # Check for large numerical changes
        numbers = re.findall(r'\d+', description)
        if len(numbers) >= 2:
            try:
                old_val = int(numbers[0])
                new_val = int(numbers[1])
                if abs(new_val - old_val) / max(old_val, 1) > 0.2:  # >20% change
                    return "major"
            except:
                pass
        
        return "minor"


# Example usage
if __name__ == "__main__":
    scraper = HeroesPatchNotesScraper()
    
    # Test scraping Gazlowe
    patches = scraper.get_hero_patch_history("Gazlowe")
    
    print(f"Found {len(patches)} patches for Gazlowe")
    
    if patches:
        print("\nMost recent patch:")
        print(json.dumps(patches[0], indent=2))

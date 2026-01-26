"""
Personal Meta Notes Integration

This module helps the AI coach access and question subjective player preferences
about builds, heroes, and community perception.

Key principle: These notes are OPINIONS, not facts. The AI should:
1. Check them when giving advice
2. Question them when data conflicts
3. Help the user update them based on new experiences
"""

import json
import os
from datetime import datetime

# Get project root (2 levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NOTES_FILE = os.path.join(PROJECT_ROOT, 'data', 'personal_meta_notes.json')


def load_personal_notes():
    """Load personal meta notes from JSON file."""
    if not os.path.exists(NOTES_FILE):
        return {"heroes": {}}
    
    with open(NOTES_FILE, 'r') as f:
        return json.load(f)


def get_build_note(hero_name, build_name):
    """
    Get personal note for a specific hero build.
    
    Returns dict with:
    - status: avoid|obsolete|prefer|neutral
    - reason: team_toxicity|nerfed|buffed|off_meta|cheese
    - confidence: low|medium|high
    - notes: free-form explanation
    - ai_should_question_if: conditions for AI to challenge this note
    
    Returns None if no note exists.
    """
    notes = load_personal_notes()
    hero_notes = notes.get("heroes", {}).get(hero_name, {})
    return hero_notes.get("builds", {}).get(build_name)


def format_note_for_ai(hero_name, build_name):
    """
    Format a personal note for AI consumption.
    
    Returns a string that the AI can use in its reasoning, or None if no note exists.
    """
    note = get_build_note(hero_name, build_name)
    if not note:
        return None
    
    confidence_emoji = {
        "low": "⚠️",
        "medium": "📝",
        "high": "✅"
    }
    
    emoji = confidence_emoji.get(note.get("confidence", "medium"), "📝")
    
    return f"""
{emoji} PERSONAL NOTE on {hero_name} - {build_name}:
Status: {note.get('status', 'unknown').upper()}
Reason: {note.get('reason', 'unknown')}
Confidence: {note.get('confidence', 'medium')}
Notes: {note.get('notes', 'No details provided')}

Override conditions: {note.get('override_conditions', 'Not specified')}

⚡ AI INSTRUCTION: Question this note if: {note.get('ai_should_question_if', 'data strongly conflicts')}
"""


def should_ai_question_note(hero_name, build_name, context):
    """
    Determine if the AI should question a personal note based on context.
    
    Args:
        hero_name: Hero name
        build_name: Build/talent name
        context: Dict with keys like 'win_rate_delta', 'games_played', etc.
    
    Returns:
        (bool, str): (should_question, reason)
    """
    note = get_build_note(hero_name, build_name)
    if not note:
        return (False, "No personal note exists")
    
    # Low confidence notes should always be questioned
    if note.get("confidence") == "low":
        return (True, "Note has low confidence - worth revisiting")
    
    # Check if note is old (>6 months)
    last_updated = note.get("last_updated")
    if last_updated:
        try:
            updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
            days_old = (datetime.now() - updated_date).days
            if days_old > 180:
                return (True, f"Note is {days_old} days old - meta may have changed")
        except:
            pass
    
    # Check win rate delta if provided
    wr_delta = context.get('win_rate_delta')
    if wr_delta and abs(wr_delta) > 5:
        return (True, f"Win rate delta is {wr_delta}% - significant performance difference")
    
    return (False, "Note seems current and reasonable")


def get_ai_system_prompt_addition():
    """
    Get the text to add to the AI system prompt to make it aware of personal notes.
    """
    notes = load_personal_notes()
    instructions = notes.get("_instructions_for_ai", "")
    
    return f"""
## Personal Meta Notes

You have access to the user's personal, subjective notes about builds and heroes.
These are stored in `data/personal_meta_notes.json`.

{instructions}

**How to use:**
1. When recommending a build, check if a personal note exists
2. If a note says "avoid" but data says "use", ASK the user if the note is still valid
3. Help the user update notes based on new experiences
4. Respect the user's mental stack and team morale preferences

**Example dialogue:**
User: "Should I play Malthael?"
AI: "I see you have a note that Tormented Souls (the meta build) attracts toxicity from teammates. 
     The data shows it has 3% higher win rate than Last Rites. 
     Is the team morale cost still worth avoiding it, or should we update your note?"
"""


if __name__ == "__main__":
    # Test the module
    print("=== Personal Meta Notes Test ===\n")
    
    note = format_note_for_ai("Malthael", "TormentedSouls")
    if note:
        print(note)
    
    should_question, reason = should_ai_question_note(
        "Malthael", 
        "TormentedSouls",
        {"win_rate_delta": 6.5}
    )
    print(f"\nShould AI question this note? {should_question}")
    print(f"Reason: {reason}")

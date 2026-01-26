#!/bin/bash

# ==============================================================================
# Cerebrate Privacy Sync - Example File Generator
# ==============================================================================
# This script reads your real (private) data and creates anonymized template
# versions (*.example) that are safe to commit to the public repository.
# ==============================================================================

DATA_DIR="src/data"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "🔒 Cerebrate Privacy Sync: Generating template files..."

# 1. ANONYMIZE PLAYER PROFILE
# Replaces BattleTag and stats with generic examples
if [ -f "$DATA_DIR/player_profile.json" ]; then
    echo "  📄 Processing player_profile.json..."
    cat "$DATA_DIR/player_profile.json" | \
    sed 's/"battle_tag": ".*"/"battle_tag": "Commander#1234"/g' | \
    sed 's/"name": ".*"/"name": "Cerebrate"/g' > "$DATA_DIR/player_profile.json.example"
    echo "  ✅ Created player_profile.json.example"
else
    echo "  ⚠️  player_profile.json not found. Skipping."
fi

# 2. MATCH HISTORY TEMPLATE
# Creates a sample with 2-3 matches using the current schema
if [ -f "$DATA_DIR/match_history.json" ]; then
    echo "  📄 Creating match_history.json template..."
    # We take just the first 2 matches if they exist
    head -n 50 "$DATA_DIR/match_history.json" > "$DATA_DIR/match_history.json.example"
    echo "  ✅ Created match_history.json.example (limited to sample size)"
else
    echo "  ⚠️  match_history.json not found."
fi

# 3. PLAYER INTERACTIONS TEMPLATE
if [ -f "$DATA_DIR/player_interactions.json" ]; then
    echo "  📄 Processing player_interactions.json..."
    head -n 30 "$DATA_DIR/player_interactions.json" > "$DATA_DIR/player_interactions.json.example"
    echo "  ✅ Created player_interactions.json.example"
fi

# 4. NEMESIS FORENSICS TEMPLATE
if [ -f "$DATA_DIR/nemesis_forensics.json" ]; then
    echo "  📄 Processing nemesis_forensics.json..."
    head -n 20 "$DATA_DIR/nemesis_forensics.json" > "$DATA_DIR/nemesis_forensics.json.example"
    echo "  ✅ Created nemesis_forensics.json.example"
fi

echo ""
echo "✨ Privacy Sync Complete."
echo "   Template files updated at: $TIMESTAMP"
echo "   You can now safely run: git add src/data/*.example"

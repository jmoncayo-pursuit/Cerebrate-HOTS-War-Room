"""
Static Map Strategy Summaries
Pre-verified, non-hallucinated summaries for quick map queries.
These are returned when no specific match context is provided.
"""

MAP_STRATEGY_SUMMARIES = {
    "Towers of Doom": {
        "win_condition": "Control Bell Towers to amplify Altar damage. The core is invulnerable—all damage comes from objectives.",
        "critical_objective": "The Boss (Headless Horseman) deals 4 core damage. Use it to finish games or force enemy response.",
        "key_timings": "First Altar: 3:00. Boss spawns: ~6:00. Altars spawn in sets of 3 (Top, Mid, Bot).",
        "macro_priority": "Escort Sappers for guaranteed 1 core damage each. They are 'walking core damage'.",
        "draft_focus": "Global heroes (Falstad, Dehaka) excel for Altar rotations. Sustained damage beats burst."
    },
    "Infernal Shrines": {
        "win_condition": "Win Shrines to summon Punishers. The Punisher targets structures and is extremely powerful early game.",
        "critical_objective": "First Punisher often decides the game tempo. Contest it with full team.",
        "key_timings": "First Shrine: 3:00. Subsequent Shrines spawn 2 min after Punisher dies.",
        "macro_priority": "Clear the 40 Shrine Guardians faster than the enemy. AoE damage is critical.",
        "draft_focus": "Johanna, Jaina, Kael'thas, and any AoE-heavy hero dominates Shrine clear speed."
    },
    "Cursed Hollow": {
        "win_condition": "Collect 3 Tributes to curse the enemy team, disabling their structures and minions.",
        "critical_objective": "The Curse is a massive siege window. Use it to push multiple lanes simultaneously.",
        "key_timings": "First Tribute: 3:00. Tributes spawn randomly in one of 6 locations.",
        "macro_priority": "Soak during Tribute fights if your team is down players. Don't fight 4v5.",
        "draft_focus": "Mobile heroes with strong teamfight (e.g., Falstad, E.T.C., Malfurion) are valuable."
    },
    "Dragon Shire": {
        "win_condition": "Control both Shrines (Top and Bot) to activate the Dragon Knight in Mid.",
        "critical_objective": "The Dragon Knight is a siege monster. Pilot it into enemy structures, not into fights.",
        "key_timings": "Shrines unlock at 1:30. Dragon Knight lasts ~40 seconds.",
        "macro_priority": "Split push to force the enemy to choose which Shrine to defend.",
        "draft_focus": "Strong solo laners (Malthael, Leoric, Blaze) hold Shrines. Global heroes enable fast rotations."
    },
    "Sky Temple": {
        "win_condition": "Capture Temples to have them fire lasers at enemy structures.",
        "critical_objective": "Temple shots deal massive structure damage. Prioritize defending your own structures.",
        "key_timings": "First Temples (Top+Mid): 1:30. Boss spawns at ~5:00.",
        "macro_priority": "You don't need to win every Temple, but don't give them all up for free.",
        "draft_focus": "Sustained damage helps hold Temples. Heroes with zoning (Chromie, Azmodan) are strong."
    },
    "Battlefield of Eternity": {
        "win_condition": "Race to kill the enemy Immortal. Your Immortal then pushes a lane and deals structure damage.",
        "critical_objective": "Immortal HP is shared. Focus fire beats split damage.",
        "key_timings": "First Immortal: 1:45. Immortals spawn alternating Top and Bot.",
        "macro_priority": "If you lose an Immortal fight badly, stall by poking the enemy Immortal to reduce its HP.",
        "draft_focus": "Single-target burst (Greymane, Valla, Hanzo) and race-oriented comps are king."
    },
    "Tomb of the Spider Queen": {
        "win_condition": "Collect Gems from enemy minions and turn them in to summon Webweavers.",
        "critical_objective": "Dying drops half your Gems. Don't overextend with a full pocket.",
        "key_timings": "First turn-in available: ~2:00. Webweavers spawn in all 3 lanes.",
        "macro_priority": "Aggressive laning and ganking to deny enemy Gems. The map is small and rotation-heavy.",
        "draft_focus": "Strong wave clear (Xul, Nazeebo, Johanna) accelerates Gem collection."
    },
    "Volskaya Foundry": {
        "win_condition": "Capture Control Points to earn a Triglav Protector, a two-player mech.",
        "critical_objective": "The Protector is extremely powerful. Use it to siege, not to chase kills.",
        "key_timings": "First Capture Point: 3:00. Protector lasts ~40 seconds.",
        "macro_priority": "Conveyors (moving platforms) can be used for creative rotations and escapes.",
        "draft_focus": "Heroes with strong point presence (Johanna, Arthas, Blaze) control the objective."
    },
    "Blackheart's Bay": {
        "win_condition": "Collect Doubloons (from chests, camps, and enemy deaths) and turn them in to Blackheart.",
        "critical_objective": "Blackheart's cannons fire at structures. The first bombardment often decides the game.",
        "key_timings": "First Chests: 0:50. Boss spawns at ~4:00 and drops 10 Doubloons.",
        "macro_priority": "Deny the Boss. It's the single largest Doubloon source.",
        "draft_focus": "Strong PvE (Greymane, Valla) and global heroes (Falstad, Dehaka) dominate."
    },
    "Warhead Junction": {
        "win_condition": "Collect Nukes and use them to deal massive structure damage.",
        "critical_objective": "Nukes deal ~60% Fort HP per hit. Save them for structures, not heroes.",
        "key_timings": "First Nukes: 2:00. Multiple Nukes spawn across the map.",
        "macro_priority": "The map is huge. Split soak is rewarded. Only group for Boss or critical fights.",
        "draft_focus": "Global heroes (Falstad, Dehaka, Brightwing) excel at collecting scattered Nukes."
    },
    "Alterac Pass": {
        "win_condition": "Escort your Cavalry and protect your Generals. The enemy General is the core.",
        "critical_objective": "Cavalry spawn periodically and push. Protect them for siege value.",
        "key_timings": "First Cavalry: 1:30. Generals have ~5000 HP and regenerate.",
        "macro_priority": "Mudpit camps (Gnolls) give armor to your cavalry. Take them before pushes.",
        "draft_focus": "Strong frontline and sustained damage to protect Cavalry during sieges."
    },
    "Hanamura Temple": {
        "win_condition": "Capture payloads and escort them to the enemy base to deal core damage.",
        "critical_objective": "Payloads deal 1-2 core damage based on map control. Contesting is critical.",
        "key_timings": "First Payload: 2:30. Camps give sappers that push lanes.",
        "macro_priority": "Recon camps provide vision and should be taken before objectives.",
        "draft_focus": "Heroes with strong lane presence and sustain for long escort fights."
    },
    "Braxis Holdout": {
        "win_condition": "Control Beacons to charge your Zerg Wave. The larger wave wins the push.",
        "critical_objective": "A 100% Zerg Wave is devastating. Don't give it up for free.",
        "key_timings": "First Beacons: 1:45. Beacons spawn Top and Bot.",
        "macro_priority": "Strong solo laners are critical. Win both lanes = 100% wave.",
        "draft_focus": "Solo laners (Malthael, Yrel, Blaze) and strong 4-man rotation heroes."
    },
    "Garden of Terror": {
        "win_condition": "Collect Seeds from camps and plant a Garden Terror to push a lane.",
        "critical_objective": "The Terror's Overgrowth ability disables structures. Use it on Forts/Keeps.",
        "key_timings": "First Seeds: 3:00. Seeds spawn from Shamblers in lane.",
        "macro_priority": "Control the large Shambler camps for accelerated Seed collection.",
        "draft_focus": "Strong wave clear and camp control. The map rewards aggressive macro."
    }
}

def get_quick_summary(map_name):
    """
    Get a quick, non-hallucinated summary for a map.
    Returns None if the map is not recognized.
    """
    return MAP_STRATEGY_SUMMARIES.get(map_name)

/**
 * Normalizes a hero name to a standard format used for file lookups and internal keys.
 * Handles casing, accents, special characters, and common aliases.
 * 
 * @param {string} name - The original hero name
 * @returns {string} - The normalized name (e.g., "Lúcio" -> "lucio", "Mal'Ganis" -> "malganis")
 */
export const normalizeHeroName = (name) => {
    if (!name) return '';

    let normalized = name.toLowerCase().trim();

    // Special cases mapping (prioritize these)
    const specialCases = {
        // Punctuation & Spacing
        "the butcher": "thebutcher",
        "butcher": "thebutcher",
        "the lost vikings": "lostvikings",
        "lost vikings": "lostvikings",
        "vikings": "lostvikings",
        "tlv": "lostvikings",
        "sgt. hammer": "sgthammer",
        "sgt hammer": "sgthammer",
        "hammer": "sgthammer",
        "lt. morales": "ltmorales",
        "lt morales": "ltmorales",
        "morales": "ltmorales",
        "d.va": "dva",
        "dva": "dva",
        "e.t.c.": "etc",
        "etc": "etc",
        "e.t.c": "etc",
        "anub'arak": "anubarak",
        "anubarak": "anubarak",
        "kael'thas": "kaelthas",
        "kaelthas": "kaelthas",
        "kel'thuzad": "kelthuzad",
        "kelthuzad": "kelthuzad",
        "zul'jin": "zuljin",
        "zuljin": "zuljin",
        "gul'dan": "guldan",
        "guldan": "guldan",
        "mal'ganis": "malganis",
        "malganis": "malganis",
        "li li": "lili",
        "lili": "lili",
        "li-ming": "liming",
        "liming": "liming",
        "li ming": "liming",
        "cho'gall": "chogall", // Should split usually but handle safely
        "gall": "gall",
        "cho": "cho",
        "lucio": "lucio",
        "lúcio": "lucio",
        "torbjorn": "torbjorn", // Overwatch names just in case
        "junkrat": "junkrat",
        // Common mistypes or short names
        "gaz": "gazlowe",
        "azmo": "azmodan",
        "naz": "nazeebo",
        "nazeebo": "nazeebo",
        "sylv": "sylvanas",
        "sylvanas": "sylvanas",
        "rag": "ragnaros",
        "ragnaros": "ragnaros",
        "val": "valla",
        "valla": "valla",
        "bw": "brightwing",
        "brightwing": "brightwing"
    };

    // 1. Direct lookup in special cases (fast path)
    if (specialCases[normalized]) {
        return specialCases[normalized];
    }

    // 2. Try stripping punctuation manually if not in special cases
    // This catches "Kael'thas" -> "kaelthas" if somehow missed above
    const stripped = normalized.replace(/[^a-z0-9]/g, "");
    if (specialCases[stripped]) {
        return specialCases[stripped];
    }

    // 3. Last result: the stripped version
    return stripped;
};

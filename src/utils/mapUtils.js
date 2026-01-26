export const getMapImagePath = (mapName) => {
    if (!mapName) return '/images/maps/unknown.png'

    // Map name normalization - handle common variations
    const nameMap = {
        'hanamura temple': 'hanamura-temple',
        'hanamura': 'hanamura',
        'cursed hollow': 'cursed-hollow',
        'dragon shire': 'dragon-shire',
        'garden of terror': 'garden-of-terror',
        'tomb of the spider queen': 'tomb-of-the-spider-queen',
        'tomb of spider queen': 'tomb-of-the-spider-queen',
        'towers of doom': 'towers-of-doom',
        'warhead junction': 'warhead-junction',
        'infernal shrines': 'infernal-shrines',
        'sky temple': 'sky-temple',
        'braxis holdout': 'braxis-holdout',
        'blackheart\'s bay': 'blackhearts-bay',
        'blackhearts bay': 'blackhearts-bay',
        'battlefield of eternity': 'battlefield-of-eternity',
        'alterac pass': 'alterac-pass',
        'volskaya foundry': 'volskaya-foundry',
    }

    const lower = mapName.toLowerCase().trim()
    const normalized = nameMap[lower] || lower
        .replace(/'/g, '')
        .replace(/\s+/g, '-')
        .replace(/\./g, '')
        .replace(/_/g, '-')

    return `/images/maps/${normalized}.png`
}

export const getMapColor = (mapName) => {
    if (!mapName) return 'var(--md-sys-color-primary)'

    // Generate consistent color from map name
    let hash = 0
    for (let i = 0; i < mapName.length; i++) {
        hash = mapName.charCodeAt(i) + ((hash << 5) - hash)
    }
    const hue = Math.abs(hash % 360)
    return `hsl(${hue}, 40%, 40%)` // Slightly desaturated for MD3 vibe
}

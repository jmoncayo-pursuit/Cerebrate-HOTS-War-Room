import { normalizeHeroName } from '../utils/heroUtils'
import LazyImage from './LazyImage'

export default function HeroPortrait({ heroName, size = 'md' }) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
    full: 'w-full h-full'
  }

  const imagePath = `/images/heroes/${normalizeHeroName(heroName)}.png`

  return (
    <LazyImage
      src={imagePath}
      alt={heroName}
      size={size}
      className={`${size === 'full' ? 'rounded-lg' : 'rounded-full border-2 border-outline-variant'}`}
      onError={() => {
        // Fallback handled by LazyImage
      }}
    />
  )
}


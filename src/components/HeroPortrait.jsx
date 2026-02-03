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
        console.warn(`Portrait missing for: ${heroName}`)
      }}
      fallback={
        <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900 border border-cyan-500/20 text-[8px] font-black text-cyan-500/50 uppercase">
          <div className="opacity-50">NO_DATA</div>
          <div>{heroName?.substring(0, 3)}</div>
        </div>
      }
    />
  )
}


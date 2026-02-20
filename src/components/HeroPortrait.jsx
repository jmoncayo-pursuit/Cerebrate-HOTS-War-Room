import { normalizeHeroName } from '../utils/heroUtils'
import LazyImage from './LazyImage'
import { Swords, Users, Skull } from 'lucide-react'

export default function HeroPortrait({ heroName, size = 'md' }) {
  const isMinion = heroName?.toLowerCase() === 'minions'
  const isGenericEnemy = heroName?.toLowerCase() === 'enemy hero'

  const imagePath = `/images/heroes/${normalizeHeroName(heroName)}.png`

  const renderFallback = () => {
    if (isMinion) {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center bg-orange-950/40 text-orange-400 border border-orange-500/30">
          <Swords size={20} className="mb-0.5" />
          <span className="text-[7px] font-black uppercase tracking-tighter">Minions</span>
        </div>
      )
    }
    if (isGenericEnemy) {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center bg-red-950/40 text-red-500 border border-red-500/30">
          <Users size={20} className="mb-0.5" />
          <span className="text-[7px] font-black uppercase tracking-tighter">Hostile</span>
        </div>
      )
    }
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900 border border-cyan-500/20 text-[8px] font-black text-cyan-500/50 uppercase">
        <div className="opacity-50">NO_DATA</div>
        <div className="text-[6px] truncate px-1">{heroName}</div>
      </div>
    )
  }

  return (
    <LazyImage
      src={imagePath}
      alt={heroName}
      size={size}
      className={`${size === 'full' ? 'rounded-lg' : 'rounded-full border-2 border-outline-variant'}`}
      fallback={renderFallback()}
    />
  )
}


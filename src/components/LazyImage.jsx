import { useState, useEffect } from 'react'

/**
 * Robust Image Component
 * Shows spinner until loaded, handles errors with fallbacks
 */
export default function LazyImage({
  src,
  alt = '',
  className = '',
  onError,
  size = 'md',
  fallback
}) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  // Reset state if src changes
  useEffect(() => {
    setIsLoading(true)
    setHasError(false)
  }, [src])

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
    full: 'w-full h-full'
  }

  // Placeholder styles
  const placeholderClass = "bg-slate-800 flex items-center justify-center font-bold text-slate-500 uppercase tracking-tighter text-[10px]"

  return (
    <div className={`${sizeClasses[size] || sizeClasses.md} ${className} relative overflow-hidden bg-black/20 flex items-center justify-center`}>
      {!hasError ? (
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-200 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setHasError(true)
            setIsLoading(false)
            if (onError) onError()
          }}
        />
      ) : (
        fallback || (
          <div className={`w-full h-full ${placeholderClass}`}>
            {alt.substring(0, 2)}
          </div>
        )
      )}

      {isLoading && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50">
          <div className="w-1/2 h-1/2 border-2 border-cyan-500/10 border-t-cyan-500/80 rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}

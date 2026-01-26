/**
 * Lightweight loading spinner component
 * Optimized for performance - no heavy animations
 */
export default function LoadingSpinner({ size = 'md', text = 'Loading...' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className="flex flex-col items-center justify-center gap-2 p-4">
      <div className={`${sizeClasses[size]} border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin`} />
      {text && <div className="text-sm text-slate-400">{text}</div>}
    </div>
  )
}

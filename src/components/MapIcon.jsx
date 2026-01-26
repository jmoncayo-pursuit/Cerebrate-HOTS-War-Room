import { useState, useEffect } from 'react'
import { getMapImagePath, getMapColor } from '../utils/mapUtils'

export default function MapIcon({ mapName, size = 'md', className = '' }) {
    const [imageLoaded, setImageLoaded] = useState(false)
    const [imageError, setImageError] = useState(false)
    const mapImagePath = getMapImagePath(mapName)
    const mapColor = getMapColor(mapName)

    useEffect(() => {
        if (!mapName) return
        const img = new Image()
        img.onload = () => {
            if (img.naturalWidth > 0) setImageLoaded(true)
        }
        img.onerror = () => setImageError(true)
        img.src = mapImagePath
    }, [mapName, mapImagePath])

    const sizeClasses = {
        'xs': 'w-5 h-5 rounded-sm shadow-sm',
        'sm': 'w-8 h-8 rounded-md shadow-sm',
        'md': 'w-12 h-12 rounded-lg shadow-sm',
        'lg': 'w-20 h-20 rounded-xl shadow-md',
        'full': 'w-full h-full',
        'absolute': 'absolute inset-0 w-full h-full'
    }

    const containerSize = sizeClasses[size] || sizeClasses['md']

    return (
        <div className={`overflow-hidden ${containerSize} ${className}`}>
            {(imageLoaded && !imageError) ? (
                <div
                    className="w-full h-full"
                    style={{
                        backgroundImage: `url(${mapImagePath})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                    }}
                />
            ) : (
                <div
                    className="w-full h-full flex items-center justify-center text-[10px] font-bold text-white/50 bg-md-surface-container"
                    style={{
                        background: `linear-gradient(135deg, ${mapColor} 0%, rgba(0,0,0,0.4) 100%)`
                    }}
                >
                    {mapName ? mapName.charAt(0).toUpperCase() : '?'}
                </div>
            )}
        </div>
    )
}

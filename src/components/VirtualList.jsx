/**
 * Lightweight Virtual Scrolling Component
 * Only renders visible items to reduce DOM nodes and memory usage
 */
import { useState, useEffect, useRef, useMemo } from 'react'

export default function VirtualList({
  items = [],
  itemHeight = 60,
  containerHeight = 400,
  renderItem,
  overscan = 5, // Render extra items above/below viewport
  className = ''
}) {
  const [scrollTop, setScrollTop] = useState(0)
  const scrollRef = useRef(null)

  // Reset scroll position when items change (e.g. during search/filtering)
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0
      setScrollTop(0)
    }
  }, [items.length])

  // Calculate visible range
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight)
    const end = Math.ceil((scrollTop + containerHeight) / itemHeight)

    return {
      start: Math.max(0, start - overscan),
      end: Math.min(items.length, end + overscan)
    }
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan])

  // Visible items
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end).map((item, idx) => ({
      item,
      index: visibleRange.start + idx
    }))
  }, [items, visibleRange.start, visibleRange.end])

  const totalHeight = items.length * itemHeight
  const offsetY = visibleRange.start * itemHeight

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop)
  }

  return (
    <div
      ref={scrollRef}
      className={`overflow-y-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map(({ item, index }) => (
            <div key={index} style={{ height: itemHeight }}>
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

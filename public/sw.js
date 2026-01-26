/**
 * Service Worker for Offline Caching
 * Caches API responses and static assets for better performance
 */

const CACHE_NAME = 'cerebrate-war-room-v1'
const API_CACHE_NAME = 'cerebrate-api-v1'

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/images/heroes/placeholder.png'
]

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.log('Cache install failed:', err)
      })
    })
  )
  self.skipWaiting()
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    })
  )
  self.clients.claim()
})

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // Cache API responses (match history, profile, etc.)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          // Return cached if available and less than 5 minutes old
          if (cachedResponse) {
            const cachedTime = cachedResponse.headers.get('sw-cached-time')
            if (cachedTime && Date.now() - parseInt(cachedTime) < 5 * 60 * 1000) {
              return cachedResponse
            }
          }

          // Fetch fresh and cache
          return fetch(event.request)
            .then(async (response) => {
              // Only cache successful responses
              if (response.ok && response.status === 200) {
                // Clone immediately before any consumption
                const clonedResponse = response.clone()
                
                // Read body from clone as array buffer (non-destructive)
                const body = await clonedResponse.arrayBuffer()
                const headers = new Headers(clonedResponse.headers)
                headers.set('sw-cached-time', Date.now().toString())
                
                // Create new response with body and updated headers
                const cacheResponse = new Response(body, {
                  status: clonedResponse.status,
                  statusText: clonedResponse.statusText,
                  headers: headers
                })
                
                // Cache asynchronously without blocking response to client
                cache.put(event.request, cacheResponse).catch(() => {
                  // Ignore cache errors silently
                })
              }
              return response
            })
            .catch(() => {
              // If network fails, return cached if available
              return cachedResponse || new Response('Offline', { status: 503 })
            })
        })
      })
    )
    return
  }

  // Cache static assets
  if (url.pathname.startsWith('/images/') || url.pathname.endsWith('.json')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse
        }
        // Fetch and cache
        return fetch(event.request).then((response) => {
          if (response.ok && response.status === 200) {
            // Clone before caching
            const clonedResponse = response.clone()
            caches.open(CACHE_NAME).then((c) => {
              c.put(event.request, clonedResponse).catch(() => {
                // Ignore cache errors
              })
            })
          }
          return response
        }).catch(() => {
          // If network fails and not in cache, return placeholder or error
          return new Response('Asset Unavailable', { status: 503 })
        })
      })
    )
    return
  }

  // For other requests, network first
  event.respondWith(
    fetch(event.request).catch(() => {
      // Silent fail for network errors to prevent console spam
      return new Response('Network Error', { status: 408 })
    })
  )
})

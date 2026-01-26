/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        glimmer: {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(34, 211, 238, 0.4)' },
          '50%': { boxShadow: '0 0 16px rgba(34, 211, 238, 0.8)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2s ease-in-out infinite',
        glimmer: 'glimmer 2s ease-in-out infinite',
        pulseGlow: 'pulseGlow 2s ease-in-out infinite',
      },
      // Material 3 Color System (Pixel Android)
      colors: {
        // Primary colors
        'md-primary': 'var(--md-sys-color-primary)',
        'md-on-primary': 'var(--md-sys-color-on-primary)',
        'md-primary-container': 'var(--md-sys-color-primary-container)',
        'md-on-primary-container': 'var(--md-sys-color-on-primary-container)',
        // Secondary colors
        'md-secondary': 'var(--md-sys-color-secondary)',
        'md-on-secondary': 'var(--md-sys-color-on-secondary)',
        'md-secondary-container': 'var(--md-sys-color-secondary-container)',
        'md-on-secondary-container': 'var(--md-sys-color-on-secondary-container)',
        // Tertiary colors
        'md-tertiary': 'var(--md-sys-color-tertiary)',
        'md-on-tertiary': 'var(--md-sys-color-on-tertiary)',
        'md-tertiary-container': 'var(--md-sys-color-tertiary-container)',
        'md-on-tertiary-container': 'var(--md-sys-color-on-tertiary-container)',
        // Error colors
        'md-error': 'var(--md-sys-color-error)',
        'md-on-error': 'var(--md-sys-color-on-error)',
        'md-error-container': 'var(--md-sys-color-error-container)',
        'md-on-error-container': 'var(--md-sys-color-on-error-container)',
        // Surface colors
        'md-background': 'var(--md-sys-color-background)',
        'md-on-background': 'var(--md-sys-color-on-background)',
        'md-surface': 'var(--md-sys-color-surface)',
        'md-on-surface': 'var(--md-sys-color-on-surface)',
        'md-surface-variant': 'var(--md-sys-color-surface-variant)',
        'md-on-surface-variant': 'var(--md-sys-color-on-surface-variant)',
        'md-outline': 'var(--md-sys-color-outline)',
        'md-outline-variant': 'var(--md-sys-color-outline-variant)',
        // Surface tones (Material 3)
        'md-surface-dim': 'var(--md-sys-color-surface-dim)',
        'md-surface-bright': 'var(--md-sys-color-surface-bright)',
        'md-surface-container-lowest': 'var(--md-sys-color-surface-container-lowest)',
        'md-surface-container-low': 'var(--md-sys-color-surface-container-low)',
        'md-surface-container': 'var(--md-sys-color-surface-container)',
        'md-surface-container-high': 'var(--md-sys-color-surface-container-high)',
        'md-surface-container-highest': 'var(--md-sys-color-surface-container-highest)',
        // Legacy colors (for backward compatibility)
        'obsidian': '#121212',
        'obsidian-panel': '#1e1e1e',
        'purple-primary': '#bb86fc',
        'cyan-safe': '#03dac6',
        'red-danger': '#cf6679',
      },
      // Material 3 Border Radius
      borderRadius: {
        'md-xs': 'var(--md-sys-shape-corner-extra-small)',
        'md-sm': 'var(--md-sys-shape-corner-small)',
        'md-md': 'var(--md-sys-shape-corner-medium)',
        'md-lg': 'var(--md-sys-shape-corner-large)',
        'md-xl': 'var(--md-sys-shape-corner-extra-large)',
      },
      // Material 3 Elevation Shadows
      boxShadow: {
        'md-elevation-0': 'var(--md-sys-elevation-level0)',
        'md-elevation-1': 'var(--md-sys-elevation-level1)',
        'md-elevation-2': 'var(--md-sys-elevation-level2)',
        'md-elevation-3': 'var(--md-sys-elevation-level3)',
        'md-elevation-4': 'var(--md-sys-elevation-level4)',
        'md-elevation-5': 'var(--md-sys-elevation-level5)',
      },
      // Material 3 Motion
      transitionDuration: {
        'md-short1': 'var(--md-sys-motion-duration-short1)',
        'md-short2': 'var(--md-sys-motion-duration-short2)',
        'md-short3': 'var(--md-sys-motion-duration-short3)',
        'md-short4': 'var(--md-sys-motion-duration-short4)',
        'md-medium1': 'var(--md-sys-motion-duration-medium1)',
        'md-medium2': 'var(--md-sys-motion-duration-medium2)',
        'md-medium3': 'var(--md-sys-motion-duration-medium3)',
        'md-medium4': 'var(--md-sys-motion-duration-medium4)',
        'md-long1': 'var(--md-sys-motion-duration-long1)',
        'md-long2': 'var(--md-sys-motion-duration-long2)',
        'md-long3': 'var(--md-sys-motion-duration-long3)',
        'md-long4': 'var(--md-sys-motion-duration-long4)',
      },
      transitionTimingFunction: {
        'md-emphasized': 'var(--md-sys-motion-easing-emphasized)',
        'md-standard': 'var(--md-sys-motion-easing-standard)',
        'md-decelerated': 'var(--md-sys-motion-easing-decelerated)',
        'md-accelerated': 'var(--md-sys-motion-easing-accelerated)',
      },
    },
  },
  plugins: [],
}


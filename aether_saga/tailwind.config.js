/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Situ8 exact colors
        'accent': {
          'primary': '#8b5cf6',
          'light': '#a78bfa',
          'dark': '#7c3aed',
          'muted': 'rgba(139, 92, 246, 0.15)',
        },
        // Frost maps to accent for compatibility
        'frost': {
          'blue': '#8b5cf6',
          'light': '#a78bfa',
          'glow': '#a78bfa',
          'muted': 'rgba(139, 92, 246, 0.15)',
        },
        'aether': {
          'dark': '#21262d',
          'darker': '#0d1117',
          'primary': '#8b5cf6',
          'success': '#22c55e',
          'warning': '#f59e0b',
          'danger': '#ef4444',
        },
        // Situ8 node colors
        'orange': '#f97316',
        'cyan': '#06b6d4',
        'pink': '#ec4899',
        // Norse Gold
        'gold': {
          'primary': '#d4a855',
          'muted': 'rgba(212, 168, 85, 0.2)',
        },
        'norse': {
          'gold': '#d4a855',
        },
        // Blood/Danger
        'blood': {
          'red': '#ef4444',
        },
        // Situ8 backgrounds
        'stone': {
          'base': '#0d1117',
          'darker': '#0d1117',
          'dark': '#161b22',
          'mid': '#21262d',
          'light': '#30363d',
        },
        // Text
        'ice': {
          'white': '#e6edf3',
        },
      },
      fontFamily: {
        'cinzel': ['Cinzel', 'serif'],
        'rajdhani': ['Rajdhani', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: 0.5 },
          '50%': { opacity: 1 },
        },
      },
      boxShadow: {
        'glow': '0 0 0 3px rgba(139, 92, 246, 0.15)',
      },
    },
  },
  plugins: [],
}

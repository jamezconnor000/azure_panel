/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aether': {
          'dark': '#0a0a1a',
          'darker': '#050510',
          'primary': '#00d4ff',
          'secondary': '#7c3aed',
          'accent': '#f59e0b',
          'success': '#10b981',
          'warning': '#f59e0b',
          'danger': '#ef4444',
        }
      }
    },
  },
  plugins: [],
}

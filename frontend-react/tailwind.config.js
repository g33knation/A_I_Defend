/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        gray: {
          900: '#0f172a', // slate-900
          800: '#1e293b', // slate-800
          700: '#334155', // slate-700
          // ... other shades if needed, but we'll rely on slate mostly
        },
        primary: {
          500: '#06b6d4', // cyan-500
          600: '#0891b2', // cyan-600
        },
        secondary: {
          500: '#8b5cf6', // violet-500
        },
      },
    },
  },
  plugins: [],
}

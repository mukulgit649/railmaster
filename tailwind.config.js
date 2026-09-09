/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        rail: {
          bg: '#F5F6F8',
          border: '#D9DDE3',
          blue: '#1D4E89',
          blueDark: '#163C69',
          red: '#B3261E',
          yellow: '#B8860B',
          green: '#1E7A34',
        },
      },
      fontFamily: {
        sans: ['Segoe UI', 'Arial', 'Helvetica', 'sans-serif'],
        mono: ['Consolas', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}

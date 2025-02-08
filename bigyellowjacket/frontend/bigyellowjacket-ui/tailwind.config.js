/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#fbbf24', // Yellow color for Big Yellow Jacket
          dark: '#b45309',
          light: '#fde68a',
        },
        secondary: {
          DEFAULT: '#1f2937',
          dark: '#111827',
          light: '#374151',
        }
      }
    },
  },
  plugins: [],
}
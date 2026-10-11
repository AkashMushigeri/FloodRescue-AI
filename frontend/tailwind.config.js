/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        disaster: {
          dark: '#0B132B',
          card: '#1C2541',
          cardBorder: '#3A506B',
          accent: '#5BC0BE',
          red: '#EF4444',
          amber: '#F59E0B',
          emerald: '#10B981',
          blue: '#3B82F6',
        }
      }
    },
  },
  plugins: [],
}

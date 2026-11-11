/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pravah: {
          teal: {
            DEFAULT: '#167F83',
            dark: '#105D63',
            light: '#2ba4a9',
            subtle: '#EAF5F4',
          },
          aqua: '#EAF5F4',
          sky: '#DCECF4',
          pale: '#EEF4F8',
          amber: '#F1B85B',
          orange: '#EF8D42',
          red: '#D95757',
          navy: '#183447',
          slate: '#647987',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

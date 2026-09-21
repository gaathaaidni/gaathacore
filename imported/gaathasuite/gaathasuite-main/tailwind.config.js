/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gaatha: {
          blue: {
            50: '#f0f7ff',
            100: '#e0effe',
            600: '#0052CC', // Primary Brand Color
            700: '#0747A6',
            800: '#003884',
          },
          gray: {
            50: '#F4F5F7',
            100: '#EBECF0',
            800: '#172B4D', // Primary Text
            900: '#091E42',
          },
          success: '#36B37E',
          danger: '#FF5630',
          warning: '#FFAB00',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
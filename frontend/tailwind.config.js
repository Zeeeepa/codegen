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
          DEFAULT: 'rgb(82, 19, 217)',
          light: 'rgb(162, 119, 255)',
          dark: 'rgb(52, 12, 140)',
        },
        accent: {
          DEFAULT: 'rgb(255, 202, 133)',
          light: 'rgb(255, 225, 180)',
          dark: 'rgb(200, 150, 80)',
        },
        success: 'rgb(66, 196, 153)',
        error: 'rgb(255, 103, 103)',
        warning: 'rgb(255, 202, 133)',
      },
    },
  },
  plugins: [],
}


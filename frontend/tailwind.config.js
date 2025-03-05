/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './app/**/*.{js,ts,jsx,tsx,mdx}',
      './pages/**/*.{js,ts,jsx,tsx,mdx}',
      './components/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
      extend: {
        colors: {
          'sage-light': '#CCD5AE',
          'sage-medium': '#E9EDC9',
          'cream': '#FEFAE0',
          'tan': '#FAEDCD',
          'brown': '#D4A373',
          'brown-dark': '#5c4935',
          'brown-medium': '#7c6247',
          'brown-light': '#83684a',
          'brown-red': '#c24e2c',
        },
      },
    },
    plugins: [],
  }
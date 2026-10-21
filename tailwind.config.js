/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        ivory:   "#F7F3ED",
        sand:    "#E7D8C8",
        espresso:"#302923",
        taupe:   "#A47C63",
      },
      fontFamily: {
        serif: ["'Playfair Display'", "Georgia", "serif"],
        sans:  ["'Inter'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}

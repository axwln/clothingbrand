/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        ivory:    "#faf7f2",
        sand:     "#e9e3d9",
        espresso: "#242320",
        taupe:    "#7c7267",
        maroon:   "#51483e",
        gold:     "#b4a087",
        'gold-ink':"#78634d",
        'dark-bg': "#191918",
        'dark-surface':"#242422",
        'dark-card':"#2b2b28",
        'dark-fg': "#f6f1e9",
        'dark-muted':"#c3baad",
        'dark-line':"#45443e",
      },
      fontFamily: {
        serif:  ["'Bodoni Moda'", "'Didot'", "Georgia", "serif"],
        sans:   ["'Jost'", "'Segoe UI'", "system-ui", "sans-serif"],
        script: ["'Pinyon Script'", "cursive"],
      },
    },
  },
  plugins: [],
}

// Larkspur Field Station - a complete fictional, AI-generated house-style example.
//
// Markdown documents use `brand: larkspur-brand`. Direct Typst documents can
// import either `theme` or spread `book-args` into a house template.

#let theme = (
  accent: rgb("#36558F"),
  accent2: rgb("#6B4E71"),
  tones: (
    note: rgb("#36558F"),
    tip: rgb("#287A61"),
    important: rgb("#6B4E71"),
    warning: rgb("#A66518"),
    caution: rgb("#A23B3B"),
  ),
)

#let author = "Larkspur Field Station"

#let colophon = [
  This field guide is a fictional, AI-generated example. Names, organizations,
  systems, events, and data are not real. It may be reused under the repository
  license. #linebreak()
]

#let book-args = (theme: theme, author: author, colophon: colophon)

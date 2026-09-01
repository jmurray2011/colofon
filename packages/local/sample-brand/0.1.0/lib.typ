// sample-brand - a demo brand for the `house` style: a theme palette + a colophon.
//
// A brand package is the one place a brand's identity lives. Spread `book-args`
// into a house template to brand a document in a single call:
//
//   #import "@local/sample-brand:0.1.0": book-args as brand
//   #show: book.with(title: "...", logo: image("/assets/logo.png", alt: "..."), ..brand)
//
// or, with the Markdown factory, name it in book.yaml: `brand: sample-brand`.

#let theme = (
  accent: rgb("#0D9488"),
  accent2: rgb("#0F766E"),
  tones: (
    note: rgb("#0D9488"),
    tip: rgb("#1F8A4C"),
    important: rgb("#0F766E"),
    warning: rgb("#C2710C"),
    caution: rgb("#C0392B"),
  ),
)

#let author = "Acme"

#let colophon = [
  Copyright #sym.copyright Acme. All rights reserved. #linebreak()
]

// spread this into a house `book.with(...)` to apply the whole brand at once
#let book-args = (theme: theme, author: author, colophon: colophon)

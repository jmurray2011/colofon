// Book-md proof: a Markdown-authored chapter (sample-chapter.md) dropped into a
// real book() alongside a Typst-authored chapter, so the Markdown chapter's
// cross-references resolve to the Typst chapter. Build with:
//   typst compile --root . --package-path packages --package-cache-path packages \
//     --font-path engine/fonts --pdf-standard ua-1 \
//     tools/factory-examples/sample-chapter.typ out.pdf
#import "@local/house:0.1.0": *
#import "@local/bookmd:0.1.0": chapter-md

#show: book.with(
  title: "Acme Relay",
  subtitle: "a book-md proof of concept",
  version: "1",
  date: "June 2026",
  part-blurbs: (
    "Stand up the software and complete its initial configuration.",
    "Wire up the moving parts.",
  ),
)

// ===== Part I - a chapter authored entirely in Markdown =====
= Install
#chapter-md(read("sample-chapter.md"), img: (p, alt) => image(p, alt: alt))

// ===== Part II - Typst-authored chapters the Markdown chapter cross-references =====
= Configure

== Reverse proxy and TLS <ch-tls>

This chapter is authored in Typst. The Markdown chapter in Part I links to it by
label, and the cross-reference resolves to this chapter's title -- Markdown and
Typst chapters live in one book and reference each other freely.

== Identity and single sign-on <ch-sso>

Also Typst-authored, also referenced from the Markdown chapter.

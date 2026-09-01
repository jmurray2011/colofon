// bookmd - author book chapters in Markdown.
//
// chapter-md(markdown) renders book-flavored Markdown into the same house
// constructs the Typst books use, so the structure, cross-references, and index
// are the engine's job, not the author's. Mappings:
//
//   `code`              -> cmd()  (styled, auto-indexed literal)
//   [text](#slug)       -> typed cross-reference (resolves to the target's title)
//   ## Heading {#id}     -> a stable label <id> for cross-references that survive edits
//   > [!note] body       -> note / tip / important / warning / caution callouts
//   ![alt](shot:path)   -> framed screenshot figure (alt becomes the caption)
//   ```lang ... ```      -> code blocks (copy-safe, like the books)
//
// Headings land at h1-level (default 2 = Chapter inside a book()'s Parts), so a
// chapter file's `#` is a Chapter, `##` a Section, `###` a Subsection.
#import "@local/house:0.1.0" as house
#import "@preview/cmarker:0.1.6"
#import "@preview/fletcher:0.5.8" as fletcher
#import "@preview/primaviz:0.8.0" as primaviz

#let _admon = ("note", "tip", "important", "warning", "caution")

// book-flavored-Markdown sugar -> the CommonMark/HTML forms cmarker understands.
#let _pre(md) = {
  // `## Heading {#id}` -> `<hN id="id">Heading</hN>` (cmarker's stable-label form)
  md = md.replace(
    regex("(?m)^(#{1,6}) +(.+?) *\\{#([A-Za-z0-9_-]+)\\} *$"),
    m => {
      let n = str(m.captures.at(0).len())
      (
        "<h"
          + n
          + " id=\""
          + m.captures.at(2)
          + "\">"
          + m.captures.at(1)
          + "</h"
          + n
          + ">"
      )
    },
  )
  // `> [!type]` admonition blockquotes -> a callout wrapping the rendered body
  md = md.replace(
    regex("(?m)^> \\[!([A-Za-z]+)\\] *\\n((?:^>.*\\n?)*)"),
    m => {
      let kind = lower(m.captures.at(0))
      if _admon.contains(kind) {
        let body = m
          .captures
          .at(1)
          .split("\n")
          .map(l => l.replace(regex("^> ?"), ""))
          .join("\n")
          .trim()
        "<!--raw-typst #" + kind + "[-->\n" + body + "\n<!--raw-typst ]-->\n"
      } else { m.text }
    },
  )
  md
}

// img: a loader the CALLER provides as `(p, alt) => image(p, alt: alt)`. A package
// cannot resolve a consumer's root-absolute asset path, so the image() call must
// live in the caller's file; pass img whenever the Markdown references images.
#let chapter-md(markdown, img: none, h1-level: 2) = {
  let load = if img != none { img } else {
    (p, ..a) => panic(
      "chapter-md: this document has images - pass img: (p, alt) => image(p, alt: alt)",
    )
  }
  cmarker.render(
    _pre(markdown),
    h1-level: h1-level,
    scope: (
      // inline `code` -> indexed literal; fenced ```blocks``` stay code blocks.
      // cmarker hands a fenced block its trailing newline, which renders as a phantom
      // empty final line (an extra numbered row); native Typst raw strips it. Match native.
      // An inline span whose text starts with U+E000 is a path() marker: it renders via
      // house.path (unboxed, wraps at separators) instead of cmd (a box). The converter uses
      // this because path()'s backtick raw literal, emitted as an inline <!--raw-typst-->,
      // breaks cmarker's code-span pairing in the same paragraph; a marked span does not.
      raw: (..a) => if a.named().at("block", default: false) {
        let txt = a.pos().first()
        if txt.ends-with("\n") { txt = txt.slice(0, -1) }
        raw(txt, ..a.named())
      } else {
        let t = a.pos().first()
        if t.starts-with("\u{E000}") {
          house.path(raw(t.trim("\u{E000}", at: start, repeat: false)))
        } else { house.cmd(t) }
      },
      // [text](#label) -> typed cross-reference; external links stay links
      link: (dest, body) => if type(dest) == label { ref(dest) } else {
        link(dest, body)
      },
      // ![alt](shot:path) -> framed screenshot figure; other images (incl. those in
      // raw-typst, which pass width: etc.) forward all args to the consumer's loader
      image: (p, ..a) => if p.starts-with("shot:") {
        figure(house.shot(load(p.slice(5), ..a)), caption: a
          .named()
          .at("alt", default: none))
      } else {
        load(p, ..a)
      },
      // house constructs reachable from <!--raw-typst--> escapes (callouts, plus the
      // structural ones a converter emits verbatim: procedure/param/figure/idx/...)
      note: house.note,
      tip: house.tip,
      important: house.important,
      warning: house.warning,
      caution: house.caution,
      cmd: house.cmd,
      path: house.path,
      param: house.param,
      procedure: house.procedure,
      idx: house.idx,
      smallcap: house.smallcap,
      shot: house.shot,
      // fletcher diagrams, reachable from <!--raw-typst--> escapes. The wrapper sets
      // clean label defaults (sans, no hyphenation, no justification) so node text
      // reads as a label, not a cramped justified paragraph.
      diagram: (..a) => {
        set text(font: "IBM Plex Sans", size: 9.5pt, hyphenate: false)
        set par(justify: false, leading: 0.55em)
        fletcher.diagram(..a)
      },
      node: fletcher.node,
      edge: fletcher.edge,
      fletcher: fletcher,
      // primaviz charts, reachable from <!--raw-typst--> escapes
      bar-chart: primaviz.bar-chart,
      primaviz: primaviz,
    ),
  )
}

// doc-md: the same book-flavored Markdown for a STANDALONE document (the factory
// doctypes: report / article / runbook / kb-article / ...), where the top-level
// `#` is a level-1 heading the doctype template styles - so callouts, cross-refs,
// code blocks, and screenshots all work exactly as in a chapter. Reuses chapter-md
// at h1-level: 1 (a chapter renders at level 2, inside a book's Parts).
#let doc-md(markdown, img: none) = chapter-md(markdown, img: img, h1-level: 1)

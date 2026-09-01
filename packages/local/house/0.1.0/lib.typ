// house - the book template (Parts > Chapters > Sections) plus the factory templates.
// Heading levels: 1 = Part, 2 = Chapter, 3 = Section, 4 = Subsection.
// PDF bookmarks nest by heading level, so this gives Part > Chapter > Section in
// the outline panel. Chapter numbers are continuous (1..N) across Parts via a
// manual counter; all numbering is rendered by the show rules below.

// ---------------- design tokens ----------------
// Neutral, shared engine defaults (NOT brand identity): the grays, code colors, fonts,
// and base size are the same for every theme. The brand-distinctive values - the accent
// palette and the callout tones - live in `default-theme` below and are overridable by
// passing `theme:` to any template.
#let ink = rgb("#1B1B22")
#let muted = rgb("#6A6E7A")
#let rulec = rgb("#D8DBE2")
#let codebg = rgb("#F7F8FA")
#let codeink = rgb("#3A4257")

#let body-font = "IBM Plex Serif"
#let head-font = "IBM Plex Sans"
#let mono-font = "IBM Plex Mono"
#let body-size = 11pt

// ---------------- theme (the brand palette) ----------------
// A document overrides any of these by passing `theme: (accent: ..., tones: (...))` to a
// template; a template merges the override over this default and publishes it via
// `theme-state` so body-level helpers (note/procedure/kicker/...) pick it up too.
#let default-theme = (
  accent: rgb("#2563EB"),
  accent2: rgb("#1D4ED8"),
  tones: (
    note: rgb("#2563EB"),
    tip: rgb("#1F8A4C"),
    important: rgb("#1D4ED8"),
    warning: rgb("#C2710C"),
    caution: rgb("#C0392B"),
  ),
)
#let theme-state = state("house-theme", default-theme)
// merge an override over the default; the nested `tones` dict is merged, not replaced,
// so a partial theme (e.g. just `accent`) keeps the default tones.
#let _theme(theme) = {
  let th = default-theme + theme
  if "tones" in theme { th.tones = default-theme.tones + theme.tones }
  th
}

// ---------------- counters ----------------
#let partc = counter("house-part")
#let chap = counter("house-chapter")
#let sec = counter("house-section")
#let appc = counter("house-appendix")
// flipped on (in main.typ) right before the appendix part: chapters past this point
// render as "Appendix A/B/C" with letter-keyed section numbers instead of "Chapter N".
#let appendix-state = state("house-appendix-mode", false)

// ---------------- semantic helpers ----------------
#let _callout(kind, tone, body) = block(
  width: 100%,
  inset: (x: 11pt, y: 9pt),
  radius: 3pt,
  above: 1.1em,
  below: 1.1em,
  breakable: false,
  fill: tone.lighten(91%),
  stroke: (left: 2.5pt + tone),
)[
  #text(
    font: head-font,
    size: 8.5pt,
    weight: 700,
    fill: tone,
    tracking: 0.4pt,
  )[#upper(kind)]
  // non-weak: a weak spacing here collapses to nothing and the label's glyph box
  // ends up overlapping the first line of the body.
  #v(4pt)
  #set text(size: 10pt)
  #set par(first-line-indent: 0pt, leading: 0.62em)
  #body
]
#let note(body) = context _callout("Note", theme-state.get().tones.note, body)
#let tip(body) = context _callout("Tip", theme-state.get().tones.tip, body)
#let important(body) = context _callout(
  "Important",
  theme-state.get().tones.important,
  body,
)
#let warning(body) = context _callout(
  "Warning",
  theme-state.get().tones.warning,
  body,
)
#let caution(body) = context _callout(
  "Caution",
  theme-state.get().tones.caution,
  body,
)

// ---- index plumbing ----
// pull a plain-string key from a cmd/path argument (string literal or `raw` backticks).
#let _idxkey(it) = {
  if type(it) == str { it } else if type(it) == content and it.func() == raw {
    it.text
  } else { none }
}
// generic path segments and example/sample values that are not useful index lookups
#let _idxstop = (
  "opt",
  "var",
  "etc",
  "tmp",
  "home",
  "usr",
  "bin",
  "data",
  "conf",
  "logs",
  "cert",
  "dashboard",
  "license",
  "tools",
  "default",
  "changeit",
  "admin",
  "active",
  "dictionaryadmin",
  "sysadmin",
  "true",
  "false",
  "none",
  "off",
  "on",
  "metadata",
  "post",
  "51200",
  "16",
  "17",
)
// auto-register a single-token literal (port, env var, path, command, file) for the index.
// path-like literals are indexed by their final segment - the filename admins look up.
#let _autoidx(it) = {
  let k = _idxkey(it)
  if k != none {
    if k.contains("/") or k.contains("\\") {
      let parts = k.split(regex("[/\\\\]")).filter(s => s.len() > 0)
      if parts.len() > 0 { k = parts.last() }
    }
    let drop = (
      k.len() < 2
        or k.contains(" ")
        or k.contains("=")
        or k.contains("<")
        or k.contains(">")
        or k.starts-with("-")
        or k.starts-with("$")
        or k.starts-with("*")
        or k.starts-with(".")
        or k.match(regex("^[0-9a-fA-F]{12,}$")) != none
        or k.match(regex("(?i)(\.com|\.org|\.net|example)$")) != none
        or (k.len() > 30 and k.contains("."))
        or _idxstop.contains(lower(k))
    )
    if not drop { [#metadata(k)<idx>] }
  }
}
// manual index entry for a concept term (placed at its primary discussion).
#let idx(key) = [#metadata(key)<idx>]

// boxed so a short literal never breaks mid-token. In a normal text column the token
// is far narrower than the available width, so it renders at full size; only when the
// container is narrower than the token (a tight table cell) does it scale down to fit,
// the same shrink-to-fit treatment code blocks get - so it never overflows a cell.
#let cmd(it) = {
  _autoidx(it)
  let t = text(
    font: mono-font,
    size: 0.92em,
    fill: codeink,
    hyphenate: false,
    it,
  )
  box(context layout(size => {
    let w = measure(t).width
    if w > size.width and size.width > 0pt {
      box(text(
        font: mono-font,
        size: 0.92em * (size.width / w),
        fill: codeink,
        hyphenate: false,
        it,
      ))
    } else { t }
  }))
}
// Windows / filesystem path - call with a `raw` literal (backticks) so backslashes survive.
// not boxed (long paths must be able to wrap at separators); hyphenation off all the same.
#let path(it) = {
  _autoidx(it)
  text(font: mono-font, size: 0.92em, fill: codeink, hyphenate: false, it)
}
#let param(name, type: none, default: none, body) = block(
  width: 100%,
  above: 0.9em,
  below: 0.9em,
)[
  #text(font: mono-font, weight: 600, fill: ink)[#name]
  #if type != none {
    text(font: head-font, size: 8.5pt, fill: muted)[ #h(6pt) #type]
  }
  #if default != none {
    text(
      font: head-font,
      size: 8.5pt,
      fill: muted,
    )[ #h(4pt) - default: #raw(default)]
  }
  #block(inset: (left: 1em, top: 3pt))[#set text(size: 9.8pt); #set par(
      first-line-indent: 0pt,
    ); #body]
]
#let procedure(title, body) = context {
  let accent = theme-state.get().accent
  block(width: 100%, above: 1.1em, below: 1.1em)[
    #text(
      font: head-font,
      size: 9pt,
      weight: 700,
      fill: accent,
      tracking: 0.5pt,
    )[#upper("Procedure")]
    #h(6pt) #text(font: head-font, size: 10.5pt, weight: 600)[#title]
    #v(4pt, weak: true)
    #body
  ]
}
// Wide-content escape: break one artifact out to the full margins. Use sparingly.
#let wide(body) = pad(x: -0.6in, body)

// Break a long code string to fit `avail` using REAL line breaks at delimiter boundaries
// (. / : - _ = ,), char-packing any single chunk that is itself too wide. No zero-width
// characters - the breaks are real newlines (visible on copy), so the ZWSP copy-safe gate
// passes. Always called inside a layout/context so `measure` resolves.
#let _breaktofit(s, avail) = {
  let fits(t) = measure([#t]).width <= avail
  let pack(atoms) = {
    let lines = ()
    let cur = ""
    for a in atoms {
      if cur == "" { cur = a } else if fits(cur + a) { cur = cur + a } else {
        lines.push(cur)
        cur = a
      }
    }
    if cur != "" { lines.push(cur) }
    lines
  }
  let segs = s
    .replace(regex("[./:_,=-]"), m => m.text + "\u{0}")
    .split("\u{0}")
    .filter(p => p != "")
  let atoms = ()
  for seg in segs {
    if fits(seg) { atoms.push(seg) } else {
      for ch in seg.clusters() { atoms.push(ch) }
    }
  }
  pack(atoms).map(l => [#l]).join(linebreak())
}

// Render a block's code lines at a fixed, readable size. A line that fits, or has spaces/
// hyphens to break on, renders highlighted and wraps with a hanging indent. A long
// space-less line (no break opportunity) is broken with real line breaks via _breaktofit
// instead of scaled - legible, never tiny, never overflowing.
#let _codelines(lines) = {
  set par(hanging-indent: 2em)
  grid(
    columns: 1fr,
    row-gutter: 0.3em,
    ..lines.map(ln => if ln.text.contains(" ") {
      ln.body
    } else {
      layout(size => if measure(ln.body).width > size.width
        and size.width > 0pt {
        _breaktofit(ln.text, size.width)
      } else {
        ln.body
      })
    }),
  )
}

// Config "settings list": render `key=value` lines stacked - key on its own line, value
// indented beneath and broken-to-fit. For config whose value is too long/unbreakable for a
// one-line code block; opt in with a ```settings fence. Lines without `=` render broken-to-fit.
#let _settings(it) = block(
  width: 100%,
  fill: codebg,
  stroke: 0.5pt + rulec,
  radius: 3pt,
  inset: (x: 9pt, y: 8pt),
  above: 1.0em,
  below: 1.0em,
  breakable: it.lines.len() > 18,
)[
  #set text(font: mono-font, size: 9pt, hyphenate: false)
  #set par(justify: false, leading: 0.58em, first-line-indent: 0pt)
  #for (i, ln) in it.lines.enumerate() {
    let t = ln.text
    if t.trim() == "" {
      v(0.3em)
    } else if t.contains("=") {
      let parts = t.split("=")
      let key = parts.first().trim()
      let value = parts.slice(1).join("=").trim()
      block(above: if i > 0 { 0.5em } else { 0em })[
        #text(fill: ink, weight: 600)[#key]
        #linebreak()
        #pad(left: 1.5em, text(fill: codeink, layout(size => _breaktofit(
          value,
          size.width,
        ))))
      ]
    } else {
      block(
        above: if i > 0 { 0.5em } else { 0em },
        layout(size => _breaktofit(t, size.width)),
      )
    }
  }
]

// Screenshot: seat a UI capture on the page with a hairline border and softly
// rounded corners (the card figures carry implicit borders; raster shots need one).
// Takes already-loaded image CONTENT, e.g. shot(image("/book/assets/x.png", alt: "...")).
// A package cannot resolve a consumer's root-absolute asset path, so the consumer
// loads the image (resolving against --root) and passes it in.
#let shot(body, w: 100%) = box(
  width: w,
  stroke: 0.75pt + rulec,
  radius: 4pt,
  clip: true,
  inset: 0pt,
  body,
)

// Synthesized small caps (IBM Plex carries no true small-cap glyphs): real capitals
// stay full height; lowercase letters render as uppercase at ~0.8em. Reads as
// "almost all-caps but not quite". Digits, spaces, and punctuation stay full size.
#let smallcap(body) = {
  set text(tracking: 0.35pt)
  show regex("[a-z]+"): it => text(size: 0.8em)[#upper(it)]
  body
}

// ---------------- the template ----------------
#let book(
  title: "",
  subtitle: "",
  version: "",
  date: "",
  logo: none,
  draft: false,
  watermark: none,
  part-blurbs: (),
  author: "",
  colophon: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  set document(title: title, author: author)
  set text(
    font: body-font,
    size: body-size,
    fill: ink,
    lang: "en",
    region: "US",
    hyphenate: true,
  )
  set par(justify: false, leading: 0.65em, spacing: 1.05em, first-line-indent: (
    amount: 1.1em,
    all: false,
  ))
  set heading(numbering: none) // numbers are rendered manually below
  show raw: set text(font: mono-font)

  // native UA-clean code block (syntect highlighting + language tag)
  show raw.where(block: true): it => if it.lang == "settings" {
    _settings(it)
  } else {
    block(
      width: 100%,
      fill: codebg,
      stroke: 0.5pt + rulec,
      radius: 3pt,
      inset: (x: 9pt, y: 8pt),
      above: 1.0em,
      below: 1.0em,
      breakable: it.lines.len() > 18,
    )[
      #if it.lang != none {
        align(right, box(
          fill: rulec,
          inset: (x: 5pt, y: 2pt),
          radius: 2pt,
          text(
            font: head-font,
            size: 7pt,
            weight: 600,
            fill: muted,
            tracking: 0.4pt,
          )[#upper(it.lang)],
        ))
        v(2pt, weak: true)
      }
      #set text(font: mono-font, size: 9pt, hyphenate: false)
      #set par(justify: false, leading: 0.58em, first-line-indent: 0pt)
      #_codelines(it.lines)
    ]
  }

  show link: it => text(fill: accent, it)
  // headings use manual numbering, so render a cross-ref as the linked title.
  show ref: it => {
    let el = it.element
    if el != none and el.func() == heading {
      link(el.location(), text(fill: accent, [#el.body]))
    } else {
      text(fill: accent, it)
    }
  }

  // booktabs tables
  set table(stroke: none, inset: (x: 8pt, y: 6pt))
  show table.cell: set par(justify: false)
  show table.cell: set text(hyphenate: false)
  show table.cell.where(y: 0): set text(
    font: head-font,
    weight: 600,
    size: 9.5pt,
  )

  // figures - captions left-aligned (consistent for both images and tables), hung tight
  show figure.caption: set align(left)
  show figure.caption: it => text(
    font: head-font,
    size: 8.5pt,
    fill: muted,
  )[#it]
  set figure(gap: 6pt)

  // ----- headings: Part / Chapter / Section / Subsection -----
  show heading: set text(font: head-font, fill: ink)
  show heading: set par(justify: false)

  // part-blurbs: one short intro per Part, passed in by each book (the book() parameter).
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    partc.step()
    context {
      let p = partc.get().first()
      let me = it.location()
      let allchaps = query(heading.where(level: 2))
      let mychaps = ()
      for (i, c) in allchaps.enumerate() {
        if query(heading.where(level: 1).before(c.location())).len() == p {
          mychaps.push((i + 1, c.body))
        }
      }
      place(top + right, dx: 0.12in, dy: 0.95in, text(
        font: head-font,
        size: 150pt,
        weight: 800,
        fill: accent.lighten(87%),
      )[#numbering("I", p)])
      place(top + left, dx: -0.32in, dy: 1.72in, rect(
        width: 3pt,
        height: 1.5in,
        fill: accent,
      ))
      place(bottom + left, dy: -0.18in, text(
        font: head-font,
        size: 8pt,
        fill: muted,
        tracking: 1.2pt,
      )[#upper(subtitle)])
      v(1.78in)
      set par(justify: false)
      text(
        font: head-font,
        size: 11.5pt,
        fill: accent,
        weight: 600,
        tracking: 2.5pt,
      )[#upper("Part") #numbering("I", p)]
      v(12pt)
      text(font: head-font, size: 32pt, weight: 700, hyphenate: false)[#it.body]
      v(20pt)
      block(width: 74%, text(
        font: body-font,
        size: 11pt,
        fill: muted,
      )[#part-blurbs.at(p - 1, default: "")])
      v(24pt)
      let isapp = appendix-state.at(me)
      grid(
        columns: 2, column-gutter: 13pt, row-gutter: 8pt,
        ..mychaps
          .enumerate()
          .map(((j, pair)) => {
            let (n, title) = pair
            (
              text(
                font: head-font,
                size: 10.5pt,
                fill: accent,
                weight: 600,
              )[#if isapp [Appendix #numbering("A", j + 1)] else [Chapter #n]],
              text(font: head-font, size: 10.5pt)[#title],
            )
          })
          .flatten()
      )
    }
    pagebreak(weak: true)
  }

  show heading.where(level: 2): it => {
    pagebreak(weak: true)
    sec.update(0)
    context { if appendix-state.get() { appc.step() } else { chap.step() } }
    v(1.15in)
    context {
      if appendix-state.get() {
        text(
          font: head-font,
          size: 12pt,
          weight: 600,
          fill: accent,
          tracking: 0.6pt,
        )[#upper("Appendix") #numbering("A", appc.get().first())]
      } else {
        text(
          font: head-font,
          size: 12pt,
          weight: 600,
          fill: accent,
          tracking: 0.6pt,
        )[#upper("Chapter") #chap.get().first()]
      }
    }
    v(8pt, weak: true)
    text(font: head-font, size: 25pt, weight: 700, hyphenate: false)[#smallcap(
      it.body,
    )]
    v(11pt, weak: true)
    line(length: 100%, stroke: 0.8pt + rulec)
    v(18pt, weak: true)
  }

  show heading.where(level: 3): it => {
    sec.step()
    context {
      let cnum = if appendix-state.get() {
        numbering("A", appc.get().first())
      } else { str(chap.get().first()) }
      let s = sec.get().first()
      block(above: 1.3em, below: 0.5em)[
        #set par(justify: false)
        #text(font: head-font, size: 14pt, weight: 600)[
          #text(fill: accent)[#cnum.#s] #h(7pt) #smallcap(it.body)
        ]
      ]
    }
  }

  show heading.where(level: 4): set text(
    font: head-font,
    size: 11.5pt,
    weight: 600,
  )

  // ----- page geometry, running head, folio -----
  set page(
    width: 7in,
    height: 9in,
    margin: (x: 1.15in, top: 0.95in, bottom: 0.9in),
    background: {
      let wm = if watermark != none { watermark } else if draft {
        "DRAFT"
      } else {
        none
      }
      if wm != none {
        // small opaque red stamp in the top margin (book's footer center is the page
        // number); horizontal, never over the body, so it stays out of copied text.
        place(top + center, dy: 0.35in, text(
          font: head-font,
          size: 7.5pt,
          weight: 700,
          tracking: 1.2pt,
          fill: rgb("#C0392B"),
        )[#upper(wm)])
      }
    },
    header: context {
      let pg = here().page()
      let opener = query(
        heading.where(level: 1).or(heading.where(level: 2)),
      ).any(h => h.location().page() == pg)
      let chaps = query(heading.where(level: 2).before(here()))
      if chaps.len() > 0 and not opener {
        set text(font: head-font, size: 8.5pt, fill: muted)
        grid(
          columns: (1fr, 1fr),
          context { smallcap(chaps.last().body) }, align(right, emph(title)),
        )
        v(3pt)
        line(length: 100%, stroke: 0.5pt + rulec)
      }
    },
    footer: context {
      let pg = here().page()
      let partopener = query(heading.where(level: 1)).any(h => (
        h.location().page() == pg
      ))
      if not partopener {
        set text(font: head-font, size: 9pt, fill: muted)
        align(center, counter(page).display())
      }
    },
  )

  // ---------------- front matter ----------------
  page(header: none, footer: none, numbering: none, margin: (x: 1in, y: 1.1in))[
    #align(center)[
      #v(1.3in)
      #if logo != none { logo }
      #v(0.95in)
      #text(font: head-font, size: 29pt, weight: 700, fill: ink)[#title]
      #v(10pt)
      #text(font: head-font, size: 14pt, weight: 500, fill: muted)[#subtitle]
      #v(14pt)
      #line(length: 28%, stroke: 1.2pt + accent)
    ]
    #place(bottom + center, dy: -0.2in)[
      #text(
        font: head-font,
        size: 10pt,
        fill: muted,
      )[Version #version #sym.dash.en #date]
    ]
  ]
  page(header: none, footer: none, numbering: none)[
    #place(bottom)[
      #set text(font: head-font, size: 9pt, fill: muted)
      #set par(justify: false, leading: 0.65em, first-line-indent: 0pt)
      #line(length: 30%, stroke: 0.5pt + rulec)
      #v(8pt)
      *#title* #linebreak() #subtitle #linebreak()
      Version #version. Document generated #date. #linebreak()
      // book-specific notices (deployment scope, status, copyright, trademark) are
      // injected by the book via `colophon`; the engine adds only the type note below.
      #if colophon != none {
        v(6pt)
        colophon
      }
      #v(6pt)
      Set in IBM Plex Serif, Sans, and Mono. Composed with Typst.
    ]
  ]

  // ----- table of contents (manual: reconstructs Part/Chapter/Section numbers) -----
  set page(numbering: "i")
  counter(page).update(1)
  v(0.4in)
  text(font: head-font, size: 22pt, weight: 700)[Contents]
  v(12pt)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(10pt)
  context {
    let pnum = 0
    let cnum = 0
    let snum = 0
    let anum = 0
    for hd in query(heading) {
      let loc = hd.location()
      let lvl = hd.level
      let pg = counter(page).at(loc).first()
      if lvl == 1 {
        pnum += 1
        block(above: 13pt, below: 5pt)[
          #text(
            font: head-font,
            weight: 700,
            size: 8.5pt,
            fill: accent,
            tracking: 1pt,
          )[#upper("Part") #numbering("I", pnum)]
          #h(7pt)
          #text(font: head-font, weight: 700, size: 11pt)[#hd.body]
        ]
      } else if lvl == 2 {
        snum = 0
        let isapp = appendix-state.at(loc)
        let cl = if isapp {
          anum += 1
          numbering("A", anum)
        } else {
          cnum += 1
          str(cnum)
        }
        block(above: 3pt, below: 3pt)[
          #grid(
            columns: (auto, 1fr, auto),
            column-gutter: 6pt,
            text(font: head-font, weight: 600)[#box(width: 1.6em)[#cl]#hd.body],
            align(bottom, box(width: 100%, inset: (bottom: 2pt), repeat[#text(
              fill: rulec,
            )[.]])),
            text(font: head-font)[#pg],
          )
        ]
      } else if lvl == 3 {
        snum += 1
        let isapp = appendix-state.at(loc)
        let cl = if isapp { numbering("A", anum) } else { str(cnum) }
        block(above: 1pt, below: 1pt, inset: (left: 1.3em))[
          #grid(
            columns: (auto, 1fr, auto),
            column-gutter: 6pt,
            text(
              font: head-font,
              size: 9.5pt,
              fill: muted,
            )[#box(width: 2.7em)[#cl.#snum]#hd.body],
            align(bottom, box(width: 100%, inset: (bottom: 2pt), repeat[#text(
              fill: rulec.lighten(20%),
              size: 9pt,
            )[.]])),
            text(font: head-font, size: 9.5pt, fill: muted)[#pg],
          )
        ]
      }
    }
  }

  // ----- list of figures -----
  context {
    let figs = query(figure.where(kind: image))
    if figs.len() > 0 {
      pagebreak(weak: true)
      v(0.4in)
      text(font: head-font, size: 22pt, weight: 700)[Figures]
      v(12pt)
      line(length: 100%, stroke: 0.8pt + rulec)
      v(10pt)
      let n = 0
      for f in figs {
        n += 1
        let pg = counter(page).at(f.location()).first()
        block(above: 11pt, below: 0pt)[
          #grid(
            columns: (auto, 1fr, auto),
            column-gutter: 6pt,
            text(font: head-font, weight: 600, size: 10pt)[Figure #n],
            align(bottom, box(width: 100%, inset: (bottom: 2pt), repeat[#text(
              fill: rulec,
            )[.]])),
            text(font: head-font, size: 10pt)[#pg],
          )
          #v(2pt, weak: true)
          #pad(left: 1.5em)[#set par(leading: 0.5em); #text(
              font: body-font,
              size: 8.5pt,
              fill: muted,
            )[#f.caption.body]]
        ]
      }
    }
  }

  // ---------------- body ----------------
  pagebreak(weak: true)
  counter(page).update(1)
  set page(numbering: "1")
  body

  // ---------------- index ----------------
  pagebreak(weak: true)
  set page(header: context {
    let pg = here().page()
    let onTitle = query(<index-title>).any(m => m.location().page() == pg)
    if not onTitle {
      set text(font: head-font, size: 8.5pt, fill: muted)
      grid(
        columns: (1fr, 1fr),
        smallcap[Index], align(right, emph(title)),
      )
      v(3pt)
      line(length: 100%, stroke: 0.5pt + rulec)
    }
  })
  [#metadata("index")<index-title>]
  v(0.1in)
  text(font: head-font, size: 22pt, weight: 700)[Index]
  v(12pt)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(12pt)
  context {
    let items = query(<idx>)
    let m = (:)
    for it in items {
      let k = it.value
      let pg = counter(page).at(it.location()).first()
      if k in m { if not m.at(k).contains(pg) { m.at(k).push(pg) } } else {
        m.insert(k, (pg,))
      }
    }
    let keys = m.keys().sorted(key: k => lower(k))
    let acc = []
    let cur = ""
    for k in keys {
      let f = upper(k.first())
      let letter = if f.match(regex("[A-Z]")) != none { f } else {
        "0-9 / symbols"
      }
      if letter != cur {
        cur = letter
        acc += block(above: 9pt, below: 3pt, breakable: false, text(
          font: head-font,
          size: 9pt,
          weight: 700,
          fill: accent,
          tracking: 0.4pt,
        )[#letter])
      }
      let pages = m.at(k).sorted().map(str).join(", ")
      acc += par(hanging-indent: 1.1em)[#k#h(0.5em)#text(fill: muted)[#pages]]
    }
    set text(font: body-font, size: 9.3pt)
    set par(
      justify: false,
      leading: 0.5em,
      spacing: 0.5em,
      first-line-indent: 0pt,
    )
    columns(2, gutter: 16pt, acc)
  }
}

// ============================================================================
// The document-factory templates and components. Purely additive: book() above is
// unaffected. Everything here reuses the tokens and helpers defined earlier in this
// file, and the shared code-block base (apply-common) uses _codelines so factory
// output is copy-paste exact like the books.
// ============================================================================

// public alias for the callout block (factory templates / examples call callout())
#let callout = _callout

// a tracked, uppercase accent kicker / label
#let kicker(s, size: 9pt, color: none, weight: 700, tracking: 0.5pt) = context {
  let c = if color == none { theme-state.get().accent } else { color }
  text(
    font: head-font,
    size: size,
    weight: weight,
    fill: c,
    tracking: tracking,
  )[#upper(s)]
}

// a keycap
#let kbd(it) = box(
  inset: (x: 4pt, y: 0.5pt),
  outset: (y: 1.5pt),
  radius: 3pt,
  fill: white,
  stroke: 0.5pt + rulec,
  text(font: head-font, size: 0.8em, fill: ink)[#it],
)

// a thin horizontal rule
#let hr(w: 100%, s: 0.8pt) = line(length: w, stroke: s + rulec)

// booktabs table from a 2-D array (first row is the header)
#let tbl(cols, data, align-spec: left) = table(
  columns: cols,
  align: align-spec,
  table.hline(stroke: 0.8pt + ink),
  ..data.first(),
  table.hline(stroke: 0.5pt + rulec),
  ..data.slice(1).flatten(),
  table.hline(stroke: 0.8pt + ink),
)

// a small color swatch
#let swatch(c) = box(
  width: 10pt,
  height: 10pt,
  radius: 2pt,
  fill: c,
  stroke: 0.5pt + rulec,
  baseline: 1.5pt,
)

// ---------------- one-pager / cheat-sheet components ----------------
// a filled status dot (pass a colour)
#let dot(c) = box(baseline: 1.5pt, circle(radius: 3pt, fill: c, stroke: none))

// compact key -> value list (shortcut -> action, command -> meaning)
#let kv(rows, gap: 8pt) = {
  set text(size: 8.5pt)
  grid(
    columns: (auto, 1fr),
    row-gutter: 4pt,
    column-gutter: gap,
    ..rows
      .map(r => (text(fill: ink)[#r.at(0)], text(fill: muted)[#r.at(1)]))
      .flatten()
  )
}

// a titled panel with a coloured header bar; stays whole within a column.
// `tone` defaults to the themed accent; pass a colour to override.
#let card(title, body, tone: none) = context {
  let t = if tone == none { theme-state.get().accent } else { tone }
  block(
    breakable: false,
    width: 100%,
    below: 9pt,
    radius: 4pt,
    clip: true,
    stroke: 0.7pt + rulec,
  )[
    #block(width: 100%, fill: t, inset: (x: 8pt, y: 4.5pt))[
      #text(
        font: head-font,
        size: 8.5pt,
        weight: 600,
        fill: white,
        tracking: 0.7pt,
      )[#upper(title)]
    ]
    #block(width: 100%, inset: (x: 8pt, y: 7pt), body)
  ]
}

// page marking (e.g. "INTERNAL"): a small, opaque, horizontal red stamp centered in the
// bottom margin - reads as a footer label and, unlike a page-spanning diagonal, never
// overlaps the body, so it does not bleed into copied text. none = off.
#let _watermark(txt) = if txt != none {
  place(bottom + center, dy: -0.42in, text(
    font: head-font,
    size: 7.5pt,
    weight: 700,
    tracking: 1.2pt,
    fill: rgb("#C0392B"),
  )[#upper(txt)])
}

// dotted leader cell for contents / figure lists
#let _leader(fill: rulec, size: 9pt) = align(
  bottom,
  box(width: 100%, inset: (bottom: 2pt), repeat[#text(
    fill: fill,
    size: size,
  )[.]]),
)

// shared base for the factory templates (applied via `#show: apply-common`). The
// code-block treatment matches book(): long lines auto-shrink (no ZWSP, no wrap).
#let apply-common(body) = {
  set text(
    font: body-font,
    size: body-size,
    fill: ink,
    lang: "en",
    region: "US",
    hyphenate: true,
  )
  set par(justify: false, leading: 0.65em, spacing: 1.05em, first-line-indent: (
    amount: 1.1em,
    all: false,
  ))
  show raw: set text(font: mono-font)

  show raw.where(block: true): it => if it.lang == "settings" {
    _settings(it)
  } else {
    block(
      width: 100%,
      fill: codebg,
      stroke: 0.5pt + rulec,
      radius: 3pt,
      inset: (x: 9pt, y: 8pt),
      above: 1.0em,
      below: 1.0em,
      breakable: it.lines.len() > 18,
    )[
      #if it.lang != none {
        align(right, box(
          fill: rulec,
          inset: (x: 5pt, y: 2pt),
          radius: 2pt,
          text(
            font: head-font,
            size: 7pt,
            weight: 600,
            fill: muted,
            tracking: 0.4pt,
          )[#upper(it.lang)],
        ))
        v(2pt, weak: true)
      }
      #set text(font: mono-font, size: 9pt, hyphenate: false)
      #set par(justify: false, leading: 0.58em, first-line-indent: 0pt)
      #_codelines(it.lines)
    ]
  }

  set table(stroke: none, inset: (x: 8pt, y: 6pt))
  show table.cell: set par(justify: false)
  show table.cell: set text(hyphenate: false)
  show table.cell.where(y: 0): set text(
    font: head-font,
    weight: 600,
    size: 9.5pt,
  )

  show figure.caption: set align(left)
  show figure.caption: it => text(
    font: head-font,
    size: 8.5pt,
    fill: muted,
  )[#it]
  set figure(gap: 6pt)

  show link: it => context text(fill: theme-state.get().accent, it)
  body
}

// front-matter title page used by the report template
#let titlepage(
  title: "",
  subtitle: "",
  version: "",
  date: "",
  logo: none,
  author: "",
  theme: (:),
) = {
  let accent = _theme(theme).accent
  page(
    header: none,
    footer: none,
    numbering: none,
    margin: (x: 1in, y: 1.1in),
  )[
    #align(center)[
      #v(1.0in)
      #if logo != none { logo }
      #v(0.8in)
      #text(font: head-font, size: 28pt, weight: 700, fill: ink)[#title]
      #v(10pt)
      #text(font: head-font, size: 14pt, weight: 500, fill: muted)[#subtitle]
      #v(14pt)
      #line(length: 28%, stroke: 1.2pt + accent)
    ]
    #place(bottom + center, dy: -0.2in)[
      #set text(font: head-font, size: 10pt, fill: muted)
      #if author != "" [ #align(center)[#author] #v(6pt) ]
      Version #version #sym.dash.en #date
    ]
  ]
}

// TEMPLATE: report (cover, contents, numbered sections, running head)
#let report(
  title: "",
  subtitle: "",
  version: "",
  date: "",
  author: "",
  logo: none,
  draft: false,
  toc: true,
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title, author: author)
  let wm = if watermark != none { watermark } else if draft { "DRAFT" } else {
    none
  }

  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.25in, top: 1.05in, bottom: 0.95in),
    background: _watermark(wm),
    header: context {
      let pg = here().page()
      let opener = query(heading.where(level: 1)).any(h => (
        h.location().page() == pg
      ))
      let secs = query(heading.where(level: 1).before(here()))
      if secs.len() > 0 and not opener {
        set text(font: head-font, size: 8.5pt, fill: muted)
        grid(
          columns: (1fr, 1fr),
          smallcap(secs.last().body), align(right, emph(title)),
        )
        v(3pt)
        line(length: 100%, stroke: 0.5pt + rulec)
      }
    },
    footer: context {
      set text(font: head-font, size: 9pt, fill: muted)
      align(center, counter(page).display())
    },
  )

  set heading(numbering: "1.1.1")
  show heading: set text(font: head-font, fill: ink)
  show heading: set par(justify: false)

  show heading.where(level: 1): it => {
    v(1.4em)
    block(above: 0pt, below: 0.6em)[
      #kicker(
        counter(heading).display(),
        size: 13pt,
        weight: 700,
        tracking: 0.4pt,
      )
      #v(5pt, weak: true)
      #text(font: head-font, size: 19pt, weight: 700)[#smallcap(it.body)]
      #v(7pt, weak: true)
      #line(length: 100%, stroke: 0.8pt + rulec)
    ]
  }
  show heading.where(level: 2): it => block(above: 1.3em, below: 0.5em)[
    #text(font: head-font, size: 13.5pt, weight: 600)[
      #text(fill: accent)[#counter(heading).display()] #h(6pt) #it.body
    ]
  ]
  show heading.where(level: 3): it => block(above: 1.0em, below: 0.3em)[
    #text(font: head-font, size: 11.5pt, weight: 600)[#it.body]
  ]

  titlepage(
    title: title,
    subtitle: subtitle,
    version: version,
    date: date,
    logo: logo,
    author: author,
    theme: th,
  )

  set page(numbering: "1")
  counter(page).update(1)
  if toc {
    v(0.2in)
    text(font: head-font, size: 22pt, weight: 700)[Contents]
    v(12pt)
    line(length: 100%, stroke: 0.8pt + rulec)
    v(10pt)
    context {
      for hd in query(heading) {
        let loc = hd.location()
        let pg = counter(page).at(loc).first()
        let n = counter(heading).at(loc)
        if hd.level == 1 {
          block(above: 11pt, below: 3pt)[
            #grid(
              columns: (auto, 1fr, auto),
              column-gutter: 6pt,
              text(font: head-font, weight: 700)[#box(width: 1.7em)[#numbering(
                  "1",
                  n.at(0),
                )]#hd.body],
              _leader(),
              text(font: head-font, weight: 700)[#pg],
            )
          ]
        } else if hd.level == 2 {
          block(above: 2pt, below: 2pt, inset: (left: 1.3em))[
            #grid(
              columns: (auto, 1fr, auto),
              column-gutter: 6pt,
              text(font: head-font, size: 10pt, fill: muted)[#box(
                  width: 2.4em,
                )[#numbering("1.1", ..n)]#hd.body],
              _leader(fill: rulec.lighten(20%)),
              text(font: head-font, size: 10pt, fill: muted)[#pg],
            )
          ]
        } else if hd.level == 3 {
          block(above: 1pt, below: 1pt, inset: (left: 3.1em))[
            #grid(
              columns: (auto, 1fr, auto),
              column-gutter: 6pt,
              text(font: head-font, size: 9pt, fill: muted)[#box(
                  width: 3.1em,
                )[#numbering("1.1.1", ..n)]#hd.body],
              _leader(fill: rulec.lighten(35%)),
              text(font: head-font, size: 9pt, fill: muted)[#pg],
            )
          ]
        }
      }
    }
    pagebreak(weak: true)
  }
  body
}

// flatten nested content sequences to a flat list of top-level blocks, leaving real
// block elements (headings, lists, tables, paragraphs) intact. doc-md output arrives
// wrapped in an outer sequence, so the one-pager unwraps it to find the `#` sections.
#let _seq-blocks(c) = if repr(c.func()) == "sequence" {
  c.children.map(_seq-blocks).flatten()
} else {
  (c,)
}

// one-pager per-card tone. Author it as the FIRST line of a `#` section with a
// raw-typst metadata marker (metadata is a builtin, so it needs no scope wiring):
//   <!--raw-typst #metadata("danger")<card-tone>-->
// "lead"/"hero" promotes the section to the full-width lead slot; "danger"/"avoid"/
// "caution" -> caution tone; "do"/"ok"/"tip" -> tip tone; "warn" -> warning; else the
// accent. `card-tone(name)` is the equivalent helper for direct-Typst authoring.
#let card-tone(name) = [#metadata(name)<card-tone>]

#let _tone-color(name, th) = {
  if name in ("danger", "avoid", "caution") { th.tones.caution } else if (
    name
      in (
        "do",
        "ok",
        "tip",
        "good",
      )
  ) { th.tones.tip } else if name in ("warn", "warning") {
    th.tones.warning
  } else if name in ("note", "info") { th.tones.note } else { th.accent }
}

// TEMPLATE: onepager (landscape; dark masthead; optional full-width lead card; an
// equal-height grid of tinted-header cards). Each top-level Markdown `#` section is a
// card; a `<!--raw-typst #metadata("...")<card-tone>-->` first line tints it (or, with
// "lead", makes it the hero). `##` is a sub-bar, `###` a subhead. card/kv/dot via raw-typst.
#let onepager(
  title: "",
  subtitle: "",
  version: "",
  logo: none,
  footer-note: none,
  cols: 3,
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)

  set page(
    width: 11in,
    height: 8.5in,
    margin: (x: 0.5in, top: 0.45in, bottom: 0.4in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 7.5pt, fill: muted)
      let total = counter(page).final().first()
      grid(
        columns: (1fr, auto),
        if footer-note != none { footer-note } else { [] },
        if total > 1 { [Page #counter(page).display() of #total] } else { [] },
      )
    },
  )

  // `##` sub-bar / `###` subhead inside a card. The sub-bar text uses a darkened tone
  // so it clears WCAG AA on the pale fill (base accent on a light tint does not).
  set heading(numbering: none)
  show heading: set par(justify: false)
  show heading.where(level: 2): it => block(
    breakable: false,
    above: 6pt,
    below: 4pt,
    width: 100%,
    radius: 2pt,
    clip: true,
    fill: accent.lighten(86%),
    inset: (x: 6pt, y: 3pt),
  )[#text(
    font: head-font,
    size: 7.5pt,
    weight: 600,
    fill: accent.darken(24%),
    tracking: 0.7pt,
  )[#upper(it.body)]]
  show heading.where(level: 3): it => block(
    above: 5pt,
    below: 2pt,
    text(font: head-font, size: 8.5pt, weight: 600, fill: ink)[#it.body],
  )

  // dense body
  set text(size: 8.6pt)
  set par(first-line-indent: 0pt, leading: 0.66em, spacing: 0.7em)
  set table(inset: (x: 6pt, y: 3.5pt))

  // masthead: dark band, reversed title, accent pill + version, accent baseline rule
  let mast = {
    block(width: 100%, fill: ink, inset: (x: 14pt, top: 10pt, bottom: 11pt))[
      #grid(
        columns: (1fr, auto),
        column-gutter: 12pt,
        align: (left + horizon, right + horizon),
        {
          if logo != none {
            box(height: 22pt, logo)
            linebreak()
            v(6pt, weak: true)
          }
          text(
            font: head-font,
            size: 22pt,
            weight: 700,
            fill: white,
            top-edge: "cap-height",
            bottom-edge: "baseline",
          )[#title]
          if subtitle != "" {
            linebreak()
            v(3.5pt, weak: true)
            text(
              font: head-font,
              size: 10.5pt,
              weight: 400,
              fill: white.transparentize(28%),
            )[#subtitle]
          }
        },
        stack(
          dir: ttb,
          spacing: 6pt,
          if watermark != none {
            align(right, box(
              fill: accent,
              radius: 20pt,
              inset: (x: 8pt, y: 3pt),
              text(
                font: head-font,
                size: 7pt,
                weight: 700,
                fill: white,
                tracking: 0.8pt,
              )[#upper(watermark)],
            ))
          } else { [] },
          if version != "" {
            align(right, text(
              font: head-font,
              size: 8.5pt,
              fill: white.transparentize(40%),
            )[#version])
          } else { [] },
        ),
      )
    ]
    block(width: 100%, height: 2pt, fill: accent)
  }

  // --- split the markdown body into cards (one per `#` section) --------------
  let kids = _seq-blocks(body)
  let preamble = ()
  let cards = ()
  let ctitle = none
  let acc = ()
  let pack(t, a) = {
    let m = a.find(c => (
      c.func() == metadata and c.has("label") and c.label == <card-tone>
    ))
    (
      title: t,
      body: a.sum(default: []),
      tone: if m != none { m.value } else { none },
    )
  }
  for child in kids {
    if child.func() == heading and child.depth == 1 {
      if ctitle != none { cards.push(pack(ctitle, acc)) }
      ctitle = child.body
      acc = ()
    } else if ctitle == none {
      preamble.push(child)
    } else {
      acc.push(child)
    }
  }
  if ctitle != none { cards.push(pack(ctitle, acc)) }

  if cards.len() == 0 {
    mast
    v(9pt)
    columns(cols, gutter: 12pt, body)
  } else {
    // card renderers: tinted, tone-aware header; faint body wash; one solid hero.
    let render-card(c, h) = {
      let tc = _tone-color(c.tone, th)
      block(
        width: 100%,
        height: h,
        breakable: false,
        radius: 4pt,
        clip: true,
        fill: tc.lighten(92%),
        stroke: (left: 3pt + tc, rest: 0.7pt + rulec),
      )[
        #block(
          width: 100%,
          fill: tc.lighten(80%),
          inset: (x: 8pt, top: 4pt, bottom: 4.5pt),
          stroke: (bottom: 1.2pt + tc),
        )[
          #text(
            font: head-font,
            size: 8pt,
            weight: 600,
            fill: tc.darken(22%),
            tracking: 1.0pt,
          )[#upper(c.title)]
        ]
        #block(width: 100%, inset: (x: 9pt, top: 9.5pt, bottom: 8pt))[
          #set list(marker: text(fill: tc)[#sym.bullet])
          #c.body
        ]
      ]
    }
    let render-hero(c) = block(
      width: 100%,
      breakable: false,
      radius: 4pt,
      clip: true,
      fill: accent.lighten(90%),
      stroke: 0.7pt + accent,
    )[
      #block(width: 100%, fill: accent, inset: (
        x: 11pt,
        top: 5pt,
        bottom: 5.5pt,
      ))[
        #text(
          font: head-font,
          size: 9pt,
          weight: 600,
          fill: white,
          tracking: 1.0pt,
        )[#upper(c.title)]
      ]
      #block(width: 100%, inset: (x: 14pt, top: 12pt, bottom: 13pt))[
        #set text(size: 15pt, weight: 500)
        #set par(leading: 0.7em)
        #c.body
      ]
    ]

    let lead = cards.find(c => c.tone in ("lead", "hero"))
    let rest = cards.filter(c => not (c.tone in ("lead", "hero")))
    let gut = 12pt

    // slim running masthead for pages after the first (keeps page 2+ from orphaning)
    let slim-mast = {
      block(width: 100%, fill: ink, inset: (x: 14pt, y: 6pt))[
        #grid(
          columns: (1fr, auto),
          align: (left + horizon, right + horizon),
          text(font: head-font, size: 12pt, weight: 700, fill: white)[#title],
          if watermark != none {
            box(
              fill: accent,
              radius: 20pt,
              inset: (x: 7pt, y: 2pt),
              text(
                font: head-font,
                size: 6.5pt,
                weight: 700,
                fill: white,
                tracking: 0.8pt,
              )[#upper(watermark)],
            )
          } else { [] },
        )
      ]
      block(width: 100%, height: 2pt, fill: accent)
    }

    context {
      let cw = (10in - (cols - 1) * gut) / cols
      let pageH = 8.5in - 0.45in - 0.4in
      let mastH = measure(box(width: 10in, mast)).height
      let slimH = measure(box(width: 10in, slim-mast)).height
      let preH = if preamble.len() > 0 {
        measure(box(width: 10in, preamble.sum())).height + 8pt
      } else { 0pt }
      let leadH = if lead != none {
        measure(box(width: 10in, render-hero(lead))).height + 10pt
      } else { 0pt }
      let avail1 = pageH - mastH - 9pt - preH - leadH // page 1, under the hero
      let availN = pageH - slimH - 8pt // later pages, under the running header

      // row units: full rows of `cols`, plus a possibly-partial tail row that
      // stretches to full width so the grid never shows a blank trailing cell.
      let nFull = calc.quo(rest.len(), cols)
      let tail = calc.rem(rest.len(), cols)
      let units = ()
      for r in range(nFull) {
        let rc = rest.slice(r * cols, r * cols + cols)
        units.push((
          cards: rc,
          ncol: cols,
          h: calc.max(
            ..rc.map(c => measure(box(width: cw, render-card(c, auto))).height),
          ),
        ))
      }
      if tail > 0 {
        let rc = rest.slice(nFull * cols)
        let tw = (10in - (tail - 1) * gut) / tail
        units.push((
          cards: rc,
          ncol: tail,
          h: calc.max(
            ..rc.map(c => measure(box(width: tw, render-card(c, auto))).height),
          ),
        ))
      }

      // pack row units onto pages by height (page 1 has less room: the hero is above)
      let pages = ()
      let cur = ()
      let used = 0pt
      let cap = avail1
      for u in units {
        let add = u.h + (if cur.len() > 0 { gut } else { 0pt })
        if cur.len() > 0 and used + add > cap + 1pt {
          pages.push(cur)
          cur = ()
          used = 0pt
          cap = availN
          add = u.h
        }
        cur.push(u)
        used += add
      }
      if cur.len() > 0 { pages.push(cur) }
      if pages.len() == 0 { pages = ((),) } // hero-only: still emit the masthead page

      // emit each page: chrome, then its rows justified to fill the page height
      for (pi, punits) in pages.enumerate() {
        let pcap = if pi == 0 { avail1 } else { availN }
        if pi == 0 {
          mast
          v(9pt)
          if preamble.len() > 0 {
            preamble.sum()
            v(8pt)
          }
          if lead != none {
            render-hero(lead)
            v(10pt)
          }
        } else {
          pagebreak()
          slim-mast
          v(8pt)
        }
        let nat = (
          punits.map(u => u.h).sum(default: 0pt)
            + calc.max(punits.len() - 1, 0) * gut
        )
        let gap = if punits.len() > 1 and nat < pcap {
          calc.min(gut + (pcap - nat) / (punits.len() - 1), 34pt)
        } else { gut }
        for (ui, u) in punits.enumerate() {
          if ui > 0 { v(gap) }
          grid(
            columns: (1fr,) * u.ncol, rows: (u.h,),
            column-gutter: gut,
            ..u.cards.map(c => render-card(c, 100%)),
          )
        }
      }
    }
  }
}

// TEMPLATE: article (compact title block, flowing sections, folio)
#let article(
  title: "",
  subtitle: "",
  byline: "",
  date: "",
  kicker-text: "",
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.4in, top: 1.0in, bottom: 1.0in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 9pt, fill: muted)
      align(center, counter(page).display())
    },
  )
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.5em, below: 0.5em)[
    #text(font: head-font, size: 15pt, weight: 600)[#it.body]
  ]
  show heading.where(level: 2): it => block(above: 1.1em, below: 0.3em)[
    #text(font: head-font, size: 12pt, weight: 600, fill: muted)[#it.body]
  ]

  block(above: 0pt, below: 1.4em)[
    #if kicker-text != "" {
      kicker(kicker-text, size: 9pt)
      v(8pt, weak: true)
    }
    #text(font: head-font, size: 27pt, weight: 700, fill: ink)[#title]
    #if subtitle != "" {
      v(8pt, weak: true)
      text(font: head-font, size: 14pt, weight: 400, fill: muted)[#subtitle]
    }
    #v(10pt, weak: true)
    #line(length: 100%, stroke: 0.8pt + rulec)
    #v(5pt, weak: true)
    #set text(font: head-font, size: 9pt, fill: muted)
    #grid(
      columns: (1fr, auto),
      [#byline], [#date],
    )
  ]
  body
}

// TEMPLATE: minutes (header block, metadata table, agenda items)
#let minutes(
  title: "Meeting Minutes",
  meeting: "",
  date: "",
  time: "",
  location: "",
  attendees: (),
  apologies: (),
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.25in, top: 1.0in, bottom: 0.95in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8.5pt, fill: muted)
      grid(
        columns: (1fr, auto),
        emph(meeting), counter(page).display(),
      )
    },
  )
  set heading(numbering: "1.")
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.2em, below: 0.45em)[
    #text(font: head-font, size: 13pt, weight: 600)[
      #text(fill: accent)[#counter(heading).display()] #h(5pt) #it.body
    ]
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rulec)
  ]
  show heading.where(level: 2): it => block(above: 0.9em, below: 0.25em, text(
    font: head-font,
    size: 11pt,
    weight: 600,
  )[#it.body])

  kicker("Meeting Minutes", size: 9pt)
  v(7pt, weak: true)
  text(font: head-font, size: 23pt, weight: 700)[#meeting]
  v(12pt, weak: true)

  let cell(label, val) = (
    text(font: head-font, size: 9pt, weight: 600, fill: muted)[#upper(label)],
    text(size: 10pt)[#val],
  )
  block(width: 100%)[
    #set par(first-line-indent: 0pt)
    #grid(
      columns: (auto, 1fr), column-gutter: 14pt, row-gutter: 5pt,
      ..cell("Date", date), ..cell("Time", time), ..cell("Location", location),
      ..cell("Present", attendees.join(", ")),
      ..(
        if apologies.len() > 0 {
          cell("Apologies", apologies.join(", "))
        } else { () }
      ),
    )
  ]
  v(6pt)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(10pt)
  body
}

// TEMPLATE: memo (memorandum header, body, one accent rule)
#let memo(
  to: "",
  from: "",
  date: "",
  re: "",
  cc: none,
  logo: none,
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: re)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.3in, top: 1.0in, bottom: 1.0in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8.5pt, fill: muted)
      align(center, counter(page).display())
    },
  )
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.1em, below: 0.3em, text(
    font: head-font,
    size: 12.5pt,
    weight: 600,
  )[#it.body])

  grid(
    columns: (1fr, auto),
    align(left + horizon)[#kicker("Memorandum", size: 11pt, tracking: 1pt)],
    if logo != none { align(right + horizon, box(height: 22pt, logo)) } else {
      []
    },
  )
  v(10pt, weak: true)
  line(length: 100%, stroke: 1.2pt + accent)
  v(10pt, weak: true)
  let row(label, val) = (
    text(font: head-font, size: 9pt, weight: 600, fill: muted)[#upper(label)],
    text(font: head-font, size: 10.5pt)[#val],
  )
  block(width: 100%)[
    #set par(first-line-indent: 0pt)
    #grid(
      columns: (auto, 1fr), column-gutter: 12pt, row-gutter: 4pt,
      ..row("To", to), ..row("From", from), ..row("Date", date),
      ..(if cc != none { row("Cc", cc) } else { () }),
      ..row("Re", re),
    )
  ]
  v(8pt)
  line(length: 100%, stroke: 0.5pt + rulec)
  v(12pt)
  body
}

// TEMPLATE: release-notes (product masthead, version sections, change categories)
#let release-notes(
  product: "",
  version: "",
  date: "",
  status: "",
  subtitle: "",
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(
    title: product + (if version != "" { " " + version } else { "" }),
  )
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.3in, top: 1.0in, bottom: 1.0in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8.5pt, fill: muted)
      grid(
        columns: (1fr, auto),
        emph(product), counter(page).display(),
      )
    },
  )
  show heading: set text(font: head-font, fill: ink)
  // a version section
  show heading.where(level: 1): it => block(above: 1.5em, below: 0.6em)[
    #block(fill: accent, inset: (x: 8pt, y: 4pt), radius: 3pt)[
      #text(fill: white, font: head-font, size: 13pt, weight: 700)[#it.body]
    ]
    #v(5pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rulec)
  ]
  // a change category (Added / Fixed / Security / ...)
  show heading.where(level: 2): it => block(above: 1.0em, below: 0.3em)[
    #text(
      font: head-font,
      size: 9.5pt,
      weight: 700,
      fill: muted,
      tracking: 0.5pt,
    )[#smallcap(it.body)]
  ]
  show heading.where(level: 3): it => block(above: 0.8em, below: 0.25em, text(
    font: head-font,
    size: 11pt,
    weight: 600,
  )[#it.body])

  kicker("Release Notes", size: 9pt)
  v(7pt, weak: true)
  text(font: head-font, size: 25pt, weight: 700)[#product]
  if subtitle != "" {
    v(7pt, weak: true)
    text(font: head-font, size: 13pt, weight: 400, fill: muted)[#subtitle]
  }
  v(10pt, weak: true)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(5pt, weak: true)
  block(below: 12pt)[
    #set text(font: head-font, size: 9pt, fill: muted)
    #set par(first-line-indent: 0pt)
    #{
      let parts = (
        if version != "" { [Version #version] },
        if status != "" { [#status] },
        if date != "" { [#date] },
      ).filter(p => p != none)
      parts.join([#h(4pt)#sym.dot.c#h(4pt)])
    }
  ]
  body
}

// TEMPLATE: runbook (operational metadata, numbered steps, callouts)
#let runbook(
  title: "",
  system: "",
  owner: "",
  version: "",
  date: "",
  last-reviewed: "",
  severity: "",
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.25in, top: 1.0in, bottom: 0.95in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8.5pt, fill: muted)
      grid(
        columns: (1fr, auto),
        emph(title), counter(page).display(),
      )
    },
  )
  set heading(numbering: "1.1")
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.2em, below: 0.45em)[
    #text(font: head-font, size: 13pt, weight: 600)[
      #text(fill: accent)[#counter(heading).display()] #h(6pt) #it.body
    ]
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rulec)
  ]
  show heading.where(level: 2): it => block(above: 0.9em, below: 0.25em, text(
    font: head-font,
    size: 11pt,
    weight: 600,
  )[#text(fill: accent)[#counter(heading).display()] #h(5pt) #it.body])

  kicker("Runbook", size: 9pt)
  v(7pt, weak: true)
  text(font: head-font, size: 23pt, weight: 700)[#title]
  v(12pt, weak: true)
  let cell(label, val) = (
    text(font: head-font, size: 9pt, weight: 600, fill: muted)[#upper(label)],
    text(size: 10pt)[#val],
  )
  block(width: 100%)[
    #set par(first-line-indent: 0pt)
    #grid(
      columns: (auto, 1fr, auto, 1fr),
      column-gutter: 12pt,
      row-gutter: 5pt,
      ..(if system != "" { cell("System", system) } else { () }),
      ..(if owner != "" { cell("Owner", owner) } else { () }),
      ..(if severity != "" { cell("Severity", severity) } else { () }),
      ..(if version != "" { cell("Version", version) } else { () }),
      ..(
        if last-reviewed != "" { cell("Last reviewed", last-reviewed) } else {
          ()
        }
      ),
      ..(if date != "" { cell("Date", date) } else { () }),
    )
  ]
  v(6pt)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(10pt)
  body
}

// TEMPLATE: kb-article (knowledge base / FAQ: applies-to header, lead summary, support footer)
#let kb-article(
  title: "",
  subtitle: "",
  category: "",
  applies-to: (),
  updated: "",
  summary: "",
  support-note: none,
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.4in, top: 1.0in, bottom: 1.0in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 9pt, fill: muted)
      align(center, counter(page).display())
    },
  )
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.4em, below: 0.4em)[
    #text(font: head-font, size: 15pt, weight: 600)[#it.body]
    #v(2pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rulec)
  ]
  show heading.where(level: 2): it => block(above: 1.1em, below: 0.3em, text(
    font: head-font,
    size: 12pt,
    weight: 600,
    fill: muted,
  )[#it.body])

  block(above: 0pt, below: 1.2em)[
    #if category != "" {
      kicker(category, size: 9pt)
      v(8pt, weak: true)
    }
    #text(font: head-font, size: 24pt, weight: 700, fill: ink)[#title]
    #if subtitle != "" {
      v(7pt, weak: true)
      text(font: head-font, size: 13pt, weight: 400, fill: muted)[#subtitle]
    }
    #v(9pt, weak: true)
    #line(length: 100%, stroke: 0.8pt + rulec)
    #v(5pt, weak: true)
    #{
      set text(font: head-font, size: 9pt, fill: muted)
      let appstr = if type(applies-to) == array {
        applies-to.join(", ")
      } else { applies-to }
      let parts = (
        if appstr != none and appstr != "" { [Applies to: #appstr] },
        if updated != "" { [Updated #updated] },
      ).filter(p => p != none)
      parts.join([#h(6pt)#sym.dot.c#h(6pt)])
    }
  ]
  if summary != "" {
    block(
      width: 100%,
      inset: (x: 11pt, y: 9pt),
      radius: 3pt,
      below: 1.2em,
      fill: accent.lighten(93%),
      stroke: (left: 2.5pt + accent),
    )[
      #set par(first-line-indent: 0pt)
      #set text(size: 10.5pt)
      #summary
    ]
  }
  body
  if support-note != none {
    v(1.2em)
    line(length: 100%, stroke: 0.5pt + rulec)
    v(6pt)
    block[
      #set par(first-line-indent: 0pt)
      #text(
        font: head-font,
        size: 9pt,
        weight: 700,
        fill: muted,
        tracking: 0.4pt,
      )[#upper("Need more help?")]
      #v(3pt, weak: true)
      #set text(size: 10pt)
      #support-note
    ]
  }
}

// TEMPLATE: bug-report (defect / security finding: severity badge, triage metadata, body)
#let bug-report(
  title: "",
  severity: "",
  status: "",
  product: "",
  version: "",
  component: "",
  discovered: "",
  owner: "",
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.25in, top: 1.0in, bottom: 0.95in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8.5pt, fill: muted)
      grid(
        columns: (1fr, auto),
        emph(title), counter(page).display(),
      )
    },
  )
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(above: 1.2em, below: 0.4em)[
    #text(font: head-font, size: 13pt, weight: 600)[#it.body]
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rulec)
  ]
  show heading.where(level: 2): it => block(above: 0.9em, below: 0.25em, text(
    font: head-font,
    size: 11pt,
    weight: 600,
  )[#it.body])

  // severity drives a coloured badge; unknown values fall back to the accent
  let sev-color = (
    "critical": rgb("#B42318"),
    "high": rgb("#B42318"),
    "medium": rgb("#B54708"),
    "low": muted,
  ).at(lower(severity), default: accent)

  kicker("Bug Report", size: 9pt)
  v(7pt, weak: true)
  text(font: head-font, size: 22pt, weight: 700, hyphenate: false)[#title]
  v(12pt, weak: true)
  let cell(label, val) = (
    text(font: head-font, size: 9pt, weight: 600, fill: muted)[#upper(label)],
    text(size: 10pt)[#val],
  )
  block(width: 100%)[
    #set par(first-line-indent: 0pt)
    #grid(
      columns: (auto, 1fr, auto, 1fr),
      column-gutter: 12pt,
      row-gutter: 6pt,
      ..(
        if severity != "" {
          (
            text(font: head-font, size: 9pt, weight: 600, fill: muted)[#upper(
              "Severity",
            )],
            box(
              fill: sev-color.lighten(85%),
              inset: (x: 6pt, y: 2pt),
              radius: 3pt,
            )[
              #text(
                font: head-font,
                size: 9pt,
                weight: 700,
                fill: sev-color,
              )[#upper(severity)]
            ],
          )
        } else { () }
      ),
      ..(if status != "" { cell("Status", status) } else { () }),
      ..(if product != "" { cell("Product", product) } else { () }),
      ..(if version != "" { cell("Version", version) } else { () }),
      ..(if component != "" { cell("Component", component) } else { () }),
      ..(if discovered != "" { cell("Discovered", discovered) } else { () }),
      ..(if owner != "" { cell("Owner", owner) } else { () }),
    )
  ]
  v(6pt)
  line(length: 100%, stroke: 0.8pt + rulec)
  v(10pt)
  body
}

// form fields: draw the visible field in the house style and record each field's
// geometry as metadata; a post-compile step (make_form.py) overlays real
// interactive AcroForm widgets at the same coordinates.
#let _fieldfill = rgb("#FCFCFD")

#let formfield(key, kind: "text", fh: 17pt, lines: 1) = {
  if kind == "check" {
    box(
      width: 13pt,
      height: 13pt,
      radius: 2pt,
      fill: white,
      stroke: 0.9pt + muted.lighten(10%),
    )[
      #context [#metadata((
        k: key,
        kind: "check",
        x: here().position().x / 1pt,
        y: here().position().y / 1pt,
        w: 13.0,
        h: 13.0,
        pg: here().page(),
      ))<ff>]
    ]
  } else {
    let hh = fh * lines
    box(
      width: 100%,
      height: hh,
      radius: 3pt,
      fill: _fieldfill,
      stroke: 0.75pt + rulec,
    )[
      #place(top + left, context [#metadata((
        k: key,
        kind: kind,
        x: here().position().x / 1pt,
        y: here().position().y / 1pt,
        h: hh / 1pt,
        pg: here().page(),
        ml: lines > 1,
      ))<ff>])
      #place(top + right, context [#metadata((
        k: key,
        xr: here().position().x / 1pt,
      ))<ffr>])
    ]
  }
}

#let flabel(s) = text(
  font: head-font,
  size: 8.5pt,
  weight: 600,
  fill: muted,
  tracking: 0.3pt,
)[#upper(s)]

#let field-block(label, key, kind: "text", lines: 1) = block(
  width: 100%,
  breakable: false,
  below: 0.72em,
)[
  #flabel(label)
  #v(3pt, weak: true)
  #formfield(key, kind: kind, lines: lines)
]

#let checkbox(key, label) = box(inset: (y: 1.5pt))[
  #box(baseline: 3pt, formfield(key, kind: "check"))
  #h(5pt)
  #text(font: head-font, size: 10pt)[#label]
]

// TEMPLATE: form (header, accent section bars, fillable fields)
#let form(
  title: "",
  subtitle: "",
  logo: none,
  form-id: "",
  intro: none,
  footer-note: none,
  watermark: none,
  theme: (:),
  body,
) = {
  let th = _theme(theme)
  let accent = th.accent
  theme-state.update(th)
  show: apply-common
  set document(title: title)
  set page(
    width: 8.5in,
    height: 11in,
    margin: (x: 1.1in, top: 0.9in, bottom: 0.85in),
    background: _watermark(watermark),
    footer: context {
      set text(font: head-font, size: 8pt, fill: muted)
      grid(
        columns: (1fr, auto),
        if footer-note != none { footer-note } else { [] },
        [Page #counter(page).display() of #counter(page).final().first()],
      )
    },
  )
  show heading: set text(font: head-font, fill: ink)
  show heading.where(level: 1): it => block(
    above: 1.0em,
    below: 0.5em,
    width: 100%,
    breakable: false,
  )[
    #block(fill: accent, inset: (x: 8pt, y: 5pt), radius: 2pt, width: 100%)[
      #text(fill: white, size: 10.5pt, weight: 600, tracking: 0.6pt)[#upper(
        it.body,
      )]
    ]
  ]
  show heading.where(level: 2): it => block(above: 0.9em, below: 0.3em, text(
    font: head-font,
    size: 10.5pt,
    weight: 600,
  )[#it.body])

  grid(
    columns: (1fr, auto),
    align: (left + horizon, right + horizon),
    if logo != none { box(height: 25pt, logo) } else { [] },
    if form-id != "" {
      text(font: head-font, size: 8.5pt, fill: muted)[Form #form-id]
    } else { [] },
  )
  v(11pt)
  text(font: head-font, size: 22pt, weight: 700)[#title]
  if subtitle != "" {
    v(4pt, weak: true)
    linebreak()
    text(font: head-font, size: 12pt, fill: muted)[#subtitle]
  }
  v(8pt)
  line(length: 100%, stroke: 1.2pt + accent)
  if intro != none {
    v(6pt)
    block(width: 100%, text(size: 10pt, fill: ink)[#intro])
  }
  v(8pt)
  body
}

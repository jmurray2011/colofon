#!/usr/bin/env python3
"""make_book - assemble a book from a YAML outline and Markdown chapters.

The book's structure is DATA. book.yaml lists the parts (each with a title, a
one-line blurb, and its chapter .md files in order); each chapter is book-flavored
Markdown (see the bookmd package). make_book validates the content in plain
English (bookmd_lint), substitutes single-source variables, generates the book()
wrapper, compiles it on the pinned toolchain, and runs the same gate as the
hand-authored books - so revising or re-versioning a book is editing Markdown and
YAML, no Typst.

    tools/make_book.py path/to/book.yaml [-o out.pdf]

book.yaml:
    title, subtitle, version, date    document metadata ({{vars}} allowed)
    logo, logo-alt                    optional cover logo (logo-alt required if logo)
    logo-width                        cover logo width (Typst length; default 2.5in)
    brand                             optional @local brand package; spreads its
                                      book-args (theme / colophon / author)
    draft: true|false                 optional DRAFT watermark
    vars: {k: v}                      inline single-source variables
    vars-from: ../release.yaml        shared variables file (inline vars override it)
    parts:                            ordered list of parts
      - title: Install
        blurb: One-line part intro.
        appendix: false               optional; true -> Appendix A/B/C from here on
        chapters:
          - chapters/01-intro.md      paths relative to this book.yaml

Anywhere in a chapter or the metadata, {{key}} is replaced by the matching variable;
a {{key}} with no variable is an error (catches typos before the compile).
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPST = os.environ.get("TYPST", os.path.expanduser("~/.local/bin/typst"))
VERAPDF = os.environ.get("VERAPDF", os.path.expanduser("~/.local/verapdf/verapdf"))
FONTS = os.path.join(WS, "engine", "fonts")
PACKAGES = os.path.join(WS, "packages")
# A missing verifier fails the build. Opting out has to be deliberate, because a
# book that reports success having verified nothing is worse than no book.
ALLOW_UNVERIFIED = os.environ.get("COLOFON_ALLOW_UNVERIFIED") == "1"


def die(msg):
    print(f"make_book: {msg}", file=sys.stderr)
    sys.exit(2)


def tstr(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def root_abs(path):
    return "/" + os.path.relpath(os.path.abspath(path), WS).replace(os.sep, "/")


def subst(text, variables, unknown):
    def repl(m):
        k = m.group(1).strip()
        if k in variables:
            return str(variables[k])
        unknown.add(k)
        return m.group(0)

    return re.sub(r"\{\{([^}]+)\}\}", repl, text)


def main():
    ap = argparse.ArgumentParser(description="assemble a book from book.yaml + Markdown chapters")
    ap.add_argument("book", help="the book.yaml outline")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    if not os.path.isfile(a.book):
        die(f"no such file: {a.book}")
    import yaml

    spec = yaml.safe_load(open(a.book, encoding="utf-8")) or {}
    base = os.path.dirname(os.path.abspath(a.book))

    if not spec.get("title"):
        die(f"{a.book}: 'title' is required")
    parts = spec.get("parts")
    if not isinstance(parts, list) or not parts:
        die(f"{a.book}: 'parts' must be a non-empty list")
    if spec.get("logo") and not spec.get("logo-alt"):
        die(f"{a.book}: 'logo' is set but 'logo-alt' is missing (UA-1 needs alt text)")

    for p in parts:
        if not p.get("title"):
            die(f"{a.book}: every part needs a 'title'")
        chs = p.get("chapters")
        if not isinstance(chs, list) or not chs:
            die(f"{a.book}: part '{p['title']}' has no chapters")
        for c in chs:
            if not os.path.isfile(os.path.join(base, c)):
                die(f"{a.book}: chapter not found: {c} (relative to {base})")

    # plain-English preflight (alt text, dangling cross-refs, missing/stale screenshots)
    import bookmd_lint

    chapter_files = [
        (os.path.join(base, c), open(os.path.join(base, c), encoding="utf-8").read())
        for p in parts for c in p["chapters"]
    ]
    problems, known = bookmd_lint.lint(chapter_files)
    if bookmd_lint.report(problems, known):
        die("fix the content problem(s) above, then rebuild")

    # single-source variables: vars-from (shared) overlaid by inline vars
    variables = {}
    if spec.get("vars-from"):
        vf = os.path.join(base, spec["vars-from"])
        if not os.path.isfile(vf):
            die(f"{a.book}: vars-from not found: {spec['vars-from']}")
        variables.update(yaml.safe_load(open(vf, encoding="utf-8")) or {})
    variables.update(spec.get("vars") or {})

    stem = os.path.splitext(os.path.basename(a.book))[0]
    builddir = os.path.join(WS, ".factory-build", "book-" + stem, "ch")
    os.makedirs(builddir, exist_ok=True)

    # substitute {{vars}} in metadata and chapters; collect any undefined references
    unknown = set()
    for k in ("title", "subtitle", "version", "date"):
        if isinstance(spec.get(k), str):
            spec[k] = subst(spec[k], variables, unknown)
    proc = {}
    for idx, (path, text) in enumerate(chapter_files):
        pp = os.path.join(builddir, f"{idx:02d}-{os.path.basename(path)}")
        open(pp, "w", encoding="utf-8").write(subst(text, variables, unknown))
        proc[path] = root_abs(pp)
    if unknown:
        die(f"undefined variable(s) used as {{{{...}}}}: {sorted(unknown)} - define them in 'vars' or 'vars-from'")

    # generate the book() wrapper; an optional `brand:` package spreads its book-args
    # (theme / colophon / author) into the book() call - the document's branding.
    brand = spec.get("brand")
    imports = [
        '#import "@local/house:0.1.0": *',
        '#import "@local/bookmd:0.1.0": chapter-md',
    ]
    if brand:
        imports.append(f'#import "@local/{brand}:0.1.0": book-args as _brand')
    head = imports + [
        "",
        "#show: book.with(",
        f"  title: {tstr(spec['title'])},",
    ]
    for k in ("subtitle", "version", "date"):
        if spec.get(k) is not None:
            v = spec[k]
            if isinstance(v, (datetime.date, datetime.datetime)):
                v = v.isoformat()
            head.append(f"  {k}: {tstr(v)},")
    if spec.get("draft"):
        head.append("  draft: true,")
    if spec.get("watermark"):
        head.append(f"  watermark: {tstr(spec['watermark'])},")
    blurbs = ", ".join(tstr(p.get("blurb", "")) for p in parts)
    head.append(f"  part-blurbs: ({blurbs}{',' if len(parts) == 1 else ''}),")
    if spec.get("logo"):
        lw = spec.get("logo-width", "2.5in")
        head.append(f"  logo: image({tstr(spec['logo'])}, alt: {tstr(spec['logo-alt'])}, width: {lw}),")
    if brand:
        head.append("  .._brand,")
    head.append(")")
    head.append("")

    body = []
    for p in parts:
        if p.get("appendix"):
            body.append("#appendix-state.update(true)")
        body.append(f"= {p['title']}")
        for c in p["chapters"]:
            ra = proc[os.path.join(base, c)]
            body.append(f"#chapter-md(read({tstr(ra)}), img: (p, ..a) => image(p, ..a))")
        body.append("")

    main_typ = os.path.join(os.path.dirname(builddir), "main.typ")
    open(main_typ, "w", encoding="utf-8").write("\n".join(head + body) + "\n")
    out = a.output or os.path.join(base, stem + ".pdf")

    # the gate: compile under ua-1 with no warnings, veraPDF ua1, no zero-width spaces
    r = subprocess.run([
        TYPST, "compile", "--root", WS,
        "--package-path", PACKAGES, "--package-cache-path", PACKAGES,
        "--font-path", FONTS, "--pdf-standard", "ua-1", main_typ, out,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        die(f"compile failed:\n{r.stderr.strip()}")
    if re.search(r"warning", r.stderr, re.I):
        die(f"compile produced warnings (gate fails):\n{r.stderr.strip()}")
    print(">> compiled under PDF/UA-1")
    if os.path.exists(VERAPDF):
        if 'isCompliant="true"' not in subprocess.run(
            [VERAPDF, "--flavour", "ua1", out], capture_output=True, text=True
        ).stdout:
            die("veraPDF: NOT PDF/UA-1 compliant")
        print(">> PDF/UA-1: compliant")
    elif ALLOW_UNVERIFIED:
        print(">> WARNING PDF/UA-1: NOT VERIFIED - veraPDF missing", file=sys.stderr)
    else:
        die(f"veraPDF not found at {VERAPDF} - cannot verify PDF/UA-1. Set VERAPDF, "
            f"or COLOFON_ALLOW_UNVERIFIED=1 to build without verification.")
    if shutil.which("pdftotext"):
        if "​" in subprocess.run(["pdftotext", "-nopgbrk", out, "-"], capture_output=True, text=True).stdout:
            die("copy-safe: zero-width spaces in the text layer")
        print(">> copy-safe: no zero-width spaces in the text layer")
    elif ALLOW_UNVERIFIED:
        print(">> WARNING copy-safe: NOT VERIFIED - pdftotext missing", file=sys.stderr)
    else:
        die("pdftotext not found - cannot run the copy-safe check. Install poppler-utils, "
            "or set COLOFON_ALLOW_UNVERIFIED=1 to build without verification.")
    print(f">> built {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()

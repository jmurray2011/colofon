#!/usr/bin/env python3
"""bookmd_lint - a plain-English preflight for book-flavored Markdown.

Catches the mistakes a non-engineer makes before the Typst compile turns them into
cryptic errors, and names the chapter and line to fix:

  - images with no alt text            ![](x.png)        -> UA-1 fails
  - cross-references to a missing id    [text](#nope)     -> dangling reference
  - screenshots missing or out of date  ![a](shot:x.png)

Run standalone:  tools/bookmd_lint.py chapter.md [more.md ...]
Importable:      lint(chapters) -> (problems, known_ids)
                 chapters = [(path, text), ...]; problem = (severity, path, line, msg)
"""
import os
import re
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify(s):
    s = s.replace("`", "")
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"\s+", "-", s.strip())


def _asset(src):
    p = src[5:] if src.startswith("shot:") else src
    return os.path.join(WS, p.lstrip("/")) if p.startswith("/") else p


def lint(chapters):
    # every id a cross-reference could resolve to: explicit {#id} plus heading slugs
    explicit, slugs = {}, set()
    for path, text in chapters:
        for line in text.splitlines():
            m = re.match(r"^#{1,6}\s+(.+?)\s*\{#([\w-]+)\}\s*$", line)
            if m:
                explicit.setdefault(m.group(2), path)
                slugs.add(slugify(m.group(1)))
            else:
                h = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
                if h:
                    slugs.add(slugify(h.group(1)))
    # Typst labels carried in raw-typst escapes (e.g. a figure's <fig-x>) are also valid targets
    labels = set()
    for _, text in chapters:
        labels.update(re.findall(r"<([a-z][a-z0-9-]+)>", text))
    known = set(explicit) | slugs | labels

    problems = []
    for path, text in chapters:
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"!\[\s*\]\(", line):
                problems.append(("error", path, i, "image has no alt text - write ![describe it](...)"))
            for m in re.finditer(r"!\[[^\]]*\]\((shot:[^)]+)\)", line):
                ap = _asset(m.group(1))
                if not os.path.isfile(ap):
                    problems.append(("error", path, i, f"screenshot not found: {m.group(1)[5:]}"))
                elif os.path.getmtime(ap) < os.path.getmtime(path):
                    problems.append(("warning", path, i,
                        f"screenshot {os.path.basename(ap)} is older than this chapter - it may be out of date"))
            for m in re.finditer(r"\]\(#([\w-]+)\)", line):
                if m.group(1) not in known:
                    problems.append(("error", path, i, f"cross-reference to #{m.group(1)} - no heading defines that id"))
    return problems, sorted(known)


def report(problems, known, out=sys.stderr):
    for sev, path, ln, msg in problems:
        rel = os.path.relpath(path, WS)
        if rel.startswith(".."):
            rel = path
        print(f"  {sev:7} {rel}:{ln}: {msg}", file=out)
    errs = [p for p in problems if p[0] == "error"]
    if errs:
        print(f"\n{len(errs)} problem(s) to fix. Defined cross-reference ids: "
              f"{', '.join(known) or '(none)'}", file=out)
    return len(errs)


def main():
    paths = sys.argv[1:]
    if not paths:
        print("usage: bookmd_lint.py chapter.md [...]", file=sys.stderr)
        return 2
    chapters = [(p, open(p, encoding="utf-8").read()) for p in paths]
    problems, known = lint(chapters)
    n = report(problems, known)
    if n == 0 and not problems:
        print("bookmd_lint: ok")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())

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
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import automation
import workspace_paths

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify(s):
    s = s.replace("`", "")
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"\s+", "-", s.strip())


def _asset(src, source, project_root):
    p = src.removeprefix("shot:")
    if p.startswith("/"):
        candidate = os.path.join(project_root, p.lstrip("/"))
    else:
        candidate = os.path.join(os.path.dirname(os.path.abspath(source)), p)
    return workspace_paths.confined_file(candidate, project_root, "screenshot")


def lint(chapters, project_root=WS):
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
                try:
                    ap = _asset(m.group(1), path, project_root)
                except workspace_paths.WorkspacePathError as e:
                    problems.append(("error", path, i, str(e)))
                    continue
                if os.path.getmtime(ap) < os.path.getmtime(path):
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
    ap = argparse.ArgumentParser(description="lint book-flavored Markdown")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--root", help="project root for assets and path confinement")
    ap.add_argument("--json", action="store_true", help="emit a structured result")
    a = ap.parse_args()
    paths = a.paths
    if not paths:
        print("usage: bookmd_lint.py chapter.md [...]", file=sys.stderr)
        return 2
    project_root = os.path.abspath(a.root or workspace_paths.project_root_for(paths[0], WS))
    chapters = []
    for path in paths:
        try:
            resolved = workspace_paths.confined_file(path, project_root, "Markdown source")
            with open(resolved, encoding="utf-8") as chapter:
                chapters.append((resolved, chapter.read()))
        except (OSError, workspace_paths.WorkspacePathError) as e:
            if a.json:
                automation.emit(automation.failure("markdown-lint", e, path))
                return 1
            raise
    problems, known = lint(chapters, project_root)
    n = len([problem for problem in problems if problem[0] == "error"])
    if a.json:
        automation.emit({
            "api_version": automation.API_VERSION,
            "defined_ids": known,
            "kind": "markdown-lint",
            "ok": n == 0,
            "problems": [
                {
                    "line": line,
                    "message": message,
                    "severity": severity,
                    "source": os.path.abspath(path),
                }
                for severity, path, line, message in problems
            ],
        })
    else:
        n = report(problems, known)
    if not a.json and n == 0 and not problems:
        print("bookmd_lint: ok")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())

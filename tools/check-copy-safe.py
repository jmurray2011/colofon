#!/usr/bin/env python3
"""Gate check: every code block in the built PDF must be copy-paste exact.

Usage: check-copy-safe.py <pdf> <source-dir>

The book's value depends on commands pasting into a shell verbatim. The engine
must never inject break characters into code (it used to seed U+200B/U+00AD for
soft-wrapping, which silently corrupted the clipboard), and code lines must not
wrap (a wrap can drop a hyphen or inject a newline on copy). This asserts both:

  1. zero U+200B (zero-width space) anywhere in the PDF text layer, and
  2. every code-block token from the source survives verbatim in the PDF text
     (a mid-token break or injected character breaks the contiguous match).

Requires pdftotext (poppler). Skips cleanly if it is absent (e.g. a container
toolchain without poppler), so it never blocks a build it cannot run.
"""
import glob
import os
import re
import shutil
import subprocess
import sys


def main():
    if len(sys.argv) != 3:
        print("usage: check-copy-safe.py <pdf> <source-dir>", file=sys.stderr)
        return 2
    pdf, srcdir = sys.argv[1], sys.argv[2]
    if not shutil.which("pdftotext"):
        print(">> copy-safe check skipped (pdftotext not found)")
        return 0
    text = subprocess.run(
        ["pdftotext", "-nopgbrk", pdf, "-"],
        capture_output=True, text=True, encoding="utf-8",
    ).stdout

    fails = []
    zwsp = text.count("​")
    if zwsp:
        fails.append(f"{zwsp} zero-width space(s) (U+200B) in the PDF text layer")

    miss = []
    for f in sorted(glob.glob(os.path.join(srcdir, "**", "*.typ"), recursive=True)):
        src = open(f, encoding="utf-8").read()
        for m in re.finditer(r"```[a-z]*\n(.*?)```", src, re.S):
            for line in m.group(1).split("\n"):
                for tok in line.split():
                    if len(tok) >= 4 and tok not in text:
                        miss.append((os.path.basename(f), tok))
    if miss:
        fails.append(f"{len(miss)} code token(s) not copy-intact in the PDF text")

    if fails:
        print(">> COPY-SAFE CHECK FAILED:", file=sys.stderr)
        for x in fails:
            print("   - " + x, file=sys.stderr)
        for f, tok in miss[:20]:
            print(f"     MISS {f}: {tok!r}", file=sys.stderr)
        return 1
    print(">> copy-safe: code blocks are paste-exact")
    return 0


sys.exit(main())

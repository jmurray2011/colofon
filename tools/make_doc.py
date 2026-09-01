#!/usr/bin/env python3
"""make_doc - the document factory.

Turn Markdown files with YAML front-matter into brand-styled PDF/UA-1 documents
using the @local/house templates. The body is book-flavored Markdown, rendered
in-process via @local/bookmd (the same as the books): GitHub-style callouts
(> [!note] ...), `code`, [cross-refs](#slug), and ![shots](shot:path) all work.

    tools/make_doc.py doc.md [-o out.pdf]      # one document
    tools/make_doc.py docs/ a.md b.md          # batch: files and/or directories

Front-matter (a YAML block between leading --- fences):

    ---
    doctype: report          # report | article | minutes | memo | release-notes |
                             #   runbook | kb-article | bug-report | onepager  (required)
    brand: sample-brand      # optional @local brand package; applies its theme
    title: My Report
    version: "1.0"
    date: June 2026
    logo: /path/to/logo.png  # report/memo only; root-absolute from the workspace
    logo-alt: Acme logo   # required when logo is set (UA-1 needs alt)
    author: Office of the X  # report only; printed on the cover
    toc: false               # report only; drop the Contents page (default true)
    ---
    # First section
    Markdown body...

Each doctype has a schema (below): required keys, and the allowed optional keys.
Unknown keys are rejected to catch typos. The gate is the same bar as the books:
compile under --pdf-standard ua-1 with no warnings, veraPDF ua1, and no zero-width
spaces. Every image (the logo, and any ![alt](src) in the body) needs non-empty alt.

The interactive form template (AcroForm) is a separate path (tools/make_form.py),
not part of this Markdown factory; `book` is authored directly as a guide.
"""
import argparse
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPST = os.environ.get("TYPST", os.path.expanduser("~/.local/bin/typst"))
VERAPDF = os.environ.get("VERAPDF", os.path.expanduser("~/.local/verapdf/verapdf"))
FONTS = os.environ.get("COLOFON_FONTS", os.path.join(WS, "engine", "fonts"))
PACKAGES = os.environ.get("COLOFON_PACKAGES", os.path.join(WS, "packages"))
# A missing verifier fails the build. Opting out has to be deliberate, because a
# document that reports success having verified nothing is worse than no document.
ALLOW_UNVERIFIED = os.environ.get("COLOFON_ALLOW_UNVERIFIED") == "1"

# per-doctype front-matter schema: required keys, plus the allowed optional keys
# (which mirror each template's parameters). logo-alt is allowed wherever logo is.
DOCTYPE_SCHEMA = {
    "report": {"required": {"title"},
               "optional": {"subtitle", "version", "date", "author", "logo", "draft", "toc",
                            "watermark"}},
    "article": {"required": {"title"},
                "optional": {"subtitle", "byline", "date", "kicker-text", "watermark"}},
    "minutes": {"required": {"meeting"},
                "optional": {"title", "date", "time", "location", "attendees", "apologies", "watermark"}},
    "memo": {"required": {"re"},
             "optional": {"to", "from", "date", "cc", "logo", "watermark"}},
    "release-notes": {"required": {"product"},
                      "optional": {"version", "date", "status", "subtitle", "watermark"}},
    "runbook": {"required": {"title"},
                "optional": {"system", "owner", "version", "date", "last-reviewed", "severity", "watermark"}},
    "kb-article": {"required": {"title"},
                   "optional": {"subtitle", "category", "applies-to", "updated", "summary", "support-note", "watermark"}},
    "bug-report": {"required": {"title"},
                   "optional": {"severity", "status", "product", "version", "component", "discovered", "owner", "watermark"}},
    "onepager": {"required": {"title"},
                 "optional": {"subtitle", "version", "logo", "cols", "footer-note", "watermark"}},
}
DOCTYPES = tuple(DOCTYPE_SCHEMA)


class BuildError(Exception):
    """A per-document failure (bad front-matter, compile/gate failure)."""


def die(msg):
    print(f"make_doc: {msg}", file=sys.stderr)
    sys.exit(2)


def split_front_matter(text, path):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise BuildError(f"{path}: no YAML front-matter (expected a leading --- ... --- block)")
    import yaml

    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise BuildError(f"{path}: invalid YAML front-matter: {e}")
    if not isinstance(meta, dict):
        raise BuildError(f"{path}: front-matter must be a YAML mapping")
    return meta, m.group(2)


def validate_meta(meta, doctype, path):
    schema = DOCTYPE_SCHEMA[doctype]
    allowed = {"doctype", "brand"} | schema["required"] | schema["optional"]
    if "logo" in schema["optional"]:
        allowed.add("logo-alt")
    missing = schema["required"] - set(meta)
    if missing:
        raise BuildError(f"{path}: doctype '{doctype}' requires front-matter key(s): {sorted(missing)}")
    unknown = set(meta) - allowed
    if unknown:
        raise BuildError(
            f"{path}: unknown front-matter key(s) for doctype '{doctype}': {sorted(unknown)} "
            f"(allowed: {sorted(allowed - {'doctype'})})"
        )
    if "logo" in meta and not meta.get("logo-alt"):
        raise BuildError(f"{path}: 'logo' is set but 'logo-alt' is missing (UA-1 needs alt text)")


def check_body_alt(body, path):
    bad = [i + 1 for i, line in enumerate(body.splitlines()) if re.search(r"!\[\s*\]\(", line)]
    if bad:
        raise BuildError(f"{path}: image(s) with empty alt text on line(s) {bad} - UA-1 needs alt")


def typst_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        v = v.isoformat()
    if isinstance(v, list):
        return "(" + ", ".join(typst_value(x) for x in v) + (",)" if len(v) == 1 else ")")
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def build_wrapper(meta, doctype, project_root=WS):
    args = []
    for k, v in meta.items():
        if k in ("doctype", "brand", "logo", "logo-alt"):
            continue
        args.append(f"  {k}: {typst_value(v)},")
    if "logo" in meta:
        args.append(f'  logo: image({typst_value(meta["logo"])}, alt: {typst_value(meta["logo-alt"])}),')
    brand = meta.get("brand")
    if brand:
        args.append("  theme: _brand.theme,")
    arglines = "\n".join(args)
    imports = '#import "@local/house:0.1.0": *\n#import "@local/bookmd:0.1.0": doc-md'
    if brand:
        consumer_brand = os.path.join(
            project_root, "packages", "local", brand, "0.1.0", "lib.typ"
        )
        if os.path.realpath(project_root) != os.path.realpath(WS) and os.path.isfile(consumer_brand):
            imports += (
                f'\n#import "/packages/local/{brand}/0.1.0/lib.typ": '
                "book-args as _brand"
            )
        else:
            imports += f'\n#import "@local/{brand}:0.1.0": book-args as _brand'
    return f"""{imports}

#show: {doctype}.with(
{arglines}
)

// book-flavored Markdown (callouts, cross-refs, code, screenshots); images load on
// the consumer side so root-absolute paths resolve against --root.
#doc-md(read("body.md"), img: (p, ..a) => image(p, ..a))
"""


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def require_verifier(path, tool, hint):
    """Refuse to pass the gate when a verifier is absent, unless told to.

    Without this the gate degrades to 'not checked' on any machine missing the
    toolchain, and the build still reports success - so a document can ship as
    accessibility-gated having never been verified.
    """
    if not ALLOW_UNVERIFIED:
        raise BuildError(
            f"{path}: {tool} not found - cannot verify the document. {hint} "
            f"Set COLOFON_ALLOW_UNVERIFIED=1 to build without verification."
        )
    print(f"make_doc: WARNING {path}: {tool} missing - built UNVERIFIED", file=sys.stderr)


def gate(wrapper, out, path, project_root=WS):
    r = run([
        TYPST, "compile", "--root", project_root,
        "--package-path", PACKAGES, "--package-cache-path", PACKAGES,
        "--font-path", FONTS, "--pdf-standard", "ua-1", wrapper, out,
    ])
    if r.returncode != 0:
        raise BuildError(f"{path}: compile failed:\n{r.stderr.strip()}")
    if re.search(r"warning", r.stderr, re.I):
        raise BuildError(f"{path}: compile produced warnings (gate fails):\n{r.stderr.strip()}")
    if os.path.exists(VERAPDF):
        r = run([VERAPDF, "--flavour", "ua1", out])
        if 'isCompliant="true"' not in r.stdout:
            raise BuildError(f"{path}: veraPDF reports NOT PDF/UA-1 compliant")
    else:
        require_verifier(path, "veraPDF", f"Expected at {VERAPDF}; set VERAPDF to override.")
    if shutil.which("pdftotext"):
        if "​" in run(["pdftotext", "-nopgbrk", out, "-"]).stdout:
            raise BuildError(f"{path}: copy-safe check failed - zero-width spaces in the text layer")
    else:
        require_verifier(path, "pdftotext", "Install poppler-utils.")


def build_one(path, output=None, project_root=WS):
    project_root = os.path.abspath(project_root)
    if not os.path.isdir(project_root):
        raise BuildError(f"{path}: project root is not a directory: {project_root}")
    meta, body = split_front_matter(open(path, encoding="utf-8").read(), path)
    doctype = meta.get("doctype")
    if doctype not in DOCTYPES:
        raise BuildError(f"{path}: doctype must be one of {list(DOCTYPES)}, got {doctype!r}")
    validate_meta(meta, doctype, path)
    check_body_alt(body, path)

    stem = os.path.splitext(os.path.basename(path))[0]
    builddir = os.path.join(project_root, ".factory-build", stem)
    os.makedirs(builddir, exist_ok=True)
    open(os.path.join(builddir, "body.md"), "w", encoding="utf-8").write(body)
    wrapper = os.path.join(builddir, "wrapper.typ")
    open(wrapper, "w", encoding="utf-8").write(
        build_wrapper(meta, doctype, project_root)
    )

    out = output or os.path.join(os.path.dirname(os.path.abspath(path)), stem + ".pdf")
    gate(wrapper, out, path, project_root)
    return out


def collect_inputs(inputs):
    files = []
    for p in inputs:
        if os.path.isdir(p):
            files.extend(sorted(glob.glob(os.path.join(p, "*.md"))))
        elif os.path.isfile(p):
            files.append(p)
        else:
            die(f"no such file or directory: {p}")
    if not files:
        die("no .md inputs found")
    return files


def project_root_for(path):
    """Use the input's Git worktree as the owner of assets and build intermediates."""
    directory = os.path.dirname(os.path.abspath(path))
    r = run(["git", "-C", directory, "rev-parse", "--show-toplevel"])
    if r.returncode == 0 and r.stdout.strip():
        return os.path.abspath(r.stdout.strip())
    return WS


def main():
    ap = argparse.ArgumentParser(description="document factory")
    ap.add_argument("inputs", nargs="+", help="Markdown file(s) and/or directories")
    ap.add_argument("-o", "--output", help="output PDF path (single input only)")
    ap.add_argument(
        "--root",
        help=(
            "Typst project root and .factory-build owner "
            "(default: each input's Git worktree, falling back to the colofon repo)."
        ),
    )
    a = ap.parse_args()

    files = collect_inputs(a.inputs)
    if a.output and len(files) > 1:
        die("-o/--output is only valid with a single input file")

    ok, failed = [], []
    for f in files:
        try:
            out = build_one(f, a.output, a.root or project_root_for(f))
            print(f">> built {out} ({os.path.getsize(out)} bytes)")
            ok.append(f)
        except BuildError as e:
            print(str(e), file=sys.stderr)
            failed.append(f)
    if len(files) > 1:
        print(f">> {len(ok)} built, {len(failed)} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

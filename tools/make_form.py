#!/usr/bin/env python3
"""make_form - overlay interactive AcroForm widgets onto a house form.

Forms are authored in Typst with the @local/house `form` template and its
field-block / checkbox / formfield helpers, which draw the visible field and
record each field's geometry as <ff>/<ffr> metadata. This compiles the static
layout, reads that geometry back with `typst query`, and overlays real fillable
AcroForm widgets (text fields, checkboxes) at the same coordinates via PyMuPDF.

    tools/make_form.py path/to/form.typ [-o out.pdf] [--debug]

This is a SEPARATE path from the Markdown factory (tools/make_doc.py): a form is
authored in Typst because fillable fields need explicit placement. The AcroForm
layer is added after compilation by PyMuPDF, so the fillable output is NOT
guaranteed PDF/UA-1 - the static base is compiled UA-1, but the widget layer is
not gate-verified. make_form prints the veraPDF verdict for transparency.

Requires PyMuPDF (pip install --user PyMuPDF).
"""
import argparse
import json
import os
import re
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPST = os.environ.get("TYPST", os.path.expanduser("~/.local/bin/typst"))
VERAPDF = os.environ.get("VERAPDF", os.path.expanduser("~/.local/verapdf/verapdf"))
FONTS = os.path.join(WS, "engine", "fonts")
PACKAGES = os.path.join(WS, "packages")

INK = (0x1B / 255, 0x1B / 255, 0x22 / 255)
ACC = (0x76 / 255, 0x54 / 255, 0xF5 / 255)
MUT = (0x6A / 255, 0x6E / 255, 0x7A / 255)


def die(msg):
    print(f"make_form: {msg}", file=sys.stderr)
    sys.exit(2)


def typst_common():
    return ["--root", WS, "--package-path", PACKAGES,
            "--package-cache-path", PACKAGES, "--font-path", FONTS]


def query(src, sel):
    r = subprocess.run(
        [TYPST, "query", *typst_common(), src, sel, "--field", "value"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"typst query {sel} failed:\n{r.stderr.strip()}")
    return json.loads(r.stdout or "[]")


def main():
    ap = argparse.ArgumentParser(description="overlay AcroForm widgets onto a house form")
    ap.add_argument("input", help="the form .typ file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--debug", action="store_true", help="draw widget borders")
    a = ap.parse_args()
    if not os.path.isfile(a.input):
        die(f"no such file: {a.input}")

    try:
        import fitz
    except ImportError:
        die("PyMuPDF is required (pip install --user PyMuPDF)")

    stem = os.path.splitext(os.path.basename(a.input))[0]
    builddir = os.path.join(WS, ".factory-build", stem)
    os.makedirs(builddir, exist_ok=True)
    static = os.path.join(builddir, "static.pdf")
    out = a.output or os.path.join(os.path.dirname(os.path.abspath(a.input)), stem + ".pdf")

    # 1. compile the static layout (UA-1 base)
    r = subprocess.run(
        [TYPST, "compile", *typst_common(), "--pdf-standard", "ua-1", a.input, static],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"compile failed:\n{r.stderr.strip()}")
    if re.search(r"warning", r.stderr, re.I):
        die(f"compile produced warnings (gate fails):\n{r.stderr.strip()}")

    # 2. read back the field geometry the formfield helper recorded
    ff = query(a.input, "<ff>")
    right_x = {d["k"]: d["xr"] for d in query(a.input, "<ffr>")}
    if not ff:
        die("no form fields found - did the document use field-block / checkbox?")

    # 3. overlay AcroForm widgets at the recorded coordinates
    doc = fitz.open(static)
    n_text = n_check = 0
    for d in ff:
        page = doc[d["pg"] - 1]
        w = fitz.Widget()
        w.field_name = d["k"]
        if d["kind"] == "check":
            x, y = d["x"], d["y"]
            w.rect = fitz.Rect(x, y, x + d["w"], y + d["h"])
            w.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
            w.field_value = False
            w.border_color = ACC if a.debug else MUT
            w.border_width = 1.0 if a.debug else 0.0
            w.fill_color = None
            n_check += 1
        else:
            left, top = d["x"], d["y"]
            right = right_x.get(d["k"], left + 200.0)
            bottom = top + d["h"]
            w.rect = fitz.Rect(left + 4.0, top + 2.5, right - 4.0, bottom - 2.5)
            w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
            w.text_font = "Helv"
            w.text_fontsize = 9 if d.get("ml") else 10
            w.text_color = INK
            w.fill_color = None
            w.border_color = ACC if a.debug else None
            w.border_width = 0.8 if a.debug else 0.0
            if d.get("ml"):
                w.field_flags = fitz.PDF_TX_FIELD_IS_MULTILINE
            n_text += 1
        page.add_widget(w)

    try:
        doc.need_appearances(True)  # let viewers regenerate field appearances
    except Exception:
        pass
    doc.save(out, deflate=True, garbage=4)
    doc.close()
    print(f">> built {out}: {n_text} text fields, {n_check} checkboxes")

    # 4. report (do not gate) the UA-1 status of the fillable output
    if os.path.exists(VERAPDF):
        r = subprocess.run([VERAPDF, "--flavour", "ua1", out], capture_output=True, text=True)
        ok = 'isCompliant="true"' in r.stdout
        print(">> PDF/UA-1 (fillable output): " + (
            "compliant"
            if ok
            else "NOT compliant - expected; the AcroForm widget layer is not gate-verified UA-1"
        ))
    else:
        # Report-only by design, but say so - silence must not read as a pass.
        print(">> PDF/UA-1 (fillable output): NOT CHECKED - veraPDF not found at "
              f"{VERAPDF}")


if __name__ == "__main__":
    main()

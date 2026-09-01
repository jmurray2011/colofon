#!/usr/bin/env python3
"""typ2md - convert a Typst book chapter into book-flavored Markdown.

The render must not change. The bulk (headings, prose, lists, bold, cmd/path,
cross-references, callouts, code) becomes clean Markdown that the bookmd layer
maps back onto the SAME house functions; structural constructs (figure, procedure,
param) and stray inline Typst become <!--raw-typst--> escapes that emit the original
Typst byte-for-byte. Release values become {{vars}} (substituted by make_book).
"""
import re
import sys

VARS = ["version", "rpm", "win-exe", "download-base", "rpm-sha256", "exe-sha256",
        "pg-win-installer"]
# distinctive vars safe to replace as bare idents inside captured Typst (not "rpm")
VARS_SUB = ["rpm-sha256", "exe-sha256", "pg-win-installer", "download-base", "win-exe"]


def match(text, i, op, cl):
    """text[i] == op; return index past the matching cl, honoring \\ escapes and strings."""
    depth = 0
    instr = None
    while i < len(text):
        c = text[i]
        if instr:
            if c == "\\" and instr == '"':  # backtick raw literals don't honor \ escapes
                i += 2
                continue
            if c == instr:
                instr = None
        elif c in '"`':
            instr = c
        elif c == op:
            depth += 1
        elif c == cl:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unmatched " + op)


def subvars(s):
    """Inside captured Typst: #version -> {{version}}; distinctive bare vars -> \"{{var}}\"."""
    s = re.sub(r"#version\b", "{{version}}", s)
    for v in VARS_SUB:
        s = re.sub(r'(?<![\w"\'-])' + re.escape(v) + r"(?![\w-])", '"{{' + v + '}}"', s)
    return s


def conv_arg(arg):
    arg = arg.strip()
    if arg.startswith('"') and arg.endswith('"'):
        return arg[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if arg.startswith("`") and arg.endswith("`"):
        return arg[1:-1]
    if arg in VARS:
        return "{{" + arg + "}}"
    return arg


def raw_block_body(expr):
    out = ""
    for p in re.split(r"\s*\+\s*", expr.strip()):
        p = p.strip()
        if p.startswith('"') and p.endswith('"'):
            out += p[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        elif p in VARS:
            out += "{{" + p + "}}"
        else:
            out += p
    return out


def protect_calls(text, names, store, with_body=False, drop_semi=False):
    """Capture #name(...) [optionally + [body]] [+ <label>] verbatim -> raw-typst placeholder.
    drop_semi: also swallow a `;` glued to the close paren (Typst markup eats it; see inline)."""
    for name in names:
        out, i, head = [], 0, "#" + name + "("
        while True:
            j = text.find(head, i)
            if j < 0:
                out.append(text[i:])
                break
            out.append(text[i:j])
            end = match(text, j + len(head) - 1, "(", ")")
            if with_body and end < len(text) and text[end] == "[":
                end = match(text, end, "[", "]")
            m = re.match(r"\s*<[a-z][a-z0-9-]+>", text[end:])
            if m:
                end += m.end()
            store.append("<!--raw-typst " + subvars(text[j:end].strip()) + "-->")
            out.append(f"\x00{len(store) - 1}\x00")
            if drop_semi and end < len(text) and text[end] == ";":
                end += 1
            i = end
        text = "".join(out)
    return text


PATH_MARK = "\ue000"  # bookmd renders a span starting with this via house.path (unboxed)


def consume_statement(text, j):
    """j at '#'; consume a whole Typst statement (#let/#set/#custom(...)). End at the
    first depth-0 newline (after any brackets), honoring strings."""
    i, depth, instr = j + 1, 0, None
    while i < len(text):
        c = text[i]
        if instr:
            if c == "\\" and instr == '"':  # backtick raw literals don't honor \ escapes
                i += 2
                continue
            if c == instr:
                instr = None
        elif c in '"`':
            instr = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "\n" and depth == 0:
            return i
        i += 1
    return len(text)


# names typ2md handles itself; everything else #ident(...) is a custom construct
KNOWN = {"cmd", "path", "note", "tip", "important", "warning", "caution", "idx",
         "version", "figure", "procedure", "param", "text", "box", "link", "h", "v",
         "smallcap", "emph", "raw", "sym"}


def protect_custom(text, store):
    """#set / #let / custom #ident(...) statements -> raw-typst verbatim."""
    out, i = [], 0
    while i < len(text):
        j = text.find("#", i)
        if j < 0:
            out.append(text[i:])
            break
        m = re.match(r"#([a-zA-Z][\w-]*)", text[j:])
        if m and (m.group(1) in ("set", "let")
                  or (m.group(1) not in KNOWN and re.match(r"\s*[(\[]", text[j + m.end():]))):
            end = consume_statement(text, j)
            out.append(text[i:j])
            store.append("<!--raw-typst " + subvars(text[j:end].strip()) + "-->")
            out.append(f"\x00{len(store) - 1}\x00")
            i = end
        else:
            out.append(text[i:j + 1])
            i = j + 1
    return "".join(out)


def convert_links(text, store):
    """#link("url")[plain text] -> [plain text](url) ; complex links -> raw-typst."""
    out, i, head = [], 0, "#link("
    while True:
        j = text.find(head, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        pe = match(text, j + 5, "(", ")")
        url = text[j + 6:pe - 1].strip()
        body, end = None, pe
        if pe < len(text) and text[pe] == "[":
            end = match(text, pe, "[", "]")
            body = text[pe + 1:end - 1]
        if url.startswith('"') and url.endswith('"') and body is not None and "#" not in body and "[" not in body:
            out.append(f"[{body}]({url[1:-1]})")
        else:
            store.append("<!--raw-typst " + subvars(text[j:end].strip()) + "-->")
            out.append(f"\x00{len(store) - 1}\x00")
        i = end
    return "".join(out)


def protect_brackets(text, name, n, store):
    """Capture #name[..]{n times} verbatim -> raw-typst placeholder."""
    out, i, head = [], 0, "#" + name + "["
    while True:
        j = text.find(head, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        end = j + len("#" + name)
        for _ in range(n):
            while end < len(text) and text[end] in " \n":
                end += 1
            end = match(text, end, "[", "]")
        store.append("<!--raw-typst " + subvars(text[j:end].strip()) + "-->")
        out.append(f"\x00{len(store) - 1}\x00")
        i = end
    return "".join(out)


def _path_span(m):
    a = m.group(1)
    if a.startswith("`"):
        c = a[1:-1]
    elif a.startswith('"'):
        c = a[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    else:
        c = a
    return "`" + PATH_MARK + c + "`"


def inline(text):
    # #cmd(arg) -> `code` (a box; non-breaking, like house.cmd).
    # #path(arg) -> `<U+E000>code` - a marked inline span bookmd routes to house.path
    # (unboxed; wraps at separators). It must be a real code span, NOT an inline
    # <!--raw-typst--> escape: a raw-typst comment mid-paragraph breaks cmarker's code-span
    # pairing, leaking literal backticks onto a later `code` in the same paragraph.
    # A `;` glued to the close paren is swallowed: Typst markup eats `#cmd("x"); y` to "x y".
    text = re.sub(r'#path\(((?:`[^`]*`|"(?:[^"\\]|\\.)*"|[^\s()]+))\);?', _path_span, text)
    text = re.sub(r'#cmd\(((?:`[^`]*`|"(?:[^"\\]|\\.)*"|[A-Za-z0-9_.-]+))\);?',
                  lambda m: "`" + conv_arg(m.group(1)) + "`", text)
    text = re.sub(r"#version\b", "{{version}}", text)
    # idx is invisible metadata; emit it on its own line so an inline raw-typst comment
    # can't break adjacent inline markdown (e.g. **bold**) in the same paragraph
    text = re.sub(r'#idx\(("(?:[^"\\]|\\.)*")\)',
                  lambda m: "<!--raw-typst #idx(" + m.group(1) + ")-->\n", text)
    # protect inline code spans so @ref / bold / italic don't reach inside them
    spans = []
    text = re.sub(r"`[^`]*`", lambda m: (spans.append(m.group(0)), f"\x01{len(spans) - 1}\x01")[1], text)
    text = text.replace("~", " ")  # Typst ~ is a non-breaking space (not inside code, protected above)
    text = re.sub(r"@([a-z][a-z0-9-]+)(?:\[([^\]]*)\])?",
                  lambda m: f"[{m.group(2) or m.group(1)}](#{m.group(1)})", text)
    # Typst *bold* -> **bold** MUST run before emph/_ (which emit *italic*), else this
    # rule double-wraps that italic into bold. `(?:[^*\n]|\n(?!\n))` lets the span wrap a
    # soft line break (a *bold* run that wraps mid-source-line) but stops at a blank line,
    # so it never swallows a paragraph break; a single-line [^*\n] match left such a span as
    # `*..*`, which Markdown renders italic (a styling drift the word-hash gate can't see).
    text = re.sub(r"(?<![A-Za-z0-9])\*((?:[^*\n]|\n(?!\n))+?)\*(?![A-Za-z0-9])", r"**\1**", text)
    # #emph[..] -> *italic*; a `;` glued to the close bracket is swallowed (Typst eats it)
    text = re.sub(r"#emph\[([^\]]*)\];?", r"*\1*", text)
    text = re.sub(r"(?<![A-Za-z0-9_])_((?:[^_\n]|\n(?!\n))+?)_(?![A-Za-z0-9_])", r"*\1*", text)
    text = re.sub("\x01(\\d+)\x01", lambda m: spans[int(m.group(1))], text)
    return text


def convert(text):
    text = re.sub(
        r'\A(?:#import\s+"[^"]+"\s*:\s*\([^)]*\)\s*\n|#import\s+"[^"]+"(?::[^\n]*)?\s*\n)+',
        "", text)
    store = []

    def ph():
        return f"\x00{len(store) - 1}\x00"

    # code fences: keep verbatim
    text = re.sub(r"```[a-z]*\n.*?\n```", lambda m: (store.append(m.group(0)), ph())[1],
                  text, flags=re.DOTALL)

    # custom #let/#set/#ident(...) statements (e.g. the glossary's g()) -> raw-typst
    text = protect_custom(text, store)

    # structural / stray-Typst constructs -> raw-typst verbatim (wrappers first, so a
    # construct like #text(size:8pt)[#raw(rpm-sha256)] is captured whole)
    text = protect_calls(text, ["figure"], store)
    text = protect_brackets(text, "procedure", 2, store)
    text = protect_calls(text, ["param", "text", "h", "v"], store, with_body=True)
    text = protect_brackets(text, "box", 1, store)
    text = protect_brackets(text, "smallcap", 1, store)
    text = convert_links(text, store)

    # #raw(...) AFTER the wrappers: block -> code fence ; inline -> raw-typst
    out, i = [], 0
    while True:
        j = text.find("#raw(", i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        end = match(text, j + 4, "(", ")")
        inner = text[j + 5:end - 1]
        lm = re.search(r',\s*lang:\s*"([a-z]+)"', inner)
        if lm and "block: true" in inner:
            store.append("```" + lm.group(1) + "\n"
                         + raw_block_body(inner[:lm.start()]) + "\n```")
        else:
            store.append("<!--raw-typst " + subvars(text[j:end].strip()) + "-->")
        out.append(ph())
        i = end
    text = "".join(out)

    text = re.sub(r"#sym\.[A-Za-z.]+",
                  lambda m: (store.append("<!--raw-typst " + m.group(0) + "-->"), ph())[1], text)

    # callouts -> > [!type] admonition (body converted by the global inline pass)
    KIND = ("note", "tip", "important", "warning", "caution")
    out, i = [], 0
    while True:
        m = re.compile(r"#(" + "|".join(KIND) + r")\[").search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        end = match(text, m.end() - 1, "[", "]")
        body = text[m.end():end - 1].strip("\n")
        body = re.sub(r"\n{2,}", "\n>\n", body)  # blank lines -> blockquote separators
        block = f"> [!{m.group(1)}]\n" + "\n".join(
            "> " + ln if ln.strip() else ">" for ln in body.split("\n"))
        out.append(block)
        i = end
    text = "".join(out)

    # headings: == / === / ==== Title <label>
    text = re.sub(r"(?m)^(=+) +(.+?)(?: +<([a-z][a-z0-9-]+)>)? *$",
                  lambda m: "#" * (len(m.group(1)) - 1) + " " + m.group(2).rstrip()
                  + (f" {{#{m.group(3)}}}" if m.group(3) else ""), text)

    # standalone Typst enumerated lists (+ item) -> Markdown ordered (cmarker reads + as a bullet)
    text = re.sub(r"(?m)^(\s*)\+ ", r"\g<1>1. ", text)

    # Typst end-of-line `\` (linebreak) -> Markdown hard break (two trailing spaces)
    text = re.sub(r"(?m)[ \t]*\\$", "  ", text)

    text = inline(text)
    for _ in range(30):  # loop: a protected construct can hold another's placeholder
        if "\x00" not in text:
            break
        text = re.sub("\x00(\\d+)\x00", lambda m: store[int(m.group(1))], text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as source:
        sys.stdout.write(convert(source.read()))

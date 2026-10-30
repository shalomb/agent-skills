"""A small Markdown subset for bundle sections. Raw HTML is always escaped.

Supported: headings, paragraphs, bullet and numbered lists, fenced code,
tables, blockquotes, and inline code, bold, italic and links. Fences tagged
`mermaid` go to the `render_diagram` hook when one is given.
"""
import html
import re

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
UNSAFE_SCHEME = re.compile(r"^\s*(javascript|data|vbscript):", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET = re.compile(r"^\s*[-*+]\s+(.*)$")
NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


def render_markdown(text, heading_offset=0, rewrite_link=None, render_diagram=None):
    rewrite = rewrite_link or (lambda target: target)

    def inline(raw):
        codes = []

        def stash(m):
            codes.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
            return f"\x00{len(codes) - 1}\x00"

        text_ = INLINE_CODE.sub(stash, raw)
        text_ = html.escape(text_, quote=False)
        text_ = LINK.sub(lambda m: _link(m, rewrite), text_)
        text_ = BOLD.sub(r"<strong>\1</strong>", text_)
        text_ = ITALIC.sub(r"<em>\1</em>", text_)
        return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text_)

    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.lstrip().startswith("```"):
            lang = line.strip()[3:].strip()
            body, i = _until_fence(lines, i + 1)
            code = "\n".join(body) + "\n" if body else ""
            if lang == "mermaid" and render_diagram:
                out.append(render_diagram("\n".join(body)))
            else:
                cls = f' class="language-{html.escape(lang)}"' if lang else ""
                out.append(f"<pre><code{cls}>{html.escape(code, quote=False)}</code></pre>")
        elif heading := HEADING.match(line):
            level = min(len(heading.group(1)) + heading_offset, 6)
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
        elif BULLET.match(line) or NUMBERED.match(line):
            pattern, tag = (BULLET, "ul") if BULLET.match(line) else (NUMBERED, "ol")
            items = []
            while i < len(lines) and (item := pattern.match(lines[i])):
                items.append(f"<li>{inline(item.group(1))}</li>")
                i += 1
            out.append(f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>")
        elif line.lstrip().startswith(">"):
            quoted = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quoted.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>\n" + render_markdown(
                "\n".join(quoted), 0, rewrite_link, render_diagram).rstrip("\n") + "\n</blockquote>")
        elif "|" in line and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]) and "-" in lines[i + 1]:
            header = _cells(line)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            head = "".join(f"<th>{inline(c)}</th>" for c in header)
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not _starts_block(lines, i):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(chr(10).join(para))}</p>")
    return "\n".join(out) + "\n" if out else ""


def _link(match, rewrite):
    label, target = match.group(1), html.unescape(match.group(2))
    if UNSAFE_SCHEME.match(target):
        return label
    return f'<a href="{html.escape(rewrite(target))}">{label}</a>'


def _until_fence(lines, i):
    body = []
    while i < len(lines) and not lines[i].lstrip().startswith("```"):
        body.append(lines[i])
        i += 1
    return body, i + 1


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _starts_block(lines, i):
    line = lines[i]
    return bool(
        line.lstrip().startswith(("```", ">")) or HEADING.match(line)
        or BULLET.match(line) or NUMBERED.match(line)
        or ("|" in line and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]) and "-" in lines[i + 1]))

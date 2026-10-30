"""Source views: one page per cited file, with an id L<n> on each line."""
import html

from .icons import icon
from .page import page


def render_source_view(path, text, report_href="report.html"):
    """`text` is the file content, or None when the file is not available."""
    head = (f'<div class="wrap"><header class="masthead">'
            f'<p class="eyebrow">{icon("code")} Source view</p>'
            f'<h1 id="source-path" data-path="{html.escape(path)}">{html.escape(path)}</h1>'
            f'<p><a href="{html.escape(report_href)}">{icon("arrow_forward")} Back to the report</a></p>'
            f'</header><article>')
    if text is None:
        body = '<p class="notice">The source of this file is not available.</p>'
    elif "\x00" in text:
        body = '<p class="notice">This is a binary file; it has no lines to show.</p>'
    else:
        rows = "".join(
            f'<tr id="L{n}"><th scope="row"><a href="#L{n}">{n}</a></th><td>{html.escape(line, quote=False)}</td></tr>'
            for n, line in enumerate(_lines(text), start=1))
        body = f'<table class="source"><tbody>{rows}</tbody></table>'
    return page(path, f"{head}{body}</article></div>")


def _lines(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return lines

"""Source views: one page per cited file, with an id L<n> on each line."""
import html
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename

from .icons import icon
from .page import inline_script, page

COPY_SCRIPT = """function copyRawCode() {
  var el = document.getElementById('raw-code');
  if (!el) return;
  var code = el.value;
  var btn = document.getElementById('copy-raw-btn');
  var label = btn ? btn.querySelector('.copy-label') : null;
  function feedback() {
    if (btn) btn.classList.add('copied');
    if (label) label.textContent = 'Copied!';
    setTimeout(function() {
      if (btn) btn.classList.remove('copied');
      if (label) label.textContent = 'Copy raw code';
    }, 2000);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(code).then(feedback, function() {
      fallbackCopy(el, feedback);
    });
  } else {
    fallbackCopy(el, feedback);
  }
}
function fallbackCopy(el, cb) {
  el.select();
  try {
    var ok = document.execCommand('copy');
    if (ok && cb) cb();
  } catch (e) {}
}"""


def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _lines(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return lines


def _get_lexer(path, text):
    try:
        return get_lexer_for_filename(Path(path).name, text, default=TextLexer())
    except Exception:
        return TextLexer()


def _highlight_lines(text, lexer):
    raw_lines = _lines(text)
    norm_text = "\n".join(raw_lines)
    try:
        formatter = HtmlFormatter(nowrap=True)
        highlighted = highlight(norm_text, lexer, formatter)
        lines = highlighted.split("\n")
        if len(lines) > len(raw_lines) and lines[-1] == "":
            lines.pop()
        if len(lines) == len(raw_lines):
            return lines
    except Exception:
        return [html.escape(line, quote=False) for line in raw_lines]
    return [html.escape(line, quote=False) for line in raw_lines]


def render_source_view(path, text, report_href="report.html", remote_info=None):
    """`text` is the file content, or None when the file is not available."""
    remote_badge = ""
    if remote_info:
        r_url = None
        if hasattr(remote_info, "file_link"):
            r_url = remote_info.file_link(path)
        elif callable(remote_info):
            r_url = remote_info(path)
        if isinstance(r_url, str):
            host = getattr(remote_info, "host", "github")
            if isinstance(remote_info, dict):
                host = remote_info.get("host", "github")
            host_label = "GitLab" if str(host).lower() == "gitlab" else "GitHub"
            remote_badge = (
                f' <a class="remote-badge" href="{html.escape(r_url)}" '
                f'target="_blank" rel="noopener noreferrer">View on {host_label} ↗</a>'
            )

    back_btn = f'<a class="source-btn back-btn" href="{html.escape(report_href)}">← Back to report</a>'

    if text is None:
        body = '<p class="notice">The source of this file is not available.</p>'
        head = (
            f'<div class="wrap source-wrap"><header class="masthead source-masthead">'
            f'<div class="source-header-top">'
            f'<p class="eyebrow">{icon("code")} Source view</p>'
            f'<div class="source-nav">{back_btn}{remote_badge}</div>'
            f'</div>'
            f'<div class="source-title-row">'
            f'<h1 id="source-path" data-path="{html.escape(path)}">{html.escape(path)}</h1>'
            f'</div>'
            f'</header><article>'
        )
        return page(path, f"{head}{body}</article></div>")

    if "\x00" in text:
        body = '<p class="notice">This is a binary file; it has no lines to show.</p>'
        head = (
            f'<div class="wrap source-wrap"><header class="masthead source-masthead">'
            f'<div class="source-header-top">'
            f'<p class="eyebrow">{icon("code")} Source view</p>'
            f'<div class="source-nav">{back_btn}{remote_badge}</div>'
            f'</div>'
            f'<div class="source-title-row">'
            f'<h1 id="source-path" data-path="{html.escape(path)}">{html.escape(path)}</h1>'
            f'</div>'
            f'</header><article>'
        )
        return page(path, f"{head}{body}</article></div>")

    lexer = _get_lexer(path, text)
    lang_name = getattr(lexer, "name", "Text")
    lang_tag = "Text" if lang_name == "Text only" else lang_name

    highlighted_lines = _highlight_lines(text, lexer)
    line_count = len(highlighted_lines)
    line_label = f"{line_count} line" if line_count == 1 else f"{line_count} lines"
    size_bytes = len(text.encode("utf-8"))
    stats_str = f"{line_label} · {_format_size(size_bytes)}"

    copy_btn = (
        f'<button type="button" class="source-btn copy-btn" id="copy-raw-btn" onclick="copyRawCode()">'
        f'<svg class="icon copy-icon" viewBox="0 -960 960 960" width="16" height="16" aria-hidden="true" fill="currentColor">'
        f'<path d="M360-240q-33 0-56.5-23.5T280-320v-480q0-33 23.5-56.5T360-880h360q33 0 56.5 23.5T800-800v480q0 33-23.5 56.5T720-240H360Zm0-80h360v-480H360v480ZM200-80q-33 0-56.5-23.5T120-160v-560h80v560h440v80H200Zm160-240v-480 480Z"/>'
        f'</svg>'
        f'<span class="copy-label">Copy raw code</span>'
        f'</button>'
        f'<textarea id="raw-code" class="sr-only" aria-hidden="true" tabindex="-1" readonly>{html.escape(text)}</textarea>'
    )

    head = (
        f'<div class="wrap source-wrap"><header class="masthead source-masthead">'
        f'<div class="source-header-top">'
        f'<p class="eyebrow">{icon("code")} Source view</p>'
        f'<div class="source-nav">{back_btn}{remote_badge}</div>'
        f'</div>'
        f'<div class="source-title-row">'
        f'<h1 id="source-path" data-path="{html.escape(path)}">{html.escape(path)}</h1>'
        f'<span class="lang-badge">{html.escape(lang_tag)}</span>'
        f'</div>'
        f'<div class="source-meta">'
        f'<span class="source-stats">{html.escape(stats_str)}</span>'
        f'{copy_btn}'
        f'</div>'
        f'</header><article>'
    )

    rows = "".join(
        f'<tr id="L{n}"><th scope="row"><a href="#L{n}">{n}</a></th><td class="code">{line}</td></tr>'
        for n, line in enumerate(highlighted_lines, start=1)
    )
    body = f'<div class="source-table-wrap"><table class="source"><tbody>{rows}</tbody></table></div>'
    scripts = f"<script>{inline_script(COPY_SCRIPT)}</script>"
    return page(path, f"{head}{body}</article></div>", scripts=scripts)


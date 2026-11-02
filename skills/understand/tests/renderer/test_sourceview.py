"""Unit tests for source views: one id L<n> on each line (spec unit 5)."""
from pages_helpers import ids_of
from understand_render.sourceview import render_source_view


def view(text, path="src/app.ts", **kw):
    return render_source_view(path, text, **kw)


def test_each_line_has_an_id_and_a_link_to_itself():
    html = view("a\nb\nc\n")
    assert ids_of(html, prefix="L") == ["L1", "L2", "L3"]
    assert '<a href="#L2">2</a>' in html


def test_final_newline_does_not_add_a_line():
    assert ids_of(view("a\nb\n"), prefix="L") == ["L1", "L2"]
    assert ids_of(view("a\nb"), prefix="L") == ["L1", "L2"]


def test_empty_file_has_one_empty_line():
    assert ids_of(view(""), prefix="L") == ["L1"]


def test_blank_lines_keep_their_ids():
    assert ids_of(view("a\n\n\nb\n"), prefix="L") == ["L1", "L2", "L3", "L4"]


def test_code_is_escaped():
    html = view("if (a < b && c > d) { '<script>' }\n")
    assert "'<script>'" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;" in html and "&amp;&amp;" in html and "&gt;" in html
    assert '<td class="code">' in html


def test_windows_line_endings_do_not_double_count_lines():
    assert ids_of(view("a\r\nb\r\n"), prefix="L") == ["L1", "L2"]


def test_view_names_its_path_and_links_back_to_the_report():
    html = view("x\n", path="src/deep/app.ts", report_href="../../../report.html")
    assert 'id="source-path"' in html and 'data-path="src/deep/app.ts"' in html
    assert 'href="../../../report.html"' in html


def test_missing_source_shows_a_notice_and_no_line_ids():
    html = render_source_view("src/gone.ts", None)
    assert "not available" in html and ids_of(html, prefix="L") == []
    assert 'data-path="src/gone.ts"' in html


def test_binary_source_shows_a_notice_and_no_line_ids():
    html = render_source_view("img.png", "PNG\x00\x01")
    assert "binary" in html and ids_of(html, prefix="L") == []


def test_syntax_highlighting_python_snippet():
    code = 'def greet(name: str):\n    # Return greeting\n    return f"Hello {name}"\n'
    html = view(code, path="src/greet.py")
    assert '<span class="k">def</span>' in html
    assert '<span class="nf">greet</span>' in html
    assert '<span class="c1"># Return greeting</span>' in html
    assert '<span class="k">return</span>' in html
    assert '<span class="lang-badge">Python</span>' in html


def test_header_bar_stats_and_copy_button():
    code = "line1\nline2\nline3\n"
    html = view(code, path="src/data.txt")
    assert '<span class="source-stats">3 lines · 18 B</span>' in html
    assert 'id="copy-raw-btn"' in html
    assert "Copy raw code" in html
    assert 'id="raw-code"' in html
    assert "copyRawCode()" in html


def test_header_back_button_and_remote_badge():
    class FakeRemote:
        host = "github"

        def file_link(self, path):
            return f"https://github.com/my-org/my-repo/blob/main/{path}"

    html = view("x = 1\n", path="src/app.py", report_href="../report.html", remote_info=FakeRemote())
    assert "← Back to report" in html
    assert 'href="../report.html"' in html
    assert "View on GitHub ↗" in html
    assert 'href="https://github.com/my-org/my-repo/blob/main/src/app.py"' in html


def test_unknown_file_type_fallback_to_text_lexer():
    html = view("hello <world>\n", path="mystery.unknown123")
    assert '<span class="lang-badge">Text</span>' in html
    assert "hello &lt;world&gt;" in html
    assert ids_of(html, prefix="L") == ["L1"]


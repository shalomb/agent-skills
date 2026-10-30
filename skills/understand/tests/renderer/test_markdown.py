"""Unit tests for the stdlib Markdown subset that sections may use."""
from understand_render.markdown import render_markdown


def md(text, **kw):
    return render_markdown(text, **kw)


def test_heading_levels_are_shifted_below_the_section_title():
    html = md("# Title\n\n## Sub\n", heading_offset=1)
    assert "<h2>Title</h2>" in html and "<h3>Sub</h3>" in html


def test_paragraph_joins_wrapped_lines():
    assert md("one\ntwo\n\nthree\n") == "<p>one\ntwo</p>\n<p>three</p>\n"


def test_inline_code_bold_and_italic():
    assert md("a `x<y` **b** *c*\n") == "<p>a <code>x&lt;y</code> <strong>b</strong> <em>c</em></p>\n"


def test_raw_html_in_markdown_is_escaped():
    html = md("<script>alert(1)</script>\n")
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_bullet_and_numbered_lists():
    assert md("- a\n- b\n") == "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n"
    assert md("1. a\n2. b\n") == "<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n"


def test_fenced_code_block_is_escaped_and_keeps_language():
    html = md("```python\nif a < b:\n    pass\n```\n")
    assert '<pre><code class="language-python">if a &lt; b:\n    pass\n</code></pre>' in html


def test_table_with_header_row():
    html = md("| A | B |\n| :-- | --: |\n| 1 | 2 |\n")
    assert "<th>A</th>" in html and "<td>2</td>" in html
    assert html.startswith('<div class="tw"><table>')


def test_blockquote():
    assert md("> quoted\n") == "<blockquote>\n<p>quoted</p>\n</blockquote>\n"


def test_link_target_goes_through_the_rewriter():
    seen = []
    html = md("[x](src/a.ts#L3)\n", rewrite_link=lambda t: seen.append(t) or "R/" + t)
    assert seen == ["src/a.ts#L3"]
    assert '<a href="R/src/a.ts#L3">x</a>' in html


def test_link_text_is_escaped():
    assert "&lt;b&gt;" in md("[<b>](x)\n")


def test_mermaid_fence_goes_to_the_diagram_hook_not_to_a_code_block():
    html = md("```mermaid\nflowchart LR\n A-->B\n```\n", render_diagram=lambda src: f"<figure>{len(src)}</figure>")
    assert html == "<figure>19</figure>\n"


def test_mermaid_fence_without_hook_is_a_plain_code_block():
    assert 'class="language-mermaid"' in md("```mermaid\nA-->B\n```\n")


def test_javascript_links_are_neutralised():
    assert "javascript:" not in md("[x](javascript:alert(1))\n")

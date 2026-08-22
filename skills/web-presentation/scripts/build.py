#!/usr/bin/env python3
"""Render a Markdown document to a self-contained, themed HTML page or slide deck.

Both modes emit a single file with no external assets, so the output can be
attached to email, dropped in Teams, or opened offline.
"""
import argparse
import datetime
import html
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

FLAG_WORDS = "GAP|CHECK|TODO|NOTE|RISK|OPEN"


def die(msg):
    sys.exit(f"error: {msg}")


def run_pandoc(md):
    """Markdown -> HTML fragment.

    --wrap=none is REQUIRED. Pandoc otherwise wraps output at 72 columns, which
    splits long opening tags (`<h2\\nid="...">`) and inline `<strong>` labels
    across lines and silently defeats every regex below.
    """
    try:
        proc = subprocess.run(
            ["pandoc", "-f", "gfm", "-t", "html5",
             "--syntax-highlighting=none", "--wrap=none"],
            input=md, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        die("pandoc not found on PATH")
    except subprocess.CalledProcessError as exc:
        die(f"pandoc failed: {exc.stderr.strip()}")
    return proc.stdout


def strip_frontmatter(md):
    return re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)


def take_title(body, override):
    """Pull the H1 out of the body; the templates render their own masthead."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S)
    if m:
        body = body[m.end():]
        found = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.group(1))).strip()
    else:
        found = None
    return body, (override or found or "Untitled")


def meta_block(body):
    """Turn a leading `**Label:** value` paragraph into a definition list.

    Labels are discovered, not hardcoded: any run of `<strong>Label:</strong>`
    pairs in the first paragraph qualifies. Adding a new preamble field to the
    source therefore needs no change here.
    """
    first = re.search(r"<p>(<strong>[^<]{2,48}:</strong>.*?)</p>", body, flags=re.S)
    if not first:
        return body
    inner = first.group(1)
    parts = re.split(r"<strong>([^<:]{2,48}):</strong>", inner)
    if len(parts) < 3:
        return body
    rows = []
    for i in range(1, len(parts) - 1, 2):
        key = parts[i]
        val = re.sub(r"\s+", " ", parts[i + 1]).strip()
        val = re.sub(r"^(<br\s*/?>)+|(<br\s*/?>)+$", "", val).strip()
        rows.append(f'<div class="meta-row"><dt>{html.escape(key)}</dt><dd>{val}</dd></div>')
    return body[:first.start()] + f'<dl class="meta">{"".join(rows)}</dl>' + body[first.end():]


def lede(body):
    return re.sub(r"<p>(<strong>The ask in one sentence:</strong>.*?)</p>",
                  r'<p class="lede">\1</p>', body, count=1, flags=re.S)


def flags(body):
    """`[GAP — ...]` markers become inline chips; standalone ones become callouts."""
    body = re.sub(
        rf"\[({FLAG_WORDS})\b([^\]]*)\]",
        lambda m: (f'<span class="flag"><span class="flag-tag">{m.group(1)}</span>'
                   f'{html.escape(m.group(2).lstrip("—- ").strip())}</span>'),
        body)
    return re.sub(r"<p>(<strong>)?(<span class=\"flag\">.*?</span>)(</strong>)?</p>",
                  r'<aside class="callout">\2</aside>', body, flags=re.S)


def wrap_tables(body):
    return body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")


def split_headings(body):
    r"""Split `<h2>3. Title</h2>` into a number chip and title span.

    Note `<h2\s+id=` rather than `<h2 id=` — see run_pandoc.
    """
    def repl(m):
        hid, text = m.group(1), m.group(2)
        flat = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", text)).strip()
        num = re.match(r"^(\d+)\.\s*(.*)$", flat)
        if num:
            return (f'<h2 id="{hid}"><span class="num">{num.group(1)}</span>'
                    f'<span class="htext">{html.escape(num.group(2))}</span></h2>')
        return f'<h2 id="{hid}" class="h2-plain"><span class="htext">{html.escape(flat)}</span></h2>'
    return re.sub(r'<h2\s+id="([^"]+)">(.*?)</h2>', repl, body, flags=re.S)


def build_toc(body):
    items = []
    for hid, inner in re.findall(r'<h2\s+id="([^"]+)"[^>]*>(.*?)</h2>', body, flags=re.S):
        n = re.search(r'<span class="num">(\d+)</span>', inner)
        t = re.search(r'<span class="htext">(.*?)</span>', inner, flags=re.S)
        label = html.unescape(re.sub("<[^>]+>", "", t.group(1))) if t else hid
        items.append(f'<li><a href="#{hid}"><span class="tn">{n.group(1) if n else "—"}</span>'
                     f'<span>{html.escape(label)}</span></a></li>')
    return "\n".join(items)


def density(chunk):
    n = len(re.sub("<[^>]+>", "", chunk))
    return 2 if n > 2600 else 1 if n > 1500 else 0


def make_slides(body):
    """One slide per H2; `---` inside a section starts a continuation slide."""
    pieces = re.split(r'(<h2\s+id="[^"]+"[^>]*>.*?</h2>)', body, flags=re.S)
    lead, slides = re.sub(r"<hr\s*/?>", "", pieces[0]), []
    for i in range(1, len(pieces), 2):
        head, content = pieces[i], pieces[i + 1] if i + 1 < len(pieces) else ""
        hid = re.search(r'id="([^"]+)"', head).group(1)
        num = re.search(r'<span class="num">(\d+)</span>', head)
        txt = re.search(r'<span class="htext">(.*?)</span>', head, flags=re.S)
        title = txt.group(1) if txt else hid
        for j, part in enumerate(re.split(r"<hr\s*/?>", content)):
            if not re.sub("<[^>]+>", "", part).strip() and j:
                continue
            eyebrow = (f'<span class="num">{num.group(1)}</span>' if num else "")
            suffix = " <span class=\"num\">cont.</span>" if j else ""
            slides.append(
                f'<section class="slide" id="{hid}{"" if not j else f"-{j}"}" data-dense="{density(part)}">'
                f'<div class="slide-head">{eyebrow}{suffix}<h2>{title}</h2></div>'
                f'<div class="slide-inner">{part}</div></section>')
    return lead, slides


DECK_JS = """
(function(){
  var deck=document.querySelector('.deck'), slides=[].slice.call(document.querySelectorAll('.slide'));
  var bar=document.querySelector('.progress'), cnt=document.querySelector('.counter');
  var hint=document.querySelector('.hint');
  function current(){
    var top=deck.scrollTop, best=0;
    slides.forEach(function(s,i){ if(s.offsetTop<=top+8) best=i; });
    return best;
  }
  function paint(){
    var i=current();
    bar.style.width=((i+1)/slides.length*100)+'%';
    cnt.textContent=(i+1)+' / '+slides.length;
  }
  function go(i){
    i=Math.max(0,Math.min(slides.length-1,i));
    deck.scrollTo({top:slides[i].offsetTop,behavior:'smooth'});
  }
  deck.addEventListener('scroll',paint,{passive:true});
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    var k=e.key;
    if(k==='ArrowRight'||k==='PageDown'||k===' '||k==='n'||k==='j'){e.preventDefault();go(current()+1);}
    else if(k==='ArrowLeft'||k==='PageUp'||k==='p'||k==='k'){e.preventDefault();go(current()-1);}
    else if(k==='Home'){e.preventDefault();go(0);}
    else if(k==='End'){e.preventDefault();go(slides.length-1);}
    else if(k==='f'){(document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen());}
    if(hint) hint.classList.add('gone');
  });
  if(location.hash){var t=document.querySelector(location.hash); if(t) deck.scrollTop=t.offsetTop;}
  paint();
  setTimeout(function(){ if(hint) hint.classList.add('gone'); },10);
})();
"""


def render_doc(title, eyebrow, built, meta_and_body, toc_html, css):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">{html.escape(eyebrow)}</p>
    <h1>{html.escape(title)}</h1>
    <p class="built">Working document &middot; generated {built}</p>
  </header>
  <nav class="side" aria-label="Contents">
    <h2>Contents</h2>
    <ol>{toc_html}</ol>
  </nav>
  <article>
{meta_and_body}
  </article>
</div>
</body>
</html>
"""


def render_deck(title, eyebrow, built, lead, slides, css, deck_css):
    title_slide = (
        f'<section class="slide slide-title" id="title" data-dense="0">'
        f'<div class="slide-inner">'
        f'<p class="eyebrow">{html.escape(eyebrow)}</p>'
        f'<h1>{html.escape(title)}</h1>{lead}'
        f'<p class="built">generated {built}</p></div></section>')
    body = "\n".join([title_slide] + slides)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{css}
{deck_css}</style>
</head>
<body>
<div class="progress"></div>
<div class="counter"></div>
<p class="hint">&larr; &rarr; to navigate &middot; f for fullscreen</p>
<main class="deck">
{body}
</main>
<script>{DECK_JS}</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=pathlib.Path, help="Markdown file to render")
    ap.add_argument("-m", "--mode", choices=("doc", "deck"), default="doc",
                    help="doc: long-form page with sidebar TOC. deck: one slide per H2")
    ap.add_argument("-o", "--out", type=pathlib.Path,
                    help="output path (default: ~/Downloads/<slug>[-deck].html)")
    ap.add_argument("-t", "--title", help="override the H1")
    ap.add_argument("-e", "--eyebrow", default="Discussion Notes",
                    help="small caps line above the title")
    ap.add_argument("--theme", type=pathlib.Path, default=ASSETS / "theme.css",
                    help="stylesheet to inline instead of the bundled theme")
    args = ap.parse_args()

    if not args.source.is_file():
        die(f"no such file: {args.source}")
    css = args.theme.read_text(encoding="utf-8")

    body = run_pandoc(strip_frontmatter(args.source.read_text(encoding="utf-8")))
    body, title = take_title(body, args.title)
    body = split_headings(flags(wrap_tables(lede(meta_block(body)))))
    built = datetime.date.today().strftime("%-d %B %Y")

    if args.mode == "doc":
        out = render_doc(title, args.eyebrow, built,
                         re.sub(r"<hr\s*/?>", "", body), build_toc(body), css)
        default = f"{args.source.stem.lower()}.html"
    else:
        lead, slides = make_slides(body)
        if not slides:
            die("no H2 headings found — deck mode needs `## ` sections")
        out = render_deck(title, args.eyebrow, built, lead, slides, css,
                          (ASSETS / "deck.css").read_text(encoding="utf-8"))
        default = f"{args.source.stem.lower()}-deck.html"

    dest = args.out or (pathlib.Path.home() / "Downloads" / default)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes)")


if __name__ == "__main__":
    main()

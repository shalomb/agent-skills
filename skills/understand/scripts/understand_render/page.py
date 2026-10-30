"""The shared HTML shell. Every page inlines its CSS; nothing loads by address."""
import html
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[2] / "assets"


def inline_css():
    tokens = (ASSETS / "tokens.css").read_text(encoding="utf-8")
    components = (ASSETS / "report.css").read_text(encoding="utf-8")
    return f"{tokens}\n{components}"


def inline_script(code):
    """Script text that cannot close its own tag."""
    return code.replace("</script", "<\\/script")


def page(title, body, scripts=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{inline_css()}</style>
</head>
<body>
{body}
{scripts}
</body>
</html>
"""

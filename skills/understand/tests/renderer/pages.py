"""Read rendered pages the way a test needs: ids, links, script sources, sections."""
from html.parser import HTMLParser
from pathlib import Path


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.script_srcs = []
        self.link_hrefs = []
        self.section_ids = []
        self.attrs_by_id = {}
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
            self.attrs_by_id[a["id"]] = {"tag": tag, **a}
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "script" and "src" in a:
            self.script_srcs.append(a["src"])
        if tag == "link" and "href" in a:
            self.link_hrefs.append(a["href"])
        if tag == "section" and "report-section" in (a.get("class") or "").split():
            self.section_ids.append(a.get("id"))

    @classmethod
    def read(cls, path):
        return cls(Path(path).read_text(encoding="utf-8"))

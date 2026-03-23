import re
import unicodedata
import html2text
from bs4 import BeautifulSoup
from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from .models import TeamsMessage, ImageMetadata
except ImportError:
    from models import TeamsMessage, ImageMetadata

class TeamsParser:
    @staticmethod
    def clean_text(text: str) -> str:
        """Deep clean junk characters, icons, and non-printable graphemes."""
        if not text: return ""
        text = "".join(c for c in text if not (0xe000 <= ord(c) <= 0xf8ff))
        text = "".join(c for c in text if unicodedata.category(c)[0] not in ['C', 'M'] or c.isspace())
        return text.strip()

    @staticmethod
    def html_to_markdown(html: str) -> str:
        """Convert Teams HTML to clean Markdown."""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        return h.handle(html).strip()

    @staticmethod
    def extract_images(html: str) -> List[ImageMetadata]:
        """Extract image metadata from Teams HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith('data:'):
                images.append(ImageMetadata(alt=img.get('alt'), src=src))
        return images

    @staticmethod
    def parse_message(
        body_html: str,
        author: str = "Unknown",
        timestamp: Optional[str] = None
    ) -> TeamsMessage:
        """Parse a single Teams message block."""
        markdown = TeamsParser.html_to_markdown(body_html)
        images = TeamsParser.extract_images(body_html)
        
        return TeamsMessage(
            author=TeamsParser.clean_text(author),
            body=TeamsParser.clean_text(markdown),
            timestamp=TeamsParser.clean_text(timestamp) if timestamp else None,
            images=images
        )

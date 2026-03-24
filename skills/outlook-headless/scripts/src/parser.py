import re
import unicodedata
from typing import List, Optional, Tuple
import html2text
from bs4 import BeautifulSoup
try:
    from .models import EmailMessage, ImageMetadata
except ImportError:
    from models import EmailMessage, ImageMetadata

class OutlookParser:
    @staticmethod
    def clean_text(text: str) -> str:
        """Deep clean junk characters, icons, and non-printable graphemes."""
        if not text:
            return ""
        # Remove Private Use Area (icons)
        text = "".join(c for c in text if not (0xe000 <= ord(c) <= 0xf8ff))
        # Remove non-printable control/format/mark characters (like \u034f)
        text = "".join(c for c in text if unicodedata.category(c)[0] not in ['C', 'M'] or c.isspace())
        return text.strip()

    @staticmethod
    def html_to_markdown(html: str) -> str:
        """Convert email HTML to clean Markdown."""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0 # No wrapping
        return h.handle(html).strip()

    @staticmethod
    def extract_images(html: str) -> List[ImageMetadata]:
        """Extract all image metadata from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt')
            title = img.get('title')
            width = img.get('width') or img.get('style', '') # Try style if attr missing
            height = img.get('height')
            
            # Ignore tiny tracker pixels or spacers
            if src and not src.startswith('data:image/gif'):
                images.append(ImageMetadata(
                    alt=alt, 
                    src=src, 
                    title=title,
                    width=str(width) if width else None,
                    height=str(height) if height else None
                ))
        return images

    @staticmethod
    def parse_list_item(item_text: str, current_count: int = 0, is_read: Optional[bool] = None) -> Optional[EmailMessage]:
        if not item_text.strip():
            return None
        
        raw_lines = [l.strip() for l in item_text.split("\n") if l.strip()]
        all_lines = [OutlookParser.clean_text(l) for l in raw_lines if OutlookParser.clean_text(l)]
        
        # Skip initials bubbles
        start_idx = 0
        while start_idx < len(all_lines) and len(all_lines[start_idx]) <= 2:
            start_idx += 1
            
        useful_lines = all_lines[start_idx:]
        if not useful_lines:
            return None
        
        list_sender = useful_lines[0]
        list_subject = useful_lines[1] if len(useful_lines) > 1 else "No Subject"
        
        timestamp = None
        to_field = []
        snippet_parts = []
        
        ts_patterns = [
            r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}:\d{2}\s+(AM|PM)$",
            r"^\d{1,2}:\d{2}\s+(AM|PM)$",
            r"^\d{1,2}/\d{1,2}(/\d{2,4})?$",
            r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}/\d{1,2}$",
            r"^(Yesterday|Today)$"
        ]
        
        for l in useful_lines[2:]:
            is_ts = any(re.match(p, l, re.IGNORECASE) for p in ts_patterns)
            if not is_ts and (":" in l and ("AM" in l or "PM" in l)):
                is_ts = True
            
            if is_ts and not timestamp:
                timestamp = l
                continue
                
            if l.lower().startswith("to:"):
                to_field.append(l[3:].strip())
                continue
            
            if l in ["Reply", "Forward", "Delete", "Archive", "Flag", "Unread", "Read"]:
                continue
                
            if len(l) > 1:
                snippet_parts.append(l)

        full_snippet = " ".join(snippet_parts)
        
        return EmailMessage(
            id=f"list-{current_count}",
            subject=list_subject,
            sender=list_sender,
            to=to_field,
            timestamp=timestamp,
            body=f"[Snippet] {full_snippet}",
            is_read=is_read
        )

    @staticmethod
    def parse_document(
        doc_html: str, 
        message_id: str,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        timestamp: Optional[str] = None,
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None
    ) -> EmailMessage:
        """Construct EmailMessage from HTML content and explicit headers."""
        markdown_body = OutlookParser.html_to_markdown(doc_html)
        images = OutlookParser.extract_images(doc_html)
        
        return EmailMessage(
            id=message_id,
            subject=OutlookParser.clean_text(subject or "No Subject"),
            sender=OutlookParser.clean_text(sender or "Unknown Sender"),
            to=[OutlookParser.clean_text(t) for t in (to or [])],
            cc=[OutlookParser.clean_text(c) for c in (cc or [])],
            timestamp=OutlookParser.clean_text(timestamp),
            body=markdown_body,
            images=images
        )

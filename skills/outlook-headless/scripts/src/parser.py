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
    def _parse_forwarded_headers(text: str) -> dict:
        """Extract From/Sent/To/Cc/Subject from a forwarded header block.

        Handles both "From: value" on one line and "From:\\nvalue" split across
        two lines (common when BeautifulSoup extracts text from <b>From:</b> value).
        """
        headers = {"from": "", "sent": "", "to": "", "cc": "", "subject": ""}
        label_map = {
            r"from|de|von": "from",
            r"sent|date|envoy[eé]\s*|datum": "sent",
            r"to|[àa]|an": "to",
            r"cc": "cc",
            r"subject|objet|betreff": "subject",
        }
        lines = [l.strip() for l in text.split("\n")]
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line:
                i += 1
                continue
            matched = False
            for pattern, key in label_map.items():
                # Case 1: "From: value" on one line
                m = re.match(rf"^(?:{pattern})\s*:\s*(.+)", line, re.IGNORECASE)
                if m:
                    headers[key] = m.group(1).strip()
                    matched = True
                    break
                # Case 2: "From:" alone, value on next line
                m = re.match(rf"^(?:{pattern})\s*:\s*$", line, re.IGNORECASE)
                if m and i + 1 < len(lines) and lines[i + 1]:
                    headers[key] = lines[i + 1].strip()
                    i += 1  # skip value line
                    matched = True
                    break
            i += 1
        return headers

    @staticmethod
    def parse_forwarded_chain(doc_html: str, parent_id: str = "0") -> List[EmailMessage]:
        """Parse forwarded email chains from within a single message body.

        Uses two strategies:
        1. DOM-based: Split on divRplyFwdMsg elements
        2. Regex fallback: Split on From:/Sent:/To: header blocks
        """
        soup = BeautifulSoup(doc_html, "html.parser")

        # Strategy 1: divRplyFwdMsg markers
        fwd_markers = soup.find_all(id=re.compile(r"(x_)?divRplyFwdMsg", re.IGNORECASE))
        if fwd_markers:
            messages = []
            for idx, marker in enumerate(fwd_markers):
                # Extract headers from the marker element text
                marker_text = marker.get_text("\n", strip=True)
                headers = OutlookParser._parse_forwarded_headers(marker_text)

                # Body is everything after the marker until the next marker
                body_parts = []
                for sibling in marker.next_siblings:
                    if hasattr(sibling, "get") and sibling.get("id") and \
                       re.match(r"(x_)?divRplyFwdMsg", sibling.get("id", ""), re.IGNORECASE):
                        break
                    if hasattr(sibling, "decode"):
                        body_parts.append(str(sibling))
                    elif isinstance(sibling, str) and sibling.strip():
                        body_parts.append(sibling)

                body_html = "".join(body_parts)
                body_md = OutlookParser.html_to_markdown(body_html) if body_html.strip() else ""

                messages.append(EmailMessage(
                    id=f"{parent_id}-fwd-{idx}",
                    sender=OutlookParser.clean_text(headers["from"]),
                    timestamp=OutlookParser.clean_text(headers["sent"]),
                    to=[OutlookParser.clean_text(t) for t in headers["to"].split(";") if t.strip()] if headers["to"] else [],
                    cc=[OutlookParser.clean_text(c) for c in headers["cc"].split(";") if c.strip()] if headers["cc"] else [],
                    subject=OutlookParser.clean_text(headers["subject"]) or None,
                    body=body_md,
                ))
            return messages

        # Strategy 2: Regex-based splitting on forwarded header blocks
        text = soup.get_text("\n", strip=False)
        # Pattern: From: ... followed by Sent/Date: ... on next lines
        header_pattern = re.compile(
            r"^(?:From|De|Von)\s*:\s*.+$",
            re.MULTILINE | re.IGNORECASE
        )
        matches = list(header_pattern.finditer(text))
        if not matches:
            return []

        # Validate each match: must be followed by Sent/Date/To lines within 4 lines
        valid_starts = []
        lines = text.split("\n")
        for match in matches:
            line_no = text[:match.start()].count("\n")
            # Check next 4 lines for Sent/Date/To pattern
            following = "\n".join(lines[line_no:line_no + 5])
            if re.search(r"(?:Sent|Date|Envoy[eé]|Datum)\s*:", following, re.IGNORECASE):
                valid_starts.append(match.start())

        if not valid_starts:
            return []

        header_pats = [
            r"^(?:From|De|Von)\s*:", r"^(?:Sent|Date|Envoy[eé]|Datum)\s*:",
            r"^(?:To|[ÀàA]|An)\s*:", r"^Cc\s*:", r"^(?:Subject|Objet|Betreff)\s*:",
        ]

        messages = []
        for idx, start in enumerate(valid_starts):
            end = valid_starts[idx + 1] if idx + 1 < len(valid_starts) else len(text)
            chunk = text[start:end]

            # Split chunk into header lines and body.
            # Consume all leading lines that are headers or blank, then body is the rest.
            chunk_lines = chunk.split("\n")
            header_lines = []
            body_start = len(chunk_lines)
            found_any_header = False
            for i, line in enumerate(chunk_lines):
                stripped = line.strip()
                is_header = any(re.match(p, stripped, re.IGNORECASE) for p in header_pats)
                if is_header:
                    header_lines.append(stripped)
                    found_any_header = True
                elif not stripped and found_any_header:
                    # Blank line after headers — skip it, might be more headers
                    continue
                elif found_any_header and not is_header and stripped:
                    # First non-header non-blank line after seeing headers = body starts
                    body_start = i
                    break

            headers = OutlookParser._parse_forwarded_headers("\n".join(header_lines))
            body_text = "\n".join(chunk_lines[body_start:]).strip()

            messages.append(EmailMessage(
                id=f"{parent_id}-fwd-{idx}",
                sender=OutlookParser.clean_text(headers["from"]),
                timestamp=OutlookParser.clean_text(headers["sent"]),
                to=[OutlookParser.clean_text(t) for t in headers["to"].split(";") if t.strip()] if headers["to"] else [],
                cc=[OutlookParser.clean_text(c) for c in headers["cc"].split(";") if c.strip()] if headers["cc"] else [],
                subject=OutlookParser.clean_text(headers["subject"]) or None,
                body=body_text,
            ))
        return messages

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

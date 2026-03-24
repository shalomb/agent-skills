from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ImageMetadata(BaseModel):
    alt: Optional[str] = None
    src: Optional[str] = None
    title: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    local_path: Optional[str] = None

class EmailMessage(BaseModel):
    id: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    to: Optional[List[str]] = Field(default_factory=list)
    cc: Optional[List[str]] = Field(default_factory=list)
    timestamp: Optional[str] = None
    body: str
    is_read: Optional[bool] = None
    images: List[ImageMetadata] = Field(default_factory=list)

class EmailSearchResult(BaseModel):
    items: List[EmailMessage]
    total_count: int

class SearchCriteria(BaseModel):
    query: Optional[str] = None
    from_sender: Optional[str] = None
    to_recipient: Optional[str] = None
    subject: Optional[str] = None
    after: Optional[str] = None # e.g. "2024-01-01"
    before: Optional[str] = None
    unread_only: bool = False
    folder: Optional[str] = None
    importance: Optional[str] = None # e.g. "high"

    def to_outlook_query(self) -> str:
        parts = []
        if self.query:
            parts.append(self.query)
        if self.from_sender:
            parts.append(f"from:{self.from_sender}")
        if self.to_recipient:
            parts.append(f"to:{self.to_recipient}")
        if self.subject:
            parts.append(f"subject:\"{self.subject}\"")
        if self.after and self.before:
            parts.append(f"received:{self.after}..{self.before}")
        elif self.after:
            parts.append(f"received:>{self.after}")
        elif self.before:
            parts.append(f"received:<{self.before}")
        if self.unread_only:
            parts.append("isread:no")
        if self.folder:
            parts.append(f"folder:\"{self.folder}\"")
        if self.importance:
            parts.append(f"importance:{self.importance}")
        return " ".join(parts)

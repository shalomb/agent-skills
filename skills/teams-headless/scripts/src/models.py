from typing import List, Optional
from pydantic import BaseModel, Field

class ImageMetadata(BaseModel):
    alt: Optional[str] = None
    src: Optional[str] = None
    local_path: Optional[str] = None

class TeamsMessage(BaseModel):
    author: str
    body: str
    timestamp: Optional[str] = None
    images: List[ImageMetadata] = Field(default_factory=list)

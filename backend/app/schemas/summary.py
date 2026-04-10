from enum import Enum
from typing import Optional
from pydantic import BaseModel

class SummaryType(Enum):
    CHUNKS = 0
    CHAPTER = 1
    BOOK = 2
    TOC = 3
    WIKI = 4

class Summary(BaseModel):
    id: str
    collection_id: str
    type: SummaryType
    summary: str
    metadata: Optional[str] = None

class SummaryCreate(BaseModel):
    collection_id: str
    type: SummaryType
    summary: str
    metadata: Optional[str] = None

class SummaryUpdate(BaseModel):
    type: SummaryType
    summary: str
    metadata: Optional[str] = None
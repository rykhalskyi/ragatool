from pydantic import BaseModel, ConfigDict
import uuid
from enum import Enum

class ImportType(str, Enum):
    NONE = "NONE"
    FILE = "FILE"
    URL  = "URL"

class CollectionBase(BaseModel):
    name: str
    description: str | None = None
    enabled: bool | None = None
    import_type: ImportType = ImportType.NONE
    model: str | None = None
    settings: str | None = None

class CollectionCreate(CollectionBase):
    pass

class Collection(CollectionBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

from typing import Optional, Dict, Any

class CollectionDetails(Collection):
    metadata: Optional[Dict[str, Any]] = None
    count: Optional[int] = None

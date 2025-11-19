from pydantic import BaseModel, ConfigDict
import uuid
from enum import Enum

class ImportType(str, Enum):
    NONE = "NONE"
    FILE = "FILE"

class CollectionBase(BaseModel):
    name: str
    description: str | None = None
    model: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    enabled: bool | None = None
    import_type: ImportType = ImportType.NONE
    locked: bool | None = None

class CollectionCreate(CollectionBase):
    pass

class Collection(CollectionBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

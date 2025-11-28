from pydantic import BaseModel, ConfigDict
import uuid
from enum import Enum

class ImportType(str, Enum):
    NONE = "NONE"
    FILE = "FILE"

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

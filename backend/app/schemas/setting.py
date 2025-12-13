from pydantic import BaseModel
from typing import Optional

class SettingBase(BaseModel):
    name: str
    value: str

class SettingCreate(SettingBase):
    pass

class Setting(SettingBase):
    description: Optional[str] = None

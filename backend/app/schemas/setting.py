from pydantic import BaseModel
from typing import Optional
from enum import Enum

class SettingsName(str, Enum):
    TWO_STEP_IMPORT = "TwoStepImport"
    FOR_TEST_ONLY = "ForTestOnly"
    CRAWL_DEPTH = "CrawlDepth"

class SettingBase(BaseModel):
    name: str
    value: str

class SettingCreate(SettingBase):
    pass

class Setting(SettingBase):
    description: Optional[str] = None

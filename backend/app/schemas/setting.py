from pydantic import BaseModel
from typing import Optional
from enum import Enum

class SettingsName(str, Enum):
    TWO_STEP_IMPORT = "TwoStepImport"
    FOR_TEST_ONLY = "ForTestOnly"
    CRAWL_DEPTH = "CrawlDepth"
    JS_RENDER_MODE = "JsRenderMode"
    RENDER_WAIT_MS = "RenderWaitMs"
    MIN_STATIC_TEXT_CHARS = "MinStaticTextChars"
    MAX_CRAWL_PAGES = "MaxCrawlPages"
    REQUEST_TIMEOUT_SEC = "RequestTimeoutSec"
    CRAWL_REQUEST_DELAY_MS = "CrawlRequestDelayMs"
    RESPECT_ROBOTS_TXT = "RespectRobotsTxt"
    ALLOW_SUBDOMAINS = "AllowSubdomains"
    RERANK_ENABLED = "RerankEnabled"
    RETRIEVAL_FETCH_K = "RetrievalFetchK"

class SettingBase(BaseModel):
    name: str
    value: str

class SettingCreate(SettingBase):
    pass

class Setting(SettingBase):
    description: Optional[str] = None

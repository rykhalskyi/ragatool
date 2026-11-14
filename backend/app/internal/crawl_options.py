import os
from dataclasses import dataclass
from typing import Optional

from app.schemas.setting import SettingsName

DEFAULT_USER_AGENT = "RagatoolBot/0.2"
VALID_RENDER_MODES = ("auto", "always", "off")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class CrawlOptions:
    js_render_mode: str = "auto"
    render_wait_ms: int = 1500
    min_static_text_chars: int = 300
    max_crawl_pages: int = 100
    request_timeout_sec: float = 20.0
    crawl_request_delay_ms: int = 300
    respect_robots_txt: bool = True
    allow_subdomains: bool = False
    allow_private_urls: bool = False
    wait_for_selector: Optional[str] = None
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_settings(cls, settings) -> "CrawlOptions":
        mode = "auto"
        if settings is not None:
            try:
                raw_mode = settings.get_setting(SettingsName.JS_RENDER_MODE)
            except Exception:
                raw_mode = None
            if isinstance(raw_mode, str) and raw_mode.strip().lower() in VALID_RENDER_MODES:
                mode = raw_mode.strip().lower()

        def setting_int(name: SettingsName, default: int) -> int:
            if settings is None:
                return default
            try:
                return int(settings.get_setting_int(name, default))
            except (TypeError, ValueError):
                return default

        def setting_bool(name: SettingsName, default: bool) -> bool:
            if settings is None:
                return default
            try:
                value = settings.get_bool(name, default)
            except Exception:
                return default
            return value if isinstance(value, bool) else default

        wait_for_selector = os.environ.get("CRAWL_WAIT_SELECTOR") or None

        return cls(
            js_render_mode=mode,
            render_wait_ms=max(0, setting_int(SettingsName.RENDER_WAIT_MS, 1500)),
            min_static_text_chars=max(0, setting_int(SettingsName.MIN_STATIC_TEXT_CHARS, 300)),
            max_crawl_pages=max(1, setting_int(SettingsName.MAX_CRAWL_PAGES, 100)),
            request_timeout_sec=max(1.0, float(setting_int(SettingsName.REQUEST_TIMEOUT_SEC, 20))),
            crawl_request_delay_ms=max(0, setting_int(SettingsName.CRAWL_REQUEST_DELAY_MS, 300)),
            respect_robots_txt=setting_bool(SettingsName.RESPECT_ROBOTS_TXT, True),
            allow_subdomains=setting_bool(SettingsName.ALLOW_SUBDOMAINS, False),
            allow_private_urls=_env_bool("ALLOW_PRIVATE_URLS", False),
            wait_for_selector=wait_for_selector,
            user_agent=DEFAULT_USER_AGENT,
        )

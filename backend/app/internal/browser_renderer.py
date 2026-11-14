import os
import threading
from dataclasses import dataclass, field
from threading import Event
from typing import Optional
from urllib.parse import urlparse

from app.internal.crawl_options import CrawlOptions
from app.internal.url_utils import ensure_host_allowed, ensure_url_allowed

BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
NETWORK_SCHEMES = {"http", "https", "ws", "wss"}
LOCAL_SCHEMES = {"data", "blob", "about"}
ANALYTICS_HOSTS = (
    "doubleclick.net",
    "facebook.net",
    "google-analytics.com",
    "googletagmanager.com",
    "hotjar.com",
    "mixpanel.com",
    "segment.io",
    "segment.com",
)
LAUNCH_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]


def _max_browsers() -> int:
    try:
        return max(1, int(os.environ.get("CRAWL_MAX_BROWSERS", "1")))
    except (TypeError, ValueError):
        return 1


_BROWSER_SEMAPHORE = threading.Semaphore(_max_browsers())


def _load_playwright():
    try:
        from playwright import sync_api

        return sync_api
    except Exception:
        return None


@dataclass
class RenderResult:
    url: str
    final_url: str
    html: str
    links: list[str] = field(default_factory=list)
    text: str = ""


class BrowserRenderer:
    def __init__(self, options: CrawlOptions):
        self.options = options
        self._playwright = None
        self._browser = None
        self._context = None
        self._started = False
        self._unavailable = False
        self._semaphore_acquired = False
        self._host_allowed: dict[str, bool] = {}

    def __enter__(self) -> "BrowserRenderer":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _ensure_started(self) -> bool:
        if self._started:
            return True
        if self._unavailable:
            return False

        sync_api = _load_playwright()
        if sync_api is None:
            print("Playwright is unavailable; falling back to static fetching")
            self._unavailable = True
            return False

        _BROWSER_SEMAPHORE.acquire()
        self._semaphore_acquired = True
        try:
            self._playwright = sync_api.sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=LAUNCH_ARGS,
            )
            self._context = self._browser.new_context(
                user_agent=self.options.user_agent,
            )
            self._context.route("**/*", self._handle_route)
            self._started = True
            return True
        except Exception as exc:
            print(f"Failed to start Playwright browser: {exc}")
            self._cleanup()
            self._unavailable = True
            return False

    def _handle_route(self, route) -> None:
        request = route.request
        if request.resource_type in BLOCKED_RESOURCE_TYPES:
            route.abort()
            return

        parsed = urlparse(request.url)
        scheme = parsed.scheme.lower()
        if scheme in LOCAL_SCHEMES:
            route.continue_()
            return
        if scheme not in NETWORK_SCHEMES:
            route.abort()
            return

        host = (parsed.hostname or "").lower()
        if any(host == blocked or host.endswith("." + blocked) for blocked in ANALYTICS_HOSTS):
            route.abort()
            return
        if not self._host_is_allowed(host):
            route.abort()
            return
        route.continue_()

    def _host_is_allowed(self, host: str) -> bool:
        if self.options.allow_private_urls:
            return True
        cached = self._host_allowed.get(host)
        if cached is not None:
            return cached
        try:
            ensure_host_allowed(host, self.options.allow_private_urls)
            allowed = True
        except ValueError:
            allowed = False
        self._host_allowed[host] = allowed
        return allowed

    def render(self, url: str, cancel_event: Optional[Event] = None) -> Optional[RenderResult]:
        try:
            ensure_url_allowed(url, self.options.allow_private_urls)
        except ValueError:
            return None

        if not self._ensure_started():
            return None
        if cancel_event is not None and cancel_event.is_set():
            return None

        page = None
        try:
            page = self._context.new_page()
            timeout_ms = int(self.options.request_timeout_sec * 1000)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            if self.options.wait_for_selector:
                try:
                    page.wait_for_selector(self.options.wait_for_selector, timeout=timeout_ms)
                except Exception:
                    pass

            try:
                page.wait_for_load_state("networkidle", timeout=min(3000, timeout_ms))
            except Exception:
                pass

            if cancel_event is not None and cancel_event.is_set():
                return None
            page.wait_for_timeout(max(0, self.options.render_wait_ms))
            self._auto_scroll(page, cancel_event)

            if cancel_event is not None and cancel_event.is_set():
                return None

            html = page.content()
            final_url = page.url
            try:
                ensure_url_allowed(final_url, self.options.allow_private_urls)
            except ValueError:
                return None

            try:
                text = page.inner_text("body")
            except Exception:
                text = ""

            try:
                links = page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.map(element => element.href)",
                )
            except Exception:
                links = []

            return RenderResult(
                url=url,
                final_url=final_url,
                html=html,
                links=[link for link in links if link],
                text=text,
            )
        except Exception as exc:
            print(f"Failed to render {url}: {exc}")
            return None
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

    def _auto_scroll(self, page, cancel_event: Optional[Event] = None) -> None:
        try:
            height = page.evaluate("() => (document.body ? document.body.scrollHeight : 0)") or 0
            viewport = page.evaluate("() => Math.max(window.innerHeight, 400)") or 400
            step = max(int(viewport), 400)
            max_steps = 50
            steps = min(max_steps, max(1, int(height / step) + 1))
            for index in range(steps):
                if cancel_event is not None and cancel_event.is_set():
                    break
                page.evaluate(f"() => window.scrollTo(0, {index * step})")
                page.wait_for_timeout(120)
            page.evaluate("() => window.scrollTo(0, 0)")
        except Exception:
            pass

    def close(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        self._cleanup()
        if self._semaphore_acquired:
            _BROWSER_SEMAPHORE.release()
            self._semaphore_acquired = False
        self._started = False

    def _cleanup(self) -> None:
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

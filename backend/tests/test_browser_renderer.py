from unittest.mock import MagicMock, patch

from app.internal import browser_renderer
from app.internal.browser_renderer import BrowserRenderer
from app.internal.crawl_options import CrawlOptions


class FakePage:
    def __init__(self):
        self.url = "http://example.com/final"
        self.closed = False

    def goto(self, url, wait_until=None, timeout=None):
        self.url = "http://example.com/final"

    def wait_for_selector(self, selector, timeout=None):
        pass

    def wait_for_load_state(self, state, timeout=None):
        pass

    def wait_for_timeout(self, timeout):
        pass

    def evaluate(self, script):
        pass

    def content(self):
        return "<html><body><p>Rendered</p></body></html>"

    def inner_text(self, selector):
        return "Rendered body text"

    def eval_on_selector_all(self, selector, script):
        return ["http://example.com/final", "http://example.com/next"]

    def close(self):
        self.closed = True


class FakeContext:
    def __init__(self):
        self.route_handler = None
        self.closed = False

    def route(self, pattern, handler):
        self.route_handler = handler

    def new_page(self):
        return FakePage()

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.context = FakeContext()
        self.closed = False

    def new_context(self, user_agent=None):
        return self.context

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self):
        self.browser = FakeBrowser()

    def launch(self, headless=None, args=None):
        return self.browser


class FakePlaywright:
    def __init__(self):
        self.chromium = FakeChromium()


class FakePlaywrightManager:
    def __init__(self, playwright):
        self.playwright = playwright

    def start(self):
        return self.playwright


class FakeSyncApi:
    def __init__(self, playwright):
        self.playwright = playwright

    def sync_playwright(self):
        return FakePlaywrightManager(self.playwright)


def make_options(**overrides):
    defaults = dict(
        js_render_mode="auto",
        render_wait_ms=0,
        request_timeout_sec=5,
        allow_private_urls=True,
    )
    defaults.update(overrides)
    return CrawlOptions(**defaults)


def test_render_returns_page_content_and_links():
    playwright = FakePlaywright()
    with patch.object(browser_renderer, "_load_playwright", return_value=FakeSyncApi(playwright)):
        renderer = BrowserRenderer(make_options())
        result = renderer.render("http://example.com")
        renderer.close()

    assert result is not None
    assert result.html == "<html><body><p>Rendered</p></body></html>"
    assert result.text == "Rendered body text"
    assert result.final_url == "http://example.com/final"
    assert result.links == ["http://example.com/final", "http://example.com/next"]
    assert renderer._semaphore_acquired is False


def test_render_degrades_when_playwright_is_unavailable():
    with patch.object(browser_renderer, "_load_playwright", return_value=None):
        renderer = BrowserRenderer(make_options())
        result = renderer.render("http://example.com")
        renderer.close()

    assert result is None


def test_resource_types_and_analytics_hosts_are_blocked():
    renderer = BrowserRenderer(make_options())

    image_route = MagicMock()
    image_route.request.resource_type = "image"
    image_route.request.url = "http://example.com/picture.png"
    renderer._handle_route(image_route)
    image_route.abort.assert_called_once()

    analytics_route = MagicMock()
    analytics_route.request.resource_type = "script"
    analytics_route.request.url = "https://www.google-analytics.com/analytics.js"
    renderer._handle_route(analytics_route)
    analytics_route.abort.assert_called_once()

    document_route = MagicMock()
    document_route.request.resource_type = "document"
    document_route.request.url = "http://example.com/page"
    renderer._handle_route(document_route)
    document_route.continue_.assert_called_once()

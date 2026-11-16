import re
from threading import Event
from unittest.mock import patch

import pytest

from app.internal.crawl_options import CrawlOptions
from app.internal.simple_crawler import simple_crawl
from app.internal.url_utils import normalize_url
from app.internal.web_fetcher import ExtractResult, FetchResult
from app.internal.browser_renderer import RenderResult


def make_options(**overrides):
    defaults = dict(
        js_render_mode="off",
        min_static_text_chars=0,
        max_crawl_pages=100,
        crawl_request_delay_ms=0,
        respect_robots_txt=False,
        allow_private_urls=True,
    )
    defaults.update(overrides)
    return CrawlOptions(**defaults)


def page(html, final_url=None):
    return FetchResult(
        url=final_url or "",
        final_url=final_url or "",
        html=html,
        status_code=200,
        content_type="text/html",
    )


class FakeFetcher:
    responses = {}

    def __init__(self, options):
        self.options = options
        self.fetched = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def fetch(self, url, cancel_event=None):
        self.fetched.append(url)
        FakeFetcher.fetched_urls.append(url)
        return FakeFetcher.responses.get(normalize_url(url))


class FakeRenderer:
    responses = {}

    def __init__(self, options):
        self.options = options

    def render(self, url, cancel_event=None):
        FakeRenderer.rendered_urls.append(url)
        return FakeRenderer.responses.get(normalize_url(url))

    def close(self):
        pass


@pytest.fixture(autouse=True)
def reset_fakes():
    FakeFetcher.responses = {}
    FakeFetcher.fetched_urls = []
    FakeRenderer.responses = {}
    FakeRenderer.rendered_urls = []
    with patch("app.internal.simple_crawler.StaticFetcher", FakeFetcher), \
         patch("app.internal.simple_crawler.BrowserRenderer", FakeRenderer):
        yield


def test_static_page_does_not_render():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><head><title>Home</title></head><body><p>Home content</p>'
            '<a href="/page2">Page 2</a></body></html>',
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><head><title>Page 2</title></head><body><p>Content of page 2</p></body></html>",
            "http://example.com/page2",
        ),
    }

    results = simple_crawl("http://example.com", Event(), None, max_depth=1, options=make_options())

    assert len(results) == 2
    assert results[0]["url"] == "http://example.com"
    assert results[0]["title"] == "Home"
    assert results[1]["url"] == "http://example.com/page2"
    assert results[1]["title"] == "Page 2"
    assert all(result["rendered"] is False for result in results)
    assert FakeRenderer.rendered_urls == []


def test_thin_spa_triggers_rendering():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><head><title>App</title></head><body><div id="root"></div>'
            '<script src="a.js"></script><script src="b.js"></script></body></html>',
            "http://example.com",
        ),
    }
    FakeRenderer.responses = {
        "http://example.com": RenderResult(
            url="http://example.com",
            final_url="http://example.com",
            html="<html><body><p>Rendered client-side content</p></body></html>",
            links=[],
            text="Rendered client-side content",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        None,
        max_depth=0,
        options=make_options(js_render_mode="auto", min_static_text_chars=300),
    )

    assert len(results) == 1
    assert results[0]["rendered"] is True
    assert "Rendered client-side content" in results[0]["text"]
    assert FakeRenderer.rendered_urls == ["http://example.com"]


def test_always_mode_renders_rich_static_page():
    FakeFetcher.responses = {
        "http://example.com": page(
            "<html><body><p>" + ("Static content " * 100) + "</p></body></html>",
            "http://example.com",
        ),
    }
    FakeRenderer.responses = {
        "http://example.com": RenderResult(
            url="http://example.com",
            final_url="http://example.com",
            html="<html><body><p>Rendered content</p></body></html>",
            links=[],
            text="Rendered content",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        None,
        max_depth=0,
        options=make_options(js_render_mode="always", min_static_text_chars=300),
    )

    assert results[0]["rendered"] is True
    assert "Rendered content" in results[0]["text"]


def test_off_mode_never_renders():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><div id="root"></div><script src="a.js"></script>'
            '<script src="b.js"></script><p>Thin</p></body></html>',
            "http://example.com",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        None,
        max_depth=0,
        options=make_options(js_render_mode="off", min_static_text_chars=300),
    )

    assert len(results) == 1
    assert results[0]["rendered"] is False
    assert FakeRenderer.rendered_urls == []


def test_playwright_unavailable_falls_back_to_static():
    FakeFetcher.responses = {
        "http://example.com": page(
            "<html><body><p>Short static text</p></body></html>",
            "http://example.com",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        None,
        max_depth=0,
        options=make_options(js_render_mode="auto", min_static_text_chars=300),
    )

    assert len(results) == 1
    assert results[0]["rendered"] is False
    assert "Short static text" in results[0]["text"]
    assert FakeRenderer.rendered_urls == ["http://example.com"]


def test_url_normalization_and_duplicate_suppression():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p>'
            '<a href="http://example.com/page2#frag">A</a>'
            '<a href="http://example.com/page2/">B</a>'
            "</body></html>",
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Page 2</p></body></html>",
            "http://example.com/page2",
        ),
    }

    results = simple_crawl("http://example.com", Event(), None, max_depth=1, options=make_options())

    assert [result["url"] for result in results] == ["http://example.com", "http://example.com/page2"]
    assert FakeFetcher.fetched_urls == ["http://example.com", "http://example.com/page2"]


def test_asset_links_are_skipped():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p>'
            '<a href="/image.png">Image</a>'
            '<a href="/app.js">JS</a>'
            '<a href="/archive.zip">Zip</a>'
            '<a href="/talk.mp4">Video</a>'
            '<a href="/page2">Page 2</a>'
            "</body></html>",
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Page 2</p></body></html>",
            "http://example.com/page2",
        ),
    }

    simple_crawl("http://example.com", Event(), None, max_depth=1, options=make_options())

    assert FakeFetcher.fetched_urls == ["http://example.com", "http://example.com/page2"]


def test_pdf_links_are_parsed():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p><a href="/manual.pdf">Manual</a></body></html>',
            "http://example.com",
        ),
        "http://example.com/manual.pdf": FetchResult(
            url="http://example.com/manual.pdf",
            final_url="http://example.com/manual.pdf",
            html="",
            status_code=200,
            content_type="application/pdf",
            content=b"%PDF-1.4 fake pdf bytes",
            is_pdf=True,
        ),
    }

    with patch(
        "app.internal.simple_crawler.extract_pdf_page",
        return_value=ExtractResult(text="Extracted PDF text", title="Manual"),
    ):
        results = simple_crawl(
            "http://example.com",
            Event(),
            None,
            max_depth=1,
            options=make_options(js_render_mode="auto"),
        )

    assert [result["url"] for result in results] == [
        "http://example.com",
        "http://example.com/manual.pdf",
    ]
    assert results[1]["text"] == "Extracted PDF text"
    assert results[1]["title"] == "Manual"
    assert results[1]["rendered"] is False
    assert FakeRenderer.rendered_urls == []


def test_max_crawl_pages():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p>'
            '<a href="/page2">Page 2</a>'
            '<a href="/page3">Page 3</a>'
            "</body></html>",
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Page 2</p></body></html>",
            "http://example.com/page2",
        ),
        "http://example.com/page3": page(
            "<html><body><p>Page 3</p></body></html>",
            "http://example.com/page3",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        None,
        max_depth=1,
        options=make_options(max_crawl_pages=2),
    )

    assert len(results) == 2
    assert FakeFetcher.fetched_urls == ["http://example.com", "http://example.com/page2"]


def test_robots_disallow_skips_page():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p><a href="/private">Private</a></body></html>',
            "http://example.com",
        ),
        "http://example.com/private": page(
            "<html><body><p>Private</p></body></html>",
            "http://example.com/private",
        ),
    }

    class FakeRobots:
        def __init__(self, user_agent, allow_private_urls=False):
            pass

        def can_fetch(self, url):
            return "/private" not in url

    with patch("app.internal.simple_crawler.RobotsCache", FakeRobots):
        results = simple_crawl(
            "http://example.com",
            Event(),
            None,
            max_depth=1,
            options=make_options(respect_robots_txt=True),
        )

    assert [result["url"] for result in results] == ["http://example.com"]
    assert FakeFetcher.fetched_urls == ["http://example.com"]


def test_duplicate_content_is_deduplicated():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><article><p>Same content</p></article>'
            '<a href="/page2">Page 2</a></body></html>',
            "http://example.com",
        ),
        "http://example.com/page2": page(
            '<html><body><article><p>Same content</p></article>'
            '<a href="/page2">Page 2</a></body></html>',
            "http://example.com/page2",
        ),
    }

    results = simple_crawl("http://example.com", Event(), None, max_depth=1, options=make_options())

    assert len(results) == 1
    assert results[0]["url"] == "http://example.com"


def test_regex_filter_applies_to_discovered_links():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p>'
            '<a href="http://example.com/page2">Page 2</a>'
            '<a href="http://example.com/other">Other</a>'
            "</body></html>",
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Page 2</p></body></html>",
            "http://example.com/page2",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        re.compile(r"http://example\.com/page2"),
        max_depth=1,
        options=make_options(),
    )

    assert [result["url"] for result in results] == ["http://example.com", "http://example.com/page2"]


def test_regex_cannot_be_bypassed_by_redirects():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p>'
            '<a href="http://example.com/page2">Page 2</a>'
            "</body></html>",
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Redirected</p></body></html>",
            "http://example.com/login",
        ),
    }

    results = simple_crawl(
        "http://example.com",
        Event(),
        re.compile(r"http://example\.com/page2"),
        max_depth=1,
        options=make_options(),
    )

    assert [result["url"] for result in results] == ["http://example.com"]


def test_off_domain_links_are_skipped():
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home</p><a href="http://other.com/page">Other</a></body></html>',
            "http://example.com",
        ),
    }

    results = simple_crawl("http://example.com", Event(), None, max_depth=1, options=make_options())

    assert len(results) == 1
    assert FakeFetcher.fetched_urls == ["http://example.com"]


def test_cancellation_returns_partial_results():
    event = Event()
    event.set()

    result = simple_crawl("http://example.com", event, None, max_depth=1, options=make_options())

    assert result == []


def test_cancellation_returns_pages_collected_so_far():
    event = Event()
    FakeFetcher.responses = {
        "http://example.com": page(
            '<html><body><p>Home content</p>'
            '<a href="/page2">Page 2</a></body></html>',
            "http://example.com",
        ),
        "http://example.com/page2": page(
            "<html><body><p>Content of page 2</p></body></html>",
            "http://example.com/page2",
        ),
    }

    def stop_after_first_page(message: str) -> None:
        if message.startswith("Imported"):
            event.set()

    results = simple_crawl(
        "http://example.com",
        event,
        None,
        max_depth=1,
        options=make_options(),
        on_progress=stop_after_first_page,
    )

    assert [result["url"] for result in results] == ["http://example.com"]

from dataclasses import dataclass
from threading import Event
from typing import Optional

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.internal.crawl_options import CrawlOptions

HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")

SPA_MARKERS = (
    'id="root"',
    "id='root'",
    'id="app"',
    "id='app'",
    "__next",
    "app-root",
    "ng-version",
    "data-reactroot",
)


@dataclass
class FetchResult:
    url: str
    final_url: str
    html: str
    status_code: int
    content_type: str


@dataclass
class ExtractResult:
    text: str
    title: str


class StaticFetcher:
    def __init__(self, options: CrawlOptions):
        self.options = options
        self._client: Optional[httpx.Client] = None

    def __enter__(self) -> "StaticFetcher":
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=self.options.request_timeout_sec,
            headers={
                "User-Agent": self.options.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def fetch(self, url: str, cancel_event: Optional[Event] = None) -> Optional[FetchResult]:
        if self._client is None:
            raise RuntimeError("StaticFetcher must be used as a context manager")

        for attempt in range(3):
            try:
                response = self._client.get(url)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2 and not _backoff(attempt, cancel_event):
                        return None
                    continue
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if content_type and not any(t in content_type for t in HTML_CONTENT_TYPES):
                    return None

                final_url = str(response.url)
                return FetchResult(
                    url=url,
                    final_url=final_url,
                    html=response.text,
                    status_code=response.status_code,
                    content_type=content_type,
                )
            except httpx.TimeoutException:
                if attempt < 2 and not _backoff(attempt, cancel_event):
                    return None
            except httpx.RequestError:
                if attempt < 2 and not _backoff(attempt, cancel_event):
                    return None
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429 or status >= 500:
                    if attempt < 2 and not _backoff(attempt, cancel_event):
                        return None
                    continue
                return None
            except Exception:
                return None

        return None


def _backoff(attempt: int, cancel_event: Optional[Event]) -> bool:
    seconds = 0.5 * (2 ** attempt)
    if cancel_event is not None:
        return not cancel_event.wait(seconds)
    import time

    time.sleep(seconds)
    return True


def extract_page(
    html: str,
    url: str,
    options: CrawlOptions,
    fallback_text: Optional[str] = None,
) -> ExtractResult:
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)

    text = ""
    try:
        text = trafilatura.extract(
            html,
            url=url,
            include_tables=True,
            include_comments=False,
        ) or ""
    except Exception:
        text = ""

    if len(text.strip()) < options.min_static_text_chars:
        try:
            recall_text = trafilatura.extract(
                html,
                url=url,
                include_tables=True,
                include_comments=False,
                favor_recall=True,
            ) or ""
        except Exception:
            recall_text = ""
        if len(recall_text.strip()) > len(text.strip()):
            text = recall_text

    if not text.strip():
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)

    if fallback_text and len(fallback_text.strip()) > len(text.strip()):
        text = fallback_text

    return ExtractResult(text=text.strip(), title=title)


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href:
            links.append(href)
    return links


def looks_like_spa(html: str) -> bool:
    lower = html.lower()
    has_marker = any(marker in lower for marker in SPA_MARKERS)
    script_count = lower.count("<script")
    return has_marker and script_count > 1


def should_render(html: str, extracted_text: str, options: CrawlOptions) -> bool:
    if options.js_render_mode == "always":
        return True
    if options.js_render_mode == "off":
        return False
    if len(extracted_text.strip()) < options.min_static_text_chars:
        return True
    return looks_like_spa(html)


def _extract_title(soup: BeautifulSoup) -> str:
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""

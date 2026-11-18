from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import Event
from typing import Optional
from urllib.parse import unquote, urljoin, urlsplit

import httpx
import trafilatura
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.internal.crawl_options import CrawlOptions
from app.internal.url_utils import ensure_url_allowed

HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
PDF_CONTENT_TYPE = "application/pdf"
PDF_MAGIC = b"%PDF"
MAX_REDIRECTS = 5

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

MIN_USEFUL_TEXT_CHARS = 80

CONTENT_SELECTORS = (
    "main",
    "article",
    '[role="main"]',
    ".documentation",
    ".content",
    "#content",
    "#main",
)

NOISE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    '[role="navigation"]',
    '[role="banner"]',
    '[role="contentinfo"]',
    '[role="complementary"]',
    '[aria-hidden="true"]',
    '[class*="cookie"]',
    '[id*="cookie"]',
    '[class*="consent"]',
    '[id*="consent"]',
    '[class*="gdpr"]',
    '[id*="gdpr"]',
    '[class*="breadcrumb"]',
    '[id*="breadcrumb"]',
)


@dataclass
class FetchResult:
    url: str
    final_url: str
    html: str
    status_code: int
    content_type: str
    content: Optional[bytes] = None
    is_pdf: bool = False


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
            follow_redirects=False,
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

    def _get_following_redirects(self, url: str) -> Optional[httpx.Response]:
        current_url = url
        for hop in range(MAX_REDIRECTS + 1):
            try:
                ensure_url_allowed(current_url, self.options.allow_private_urls)
            except ValueError:
                return None
            response = self._client.get(current_url)
            if response.has_redirect_location:
                if hop == MAX_REDIRECTS:
                    return None
                current_url = urljoin(str(response.url), response.headers["location"])
                continue
            if 300 <= response.status_code < 400:
                return None
            return response
        return None

    def fetch(self, url: str, cancel_event: Optional[Event] = None) -> Optional[FetchResult]:
        if self._client is None:
            raise RuntimeError("StaticFetcher must be used as a context manager")

        for attempt in range(3):
            try:
                response = self._get_following_redirects(url)
                if response is None:
                    return None
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2 and not _backoff(attempt, cancel_event):
                        return None
                    continue
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                final_url = str(response.url)
                kind = _response_kind(final_url, content_type, response.content)

                if kind is None:
                    return None

                if kind == "pdf":
                    return FetchResult(
                        url=url,
                        final_url=final_url,
                        html="",
                        status_code=response.status_code,
                        content_type=content_type,
                        content=response.content,
                        is_pdf=True,
                    )

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


def _response_kind(url: str, content_type: str, content: bytes) -> Optional[str]:
    """Return ``pdf``, ``html`` or ``None`` for a fetched response.

    An explicit HTML content type always wins over a ``.pdf`` extension so an
    HTML error/landing page at a ``.pdf`` URL is still parsed as HTML.
    """
    path_is_pdf = urlsplit(url).path.lower().endswith(".pdf")
    body_is_pdf = content.lstrip().startswith(PDF_MAGIC)
    if PDF_CONTENT_TYPE in content_type:
        return "pdf" if body_is_pdf else None
    if any(t in content_type for t in HTML_CONTENT_TYPES):
        return "html"
    if path_is_pdf:
        return "pdf" if body_is_pdf else None
    if not content_type:
        return "pdf" if body_is_pdf else "html"
    return None


def extract_pdf_page(content: bytes, url: str) -> ExtractResult:
    pages = []
    title = ""
    try:
        reader = PdfReader(BytesIO(content))
        try:
            metadata_title = reader.metadata.title if reader.metadata else None
            title = str(metadata_title).strip() if metadata_title else ""
        except Exception:
            title = ""

        for pdf_page in reader.pages:
            try:
                page_text = pdf_page.extract_text() or ""
            except Exception:
                page_text = ""
            if page_text.strip():
                pages.append(page_text)
    except Exception:
        pages = []

    if not title:
        title = unquote(Path(urlsplit(url).path).name) or "PDF"

    return ExtractResult(text=_normalize_text("\n\n".join(pages)), title=title)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def extract_page(
    html: str,
    url: str,
    options: CrawlOptions,
    fallback_text: Optional[str] = None,
) -> ExtractResult:
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)

    text = _trafilatura_extract(html, url, favor_precision=True)
    dom_text, has_container = _extract_dom_text(soup)

    if has_container:
        # A semantic <main>/<article> container recovers short documentation
        # pages that trafilatura's precision pass misses, without escalating
        # to recall mode (which re-introduces chrome).
        if len(text.strip()) < MIN_USEFUL_TEXT_CHARS and len(dom_text.strip()) > len(text.strip()):
            text = dom_text
        if not text.strip():
            text = _trafilatura_extract(html, url, favor_recall=True) or dom_text
    else:
        if len(text.strip()) < MIN_USEFUL_TEXT_CHARS:
            balanced = _trafilatura_extract(html, url)
            if len(balanced.strip()) > len(text.strip()):
                text = balanced
        if not text.strip():
            text = _trafilatura_extract(html, url, favor_recall=True)
        if not text.strip():
            text = dom_text

    # Rendered body text is a last resort only: it almost always contains
    # navigation, cookie banners and other chrome, so it must never replace
    # a successful main-content extraction.
    fallback_text = (fallback_text or "").strip()
    if not text.strip() and fallback_text:
        text = fallback_text

    return ExtractResult(text=text.strip(), title=title)


def _trafilatura_extract(html: str, url: str, **kwargs) -> str:
    try:
        text = trafilatura.extract(
            html,
            url=url,
            include_tables=True,
            include_comments=False,
            include_links=False,
            deduplicate=True,
            **kwargs,
        ) or ""
    except Exception:
        return ""
    return _deduplicate_text(text)


def _deduplicate_text(text: str) -> str:
    seen: set[str] = set()
    lines = []
    for line in text.splitlines():
        key = " ".join(line.split()).lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        lines.append(line.strip())
    return "\n".join(lines)


def _extract_dom_text(soup: BeautifulSoup) -> tuple[str, bool]:
    container = None
    for selector in CONTENT_SELECTORS:
        try:
            container = soup.select_one(selector)
        except Exception:
            container = None
        if container is not None:
            break

    has_container = container is not None
    if container is None:
        container = soup.body or soup

    for selector in NOISE_SELECTORS:
        try:
            for tag in container.select(selector):
                tag.decompose()
        except Exception:
            continue

    return container.get_text("\n", strip=True), has_container


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

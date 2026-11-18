import math
import re
from collections import Counter, deque
from hashlib import sha256
from re import Pattern
from threading import Event
from typing import Callable, Optional
from urllib.parse import urljoin

from app.internal.browser_renderer import BrowserRenderer
from app.internal.crawl_options import CrawlOptions
from app.internal.url_utils import (
    RobotsCache,
    ensure_url_allowed,
    is_asset_url,
    is_http_url,
    normalize_url,
    same_site,
)
from app.internal.web_fetcher import (
    StaticFetcher,
    extract_links,
    extract_page,
    extract_pdf_page,
    should_render,
)


def simple_crawl(
    start_url,
    cancel_event: Event,
    regex: Optional[Pattern[str]] = None,
    max_depth: int = 1,
    options: Optional[CrawlOptions] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> list[dict]:
    options = options or CrawlOptions()
    start = normalize_url(start_url)
    if not is_http_url(start):
        return []

    robots = (
        RobotsCache(options.user_agent, allow_private_urls=options.allow_private_urls)
        if options.respect_robots_txt
        else None
    )
    renderer = BrowserRenderer(options)
    visited: set[str] = set()
    seen_content: set[str] = set()
    queue = deque([(start, 0)])
    results: list[dict] = []
    requests_made = 0

    def finalize() -> list[dict]:
        # Strip chrome (menus, sidebars, footers, ...) that repeats across the
        # crawled pages. Callers decide whether to keep partial results.
        _strip_repeated_blocks(results)
        return results

    try:
        with StaticFetcher(options) as fetcher:
            while queue:
                if cancel_event.is_set():
                    # Return what has been collected so far. Callers decide
                    # whether to keep or discard partial crawl results.
                    return finalize()

                url, depth = queue.popleft()
                if url in visited or depth > max_depth:
                    continue
                if len(visited) >= options.max_crawl_pages:
                    break

                try:
                    ensure_url_allowed(url, options.allow_private_urls)
                except ValueError as exc:
                    print(f"Skipping {url}: {exc}")
                    visited.add(url)
                    continue

                if robots is not None and not robots.can_fetch(url):
                    _report(on_progress, f"Skipping {url} (robots.txt)")
                    visited.add(url)
                    continue

                visited.add(url)

                if requests_made > 0 and options.crawl_request_delay_ms > 0:
                    if cancel_event.wait(options.crawl_request_delay_ms / 1000):
                        return finalize()
                requests_made += 1

                _report(on_progress, f"Crawling [{depth}] {url}")

                fetched = fetcher.fetch(url, cancel_event)
                if cancel_event.is_set():
                    return finalize()

                if fetched is not None:
                    try:
                        ensure_url_allowed(fetched.final_url, options.allow_private_urls)
                    except ValueError as exc:
                        print(f"Skipping {fetched.final_url}: {exc}")
                        continue

                if fetched is not None and fetched.is_pdf:
                    extracted = extract_pdf_page(fetched.content, fetched.final_url)
                    final_url = fetched.final_url
                    links = []
                    rendered = False
                else:
                    render_needed = options.js_render_mode == "always" or (
                        fetched is None and options.js_render_mode != "off"
                    )
                    if fetched is not None and options.js_render_mode != "off":
                        static_text = extract_page(fetched.html, fetched.final_url, options).text
                        render_needed = should_render(fetched.html, static_text, options)

                    rendered_page = None
                    if render_needed and options.js_render_mode != "off":
                        rendered_page = renderer.render(url, cancel_event)
                        if cancel_event.is_set():
                            return finalize()

                    if rendered_page is not None:
                        extracted = extract_page(
                            rendered_page.html,
                            rendered_page.final_url,
                            options,
                            fallback_text=rendered_page.text,
                        )
                        final_url = rendered_page.final_url
                        links = rendered_page.links or extract_links(rendered_page.html, final_url)
                        rendered = True
                    elif fetched is not None:
                        extracted = extract_page(fetched.html, fetched.final_url, options)
                        final_url = fetched.final_url
                        links = extract_links(fetched.html, final_url)
                        rendered = False
                    else:
                        continue

                normalized_final = normalize_url(final_url)
                if regex is not None and normalized_final != url and not regex.match(normalized_final):
                    continue

                text = extracted.text.strip()
                if not text:
                    continue

                content_hash = sha256(" ".join(text.split()).encode("utf-8")).hexdigest()
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                results.append({
                    "url": url,
                    "text": text,
                    "title": extracted.title,
                    "final_url": final_url,
                    "rendered": rendered,
                })
                _report(on_progress, f"Imported {url}")

                if depth == max_depth:
                    continue

                for link in links:
                    if cancel_event.is_set():
                        return finalize()
                    candidate = normalize_url(urljoin(final_url, link))
                    if candidate in visited:
                        continue
                    if not _link_allowed(candidate, start, options, regex):
                        continue
                    queue.append((candidate, depth + 1))
    finally:
        renderer.close()

    return finalize()


def _strip_repeated_blocks(pages: list[dict]) -> None:
    """Remove blocks that repeat across most pages of a crawl.

    Documentation sites (and most sites) render the same menu, sidebar,
    breadcrumb and footer on every page. Exact repeated blocks across a
    majority of pages are chrome, not content, so drop them in place.
    """
    if len(pages) < 3:
        return

    page_blocks = []
    counts: Counter[str] = Counter()
    for page in pages:
        blocks, joiner = _split_blocks(page["text"])
        normalized = [_normalize_block(block) for block in blocks]
        page_blocks.append((page, blocks, normalized, joiner))
        counts.update({key for key in normalized if len(key) >= 2})

    threshold = max(3, math.ceil(len(pages) * 0.6))
    repeated = {key for key, count in counts.items() if count >= threshold}
    if not repeated:
        return

    cleaned = []
    for page, blocks, normalized, joiner in page_blocks:
        kept = [block for block, key in zip(blocks, normalized) if key not in repeated]
        text = joiner.join(kept).strip()
        if text:
            page["text"] = text
            cleaned.append(page)

    pages[:] = cleaned


def _split_blocks(text: str) -> tuple[list[str], str]:
    if "\n\n" in text:
        parts = re.split(r"\n\s*\n", text)
        joiner = "\n\n"
    else:
        parts = text.split("\n")
        joiner = "\n"
    return [part.strip() for part in parts if part.strip()], joiner


def _normalize_block(block: str) -> str:
    return " ".join(block.split()).lower()


def _link_allowed(
    url: str,
    start_url: str,
    options: CrawlOptions,
    regex: Optional[Pattern[str]],
) -> bool:
    """Filter discovered links. The start URL is always imported, even if it
    does not match ``regex``; redirect targets are checked separately."""
    if not is_http_url(url):
        return False
    if is_asset_url(url):
        return False
    if not same_site(url, start_url, options.allow_subdomains):
        return False
    if regex is not None and not regex.match(url):
        return False
    return True


def _report(on_progress: Optional[Callable[[str], None]], message: str) -> None:
    if on_progress is None:
        return
    try:
        on_progress(message)
    except Exception:
        pass

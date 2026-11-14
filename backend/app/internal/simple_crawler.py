from collections import deque
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
) -> Optional[list[dict]]:
    options = options or CrawlOptions()
    start = normalize_url(start_url)
    if not is_http_url(start):
        return []

    robots = RobotsCache(options.user_agent) if options.respect_robots_txt else None
    renderer = BrowserRenderer(options)
    visited: set[str] = set()
    seen_content: set[str] = set()
    queue = deque([(start, 0)])
    results: list[dict] = []
    requests_made = 0

    try:
        with StaticFetcher(options) as fetcher:
            while queue:
                if cancel_event.is_set():
                    return None

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
                        return None
                requests_made += 1

                _report(on_progress, f"Crawling [{depth}] {url}")

                fetched = fetcher.fetch(url, cancel_event)
                if cancel_event.is_set():
                    return None

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
                            return None

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
                        return None
                    candidate = normalize_url(urljoin(final_url, link))
                    if candidate in visited:
                        continue
                    if not _link_allowed(candidate, start, options, regex):
                        continue
                    queue.append((candidate, depth + 1))
    finally:
        renderer.close()

    return results


def _link_allowed(
    url: str,
    start_url: str,
    options: CrawlOptions,
    regex: Optional[Pattern[str]],
) -> bool:
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


def crawl_from_list(urls):
    options = CrawlOptions()
    results = []
    with StaticFetcher(options) as fetcher:
        for url in urls:
            fetched = fetcher.fetch(url)
            if fetched is None:
                continue
            if fetched.is_pdf:
                extracted = extract_pdf_page(fetched.content, fetched.final_url)
            else:
                extracted = extract_page(fetched.html, fetched.final_url, options)
            if extracted.text:
                results.append({
                    "url": url,
                    "text": extracted.text,
                    "title": extracted.title,
                    "final_url": fetched.final_url,
                    "rendered": False,
                })
    return results

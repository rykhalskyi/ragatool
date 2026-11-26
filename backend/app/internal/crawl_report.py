from collections import Counter
from dataclasses import dataclass, field

REASON_LABELS = {
    "unsupported_scheme": "not http(s)",
    "asset": "asset/binary file",
    "off_site": "different site",
    "regex": "excluded by filter",
    "duplicate_url": "duplicate URL",
    "depth_limit": "beyond crawl depth",
    "robots": "blocked by robots.txt",
    "blocked_private_address": "private address",
    "redirect_regex": "redirect excluded by filter",
    "empty_text": "no text extracted",
    "duplicate_content": "duplicate content",
    "fetch_failed": "fetch failed",
    "page_limit": "max pages reached",
    "invalid_start": "invalid start URL",
    "cancelled": "crawl cancelled",
}


def reason_label(reason: str) -> str:
    return REASON_LABELS.get(reason, reason)


@dataclass
class LinkOutcome:
    url: str
    reason: str


@dataclass
class PageLinkReport:
    url: str
    depth: int
    found: int = 0
    accepted: list[str] = field(default_factory=list)
    rejected: list[LinkOutcome] = field(default_factory=list)

    def reason_counts(self) -> Counter:
        return Counter(outcome.reason for outcome in self.rejected)


@dataclass
class CrawlReport:
    start_url: str = ""
    pages: list[PageLinkReport] = field(default_factory=list)
    skipped_pages: list[LinkOutcome] = field(default_factory=list)

    @property
    def total_found(self) -> int:
        return sum(page.found for page in self.pages)

    @property
    def total_queued(self) -> int:
        return sum(len(page.accepted) for page in self.pages)

    @property
    def total_skipped_links(self) -> int:
        return sum(len(page.rejected) for page in self.pages)

    def summary_lines(self, max_detail_lines: int = 300) -> list[str]:
        """Human readable report of the links that were found and followed."""
        lines = [
            (
                f"Crawl report for {self.start_url}: {len(self.pages)} page(s) parsed, "
                f"{self.total_found} link(s) found, {self.total_queued} queued"
            )
        ]

        for page in self.pages:
            lines.append(f"[{page.url}] found {page.found} link(s): queued {len(page.accepted)}")

        detail: list[str] = []
        for page in self.pages:
            for url in page.accepted:
                detail.append(f"  queued  {url}")

        if detail:
            lines.extend(detail[:max_detail_lines])
            remaining = len(detail) - max_detail_lines
            if remaining > 0:
                lines.append(f"  ... and {remaining} more link(s) not shown")

        return lines

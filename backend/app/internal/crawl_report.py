from collections import Counter
from dataclasses import dataclass, field

# Keep the report bounded so very large crawls cannot exhaust memory. Totals are
# tracked separately, so counts stay accurate even when stored samples are capped.
MAX_STORED_LINKS_PER_PAGE = 200
MAX_STORED_SKIPPED_PAGES = 1000

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
    accepted_total: int = 0
    rejected_total: int = 0

    def add_accepted(self, url: str) -> None:
        self.accepted_total += 1
        if len(self.accepted) < MAX_STORED_LINKS_PER_PAGE:
            self.accepted.append(url)

    def add_rejected(self, outcome: LinkOutcome) -> None:
        self.rejected_total += 1
        if len(self.rejected) < MAX_STORED_LINKS_PER_PAGE:
            self.rejected.append(outcome)

    def reason_counts(self) -> Counter:
        return Counter(outcome.reason for outcome in self.rejected)


@dataclass
class CrawlReport:
    start_url: str = ""
    pages: list[PageLinkReport] = field(default_factory=list)
    skipped_pages: list[LinkOutcome] = field(default_factory=list)

    def add_skipped(self, outcome: LinkOutcome) -> None:
        if len(self.skipped_pages) < MAX_STORED_SKIPPED_PAGES:
            self.skipped_pages.append(outcome)

    @property
    def total_found(self) -> int:
        return sum(page.found for page in self.pages)

    @property
    def total_queued(self) -> int:
        return sum(page.accepted_total for page in self.pages)

    @property
    def total_skipped_links(self) -> int:
        return sum(page.rejected_total for page in self.pages)

    def summary_lines(self, max_detail_lines: int = 300) -> list[str]:
        """Human readable report of the links that were found and followed."""
        lines = [
            (
                f"Crawl report for {self.start_url}: {len(self.pages)} page(s) parsed, "
                f"{self.total_found} link(s) found, {self.total_queued} queued"
            )
        ]

        for page in self.pages:
            lines.append(
                f"[{page.url}] found {page.found} link(s): queued {page.accepted_total}"
            )

        detail: list[str] = []
        for page in self.pages:
            for url in page.accepted:
                detail.append(f"  queued  {url}")

        if detail:
            lines.extend(detail[:max_detail_lines])
            shown = min(len(detail), max_detail_lines)
            remaining = self.total_queued - shown
            if remaining > 0:
                lines.append(f"  ... and {remaining} more link(s) not shown")

        return lines

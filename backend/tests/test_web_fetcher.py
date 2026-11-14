from unittest.mock import patch

from app.internal.crawl_options import CrawlOptions
from app.internal.web_fetcher import StaticFetcher, _response_kind, extract_pdf_page


def make_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return bytes(output)


def test_response_kind_detection():
    assert _response_kind("https://example.com/manual.pdf", "", b"%PDF-1.4") == "pdf"
    assert _response_kind("https://example.com/download?id=1", "application/pdf", b"%PDF-1.4") == "pdf"
    assert _response_kind("https://example.com/page", "text/html", b"<html></html>") == "html"
    assert _response_kind("https://example.com/manual.pdf", "text/html", b"<html></html>") == "html"
    assert _response_kind("https://example.com/page", "application/octet-stream", b"data") is None
    assert _response_kind("https://example.com/download", "application/pdf", b"not a pdf") is None
    assert _response_kind("https://example.com/download?id=1", "", b"%PDF-1.4") == "pdf"
    assert _response_kind("https://example.com/page", "", b"<html></html>") == "html"


def test_extract_pdf_page_extracts_text_and_title():
    extracted = extract_pdf_page(make_pdf("Hello PDF"), "https://example.com/files/manual.pdf")

    assert "Hello PDF" in extracted.text
    assert extracted.title == "manual.pdf"


class FakeResponse:
    def __init__(
        self,
        url,
        content_type,
        content,
        status_code=200,
        is_redirect=False,
        location=None,
    ):
        self.url = url
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        if location is not None:
            self.headers["location"] = location
        self.content = content
        self.has_redirect_location = is_redirect and location is not None

    def raise_for_status(self):
        pass

    @property
    def text(self):
        return self.content.decode("utf-8", "replace")


class FakeClient:
    def __init__(self, responses):
        self.responses = responses if isinstance(responses, dict) else {"*": responses}
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        if "*" in self.responses:
            return self.responses["*"]
        return self.responses[url]

    def close(self):
        pass


def test_static_fetcher_accepts_pdf_content():
    fetcher = StaticFetcher(CrawlOptions(allow_private_urls=True))
    fetcher._client = FakeClient(
        FakeResponse(
            "https://example.com/manual.pdf",
            "application/pdf",
            make_pdf("Hello PDF"),
        )
    )

    result = fetcher.fetch("https://example.com/manual.pdf")

    assert result is not None
    assert result.is_pdf is True
    assert result.content.startswith(b"%PDF")


def test_static_fetcher_rejects_non_html_non_pdf_content():
    fetcher = StaticFetcher(CrawlOptions(allow_private_urls=True))
    fetcher._client = FakeClient(
        FakeResponse("https://example.com/image.png", "image/png", b"\x89PNG")
    )

    assert fetcher.fetch("https://example.com/image.png") is None


def test_public_redirect_is_followed():
    start = FakeResponse(
        "https://example.com/start",
        "text/html",
        b"",
        status_code=302,
        is_redirect=True,
        location="/final",
    )
    final = FakeResponse(
        "https://example.com/final",
        "text/html",
        b"<html><body>ok</body></html>",
    )
    client = FakeClient({start.url: start, final.url: final})
    fetcher = StaticFetcher(CrawlOptions(allow_private_urls=True))
    fetcher._client = client

    result = fetcher.fetch("https://example.com/start")

    assert result is not None
    assert result.final_url == "https://example.com/final"
    assert client.calls == ["https://example.com/start", "https://example.com/final"]


def test_redirect_to_private_address_is_not_followed():
    start = FakeResponse(
        "https://example.com/start",
        "text/html",
        b"",
        status_code=302,
        is_redirect=True,
        location="http://127.0.0.1/secret",
    )
    client = FakeClient({start.url: start})
    fetcher = StaticFetcher(CrawlOptions(allow_private_urls=False))
    fetcher._client = client

    def guard(url, allow_private=False):
        if "127.0.0.1" in url:
            raise ValueError("private")

    with patch("app.internal.web_fetcher.ensure_url_allowed", side_effect=guard):
        assert fetcher.fetch("https://example.com/start") is None

    assert client.calls == ["https://example.com/start"]


def test_redirect_without_location_returns_none():
    start = FakeResponse(
        "https://example.com/start",
        "text/html",
        b"",
        status_code=302,
        is_redirect=True,
    )
    fetcher = StaticFetcher(CrawlOptions(allow_private_urls=True))
    fetcher._client = FakeClient({start.url: start})

    assert fetcher.fetch("https://example.com/start") is None

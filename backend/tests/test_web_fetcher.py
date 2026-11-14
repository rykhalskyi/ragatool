from app.internal.crawl_options import CrawlOptions
from app.internal.web_fetcher import StaticFetcher, _is_pdf, extract_pdf_page


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


def test_is_pdf_detection():
    assert _is_pdf("https://example.com/manual.pdf", "")
    assert _is_pdf("https://example.com/download?id=1", "application/pdf")
    assert not _is_pdf("https://example.com/page", "text/html")


def test_extract_pdf_page_extracts_text_and_title():
    extracted = extract_pdf_page(make_pdf("Hello PDF"), "https://example.com/files/manual.pdf")

    assert "Hello PDF" in extracted.text
    assert extracted.title == "manual.pdf"


class FakeResponse:
    def __init__(self, url, content_type, content):
        self.url = url
        self.status_code = 200
        self.headers = {"content-type": content_type}
        self.content = content

    def raise_for_status(self):
        pass

    @property
    def text(self):
        return self.content.decode("utf-8", "replace")


class FakeClient:
    def __init__(self, response):
        self.response = response

    def get(self, url):
        return self.response

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

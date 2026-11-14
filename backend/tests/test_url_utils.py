from app.internal.url_utils import (
    is_asset_url,
    is_http_url,
    normalize_url,
    registrable_domain,
    same_site,
)


def test_normalize_url_lowercases_and_strips_fragment_and_slash():
    assert normalize_url("HTTP://Example.COM/Path/#section") == "http://example.com/Path"


def test_normalize_url_sorts_query_parameters():
    assert normalize_url("https://example.com/page?b=2&a=1") == "https://example.com/page?a=1&b=2"


def test_normalize_url_drops_default_ports():
    assert normalize_url("http://example.com:80/page") == "http://example.com/page"
    assert normalize_url("https://example.com:443/page") == "https://example.com/page"


def test_http_url_detection():
    assert is_http_url("https://example.com")
    assert not is_http_url("mailto:user@example.com")
    assert not is_http_url("javascript:alert(1)")
    assert not is_http_url("file:///etc/passwd")


def test_asset_detection():
    assert is_asset_url("https://example.com/image.png")
    assert is_asset_url("https://example.com/app.js")
    assert is_asset_url("https://example.com/talk.mp4")
    assert is_asset_url("https://example.com/book.epub")
    assert not is_asset_url("https://example.com/manual.pdf")
    assert not is_asset_url("https://example.com/page")


def test_same_site_respects_subdomain_setting():
    start = "https://docs.example.com/start"
    assert same_site("https://docs.example.com/other", start)
    assert not same_site("https://api.example.com/other", start)
    assert same_site("https://api.example.com/other", start, allow_subdomains=True)
    assert not same_site("https://other.com/page", start, allow_subdomains=True)


def test_registrable_domain_handles_multi_level_suffixes():
    assert registrable_domain("docs.example.co.uk") == "example.co.uk"
    assert registrable_domain("docs.example.com") == "example.com"
    assert registrable_domain("localhost") == "localhost"

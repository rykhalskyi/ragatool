import ipaddress
import os
import socket
import threading
from typing import Optional
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ASSET_EXTENSIONS = {
    ".7z", ".aac", ".ai", ".avi", ".azw", ".azw3", ".bmp", ".css", ".csv",
    ".djvu", ".doc", ".docx", ".eot", ".epub", ".eps", ".flac", ".gif",
    ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".m3u8", ".m4a", ".m4v",
    ".map", ".mobi", ".mov", ".mp3", ".mp4", ".mpd", ".mpeg", ".ogg", ".ogv",
    ".opus", ".otf", ".png", ".ppt", ".pptx", ".ps", ".psd", ".rar",
    ".rss", ".svg", ".swf", ".tar", ".tgz", ".tif", ".tiff", ".ttf", ".wav",
    ".webm", ".webmanifest", ".webp", ".wmv", ".woff", ".woff2", ".xls",
    ".xlsx", ".xml", ".zip",
}

MULTI_LEVEL_SUFFIXES = {
    "ac.uk", "co.in", "co.jp", "co.nz", "co.uk", "co.za", "com.au", "com.br",
    "com.cn", "com.hk", "com.mx", "com.sg", "com.tr", "gov.uk", "org.uk",
}


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parsed.path or ""
    if path.endswith("/"):
        path = path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunsplit((scheme, netloc, path, query, ""))


def is_http_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme.lower() in ("http", "https") and bool(parsed.hostname)


def is_asset_url(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return os.path.splitext(path)[1] in ASSET_EXTENSIONS


def registrable_domain(host: str) -> str:
    host = (host or "").lower().strip(".")
    if not host or ":" in host:
        return host
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    suffix = ".".join(labels[-2:])
    if suffix in MULTI_LEVEL_SUFFIXES:
        return ".".join(labels[-3:])
    return suffix


def same_site(url: str, start_url: str, allow_subdomains: bool = False) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    start_host = (urlsplit(start_url).hostname or "").lower()
    if not host or not start_host:
        return False
    if host == start_host:
        return True
    if not allow_subdomains:
        return False
    return registrable_domain(host) == registrable_domain(start_host)


def ensure_url_allowed(url: str, allow_private: bool = False) -> None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    host = parsed.hostname
    if not host:
        raise ValueError("URL has no host")
    if allow_private:
        return

    try:
        addresses = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve host: {host}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"URL resolves to a non-public address: {host}")


class RobotsCache:
    def __init__(self, user_agent: str, timeout: float = 10.0):
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: dict[str, Optional[RobotFileParser]] = {}
        self._lock = threading.Lock()

    def can_fetch(self, url: str) -> bool:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            return True
        base = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        robots_url = urljoin(base + "/", "robots.txt")

        with self._lock:
            if base in self._cache:
                parser = self._cache[base]
            else:
                parser = self._load(robots_url)
                self._cache[base] = parser

        if parser is None:
            return True
        return parser.can_fetch(self.user_agent, url)

    def _load(self, robots_url: str) -> Optional[RobotFileParser]:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        request = Request(robots_url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read().decode("utf-8", "replace")
            parser.parse(content.splitlines())
            return parser
        except HTTPError as exc:
            if exc.code in (401, 403):
                parser.disallow_all = True
                return parser
            return None
        except Exception:
            return None

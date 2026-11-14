import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.internal.browser_renderer import BrowserRenderer
from app.internal.crawl_options import CrawlOptions

pytestmark = pytest.mark.skipif(
    os.environ.get("CRAWL_INTEGRATION") != "1",
    reason="set CRAWL_INTEGRATION=1 to run real Chromium tests",
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def test_real_chromium_renders_local_page(tmp_path):
    (tmp_path / "index.html").write_text(
        "<html><body><h1>Integration rendering works</h1></body></html>",
        encoding="utf-8",
    )
    handler = partial(QuietHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/"
        options = CrawlOptions(
            js_render_mode="always",
            render_wait_ms=0,
            allow_private_urls=True,
        )
        with BrowserRenderer(options) as renderer:
            result = renderer.render(url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert result is not None
    assert "Integration rendering works" in result.text

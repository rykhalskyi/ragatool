import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

def simple_crawl(start_url, max_depth=1):
    visited = set()
    queue = deque([(start_url, 0)])
    domain = urlparse(start_url).netloc

    results = []   # ← list of {url, text}

    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue

        visited.add(url)
        print(f"[Depth {depth}] {url}")

        # Fetch page
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text from the page
        text = soup.get_text(" ", strip=True)
        results.append({"url": url, "text": text})

        # If already at max depth, don't collect more links
        if depth == max_depth:
            continue

        # Extract and process internal links
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            parsed = urlparse(link)

            # Only follow links inside same domain
            if parsed.netloc == domain:
                link = link.split("#")[0]  # remove fragments
                if link not in visited:
                    queue.append((link, depth + 1))

    return results
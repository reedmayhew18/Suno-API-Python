"""
HTTP client wrapper using httpx for Suno API external calls.
"""
import httpx
from app.config import settings

# Default headers for Suno API requests
DEFAULT_HEADERS = {
    "Content-Type": "text/plain;charset=UTF-8",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Referer": "https://suno.com/",
    "Origin": "https://suno.com",
    "Accept": "*/*",
}

# Initialize HTTPX client
client = httpx.Client(
    timeout=settings.chat_timeout,
    headers=DEFAULT_HEADERS,
    proxies=settings.proxy or None,
)

def do_request(method: str, url: str, *, headers: dict = None, data: bytes = None, json: object = None) -> httpx.Response:
    """
    Send an HTTP request to the specified URL, merging default headers with provided ones.
    Raises httpx.HTTPError on network/HTTP issues.
    """
    merged_headers = DEFAULT_HEADERS.copy()
    if headers:
        merged_headers.update(headers)
    response = client.request(method, url, headers=merged_headers, content=data, json=json)
    response.raise_for_status()
    return response
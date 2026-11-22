import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Apple's CDN seems to answer uncached pages with 429 when the request has a non-browser User-Agent
session = requests.Session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

# Do 3 retries on errors we can recover from
retries = Retry(
    total=3,
    connect=1,
    backoff_factor=2,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
    retry_after_max=30,
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

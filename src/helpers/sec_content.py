"""
Shared fetching and parsing of Apple's security content page (support.apple.com/100100).
"""

import lxml.html

from helpers.session import session

URL = "https://support.apple.com/en-us/100100"
# The latest page contains items only 2024+, this one has ones from 2022 and 2023
URL_OLD = "https://support.apple.com/en-us/121012"


def request_sec_page(url: str = URL) -> str:
    response = session.get(url, timeout=60)
    # Fail on error (non 2xx) statuses
    response.raise_for_status()
    return response.text


def retrieve_page(html: str | None = None) -> list[list[lxml.html.HtmlElement]]:
    if html is None:
        html = request_sec_page()

    main_page = lxml.html.document_fromstring(html)

    table = main_page.xpath("//table/tbody")[0].findall("tr")
    all_release_rows = []

    for row in table[1:]:
        all_release_rows.append(list(row.getchildren()))

    return all_release_rows

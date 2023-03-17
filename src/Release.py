"""
Class and functions for organizing data for the individual release.

Input format is an lxml release row on the Apple Security Content page:
-----
[
    [
        "<a href="https://support.apple.com/en-us/HT213055">macOS Big Sur 11.6.3</a>",
        "macOS Big Sur",
        "26 Jan 2022"
    ]
]
-----

Return format:
-----
[
    Class Release (
        "name": "iOS and iPadOS 14.7",
        "emoji": "📱",
        "security_content_link": "https://support.apple.com/en-us/HT212623",
        "release_date": "26 Jan 2022",
        "num_of_bugs": 37,
        "num_of_zero_days": 3,
        "zero_days": {
            "CVE-2021-30761": "WebKit",
            "CVE-2021-30762": "WebKit",
            "CVE-2021-30713": "TCC"
        },
        "num_entries_added": 8,
        "num_entries_updated": 1
    )
]
-----
"""

import re

import lxml.html
import requests

import helpers.get_date as get_date


class Release:
    def __init__(self, release_row: list[lxml.html.HtmlElement]) -> None:
        self.__name: str = self.retrieve_name(release_row)
        self.__emoji: str = self.retrieve_emoji(self.__name)
        self.__security_content_link: str = self.retrieve_security_content_link(release_row)
        self.__release_date: str = release_row[2].text_content()

        if self.__security_content_link:
            try:
                sec_content_page_html = requests.get(self.__security_content_link, timeout=60).text

                sec_content_page = lxml.html.document_fromstring(sec_content_page_html).text_content()
                sec_content_page = (
                    sec_content_page_html.split("About Apple security updates", 1)[1]
                    .split("Published Date", 1)[0]
                    .replace("&nbsp;", " ")
                )
                sec_content_page = " ".join(sec_content_page.split())

                sec_content_page_html = sec_content_page_html.replace("\n", "").replace("&nbsp;", " ")

            except Exception as e:
                print(f"ERROR: security content parsing failed for\n{self.__name}\n" + str(e) + "\n")
                self.__security_content_link = ""
                sec_content_page_html = ""
                sec_content_page = ""
        else:
            sec_content_page_html = ""
            sec_content_page = ""

        self.__num_of_bugs: int = self.retrieve_num_of_bugs(release_row, sec_content_page)
        self.__zero_days: dict = self.retrieve_zero_days(sec_content_page_html)
        self.__num_of_zero_days: int = len(self.__zero_days)

        self.__num_entries_added: int = sec_content_page.count(f"added {get_date.format_two()}")
        self.__num_entries_updated: int = sec_content_page.count(f"updated {get_date.format_two()}")

    @staticmethod
    def retrieve_name(release_row: list) -> str:
        name = release_row[0].text_content()

        # for releases with "macOS Monterey 12.0.1 (Advisory includes security content of..."
        # and for "watchOS 9.0.2\nThis update has no published CVE entries."
        name = name.split("(Advisory", 1)[0].split("\n", 1)[0].strip()

        # "no details yet" releases might have this bracket alongside of their name
        name = name.split("(details available soon)", 1)[0].strip()

        if "iOS" in name and "iPadOS" in name:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            name = name.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        if "macOS" in name and "Update" in name:
            # for releases "macOS Big Sur 11.2.1, macOS Catalina 10.15.7 Supplemental Update,..."
            name = name.split(",", 1)[0].strip()
            name += " and older"

        return name

    @property
    def name(self) -> str:
        return self.__name

    @staticmethod
    def retrieve_emoji(release_name: str) -> str:
        """Set an emoji depending on the name of the release."""

        emoji_dict = {
            "iOS": "📱",
            "tvOS": "📺",
            "macOS": "💻",
            "watchOS": "⌚",
            "Safari": "🌐",
            "Security Update": "🖥️",
            "iPadOS": "📱",
            "Apple Music": "🎵",
            "Apple TV": "📺",
            "GarageBand": "🎵",
            "iCloud": "☁️",
            "iTunes": "🎵",
            "Shazam": "🎵",
        }

        for key, value in emoji_dict.items():
            if key in release_name:
                return value

        return "🛠️"

    @property
    def emoji(self) -> str:
        return self.__emoji

    @staticmethod
    def retrieve_security_content_link(release_row: list) -> str:
        tmp = release_row[0].xpath(".//a/@href")

        if tmp != []:
            return tmp[0]
        else:
            return ""

    @property
    def security_content_link(self) -> str:
        return self.__security_content_link

    @property
    def release_date(self) -> str:
        return self.__release_date

    @staticmethod
    def retrieve_num_of_bugs(release_row: list, sec_content_page: str) -> int:
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0].text_content():
            return -1
        else:
            return len(re.findall("(?i)CVE-[0-9]{4}-[0-9]+", sec_content_page))

    @property
    def num_of_bugs(self) -> int:
        return self.__num_of_bugs

    def get_format_num_of_bugs(self) -> str:
        if self.__num_of_bugs > 1:
            return f"{self.__num_of_bugs} bugs fixed"

        if self.__num_of_bugs == 1:
            return f"{self.__num_of_bugs} bug fixed"

        if self.__num_of_bugs == -1:
            return "no details yet"

        return "no bugs fixed"

    @staticmethod
    def retrieve_zero_days(sec_content_html: str) -> dict:
        """Check for "in the wild" or "actively exploited", indicating a fixed zero-day."""

        entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", sec_content_html)
        zero_days = {}

        for entry in entries:
            if "in the wild" in entry or "actively exploited" in entry:
                cve = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]+", entry)[0]
                zero_days[cve] = re.findall(r"(?i).+?(?=<\/strong>)", entry)[0]

        return zero_days

    @property
    def zero_days(self) -> dict:
        return self.__zero_days

    @property
    def num_of_zero_days(self) -> int:
        return self.__num_of_zero_days

    def get_format_num_of_zero_days(self) -> str:
        if self.__num_of_zero_days > 1:
            return f"{self.__num_of_zero_days} zero-days"

        if self.__num_of_zero_days == 1:
            return f"{self.__num_of_zero_days} zero-day"

        return "no zero-days"

    @property
    def num_entries_added(self) -> int:
        return self.__num_entries_added

    def get_format_num_entries_added(self) -> str:
        return f"{self.__num_entries_added} added"

    @property
    def num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        return f"{self.__num_entries_updated} updated"

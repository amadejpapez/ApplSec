"""
Class and functions for organizing data for the individual release.

Input format is a list of lxml.html.HtmlElement (release row on the initial Security page):
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
        "emoji": ":iphone:",
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
    def __init__(self, release_row: list) -> None:
        self.__name: str
        self.__emoji: str
        self.__security_content_link: str
        self.__release_date: str
        self.__num_of_bugs: int
        self.__num_of_zero_days: int
        self.__zero_days: dict
        self.__num_entries_added: int
        self.__num_entries_updated: int

        self.set_name(release_row)
        self.set_emoji()
        self.set_security_content_link(release_row)
        self.set_release_date(release_row)

        if self.__name == "tvOS 14.6":
            self.__security_content_link = ""

        if self.__security_content_link:
            sec_content_page_html = requests.get(self.__security_content_link, timeout=60).text

            sec_content_page = lxml.html.document_fromstring(sec_content_page_html).text_content()
            sec_content_page = (
                sec_content_page_html.split("About Apple security updates", 1)[1]
                .split("Additional recognition", 1)[0]
                .replace("&nbsp;", " ")
            )
            sec_content_page = " ".join(sec_content_page.split())

            sec_content_page_html = sec_content_page_html.replace("\n", "").replace("&nbsp;", " ")
        else:
            sec_content_page_html = ""
            sec_content_page = ""

        self.set_num_of_bugs(release_row, sec_content_page)
        self.set_zero_days(sec_content_page_html)
        self.set_num_entries_changed(sec_content_page)

    def set_name(self, release_row: list) -> None:
        self.__name = release_row[0].text_content()

        # for releases with "macOS Monterey 12.0.1 (Advisory includes security content of..."
        # and for "watchOS 9.0.2\nThis update has no published CVE entries."
        self.__name = self.__name.split("(Advisory", 1)[0].split("\n", 1)[0].strip()

        # "no details yet" releases might have this bracket alongside of their name
        self.__name = self.__name.split("(details available soon)", 1)[0].strip()

        if "iOS" in self.__name and "iPadOS" in self.__name:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            self.__name = self.__name.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        if "macOS" in self.__name and "Update" in self.__name:
            # for releases "macOS Big Sur 11.2.1, macOS Catalina 10.15.7 Supplemental Update,..."
            self.__name = self.__name.split(",", 1)[0].strip()
            self.__name += " and older"

    def get_name(self) -> str:
        return self.__name

    def set_security_content_link(self, release_row: list) -> None:
        tmp = release_row[0].xpath(".//a/@href")

        if tmp != []:
            self.__security_content_link = tmp[0]
        else:
            self.__security_content_link = ""

    def get_security_content_link(self) -> str:
        return self.__security_content_link

    def set_release_date(self, release_row: list) -> None:
        self.__release_date = release_row[2].text_content()

    def get_release_date(self) -> str:
        return self.__release_date

    def set_emoji(self) -> None:
        """Set an emoji depending on the title."""

        emoji_dict = {
            "Apple Music": ":musical_note:",
            "Apple TV": ":tv:",
            "GarageBand": ":musical_note:",
            "iCloud": ":cloud:",
            "iOS": ":iphone:",
            "iPadOS": ":iphone:",
            "iTunes": ":musical_note:",
            "macOS": ":computer:",
            "Safari": ":globe_with_meridians:",
            "Security Update": ":computer:",
            "Shazam": ":musical_note:",
            "tvOS": ":tv:",
            "watchOS": ":watch:",
        }

        for key, value in emoji_dict.items():
            if key in self.__name:
                self.__emoji = value
                return

        self.__emoji = ":hammer_and_wrench:"

    def get_emoji(self) -> str:
        return self.__emoji

    def set_zero_days(self, sec_content_html: str) -> None:
        """Check for "in the wild" or "actively exploited", indicating a fixed zero-day."""

        entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", sec_content_html)
        zero_days = {}

        for entry in entries:
            if "in the wild" in entry or "actively exploited" in entry:
                cve = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]+", entry)[0]
                zero_days[cve] = re.findall(r"(?i).+?(?=<\/strong>)", entry)[0]

        self.__num_of_zero_days = len(zero_days)
        self.__zero_days = zero_days

    def get_num_of_zero_days(self) -> int:
        return self.__num_of_zero_days

    def get_format_num_of_zero_days(self) -> str:
        if self.__num_of_zero_days > 1:
            return f"{self.__num_of_zero_days} zero-days"

        if self.__num_of_zero_days == 1:
            return f"{self.__num_of_zero_days} zero-day"

        return "no zero-days"

    def get_zero_days(self) -> dict:
        return self.__zero_days

    def set_num_of_bugs(self, release_row: list, sec_content_page: str) -> None:
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0].text_content():
            self.__num_of_bugs = -1
        else:
            self.__num_of_bugs = len(re.findall("(?i)CVE-[0-9]{4}-[0-9]+", sec_content_page))

    def get_num_of_bugs(self) -> int:
        return self.__num_of_bugs

    def get_format_num_of_bugs(self) -> str:
        if self.__num_of_bugs > 1:
            return f"{self.__num_of_bugs} bugs fixed"

        if self.__num_of_bugs == 1:
            return f"{self.__num_of_bugs} bug fixed"

        if self.__num_of_bugs == -1:
            return "no details yet"

        return "no bugs fixed"

    def set_num_entries_changed(self, sec_content_page: str) -> None:
        """
        Return if any entries were added or updated.
        Post is made at the start of each day for any changes made on the previous day.
        """

        date_format_two = get_date.format_two()

        self.__num_entries_added = len(re.findall(f"added {date_format_two}", sec_content_page))
        self.__num_entries_updated = len(re.findall(f"updated {date_format_two}", sec_content_page))

    def get_num_entries_added(self) -> int:
        return self.__num_entries_added

    def get_format_num_entries_added(self) -> str:
        return f"{self.__num_entries_added} added"

    def get_num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        return f"{self.__num_entries_updated} updated"

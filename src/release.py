"""
Example:

Class Release (
    "name": "iOS and iPadOS 16.5",
    "emoji": "📱",
    "release_notes_link": "https://developer.apple.com/news/releases/?id=05182023g",
    "security_content_link": "https://support.apple.com/en-us/HT212623",
    "zero_days": {
        "CVE-2023-32409": "WebKit",
        "CVE-2023-28204": "WebKit",
        "CVE-2023-32373": "WebKit"
    },
    "release_date": "18 May 2023",
    "num_of_bugs": 39,
    "num_of_zero_days": 3,
    "num_entries_added": 0,
    "num_entries_updated": 1
)
"""

from __future__ import annotations

import re

import lxml.etree
import lxml.html
import requests

import helpers.get_date as get_date


class Release:
    def __init__(
        self,
        name: str,
        emoji: str,
        release_notes_link: str,
        security_content_link: str,
        release_date: str,
        zero_days: dict[str, str],
        num_of_bugs: int,
        num_of_zero_days: int,
        num_entries_added: int,
        num_entries_updated: int,
    ):
        self.name = name
        self.emoji = emoji
        self.release_notes_link = release_notes_link
        self.security_content_link = security_content_link
        self.release_date = release_date
        self.zero_days = zero_days
        self.num_of_bugs = num_of_bugs
        self.num_of_zero_days = num_of_zero_days
        self.num_entries_added = num_entries_added
        self.num_entries_updated = num_entries_updated

    def get_format_num_of_bugs(self) -> str:
        if self.num_of_bugs > 1:
            return f"{self.num_of_bugs} bugs fixed"

        if self.num_of_bugs == 1:
            return f"{self.num_of_bugs} bug fixed"

        if self.num_of_bugs == -1:
            return "no details yet"

        return "no CVE entries"

    def get_format_num_of_zero_days(self) -> str:
        if self.num_of_zero_days > 1:
            return f"{self.num_of_zero_days} zero-days"

        if self.num_of_zero_days == 1:
            return f"{self.num_of_zero_days} zero-day"

        return "no zero-days"

    def get_format_num_entries_added(self) -> str:
        return f"{self.num_entries_added} added"

    def get_format_num_entries_updated(self) -> str:
        return f"{self.num_entries_updated} updated"

    @staticmethod
    def parse_from_table(row: list[lxml.html.HtmlElement]) -> Release:
        """
        Input format is the release row from the Apple Security Content page.
        All 3 elements are of type lxml.html.HtmlElement. This is an example of their contents:
        -----
        [
            "<a href="https://support.apple.com/en-us/HT213055">macOS Big Sur 11.6.3</a>",
            "macOS Big Sur",
            "26 Jan 2022"
        ]
        -----
        """

        name = Release.parse_name(row)
        security_content_link = Release.parse_security_content_link(row)

        if security_content_link:
            try:
                sec_content_page_html = requests.get(security_content_link, timeout=60).text

                sec_content_page = lxml.html.document_fromstring(sec_content_page_html).text_content()
                sec_content_page = (
                    sec_content_page_html.split("About Apple security updates", 1)[1]
                    .split("Published Date", 1)[0]
                    .replace("&nbsp;", " ")
                )
                sec_content_page = " ".join(sec_content_page.split())

                sec_content_page_html = sec_content_page_html.replace("\n", "").replace("&nbsp;", " ")

            except Exception as e:
                print(f"ERROR: security content parsing failed for\n{name}\n" + str(e) + "\n")
                security_content_link = ""
                sec_content_page_html = ""
                sec_content_page = ""
        else:
            sec_content_page_html = ""
            sec_content_page = ""

        zero_days_tmp = Release.parse_zero_days(sec_content_page_html)

        return Release(
            name,
            Release.parse_emoji(name),
            "",
            security_content_link,
            row[2].text_content(),
            zero_days_tmp,
            Release.parse_num_of_bugs(row, sec_content_page),
            len(zero_days_tmp),
            sec_content_page.count(f"added {get_date.format_two()}"),
            sec_content_page.count(f"updated {get_date.format_two()}"),
        )

    @staticmethod
    def parse_name(release_row: list[lxml.html.HtmlElement]) -> str:
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

    @staticmethod
    def parse_emoji(release_name: str) -> str:
        """Set an emoji depending on the name of the release."""

        emoji_dict = {
            "Apple Music": "🎵",
            "Apple TV": "📺",
            "GarageBand": "🎵",
            "iCloud": "☁️",
            "iOS": "📱",
            "iPadOS": "📱",
            "iTunes": "🎵",
            "macOS": "💻",
            "Safari": "🌐",
            "Security Update": "🖥️",
            "Shazam": "🎵",
            "tvOS": "📺",
            "watchOS": "⌚",
            "Xcode": "🔨",
        }

        for key, value in emoji_dict.items():
            if key in release_name:
                return value

        return "🛠️"

    @staticmethod
    def parse_security_content_link(release_row: list[lxml.html.HtmlElement]) -> str:
        tmp = release_row[0].xpath(".//a/@href")

        if tmp != []:
            return tmp[0]
        else:
            return ""

    @staticmethod
    def parse_num_of_bugs(release_row: list[lxml.html.HtmlElement], sec_content_page: str) -> int:
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0].text_content():
            return -1
        else:
            return len(re.findall("(?i)CVE-[0-9]{4}-[0-9]+", sec_content_page))

    @staticmethod
    def parse_zero_days(sec_content_html: str) -> dict[str, str]:
        """Check for "in the wild" or "actively exploited", indicating a fixed zero-day."""
        zero_days: dict[str, str] = {}

        if "actively exploited" not in sec_content_html:
            if "in the wild" not in sec_content_html:
                # if there isn't any zero days, end early
                return zero_days

        entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", sec_content_html)

        for entry in entries:
            if "in the wild" in entry or "actively exploited" in entry:
                cve = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]+", entry)[0]
                zero_days[cve] = re.findall(r"(?i).+?(?=<\/strong>)", entry)[0]

        return zero_days

    @staticmethod
    def from_rss_release(xml_item: lxml.etree._Element) -> Release:
        """
        Input format is of type lxml.etree._Element from Apple Releases page.
        Example item from Apple Releases RSS feed:
        -----
        <item xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
            <title>iPadOS 15.7.3 (19H307)</title>
            <link>https://developer.apple.com/news/releases/?id=01232023a</link>
            <guid>https://developer.apple.com/news/releases/?id=01232023a</guid>
            <description>View downloads</description>
            <pubDate>Mon, 23 Jan 2023 09:00:00 PST</pubDate>
            <content:encoded>&lt;p&gt;&lt;a href=/download class=more&gt;View downloads&lt;/a&gt;&lt;/p&gt;</content:encoded>
        </item>
        -----
        """

        name = xml_item.xpath("title")[0].text

        return Release(name, Release.parse_emoji(name), xml_item.xpath("link")[0].text, "", "", {}, 0, 0, 0, 0)

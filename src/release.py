"""
Example:

Class Release (
    "name": "iOS and iPadOS 16.5",
    "emoji": "📱",
    "release_notes_link": "https://developer.apple.com/news/releases/?id=05182023g",
    "security_content_link": "https://support.apple.com/kb/HT212623",
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
            "<a href="https://support.apple.com/kb/HT213055">macOS Big Sur 11.6.3</a>",
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

                sec_content_page = sec_content_page_html.replace("&nbsp;", " ")
                sec_content_page = " ".join(sec_content_page.split())

            except Exception as e:
                print(f"ERROR: security content parsing failed for\n{name}\n" + str(e) + "\n")
                security_content_link = ""
                sec_content_page = ""
        else:
            sec_content_page = ""

        zero_days_tmp = Release.parse_zero_days(sec_content_page)

        return Release(
            name=name,
            emoji=Release.parse_emoji(name),
            release_notes_link="",
            security_content_link=security_content_link,
            release_date=Release.parse_release_date(row),
            zero_days=zero_days_tmp,
            num_of_bugs=Release.parse_num_of_bugs(row, sec_content_page),
            num_of_zero_days=len(zero_days_tmp),
            num_entries_added=sec_content_page.count(f"added {get_date.format_two()}"),
            num_entries_updated=sec_content_page.count(f"updated {get_date.format_two()}"),
        )

    @staticmethod
    def parse_name(release_row: list[lxml.html.HtmlElement]) -> str:
        name = release_row[0].text_content().replace("\xa0", " ")

        # handle "macOS Monterey 12.0.1 (Advisory includes security content of..."
        name = name.split("(Advisory", 1)[0]

        # handle "watchOS 9.0.2\nThis update has no published CVE entries."
        name = name.replace("This update has no published CVE entries.", "")

        name = name.replace("\n", "").strip()

        # "no details yet" releases might have this bracket alongside of their name
        name = re.sub(r"(?i)\(?details (available|coming) soon\.?\)?", "", name).strip()

        # "iOS 15.3 and iPadOS 15.3" -> "iOS and iPadOS 15.3"
        if "iOS" in name and "iPadOS" in name:
            ver = re.findall(r"iOS (.+?) (?:and|&) iPadOS", name)[0]
            if re.findall(rf"iOS {re.escape(ver)} (?:and|&) iPadOS {re.escape(ver)}", name):
                name = name.replace(re.findall(rf"iOS {re.escape(ver)} (?:and|&)", name)[0], "iOS and")

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
            "visionOS": "🥽",
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
            if tmp[0].startswith("/"):
                return "https://support.apple.com" + tmp[0]

            # some releases are listed with http, upgrade them
            return tmp[0].replace("http:", "https:")
        else:
            return ""

    @staticmethod
    def parse_release_date(release_row: list[lxml.html.HtmlElement]) -> str:
        release_date = release_row[2].text_content()

        return release_date.replace("\n", "").strip()

    @staticmethod
    def parse_num_of_bugs(release_row: list[lxml.html.HtmlElement], sec_content_page: str) -> int:
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0].text_content():
            return -1
        elif sec_content_page == "":
            return 0
        else:
            return len(re.findall("(?i)CVE-[0-9]{4}-[0-9]+", sec_content_page))

    @staticmethod
    def parse_zero_days(sec_content_html: str) -> dict[str, str]:
        """Check for "in the wild" or "actively exploited", indicating a fixed zero-day."""
        zero_days: dict[str, str] = {}

        if sec_content_html == "":
            return zero_days

        if (
            "in the wild" not in sec_content_html
            and "actively exploited" not in sec_content_html
            and "may have been exploited" not in sec_content_html
        ):
            # if there isn't any zero days, end early
            return zero_days

        sec_content_html = sec_content_html.replace("\n", " ")

        entries = Release.get_html_entries(sec_content_html)

        for entry in entries:
            if (
                "in the wild" in entry
                or "actively exploited" in entry
                or "may have been exploited" in entry
            ):
                name = Release.get_html_entry_title(entry)
                cves = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]+", entry)
                for cve in cves:
                    zero_days[cve] = name

        return zero_days

    @staticmethod
    def get_html_entries(sec_content_html: str) -> list[str]:
        sec_content_html = sec_content_html.split("Additional recognition", 1)[0]
        sec_content_html = sec_content_html.replace("\n", " ")

        entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|</div>)", sec_content_html)
        entries += re.findall(r"(?i)(?<=<b>).*?(?=<b>|<h2)", sec_content_html)
        entries += re.findall(r"(?i)(?<=<h3 class=\"gb-header\">).*?(?=<h3|<h2)", sec_content_html)

        return entries

    @staticmethod
    def get_html_entry_title(entry: str) -> str:
        return re.findall(r"(?i).+?(?=</strong>|</b>|</h3>)", entry)[0]

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

import datetime
import re

import requests


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

        if self.__security_content_link:
            sec_content_html = requests.get(self.__security_content_link).text
            sec_content_html = sec_content_html.replace("\n", "").replace("&nbsp;", " ")
        else:
            sec_content_html = ""

        self.set_num_of_bugs(release_row, sec_content_html)
        self.set_zero_days(sec_content_html)
        self.set_num_entries_changed(sec_content_html)

    def set_name(self, release_row: list) -> None:
        self.__name = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release_row[0])[0]
        # for releases like "macOS Monterey 12.0.1 (Advisory includes security content of..."
        self.__name = self.__name.split("(Advisory", 1)[0].strip()

        if "iOS" in self.__name and "iPadOS" in self.__name:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            self.__name = (
                self.__name.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")
            )

        if "macOS" in self.__name and "Update" in self.__name:
            # for releases "macOS Big Sur 11.2.1, macOS Catalina 10.15.7 Supplemental Update,..."
            self.__name = self.__name.split(",", 1)[0].strip()
            self.__name += " and older"

    def get_name(self) -> str:
        return self.__name

    def set_security_content_link(self, release_row: list) -> None:
        if "href" in release_row[0]:
            self.__security_content_link = re.findall(
                r'(?i)href="(.+?)"', release_row[0]
            )[0]
        else:
            self.__security_content_link = ""

    def get_security_content_link(self) -> str:
        return self.__security_content_link

    def set_release_date(self, release_row: list) -> None:
        self.__release_date = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release_row[2])[0]

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

        entries = re.findall(
            r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", sec_content_html
        )
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

    def set_num_of_bugs(self, release_row: list, sec_content_html: str) -> None:
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0]:
            self.__num_of_bugs = -1
        else:
            self.__num_of_bugs = len(
                re.findall("(?i)CVE-[0-9]{4}-[0-9]+", sec_content_html)
            )

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

    def set_num_entries_changed(self, sec_content_html: str) -> None:
        """
        Return if any entries were added or updated.
        Tweet is made at the start of each day for any changes made on the previous day.

        Date format: January 2, 2022
        """

        previous_day = datetime.date.today() - datetime.timedelta(1)
        date_format_two = (
            f"{previous_day.strftime('%B')} {previous_day.day}, {previous_day.year}"
        )

        self.__num_entries_added = len(
            re.findall(f"added {date_format_two}", sec_content_html)
        )
        self.__num_entries_updated = len(
            re.findall(f"updated {date_format_two}", sec_content_html)
        )

    def get_num_entries_added(self) -> int:
        return self.__num_entries_added

    def get_format_num_entries_added(self) -> str:
        return f"{self.__num_entries_added} added"

    def get_num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        return f"{self.__num_entries_updated} updated"

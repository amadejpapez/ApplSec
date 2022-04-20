import datetime
import re

import requests


class Release:
    def __init__(self, release_row: list):
        self.__name: str
        self.__emoji: int
        self.__release_notes_link: str
        self.__release_date: str
        self.__num_of_bugs: int
        self.__num_of_zero_days: int
        self.__zero_days: dict
        self.__num_entries_added: int
        self.__num_entries_updated: int

        self.set_name(release_row)
        self.set_emoji()
        self.set_release_notes_link(release_row)
        self.set_release_date(release_row)

        if self.__release_notes_link is not None:
            release_notes = requests.get(self.__release_notes_link).text
            release_notes = release_notes.replace("\n", "").replace("&nbsp;", " ")
        else:
            release_notes = ""

        self.set_num_of_bugs(release_row, release_notes)
        self.set_zero_days(release_notes)
        self.set_num_entries_changed(release_notes)

    def set_name(self, release_row: list):
        self.__name = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release_row[0])[0]

        if "iOS" in self.__name and "iPadOS" in self.__name:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            self.__name = self.__name.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

    def get_name(self) -> str:
        return self.__name

    def set_release_notes_link(self, release_row: list):
        if "href" in release_row[0]:
            self.__release_notes_link = re.findall(r'(?i)href="(.+?)"', release_row[0])[0]
        else:
            self.__release_notes_link = None

    def get_release_notes_link(self) -> str:
        return self.__release_notes_link

    def set_release_date(self, release_row: list):
        self.__release_date = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release_row[2])[0]

    def get_release_date(self) -> str:
        return self.__release_date

    def set_emoji(self):
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
            "watchOS": ":watch:"
        }

        for key, value in emoji_dict.items():
            if key in self.__name:
                self.__emoji = value
                return

        self.__emoji = ":hammer_and_wrench:"

    def get_emoji(self) -> str:
        return self.__emoji

    def set_zero_days(self, release_notes: str):
        """Check for "in the wild" or "actively exploited", indicating a fixed zero-day."""

        entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", release_notes)
        zero_days = {}

        for entry in entries:
            if "in the wild" in entry or "actively exploited" in entry:
                cve = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]{4,5}", entry)[0]
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

    def get_zero_days(self) -> dict:
        return self.__zero_days

    def set_num_of_bugs(self, release_row: list, release_notes: dict):
        """Return a number of CVEs fixed."""

        if "soon" in release_row[0]:
            self.__num_of_bugs = -1
        else:
            self.__num_of_bugs = len(re.findall("(?i)CVE-[0-9]{4}-[0-9]{4,5}", release_notes))

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

    def set_num_entries_changed(self, release_notes: str):
        """
        Return if any entries were added or updated.
        Tweet is made at the start of each day for any changes made on the previous day.

        Date format: January 2, 2022
        """

        previous_day = datetime.date.today() - datetime.timedelta(1)
        date_format_two = (
            f"{previous_day.strftime('%B')} {previous_day.day}, {previous_day.year}"
        )

        self.__num_entries_added = len(re.findall(f"added {date_format_two}", release_notes))
        self.__num_entries_updated = len(re.findall(f"updated {date_format_two}", release_notes))

    def get_num_entries_added(self) -> int:
        return self.__num_entries_added

    def get_format_num_entries_added(self) -> str:
        if self.__num_entries_added > 1:
            return f"{self.__num_entries_added} entries added"

        if self.__num_entries_added == 1:
            return "1 entry added"

        return None

    def get_num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        if self.__num_entries_updated > 1:
            return f"{self.__num_entries_updated} entries updated"

        if self.__num_entries_added == 1:
            return "1 entry updated"

        return None

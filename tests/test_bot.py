import copy
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import format_tweet
from gather_info import determine_latest_versions, get_info

LOC = os.path.abspath(os.path.join(__file__, "../examples.json"))

with open(LOC, "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

stored_data = copy.deepcopy(example_file["stored_data"])


class ReleaseTest:
    def __init__(self, release_info: dict):
        self.__name: str = release_info["name"]
        self.__emoji: str = release_info["emoji"]
        self.__security_content_link: str = release_info["security_content_link"]
        self.__release_date: str = release_info["release_date"]
        self.__num_of_bugs: int = release_info["num_of_bugs"]
        self.__num_of_zero_days: int = release_info["num_of_zero_days"]
        self.__zero_days: dict = release_info["zero_days"]
        self.__num_entries_added: int = release_info["num_entries_added"]
        self.__num_entries_updated: int = release_info["num_entries_updated"]

    def get_name(self) -> str:
        return self.__name

    def get_security_content_link(self) -> str:
        return self.__security_content_link

    def set_release_date(self, release_row: list):
        self.__release_date = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release_row[2])[0]

    def get_release_date(self) -> str:
        return self.__release_date

    def get_emoji(self) -> str:
        return self.__emoji

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

    def get_num_entries_added(self) -> int:
        return self.__num_entries_added

    def get_format_num_entries_added(self) -> str:
        if self.__num_entries_added > 1:
            return f"{self.__num_entries_added} entries added"

        if self.__num_entries_added == 1:
            return "1 entry added"

        return ""

    def get_num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        if self.__num_entries_updated > 1:
            return f"{self.__num_entries_updated} entries updated"

        if self.__num_entries_updated == 1:
            return "1 entry updated"

        return ""

    def print_all_data(self):
        print(
            f'"{self.__name}":' + " { \n"
            f'    "name": "{self.__name}",\n'
            f'    "emoji": "{self.__emoji}",\n'
            f'    "security_content_link": "{self.__security_content_link}",\n'
            f'    "release_date": "{self.__release_date}",\n'
            f'    "num_of_bugs": {self.__num_of_bugs},\n'
            f'    "num_of_zero_days": {self.__num_of_zero_days},\n'
            f'    "zero_days": {self.__zero_days},\n'
            f'    "num_entries_added": {self.__num_entries_added},\n'
            f'    "num_entries_updated": {self.__num_entries_updated}\n'
            "},\n"
        )


def compare(releases_info, example):
    for release, (_, expected) in zip(releases_info, example.items()):
        assert release.get_name() == expected["name"]
        assert release.get_emoji() == expected["emoji"], release.get_name()
        assert release.get_security_content_link() == expected["security_content_link"], release.get_name()
        assert release.get_release_date() == expected["release_date"], release.get_name()
        assert release.get_num_of_bugs() == expected["num_of_bugs"], release.get_name()
        assert release.get_num_of_zero_days() == expected["num_of_zero_days"], release.get_name()
        assert release.get_zero_days() == expected["zero_days"], release.get_name()
        assert release.get_num_entries_added() == expected["num_entries_added"], release.get_name()
        assert release.get_num_entries_updated() == expected["num_entries_updated"], release.get_name()


def test_get_info():
    """
    Tests get_info() on a big number of releases.
    Checks number of returned releases and if titles match.
    """

    releases = example_file["last_one_year_table"]
    releases_info = get_info(releases)

    # check if get_info() returned the correct number of releases
    assert len(releases) == len(list(releases_info))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, value in enumerate(releases):
        title = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", value[0])[0]
        # for releases like "macOS Monterey 12.0.1 (Advisory includes security content of..."
        title = title.split("(Advisory", 1)[0].strip()

        if "iOS" in title and "iPadOS" in title:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            title = title.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        if "macOS" in title and "Update" in title:
            # for releases "macOS Big Sur 11.2.1, macOS Catalina 10.15.7 Supplemental Update,..."
            title = title.split(",", 1)[0].strip()
            title += " and older"

        assert title == releases_info[i].get_name()


def test_get_info_2():
    releases_info = get_info(example_file["get_info_table"])

    compare(releases_info, example_file["get_info_info"])

    tweet_format = format_tweet.new_updates(
        list(releases_info), copy.deepcopy(example_file["stored_data"])
    )

    assert tweet_format == example_file["get_info_tweet"]


def test_new_updates():
    releases_info = get_info(example_file["new_releases_table"])

    compare(releases_info, example_file["new_releases_info"])

    tweet_format = format_tweet.new_updates(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["new_releases_tweet"]


def test_new_updates_only_one():
    releases_info = get_info(example_file["new_releases_one_table"])

    tweet_format = format_tweet.new_updates(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["new_releases_one_tweet"]


def test_ios_modules():
    releases_info = get_info(example_file["ios_modules_table"])

    compare(releases_info, example_file["ios_modules_info"])

    tweet_format = format_tweet.top_ios_modules(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["ios_modules_tweet"]


def test_entry_changes():
    releases_info = []
    for _, value in example_file["entry_changes_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.entry_changes(list(releases_info))

    assert tweet_format == example_file["entry_changes_tweet"]


def test_security_content_soon():
    releases_info = []
    for _, value in example_file["security_content_soon_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.security_content_available(
        list(releases_info), stored_data
    )

    assert tweet_format == []
    assert (
        stored_data["details_available_soon"]
        == example_file["security_content_soon_file"]
    )


def test_security_content_available():
    releases_info = []
    for _, value in example_file["security_content_available_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.security_content_available(
        list(releases_info), stored_data
    )

    assert tweet_format == example_file["security_content_available_tweet"]
    assert stored_data["details_available_soon"] == []


def test_yearly_report():
    latest_versions = determine_latest_versions(
        example_file["last_one_year_table"][:50]
    )

    for system, version in latest_versions.items():
        tweet_format = format_tweet.yearly_report(
            example_file["last_one_year_table"],
            system,
            version[0],
            copy.deepcopy(stored_data),
        )

        assert tweet_format[0] == example_file["yearly_report_" + system + "_tweet"][0]


def test_zero_day():
    releases_info = get_info(example_file["zero_day_releases_table"])

    compare(releases_info, example_file["zero_day_releases_info"])

    tweet_format = format_tweet.zero_days(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["zero_day_releases_tweet"]


def test_zero_day_new_old():
    releases_info = []
    for _, value in example_file["zero_day_releases_new_old_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.zero_days(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["zero_day_releases_new_old_tweet"]


def test_zero_day_new():
    releases_info = []
    for _, value in example_file["zero_day_releases_new_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.zero_days(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["zero_day_releases_new_tweet"]


def test_zero_day_old():
    releases_info = []
    for _, value in example_file["zero_day_releases_old_info"].items():
        releases_info.append(ReleaseTest(value))

    tweet_format = format_tweet.zero_days(
        list(releases_info), copy.deepcopy(stored_data)
    )

    assert tweet_format == example_file["zero_day_releases_old_tweet"]

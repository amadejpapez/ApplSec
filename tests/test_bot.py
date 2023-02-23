import copy
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import lxml.html

import helpers.get_version_info as get_version_info
import main
import post_format
from Release import Release


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
        return f"{self.__num_entries_added} added"

    def get_num_entries_updated(self) -> int:
        return self.__num_entries_updated

    def get_format_num_entries_updated(self) -> str:
        return f"{self.__num_entries_updated} updated"

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


def compare(release_obj, example):
    for release, (_, expected) in zip(release_obj, example.items()):
        assert release.get_name() == expected["name"]
        assert release.get_emoji() == expected["emoji"], release.get_name()
        assert release.get_security_content_link() == expected["security_content_link"], release.get_name()
        assert release.get_release_date() == expected["release_date"], release.get_name()
        assert release.get_num_of_bugs() == expected["num_of_bugs"], release.get_name()
        assert release.get_num_of_zero_days() == expected["num_of_zero_days"], release.get_name()
        assert release.get_zero_days() == expected["zero_days"], release.get_name()
        assert release.get_num_entries_added() == expected["num_entries_added"], release.get_name()
        assert release.get_num_entries_updated() == expected["num_entries_updated"], release.get_name()


def convert_to_lxml_class(release_rows: list) -> list:
    releases_tmp = []

    for row in release_rows:
        tmp = []
        for x in row:
            tmp.append(lxml.html.document_fromstring(x))

        releases_tmp.append(tmp)

    return releases_tmp


def convert_to_release_class(release_rows: list) -> list:
    releases_obj = []

    for row in convert_to_lxml_class(release_rows):
        releases_obj.append(Release(row))

    return releases_obj


def convert_to_release_test_class(release_info: dict) -> list:
    releases_class = []

    for _, value in release_info.items():
        releases_class.append(ReleaseTest(value))

    return releases_class


LOC = os.path.abspath(os.path.join(__file__, "../examples.json"))

with open(LOC, "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

stored_data = copy.deepcopy(example_file["stored_data"])

latest_versions = get_version_info.latest(
    convert_to_lxml_class(example_file["last_one_year_table"][:50])
)

coll = {
    "new_releases": [],
    "ios_release": [],
    "changed_releases": [],
    "sec_content_available": [],
    "zero_day_releases": [],
    "yearly_report": [],
}


def test_release_class():
    """
    Tests Release class on a big number of releases.
    Checks number of returned releases and if titles match.
    """

    releases = example_file["last_one_year_table"]
    releases_obj = convert_to_release_class(releases)

    # check if Release returned the correct number of releases
    assert len(releases) == len(list(releases_obj))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, value in enumerate(releases):
        title = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", value[0])[0]
        # for releases like "macOS Monterey 12.0.1 (Advisory includes security content of..."
        title = title.split("(Advisory", 1)[0].strip().split("\n", 1)[0].strip()

        if "iOS" in title and "iPadOS" in title:
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            title = title.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        if "macOS" in title and "Update" in title:
            # for releases "macOS Big Sur 11.2.1, macOS Catalina 10.15.7 Supplemental Update,..."
            title = title.split(",", 1)[0].strip()
            title += " and older"

        assert title == releases_obj[i].get_name()


def test_release_class_2():
    releases_obj = convert_to_release_class(example_file["release_rows_table"])

    compare(releases_obj, example_file["release_rows_info"])

    coll["new_releases"] = []

    main.check_new_releases(coll, copy.deepcopy(stored_data), latest_versions, releases_obj)

    post = post_format.new_updates(coll["new_releases"])

    assert post == example_file["release_rows_post"]

def test_new_updates():
    releases_obj = convert_to_release_class(example_file["new_releases_table"])

    compare(releases_obj, example_file["new_releases_info"])

    coll["new_releases"] = []

    main.check_new_releases(coll, copy.deepcopy(stored_data), latest_versions, releases_obj)

    post = post_format.new_updates(coll["new_releases"])

    assert post == example_file["new_releases_post"]


def test_new_updates_only_one():
    releases_obj = convert_to_release_class(example_file["new_releases_one_table"])

    coll["new_releases"] = []

    main.check_new_releases(coll, copy.deepcopy(stored_data), latest_versions, releases_obj)

    post = post_format.new_updates(coll["new_releases"])

    assert post == example_file["new_releases_one_post"]


def test_ios_modules():
    releases_obj = convert_to_release_class(example_file["ios_modules_table"])

    compare(releases_obj, example_file["ios_modules_info"])

    lat_ios_ver = str(latest_versions["iOS"][0])
    coll["ios_release"] = []

    for release in releases_obj:
        main.check_latest_ios_release(coll, copy.deepcopy(stored_data), release, lat_ios_ver)

    post = post_format.top_ios_modules(coll["ios_release"])

    assert post == example_file["ios_modules_post"]


def test_entry_changes():
    releases_obj = convert_to_release_test_class(example_file["entry_changes_info"])

    post = post_format.entry_changes(releases_obj)

    assert post == example_file["entry_changes_post"]


def test_security_content_soon():
    releases_obj = convert_to_release_test_class(example_file["security_content_soon_info"])

    for release in releases_obj:
        main.save_sec_content_no_details_yet(stored_data, release)

    assert (
        stored_data["details_available_soon"]
        == example_file["security_content_soon_file"]
    )

    # test if result is the same when same data comes in the next time
    releases_obj = convert_to_release_test_class(example_file["security_content_soon_info"])

    for release in releases_obj:
        main.save_sec_content_no_details_yet(stored_data, release)

    assert (
        stored_data["details_available_soon"]
        == example_file["security_content_soon_file"]
    )


def test_security_content_available():
    releases_rows = convert_to_lxml_class(example_file["security_content_available_info"])

    stored_data["details_available_soon"] = example_file["security_content_soon_file"]
    coll["sec_content_available"] = []

    main.check_if_sec_content_available(coll, stored_data, releases_rows)

    post = post_format.security_content_available(coll["sec_content_available"])

    assert post == example_file["security_content_available_post"]
    assert stored_data["details_available_soon"] == []


def test_yearly_report():
    for system, version in latest_versions.items():
        post = post_format.yearly_report(
            convert_to_lxml_class(example_file["last_one_year_table"]),
            system,
            version[0],
        )

        assert post[0] == example_file["yearly_report_" + system + "_post"][0]


def test_zero_day():
    releases_obj = convert_to_release_class(example_file["zero_day_releases_table"])
    coll["new_releases"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    compare(releases_obj, example_file["zero_day_releases_info"])

    main.check_for_zero_day_releases(coll, copy.deepcopy(stored_data))

    post = post_format.zero_days(coll["zero_day_releases"], copy.deepcopy(stored_data))

    assert post == example_file["zero_day_releases_post"]


def test_zero_day_new_old():
    releases_obj = convert_to_release_test_class(example_file["zero_day_releases_new_old_info"])
    coll["new_releases"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    main.check_for_zero_day_releases(coll, copy.deepcopy(stored_data))

    post = post_format.zero_days(coll["zero_day_releases"], copy.deepcopy(stored_data))

    assert post == example_file["zero_day_releases_new_old_post"]


def test_zero_day_new():
    releases_obj = convert_to_release_test_class(example_file["zero_day_releases_new_info"])
    coll["new_releases"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    main.check_for_zero_day_releases(coll, copy.deepcopy(stored_data))

    post = post_format.zero_days(coll["zero_day_releases"], copy.deepcopy(stored_data))

    assert post == example_file["zero_day_releases_new_post"]


def test_zero_day_old():
    releases_obj = convert_to_release_test_class(example_file["zero_day_releases_old_info"])
    coll["new_releases"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    main.check_for_zero_day_releases(coll, copy.deepcopy(stored_data))

    post = post_format.zero_days(coll["zero_day_releases"], copy.deepcopy(stored_data))

    assert post == example_file["zero_day_releases_old_post"]

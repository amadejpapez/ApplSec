import copy
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from format_tweets.new_updates import format_new_updates, format_ios_modules
from format_tweets.release_changes import format_entry_changes, format_release_notes_available
from format_tweets.yearly_report import format_yearly_report
from format_tweets.zero_days import format_zero_days
from gather_info import determine_latest_versions, get_info

LOC = os.path.abspath(os.path.join(__file__, "../examples.json"))

with open(LOC, "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

stored_data = copy.deepcopy(example_file["stored_data"])


def test_get_info():
    """
    Tests get_info() on a big number of releases.
    Checks number of returned releases and if titles match.
    """

    releases = example_file["all_releases"]
    releases_info = get_info(releases)

    # check if get_info() returned the correct number of releases
    assert len(releases) == len(list(releases_info))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    titles = []
    for i, value in enumerate(releases):
        if value[2] != "Preinstalled":
            title = re.findall(
                r"(?i)(?<=\">)[^<]+|(?<=<p>)[^<]+|^.+?(?=<br>)", value[0]
            )[0]
        else:
            title = value[0]

        if "macOS" in title:
            title = title.split(",", 1)[0]
        elif "iOS" in title and "iPad" in title:
            title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

        if title in titles:
            title += "*"

        titles.append(title)

        assert title == list(releases_info)[i]


def test_new_updates():
    releases_info = example_file["new_releases"]

    formatted = format_new_updates(dict(releases_info), stored_data)

    assert formatted == example_file["new_releases_expected"]


def test_get_info_results():
    releases_info = get_info(example_file["get_info_results"])

    formatted = format_new_updates(
        dict(releases_info), copy.deepcopy(example_file["stored_data"])
    )

    assert formatted == example_file["new_releases_expected"]

    # check if get_info() results match to the pre-existing info
    assert releases_info == example_file["new_releases"]


def test_ios_modules():
    releases_info = example_file["ios_modules"]

    formatted = format_ios_modules(dict(releases_info), stored_data)

    assert formatted == example_file["ios_modules_expected"]


def test_entry_changes():
    releases_info = example_file["entry_changes"]

    formatted = format_entry_changes(dict(releases_info))

    assert formatted == example_file["entry_changes_expected"]


def test_release_notes_soon():
    releases_info = example_file["release_notes_soon"]

    formatted = format_release_notes_available(dict(releases_info), stored_data)

    assert formatted is None
    assert (
        stored_data["details_available_soon"]
        == example_file["release_notes_soon_expected"]
    )


def test_release_notes_available():
    releases_info = example_file["release_notes_available"]

    formatted = format_release_notes_available(dict(releases_info), stored_data)

    assert formatted == example_file["release_notes_available_expected"]
    assert stored_data["details_available_soon"] == []


def test_yearly_report():
    latest_versions = determine_latest_versions(example_file["all_releases"][:50])

    for system, version in latest_versions.items():
        formatted = format_yearly_report(
            example_file["all_releases"], system, version[0], stored_data
        )

        if system == "iOS and iPadOS":
            system = "iOS"

        assert formatted[0] == example_file["yearly_report_expected_" + system][0]


def test_zero_day():
    releases_info = example_file["zero_day_releases"]

    formatted = format_zero_days(dict(releases_info), stored_data)

    assert formatted == example_file["zero_day_releases_expected"]


def test_zero_day_get_info():
    releases_info = get_info(example_file["zero_day_get_info"])

    formatted = format_zero_days(
        dict(releases_info), copy.deepcopy(example_file["stored_data"])
    )

    assert formatted == example_file["zero_day_get_info_expected"]

import copy
import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from format_tweets.new_updates import format_ios_modules, format_new_updates
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

    releases = example_file["last_one_year_table"]
    releases_info = get_info(releases)

    # check if get_info() returned the correct number of releases
    assert len(releases) == len(list(releases_info))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    titles = []
    for i, value in enumerate(releases):
        title = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", value[0])[0]

        if "iOS" in title and "iPad" in title:
            title = title.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        if title in titles:
            title += "*"

        titles.append(title)

        assert title == list(releases_info)[i]


def test_get_info_2():
    releases_info = get_info(example_file["get_info_table"])

    assert releases_info == example_file["get_info_info"]

    tweet_format = format_new_updates(
        dict(releases_info), copy.deepcopy(example_file["stored_data"])
    )

    assert tweet_format == example_file["get_info_tweet"]


def test_new_updates():
    releases_info = get_info(example_file["new_releases_table"])

    assert releases_info == example_file["new_releases_info"]

    tweet_format = format_new_updates(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["new_releases_tweet"]


def test_new_updates_only_one():
    releases_info = example_file["new_releases_one_info"]

    tweet_format = format_new_updates(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["new_releases_one_tweet"]


def test_ios_modules():
    releases_info = get_info(example_file["ios_modules_table"])

    assert releases_info == example_file["ios_modules_info"]

    tweet_format = format_ios_modules(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["ios_modules_tweet"]


def test_entry_changes():
    releases_info = example_file["entry_changes_info"]

    tweet_format = format_entry_changes(dict(releases_info))

    assert tweet_format == example_file["entry_changes_tweet"]


def test_release_notes_soon():
    releases_info = example_file["release_notes_soon_info"]

    tweet_format = format_release_notes_available(dict(releases_info), stored_data)

    assert tweet_format is None
    assert (
        stored_data["details_available_soon"] == example_file["release_notes_soon_file"]
    )


def test_release_notes_available():
    releases_info = example_file["release_notes_available_info"]

    tweet_format = format_release_notes_available(dict(releases_info), stored_data)

    assert tweet_format == example_file["release_notes_available_tweet"]
    assert stored_data["details_available_soon"] == []


def test_yearly_report():
    latest_versions = determine_latest_versions(
        example_file["last_one_year_table"][:50]
    )

    for system, version in latest_versions.items():
        tweet_format = format_yearly_report(
            example_file["last_one_year_table"],
            system,
            version[0],
            copy.deepcopy(stored_data)
        )

        if system == "iOS and iPadOS":
            system = "iOS"

        assert tweet_format[0] == example_file["yearly_report_" + system + "_tweet"][0]


def test_zero_day():
    releases_info = get_info(example_file["zero_day_releases_table"])

    assert releases_info == example_file["zero_day_releases_info"]

    tweet_format = format_zero_days(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["zero_day_releases_tweet"]


def test_zero_day_1_1():
    releases_info = example_file["zero_day_releases_1_1_info"]

    tweet_format = format_zero_days(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["zero_day_releases_1_1_tweet"]


def test_zero_day_0_1():
    releases_info = example_file["zero_day_releases_0_1_info"]

    tweet_format = format_zero_days(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["zero_day_releases_0_1_tweet"]


def test_zero_day_1_0():
    releases_info = example_file["zero_day_releases_1_0_info"]

    tweet_format = format_zero_days(dict(releases_info), copy.deepcopy(stored_data))

    assert tweet_format == example_file["zero_day_releases_1_0_tweet"]

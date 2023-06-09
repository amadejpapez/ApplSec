import json
import os

import lxml.html
import pytest
from freezegun import freeze_time

import helpers.get_version_info as get_version_info
import helpers.post_format as post_format
import main
from helpers.PostedFile import PostedFile
from Release import Release


def compare(release_obj: list[Release], example: dict):
    for release, (_, expected) in zip(release_obj, example.items()):
        assert release.name == expected["name"]
        assert release.emoji == expected["emoji"], release.name
        assert release.release_date == expected["release_date"], release.name
        assert release.security_content_link == expected["security_content_link"], release.name
        assert release.zero_days == expected["zero_days"], release.name
        assert release.num_of_bugs == expected["num_of_bugs"], release.name
        assert release.num_of_zero_days == expected["num_of_zero_days"], release.name
        assert release.num_entries_added == expected["num_entries_added"], release.name
        assert release.num_entries_updated == expected["num_entries_updated"], release.name


def convert_to_lxml_class(release_rows: list) -> list:
    releases_tmp = []

    for row in release_rows:
        tmp = []
        for x in row:
            tmp.append(lxml.html.document_fromstring(x))

        releases_tmp.append(tmp)

    return releases_tmp


def convert_to_release_from_table(release_rows: list) -> list:
    releases_obj = []

    for row in convert_to_lxml_class(release_rows):
        releases_obj.append(Release.parse_from_table(row))

    return releases_obj


def convert_to_release_from_dict(release_info: dict) -> list:
    releases_class = []

    for _, value in release_info.items():
        release_notes_link = value["release_notes_link"] if ("release_notes_link" in value) else ""

        releases_class.append(
            Release(
                value["name"],
                value["emoji"],
                release_notes_link,
                value["security_content_link"],
                value["release_date"],
                value["zero_days"],
                value["num_of_bugs"],
                value["num_of_zero_days"],
                value["num_entries_added"],
                value["num_entries_updated"],
            )
        )

    return releases_class


with open("src/tests/examples_sec_content.json", "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

PostedFile.reset()

latest_versions = get_version_info.latest(
    convert_to_lxml_class(example_file["last_one_year_table"][:50])
)

coll = {
    "new_releases": [],
    "ios_release": [],
    "changed_releases": [],
    "sec_content_available": [],
    "zero_day_releases": [],
}


def test_posted_data_json():
    """
    Verify that the file is generated in /src and that reading/saving works.
    """
    if os.path.exists("src/posted_data.json"):
        os.remove("src/posted_data.json")

    with pytest.raises(AssertionError):
        PostedFile.read()

    # PostedFile.save(example_file["posted_data_test"])

    assert os.path.isfile("src/posted_data.json") is True
    assert PostedFile.read() == example_file["posted_data_test"]


def test_release_class():
    """
    Tests Release class on a big number of releases.
    Checks number of returned releases and if titles match.
    """

    releases = example_file["last_one_year_table"]
    releases_obj = convert_to_lxml_class(releases)

    # check if Release returned the correct number of releases
    assert len(releases) == len(list(releases_obj))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, _ in enumerate(releases):
        assert (
            Release.parse_name([lxml.html.document_fromstring(releases[i][0])])
            == Release.parse_name(releases_obj[i])
        )


def test_release_class_2():
    releases_obj = convert_to_lxml_class(example_file["new_sec_content_rows_table"])
    PostedFile.reset()

    compare(
        convert_to_release_from_table(example_file["new_sec_content_rows_table"]),
        example_file["new_sec_content_rows_info"],
    )

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == example_file["new_sec_content_rows_post"]


def test_new_sec_content():
    releases_obj = convert_to_lxml_class(example_file["new_sec_content_table"])
    PostedFile.reset()

    compare(
        convert_to_release_from_table(example_file["new_sec_content_table"]),
        example_file["new_sec_content_info"],
    )

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == example_file["new_sec_content_post"]
    assert PostedFile.data == example_file["new_sec_content_posted_data"]


def test_new_sec_content_only_one():
    releases_obj = convert_to_lxml_class(example_file["new_sec_content_one_table"])
    PostedFile.reset()

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == example_file["new_sec_content_one_post"]


def test_new_sec_content_details_soon():
    releases_obj = convert_to_lxml_class(example_file["new_sec_content_details_soon_table"])
    PostedFile.reset()

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == example_file["new_sec_content_details_soon_post"]
    assert PostedFile.data == example_file["new_sec_content_details_soon_posted_data"]


def test_ios_modules():
    releases_obj = convert_to_release_from_table(example_file["ios_modules_table"])
    PostedFile.reset()

    compare(releases_obj, example_file["ios_modules_info"])

    lat_ios_ver = str(latest_versions["iOS"][0])
    coll["ios_release"] = []

    for release in releases_obj:
        main.check_latest_ios_release(coll, release, lat_ios_ver)

    post = post_format.top_ios_modules(coll["ios_release"])

    assert post == example_file["ios_modules_post"]


def test_entry_changes():
    releases_obj = convert_to_release_from_dict(example_file["entry_changes_info"])

    post = post_format.entry_changes(releases_obj)

    assert post == example_file["entry_changes_post"]


@freeze_time("2023-03-17")
def test_entry_changes2():
    """Test that both first and Additional Recognition sections are checked."""

    releases_obj = convert_to_release_from_table(example_file["entry_changes2_table"])

    post = post_format.entry_changes(releases_obj)

    assert post == example_file["entry_changes2_post"]


def test_security_content_soon():
    releases_obj = convert_to_release_from_dict(example_file["security_content_soon_info"])
    PostedFile.reset()

    for release in releases_obj:
        main.save_sec_content_no_details_yet(release)

    assert PostedFile.data["details_available_soon"] == example_file["security_content_soon_file"]

    # test if result is the same when same data comes in the next time
    releases_obj = convert_to_release_from_dict(example_file["security_content_soon_info"])

    for release in releases_obj:
        main.save_sec_content_no_details_yet(release)

    assert PostedFile.data["details_available_soon"] == example_file["security_content_soon_file"]


def test_security_content_available():
    releases_rows = convert_to_lxml_class(example_file["security_content_available_info"])
    PostedFile.reset()

    PostedFile.data["details_available_soon"] = example_file["security_content_soon_file"]
    coll["new_sec_content"] = []

    main.check_if_sec_content_available(coll, releases_rows)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == example_file["security_content_available_post"]
    assert PostedFile.data["details_available_soon"] == []


def test_yearly_report():
    for system, version in latest_versions.items():
        post = post_format.yearly_report(
            convert_to_lxml_class(example_file["last_one_year_table"]),
            system,
            version[0],
        )

        assert post[0] == example_file["yearly_report_" + system + "_post"][0]


def test_zero_day():
    releases_obj = convert_to_release_from_table(example_file["zero_day_releases_table"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    compare(releases_obj, example_file["zero_day_releases_info"])

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == example_file["zero_day_releases_post"]
    assert PostedFile.data == example_file["zero_day_releases_posted_data"]


def test_zero_day_new_old():
    releases_obj = convert_to_release_from_dict(example_file["zero_day_releases_new_old_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == example_file["zero_day_releases_new_old_post"]


def test_zero_day_new():
    releases_obj = convert_to_release_from_dict(example_file["zero_day_releases_new_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == example_file["zero_day_releases_new_post"]


def test_zero_day_old():
    releases_obj = convert_to_release_from_dict(example_file["zero_day_releases_old_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == example_file["zero_day_releases_old_post"]

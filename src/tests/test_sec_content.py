import lxml.html
from freezegun import freeze_time

import helpers.get_version_info as get_version_info
import helpers.post_format as post_format
import main
from helpers.PostedFile import PostedFile
from Release import Release
from tests.helpers import compare, info_to_release, read_examples, row_to_lxml, row_to_release

examples = read_examples("examples_sec_content")

latest_versions = get_version_info.latest(row_to_lxml(examples["last_one_year_table"][:50]))

coll = {
    "new_releases": [],
    "ios_release": [],
    "changed_releases": [],
    "sec_content_available": [],
    "zero_day_releases": [],
}

PostedFile.reset()


def test_release_class():
    """
    Tests Release class on a big number of releases.
    Checks number of returned releases and if titles match.
    """

    releases = examples["last_one_year_table"]
    releases_obj = row_to_lxml(releases)

    # check if Release returned the correct number of releases
    assert len(releases) == len(list(releases_obj))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, _ in enumerate(releases):
        assert Release.parse_name([lxml.html.document_fromstring(releases[i][0])]) == Release.parse_name(
            releases_obj[i]
        )


def test_release_class_2():
    releases_obj = row_to_lxml(examples["new_sec_content_rows_table"])
    PostedFile.reset()

    compare(
        row_to_release(examples["new_sec_content_rows_table"]),
        examples["new_sec_content_rows_info"],
    )

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == examples["new_sec_content_rows_post"]


def test_new_sec_content():
    releases_obj = row_to_lxml(examples["new_sec_content_table"])
    PostedFile.reset()

    compare(
        row_to_release(examples["new_sec_content_table"]),
        examples["new_sec_content_info"],
    )

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == examples["new_sec_content_post"]
    assert PostedFile.data == examples["new_sec_content_posted_data"]


def test_new_sec_content_only_one():
    releases_obj = row_to_lxml(examples["new_sec_content_one_table"])
    PostedFile.reset()

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == examples["new_sec_content_one_post"]


def test_new_sec_content_details_soon():
    releases_obj = row_to_lxml(examples["new_sec_content_details_soon_table"])
    PostedFile.reset()

    coll["new_sec_content"] = []

    main.check_new_security_content(coll, latest_versions, releases_obj)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == examples["new_sec_content_details_soon_post"]
    assert PostedFile.data == examples["new_sec_content_details_soon_posted_data"]


def test_ios_modules():
    releases_obj = row_to_release(examples["ios_modules_table"])
    PostedFile.reset()

    compare(releases_obj, examples["ios_modules_info"])

    lat_ios_ver = str(latest_versions["iOS"][0])
    coll["ios_release"] = []

    for release in releases_obj:
        main.check_latest_ios_release(coll, release, lat_ios_ver)

    post = post_format.top_ios_modules(coll["ios_release"])

    assert post == examples["ios_modules_post"]


def test_entry_changes():
    releases_obj = info_to_release(examples["entry_changes_info"])

    post = post_format.entry_changes(releases_obj)

    assert post == examples["entry_changes_post"]


@freeze_time("2023-03-17")
def test_entry_changes2():
    """Test that both first and Additional Recognition sections are checked."""

    releases_obj = row_to_release(examples["entry_changes2_table"])

    post = post_format.entry_changes(releases_obj)

    assert post == examples["entry_changes2_post"]


def test_security_content_soon():
    releases_obj = info_to_release(examples["security_content_soon_info"])
    PostedFile.reset()

    for release in releases_obj:
        main.save_sec_content_no_details_yet(release)

    assert PostedFile.data["details_available_soon"] == examples["security_content_soon_file"]

    # test if result is the same when same data comes in the next time
    releases_obj = info_to_release(examples["security_content_soon_info"])

    for release in releases_obj:
        main.save_sec_content_no_details_yet(release)

    assert PostedFile.data["details_available_soon"] == examples["security_content_soon_file"]


def test_security_content_available():
    releases_rows = row_to_lxml(examples["security_content_available_info"])
    PostedFile.reset()

    PostedFile.data["details_available_soon"] = examples["security_content_soon_file"]
    coll["new_sec_content"] = []

    main.check_if_sec_content_available(coll, releases_rows)

    post = post_format.new_security_content(coll["new_sec_content"])

    assert post == examples["security_content_available_post"]
    assert PostedFile.data["details_available_soon"] == []


def test_yearly_report():
    for system, version in latest_versions.items():
        post = post_format.yearly_report(
            row_to_lxml(examples["last_one_year_table"]),
            system,
            version[0],
        )

        assert post[0] == examples["yearly_report_" + system + "_post"][0]


def test_zero_day():
    releases_obj = row_to_release(examples["zero_day_releases_table"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    compare(releases_obj, examples["zero_day_releases_info"])

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == examples["zero_day_releases_post"]
    assert PostedFile.data == examples["zero_day_releases_posted_data"]


def test_zero_day_new_old():
    releases_obj = info_to_release(examples["zero_day_releases_new_old_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == examples["zero_day_releases_new_old_post"]


def test_zero_day_new():
    releases_obj = info_to_release(examples["zero_day_releases_new_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == examples["zero_day_releases_new_post"]


def test_zero_day_old():
    releases_obj = info_to_release(examples["zero_day_releases_old_info"])
    coll["new_sec_content"] = releases_obj
    coll["zero_day_releases"] = []
    coll["sec_content_available"] = []

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    main.check_for_zero_day_releases(coll)

    post = post_format.zero_days(coll["zero_day_releases"])

    assert post == examples["zero_day_releases_old_post"]

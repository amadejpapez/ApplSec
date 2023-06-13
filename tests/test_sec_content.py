import lxml.html
from freezegun import freeze_time
from helpers_test import compare, info_to_release, read_examples, row_to_lxml, row_to_release

import helpers.get_version_info as get_version_info
import post.sec_content as sec_content
from helpers.posted_file import PostedFile
from release import Release

examples = read_examples("posts_sec")

latest_versions = get_version_info.latest(row_to_lxml(examples["last_one_year_table"][:50]))


def test_release_class_parsing() -> None:
    """Test Release class parsing on a big number of releases."""
    releases = examples["last_one_year_table"]
    releases_obj = row_to_release(releases)

    # check if Release returned the correct number of releases
    assert len(releases) == len(list(releases_obj))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, _ in enumerate(releases):
        assert Release.parse_name([lxml.html.document_fromstring(releases[i][0])]) == releases_obj[i].name


def test_release_class_safari() -> None:
    """Test Release class on weirdly named Safari releases."""
    PostedFile.reset()
    releases_obj = row_to_release(examples["new_sec_content_rows_table"])

    compare(releases_obj, examples["new_sec_content_rows_info"])

    new_releases = sec_content.get_new(row_to_lxml(examples["new_sec_content_rows_table"]))

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_rows_post_mastodon"]

    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_rows_post_twitter"]


def test_new_sec_content() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_table"])
    PostedFile.reset()

    compare(row_to_release(examples["new_sec_content_table"]), examples["new_sec_content_info"])

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == []
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == []


def test_new_sec_content_only_one() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_one_table"])
    PostedFile.reset()

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_one_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_one_post_twitter"]


def test_new_sec_content_details_soon() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_details_soon_table"])
    PostedFile.reset()

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_details_soon_post"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_details_soon_post"]

    assert PostedFile.data == examples["new_sec_content_details_soon_posted_data"]


def test_ios_modules() -> None:
    releases_obj = row_to_release(examples["ios_modules_table"])
    PostedFile.reset()

    compare(releases_obj, examples["ios_modules_info"])

    new_releases = sec_content.get_new_ios_release(releases_obj, latest_versions)

    post = sec_content.format_ios_release(new_releases)
    assert post == examples["ios_modules_post"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content.get_new_ios_release(releases_obj, latest_versions)

    post = sec_content.format_ios_release(new_releases)
    assert post == []


def test_entry_changes() -> None:
    releases_obj = info_to_release(examples["entry_changes_info"])

    post = sec_content.format_entry_changes_mastodon(releases_obj)
    assert post == examples["entry_changes_post_mastodon"]
    post = sec_content.format_entry_changes_twitter(releases_obj)
    assert post == examples["entry_changes_post_twitter"]


@freeze_time("2023-03-17")
def test_entry_changes2() -> None:
    """Test that both first and Additional Recognition sections are checked."""
    releases_obj = row_to_release(examples["entry_changes2_table"])

    post = sec_content.format_entry_changes_mastodon(releases_obj)
    assert post == examples["entry_changes2_post_mastodon"]
    post = sec_content.format_entry_changes_twitter(releases_obj)
    assert post == examples["entry_changes2_post_twitter"]


def test_security_content_soon() -> None:
    releases_obj = row_to_lxml(examples["security_content_soon_info"])
    PostedFile.reset()

    sec_content.get_new(releases_obj)

    assert PostedFile.data["details_available_soon"] == examples["security_content_soon_file"]

    # test if result is the same when same data comes in the next time
    releases_obj = row_to_lxml(examples["security_content_soon_info"])

    sec_content.get_new(releases_obj)

    assert PostedFile.data["details_available_soon"] == examples["security_content_soon_file"]


def test_security_content_available() -> None:
    releases_rows = row_to_lxml(examples["security_content_available_info"])
    PostedFile.reset()

    PostedFile.data["details_available_soon"] = examples["security_content_soon_file"]

    new_releases = sec_content.get_if_available(releases_rows)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["security_content_available_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["security_content_available_post_twitter"]

    assert PostedFile.data["details_available_soon"] == []

    # test again after posting and verify it returns nothing
    new_releases = sec_content.get_if_available(releases_rows)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == []
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == []


def test_yearly_report() -> None:
    for system, version in latest_versions.items():
        post = sec_content.format_yearly_report(
            row_to_lxml(examples["last_one_year_table"]),
            system,
            version[0],
        )

        assert post[0] == examples["yearly_report_" + system + "_post"][0]


def test_zero_day() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_releases = sec_content.get_new(releases_obj)
    new_zero_days = sec_content.get_new_zero_days(new_releases)

    post = sec_content.format_zero_days(new_zero_days)
    assert post == examples["zero_day_releases_post"]

    assert PostedFile.data == examples["zero_day_releases_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content.get_new(releases_obj)
    new_zero_days = sec_content.get_new_zero_days(new_releases)

    post = sec_content.format_zero_days(new_zero_days)
    assert post == []


def test_zero_day_new_old() -> None:
    new_releases = info_to_release(examples["zero_day_releases_new_old_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_new_old_post"]


def test_zero_day_new() -> None:
    new_releases = info_to_release(examples["zero_day_releases_new_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_new_post"]


def test_zero_day_old() -> None:
    new_releases = info_to_release(examples["zero_day_releases_old_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_old_post"]

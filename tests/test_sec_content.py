import lxml.html
from freezegun import freeze_time
from helpers_test import compare, info_to_release, read_examples, row_to_lxml, row_to_release

import helpers.get_version_info as get_version_info
import post.sec_content as sec_content
from helpers.posted_file import PostedFile
from release import Release

examples = read_examples("posts_sec")

latest_versions = get_version_info.latest(row_to_lxml(examples["last_one_year_table"][:50]))


def test_sec_page_download() -> None:
    """Verify successful download, parse first and that there are min 100 items."""
    releases = sec_content.retrieve_page()

    Release.parse_from_table(releases[0])
    assert len(releases) > 100


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


def test_new_sec_content_from_example_html() -> None:
    PostedFile.reset()

    with open("tests/fixtures/sec_page.html", "r", encoding="utf-8") as my_file:
        releases = sec_content.retrieve_page(my_file.read())

    releases_obj = []
    for x in releases:
        releases_obj.append(Release.parse_from_table(x))

    post = sec_content.format_new_sec_content_mastodon(releases_obj[:20])
    assert post == examples["new_sec_content_from_html_post"]


def test_new_sec_content_only_one() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_one_table"])
    PostedFile.reset()

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_one_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_one_post_twitter"]


def test_new_sec_content_details_soon() -> None:
    # details available soon
    releases_obj = row_to_lxml(examples["new_sec_content_details_soon_table"])
    PostedFile.reset()

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_details_soon_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_details_soon_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_details_soon_posted_data"]

    # details now available
    releases_obj = row_to_lxml(examples["new_sec_content_details_available_table"])
    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_details_available_post_mastodon"]
    post = sec_content.format_new_sec_content_twitter(new_releases)
    assert post == examples["new_sec_content_details_available_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_details_available_posted_data"]


def test_new_sec_content_rsr() -> None:
    # Rapid Security Response (RSR)
    releases_obj = row_to_lxml(examples["new_sec_content_rsr"])
    PostedFile.reset()

    new_releases = sec_content.get_new(releases_obj)

    post = sec_content.format_new_sec_content_mastodon(new_releases)
    assert post == examples["new_sec_content_rsr_post"]


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


def test_ios_modules_no_other_vulnerabilities() -> None:
    releases_obj = row_to_release(examples["ios_modules_no_other_table"])
    PostedFile.reset()

    new_releases = sec_content.get_new_ios_release(releases_obj, latest_versions)

    post = sec_content.format_ios_release(new_releases)
    assert post == examples["ios_modules_no_other_post"]


def test_ios_modules_one_other_vulnerability() -> None:
    # uses iTunes release as it was the only one easy to find with bugs in 5 modules
    releases_obj = info_to_release(examples["ios_modules_one_other_info"])
    PostedFile.reset()

    post = sec_content.format_ios_release(releases_obj)
    assert post == examples["ios_modules_one_other_post"]


def test_entry_changes() -> None:
    releases_obj = info_to_release(examples["entry_changes_info"])

    post = sec_content.format_entry_changes_mastodon(releases_obj)
    assert post == examples["entry_changes_post_mastodon"]
    post = sec_content.format_entry_changes_twitter(releases_obj)
    assert post == examples["entry_changes_post_twitter"]


@freeze_time("2023-03-17")
def test_entry_changes2() -> None:
    """Test that both first and Additional Recognition sections are checked."""
    releases = row_to_lxml(examples["entry_changes2_table"])
    releases_obj = sec_content.get_entry_changes(releases)

    post = sec_content.format_entry_changes_mastodon(releases_obj)
    assert post == examples["entry_changes2_post_mastodon"]
    post = sec_content.format_entry_changes_twitter(releases_obj)
    assert post == examples["entry_changes2_post_twitter"]


@freeze_time("2023-03-17")
def test_entry_changes_only_one() -> None:
    releases = row_to_lxml(examples["entry_changes_one_table"])
    releases_obj = sec_content.get_entry_changes(releases)

    post = sec_content.format_entry_changes_mastodon(releases_obj)
    assert post == examples["entry_changes_one_post_mastodon"]
    post = sec_content.format_entry_changes_twitter(releases_obj)
    assert post == examples["entry_changes_one_post_twitter"]


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
    latest_versions: dict[str, list] = {"iOS and iPadOS": [15], "macOS": [12, "Monterey"], "tvOS": [15], "watchOS": [8]}
    releases_obj = row_to_release(examples["yearly_report_table"])
    PostedFile.reset()

    data = sec_content.get_yearly_report(releases_obj, latest_versions)

    assert data == [["iOS and iPadOS", 15], ["macOS", 12], ["tvOS", 15], ["watchOS", 8]]
    data.remove(["iOS and iPadOS", 15])
    data.append(["iOS", 15])

    for item in data:
        post = sec_content.format_yearly_report(
            row_to_lxml(examples["last_one_year_table"]),
            str(item[0]),
            int(item[1]),
        )

        assert post[0] == examples["yearly_report_" + str(item[0]) + "_post"][0]

    assert PostedFile.data["posts"]["yearly_report"] == ["iOS and iPadOS", "macOS", "tvOS", "watchOS"]

    # try again, should return empty
    data = sec_content.get_yearly_report(releases_obj, latest_versions)
    assert data == []

    # try again with one being be removed from the PostedFile
    PostedFile.data["posts"]["yearly_report"] = ["iOS and iPadOS", "macOS", "tvOS"]
    data = sec_content.get_yearly_report(releases_obj, latest_versions)
    assert data == [["watchOS", 8]]


def test_zero_day_many_new_one_old() -> None:
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


def test_zero_day_one_new_many_old() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = [
        "CVE-2021-30869",
        "CVE-2021-30860",
        "CVE-2021-31010",
    ]

    new_releases = sec_content.get_new(releases_obj)
    new_zero_days = sec_content.get_new_zero_days(new_releases)

    post = sec_content.format_zero_days(new_zero_days)
    assert post == examples["zero_day_releases_one_new_many_old_post"]


def test_zero_day_many_new_many_old() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = [
        "CVE-2021-30860",
        "CVE-2021-31010",
    ]

    new_releases = sec_content.get_new(releases_obj)
    new_zero_days = sec_content.get_new_zero_days(new_releases)

    post = sec_content.format_zero_days(new_zero_days)
    assert post == examples["zero_day_releases_many_new_many_old_post"]


def test_zero_day_many_new() -> None:
    new_releases = info_to_release(examples["zero_day_releases_two_info"])

    PostedFile.reset()

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_many_new_post"]


def test_zero_day_many_old() -> None:
    new_releases = info_to_release(examples["zero_day_releases_two_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = [
        "CVE-2021-30869",
        "CVE-2021-30858",
    ]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_many_old_post"]


def test_zero_day_one_new_one_old() -> None:
    new_releases = info_to_release(examples["zero_day_releases_two_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_one_new_one_old_post"]


def test_zero_day_one_new() -> None:
    new_releases = info_to_release(examples["zero_day_releases_one_new_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_one_new_post"]


def test_zero_day_one_old() -> None:
    new_releases = info_to_release(examples["zero_day_releases_one_old_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2021-30869"]

    new_zero_days = sec_content.get_new_zero_days(new_releases)
    post = sec_content.format_zero_days(new_zero_days)

    assert post == examples["zero_day_releases_one_old_post"]

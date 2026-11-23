import pytest
from helpers_test import compare, failing_get, read_examples, row_to_lxml, row_to_release

import helpers.sec_content as sec_content
import post.sec_content_new as sec_content_new
from helpers.posted_file import PostedFile
from release import Release

examples = read_examples("posts_sec")


def test_sec_page_download() -> None:
    """Verify successful download, parse first and that there are min 100 items."""
    releases = sec_content.retrieve_page()

    Release.parse_from_table(releases[0])
    assert len(releases) > 60


def test_release_class_safari() -> None:
    """Verify parsing on weirdly named Safari releases."""
    PostedFile.reset()
    releases_obj = row_to_release(examples["new_sec_content_rows_table"])

    compare(releases_obj, examples["new_sec_content_rows_info"])

    new_releases = sec_content_new.get_new(row_to_lxml(examples["new_sec_content_rows_table"]))

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_rows_post_mastodon"]

    post = sec_content_new.format_twitter(new_releases)
    assert post == examples["new_sec_content_rows_post_twitter"]


def test_new_sec_content() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_table"])
    PostedFile.reset()

    compare(row_to_release(examples["new_sec_content_table"]), examples["new_sec_content_info"])

    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_post_mastodon"]
    post = sec_content_new.format_twitter(new_releases)
    assert post == examples["new_sec_content_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == []
    post = sec_content_new.format_twitter(new_releases)
    assert post == []


def test_new_sec_content_from_example_html() -> None:
    PostedFile.reset()

    with open("tests/fixtures/sec_page_2024.html", "r", encoding="utf-8") as my_file:
        releases = sec_content.retrieve_page(my_file.read())

    releases_obj = []
    for x in releases:
        releases_obj.append(Release.parse_from_table(x))

    post = sec_content_new.format_mastodon(releases_obj[:20])
    assert post == examples["new_sec_content_from_html_post"]


def test_new_sec_content_only_one() -> None:
    releases_obj = row_to_lxml(examples["new_sec_content_one_table"])
    PostedFile.reset()

    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_one_post_mastodon"]
    post = sec_content_new.format_twitter(new_releases)
    assert post == examples["new_sec_content_one_post_twitter"]


def test_new_sec_content_details_soon() -> None:
    # details available soon
    releases_obj = row_to_lxml(examples["new_sec_content_details_soon_table"])
    PostedFile.reset()

    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_details_soon_post_mastodon"]
    post = sec_content_new.format_twitter(new_releases)
    assert post == examples["new_sec_content_details_soon_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_details_soon_posted_data"]

    # verify it returns no releases the second time
    new_releases2 = sec_content_new.get_new(releases_obj)
    assert new_releases2 == []

    # details now available
    releases_obj = row_to_lxml(examples["new_sec_content_details_available_table"])
    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_details_available_post_mastodon"]
    post = sec_content_new.format_twitter(new_releases)
    assert post == examples["new_sec_content_details_available_post_twitter"]

    assert PostedFile.data == examples["new_sec_content_details_available_posted_data"]

    # verify it returns no releases the second time
    new_releases2 = sec_content_new.get_if_available(releases_obj)

    post = sec_content_new.format_mastodon(new_releases2)
    assert post == []
    post = sec_content_new.format_twitter(new_releases2)
    assert post == []


def test_new_sec_content_rsr() -> None:
    # Rapid Security Response (RSR)
    releases_obj = row_to_lxml(examples["new_sec_content_rsr"])
    PostedFile.reset()

    new_releases = sec_content_new.get_new(releases_obj)

    post = sec_content_new.format_mastodon(new_releases)
    assert post == examples["new_sec_content_rsr_post"]


def test_release_failed_fetch_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that a failed security content fetch raises, so the release is not posted with wrong data and marked as posted."""
    PostedFile.reset()
    PostedFile.data["posts"]["new_sec_content"] = ["placeholder"]
    monkeypatch.setattr("release.session.get", failing_get)

    with pytest.raises(ConnectionError):
        sec_content_new.get_new(row_to_lxml(examples["last_one_year_table"][6:7]))

    assert PostedFile.data["posts"]["new_sec_content"] == ["placeholder"]

from freezegun import freeze_time
from helpers_test import read_examples

import post.rss_releases as rss_releases
from helpers.posted_file import PostedFile
from release import Release

examples = read_examples("posts_rss")

with open("tests/fixtures/releases_feed.rss", "r", encoding="utf-8") as my_file:
    rss_feed = rss_releases.retrieve_rss(my_file.read())


def test_rss_feed_download() -> None:
    """Verify successful download, parse and that there are min 10 items."""
    xml_tree = rss_releases.retrieve_rss()
    releases = xml_tree.xpath("//item")

    Release.from_rss_release(releases[0])
    assert len(releases) > 10


@freeze_time("2024-08-28 10:00:00")
def test_rss_releases() -> None:
    """Verify new releases with one of them already posted."""
    PostedFile.reset()

    PostedFile.data["posts"]["new_releases"] = ["tvOS 18 beta 8 (22J5356a)"]

    new_releases = rss_releases.get_new(rss_feed)

    post = rss_releases.format_releases(new_releases)
    assert post == examples["new_releases_post"]

    assert PostedFile.data == examples["new_releases_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = rss_releases.get_new(rss_feed)

    post = rss_releases.format_releases(new_releases)
    assert post == []


@freeze_time("2024-08-29")
def test_rss_releases_midnight() -> None:
    """Verify that at midnight, it checks releases for the previous day."""
    PostedFile.reset()

    PostedFile.data["posts"]["new_releases"] = ["tvOS 18 beta 8 (22J5356a)"]

    new_releases = rss_releases.get_new(rss_feed)
    post = rss_releases.format_releases(new_releases)

    assert post == examples["new_releases_post"]
    assert PostedFile.data == examples["new_releases_posted_data"]


@freeze_time("2024-08-30")
def test_rss_releases_none() -> None:
    """Verify that a day with no releases returns no releases."""
    PostedFile.reset()

    new_releases = rss_releases.get_new(rss_feed)

    assert new_releases == []
    assert PostedFile.data == examples["posted_data"]


@freeze_time("2024-08-28 10:00:00")
def test_rss_releases_only_one() -> None:
    """Verify new releases with the second last one already posted return only the last one."""
    PostedFile.reset()

    PostedFile.data["posts"]["new_releases"] = ["iPadOS 18.1 beta 3 (22B5034e)"]

    new_releases = rss_releases.get_new(rss_feed)

    post = rss_releases.format_releases(new_releases)
    assert post == examples["new_releases_one_post"]

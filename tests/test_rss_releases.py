from freezegun import freeze_time
from helpers_test import read_examples

import post.rss_releases as rss_releases
from helpers.posted_file import PostedFile
from release import Release

examples = read_examples("posts_rss")


def test_rss_feed_download() -> None:
    """Verify successful download, parse first and that there are min 10 items."""
    xml_tree = rss_releases.retrieve_rss()
    releases = xml_tree.xpath("//item")

    Release.from_rss_release(releases[0])
    assert len(releases) > 10


@freeze_time("2023-06-05 10:00:00")
def test_rss_releases() -> None:
    """Test new releases with one of them already posted."""
    rss_feed = ""
    PostedFile.reset()

    PostedFile.data["posts"]["new_releases"] = ["macOS 13.4 (22F66 | 22F2073)"]

    with open("tests/fixtures/rss_feed.xml", "r", encoding="utf-8") as my_file:
        rss_feed = rss_releases.retrieve_rss(my_file.read())

    new_releases = rss_releases.get_new(rss_feed)

    post = rss_releases.format_releases(new_releases)
    assert post == examples["new_releases_post"]

    assert PostedFile.data == examples["new_releases_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = rss_releases.get_new(rss_feed)

    post = rss_releases.format_releases(new_releases)
    assert post == []


@freeze_time("2023-06-06")
def test_rss_releases_midnight() -> None:
    """Verify that midnight of 6 June 2023, checks releases for 5 June 2023."""
    rss_feed = ""
    PostedFile.reset()

    PostedFile.data["posts"]["new_releases"] = ["macOS 13.4 (22F66 | 22F2073)"]

    with open("tests/fixtures/rss_feed.xml", "r", encoding="utf-8") as my_file:
        rss_feed = rss_releases.retrieve_rss(my_file.read())

    new_releases = rss_releases.get_new(rss_feed)
    post = rss_releases.format_releases(new_releases)

    assert post == examples["new_releases_post"]
    assert PostedFile.data == examples["new_releases_posted_data"]


@freeze_time("2023-06-07")
def test_rss_releases_none() -> None:
    """Check for 7 June 2023, there should be no releases returned for that date."""
    rss_feed = ""
    PostedFile.reset()

    with open("tests/fixtures/rss_feed.xml", "r", encoding="utf-8") as my_file:
        rss_feed = rss_releases.retrieve_rss(my_file.read())

    new_releases = rss_releases.get_new(rss_feed)

    assert new_releases == []
    assert PostedFile.data == examples["posted_data"]

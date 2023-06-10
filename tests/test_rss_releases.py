import lxml.etree
from helpers_test import read_examples

import post.rss_releases as rss_releases
from helpers.posted_file import PostedFile

examples = read_examples("posts_rss")


def test_rss_releases() -> None:
    rss_feed = ""
    PostedFile.reset()

    with open("tests/fixtures/rss_feed.xml", "r", encoding="utf-8") as my_file:
        rss_feed = lxml.etree.fromstring(my_file.read().encode("utf-8"), None)

    new_releases = rss_releases.get_new(rss_feed)
    post = rss_releases.format_releases(new_releases)

    assert post == examples["new_releases_post"]
    assert PostedFile.data == examples["posted_data_new"]

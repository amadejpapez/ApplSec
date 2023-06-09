import lxml.etree
from helpers_test import read_examples

import helpers.post_format as post_format
import main
from helpers.PostedFile import PostedFile

examples = read_examples("posts_rss")

coll = {
    "new_releases": [],
    "ios_release": [],
    "changed_releases": [],
    "sec_content_available": [],
    "zero_day_releases": [],
}


def test_rss_releases():
    rss_feed = ""
    PostedFile.reset()

    with open("tests/fixtures/rss_feed.xml", "r", encoding="utf-8") as my_file:
        rss_feed = lxml.etree.fromstring(my_file.read().encode("utf-8"), None)

    main.check_new_releases(coll, rss_feed)
    post = post_format.new_updates(coll["new_releases"])

    assert post == examples["new_releases_post"]
    assert PostedFile.data == examples["posted_data_new"]

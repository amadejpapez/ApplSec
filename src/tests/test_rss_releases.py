import json

import lxml.etree

import helpers.post_format as post_format
import main
from helpers.PostedFile import PostedFile

with open("src/tests/examples_rss.json", "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

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

    with open("src/tests/example_rss.xml", "r", encoding="utf-8") as my_file:
        rss_feed = lxml.etree.fromstring(my_file.read().encode("utf-8"), None)

    main.check_new_releases(coll, rss_feed)
    post = post_format.new_updates(coll["new_releases"])

    assert post == example_file["new_releases_post"]
    assert PostedFile.data == example_file["posted_data_new"]

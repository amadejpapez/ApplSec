import copy
import json

import lxml.etree

import helpers.post_format as post_format
import main

with open("src/tests/examples_rss.json", "r", encoding="utf-8") as my_file:
    example_file = json.load(my_file)

posted_data = copy.deepcopy(example_file["posted_data"])

coll = {
    "new_releases": [],
    "ios_release": [],
    "changed_releases": [],
    "sec_content_available": [],
    "zero_day_releases": [],
}


def test_rss_releases():
    rss_feed = ""
    posted_data_test = copy.deepcopy(posted_data)

    with open("src/tests/example_rss.xml", "r", encoding="utf-8") as my_file:
        rss_feed = lxml.etree.fromstring(my_file.read().encode("utf-8"), None)

    main.check_new_releases(coll, posted_data_test, rss_feed)
    post = post_format.new_updates(coll["new_releases"])

    assert posted_data_test == example_file["posted_data_new"]
    assert post == example_file["new_releases_post"]

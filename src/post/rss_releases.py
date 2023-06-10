import lxml.etree
import lxml.html
import requests

from helpers.PostedFile import PostedFile
from Release import Release


def retrieve_rss() -> lxml.etree._ElementTree:
    rss_feed = requests.get(
        "https://developer.apple.com/news/releases/rss/releases.rss", timeout=60
    ).text.encode("utf-8")
    xml_tree = lxml.etree.fromstring(rss_feed, None)

    return xml_tree


def get_new() -> list[Release]:
    """Return new releases from RSS that have not been posted yet."""
    new_releases = []
    xml_tree = retrieve_rss()

    for el in xml_tree.xpath("//item"):
        name = el.xpath("title")[0].text
        emoji = Release.parse_emoji(name)

        if name in PostedFile.data["posts"]["new_releases"]:
            break

        # skip releases that do not have an emoji in parse_emoji()
        # specifically to skip updates for App Store Connect, TestFlight and similar
        if emoji == "🛠️":
            continue

        if name not in PostedFile.data["posts"]["new_releases"]:
            PostedFile.data["posts"]["new_releases"].append(name)
            new_releases.append(Release.from_rss_release(el))

        assert (len(new_releases) < 20
        ), "ERROR: More than 20 new releases detected. Something may not be right. Verify posted_data.json[posts][new_releases]."

    return new_releases

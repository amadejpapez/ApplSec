import lxml.etree
import lxml.html
import requests

from helpers.posted_file import PostedFile
from release import Release


def retrieve_rss() -> lxml.etree._ElementTree:
    rss_feed = requests.get(
        "https://developer.apple.com/news/releases/rss/releases.rss", timeout=60
    ).text.encode("utf-8")
    xml_tree = lxml.etree.fromstring(rss_feed, None)

    return xml_tree


def get_new(xml_tree: lxml.etree._ElementTree = retrieve_rss()) -> list[Release]:
    """Return new releases from RSS that have not been posted yet."""
    new_releases = []

    for el in xml_tree.xpath("//item"):
        name = el.xpath("title")[0].text
        emoji = Release.parse_emoji(name)

        if name in PostedFile.data["posts"]["new_releases"]:
            break

        # skip releases that do not have an emoji in parse_emoji()
        # specifically to skip updates for App Store Connect, TestFlight and similar
        if emoji == "🛠️":
            continue

        new_releases.append(Release.from_rss_release(el))

        assert (len(new_releases) < 20
        ), "ERROR: More than 20 new releases detected. Something may not be right. Verify posted_data.json[posts][new_releases]."

    # reverse it, so the last release from the page is at the end in posted_data.json
    new_releases.reverse()
    for release in new_releases:
        if release.name not in PostedFile.data["posts"]["new_releases"]:
            PostedFile.data["posts"]["new_releases"].append(release.name)

    return new_releases


def format_releases(releases: list[Release]) -> list:
    """
    💥 NEW UPDATES RELEASED 💥

    📱 iOS 16.6 beta 2 (20G5037d)
    📱 iPadOS 16.6 beta 2 (20G5037d)
    💻 macOS 13.5 beta 2 (22G5038d)
    """
    post_text = []

    releases.sort(key=lambda x: (x.name.lower()))

    for release in releases:
        post_text.append(f"{release.emoji} {release.name}\n")

    if len(releases) == 1:
        post_text.insert(0, "💥 NEW UPDATE RELEASED 💥\n\n")
    else:
        post_text.insert(0, "💥 NEW UPDATES RELEASED 💥\n\n")

    return post_text

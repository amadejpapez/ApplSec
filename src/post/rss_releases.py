import lxml.etree
import lxml.html
import requests

import helpers.get_date as get_date
from helpers.posted_file import PostedFile
from release import Release


def _request_rss_feed() -> str:
    return requests.get("https://developer.apple.com/news/releases/rss/releases.rss", timeout=60).text


def retrieve_rss(rss: str = _request_rss_feed()) -> lxml.etree._Element:
    return lxml.etree.fromstring(rss.encode("utf-8"), None)


def get_new(xml_tree: lxml.etree._Element = retrieve_rss()) -> list[Release]:
    """Return new (beta) releases from RSS that have not been posted yet."""
    new_releases = []

    for el in xml_tree.xpath("//item"):
        name = el.xpath("title")[0].text
        emoji = Release.parse_emoji(name)

        # break if not today's date
        if get_date.format_one() not in el.xpath("pubDate")[0].text:
            break

        # post only beta releases
        if "beta" not in name and "RC" not in name:
            continue

        # break if already posted
        if name in PostedFile.data["posts"]["new_releases"]:
            break

        # skip releases that do not have an emoji in parse_emoji()
        # specifically to skip updates for App Store Connect, TestFlight and similar
        if emoji == "🛠️":
            continue

        new_releases.append(Release.from_rss_release(el))

    # reverse it, so the last release from the page is at the end in posted_data.json
    new_releases.reverse()
    for release in new_releases:
        if release.name not in PostedFile.data["posts"]["new_releases"]:
            PostedFile.data["posts"]["new_releases"].append(release.name)

    return new_releases


def format_releases(releases: list[Release]) -> list[str]:
    """
    🧪 NEW BETA RELEASES 🧪

    📱 iOS 16.6 beta 2 (20G5037d)
    📱 iPadOS 16.6 beta 2 (20G5037d)
    💻 macOS 13.5 beta 2 (22G5038d)
    """
    if not releases:
        return []

    post_text = []

    releases.sort(key=lambda x: (x.name.lower()))

    for release in releases:
        post_text.append(f"{release.emoji} {release.name}\n")

    if len(releases) == 1:
        post_text.insert(0, "🧪 NEW BETA RELEASE 🧪\n\n")
    else:
        post_text.insert(0, "🧪 NEW BETA RELEASES 🧪\n\n")

    post_text.append("https://developer.apple.com/news/releases")

    return post_text

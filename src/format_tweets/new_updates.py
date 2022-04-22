import collections
import re

import requests


def format_new_updates(releases_info: list, stored_data: dict) -> list:
    """
    -----
    💥 NEW UPDATES RELEASED 💥

    🌐 Safari 15.3 - 4 bugs fixed
    💻 Security Update 2022-001 Catalina - 5 bugs fixed
    💻 macOS Big Sur 11.6.3 - 7 bugs fixed
    💻 macOS Monterey 12.2 - 13 bugs fixed
    -----
    📱 iOS and iPadOS 15.3 - 10 bugs fixed
    ⌚ watchOS 8.4 - 8 bugs fixed
    https://support.apple.com/en-us/HT201222
    -----
    """

    tweet_text = []

    for release in list(releases_info):
        if release.get_name() in stored_data["tweeted_today"]["new_updates"]:
            releases_info.remove(release)
        else:
            stored_data["tweeted_today"]["new_updates"].append(release.get_name())

    if not releases_info:
        return []

    releases_info.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    if len(releases_info) == 1:
        tweet_text.insert(0, ":collision: NEW UPDATE RELEASED :collision:\n\n")

        if releases_info[0].get_release_notes_link():
            # if there is only one release, add its notes as a link
            tweet_text.append(releases_info[0].get_release_notes_link())
    else:
        tweet_text.insert(0, ":collision: NEW UPDATES RELEASED :collision:\n\n")
        tweet_text.append("https://support.apple.com/en-us/HT201222")

    return tweet_text


def format_ios_modules(releases_info: list, stored_data: dict) -> list:
    """
    -----------------------------
    ⚒ FIXED IN iOS 14.7 ⚒

    - 4 bugs in WebKit
    - 3 bugs in FontParser
    - 3 bugs in Model I/O
    - 2 bugs in CoreAudio
    and 25 other vulnerabilities fixed
    https://support.apple.com/kb/HT212601
    -----------------------------
    """

    for release in list(releases_info):
        if release.get_name() in stored_data["tweeted_today"]["ios_modules"]:
            releases_info.remove(release)
        else:
            stored_data["tweeted_today"]["ios_modules"] = release.get_name()

    if not releases_info:
        return []

    for release in releases_info:
        release_note = requests.get(release.get_release_notes_link()).text
        release_note = release_note.split("Additional recognition", 1)[0]

        search_modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", release_note)
        )
        modules = collections.OrderedDict(
            sorted(search_modules.items(), reverse=True, key=lambda x: x[1])
        )

        tweet_text = [
            f":hammer_and_pick: FIXED IN {release.get_name()} :hammer_and_pick:\n\n"
        ]
        num_bugs = 0

        for key, value in modules.items():
            if len(tweet_text) < 5:
                num_bugs += value
                if value > 1:
                    tweet_text.append(f"- {value} bugs in {key}\n")
                else:
                    tweet_text.append(f"- {value} bug in {key}\n")

        num_bugs = release.get_num_of_bugs() - num_bugs

        if num_bugs > 0:
            tweet_text.append(f"and {num_bugs} other vulnerabilities fixed\n")

        tweet_text.append(f"{release.get_release_notes_link()}\n")

    return tweet_text

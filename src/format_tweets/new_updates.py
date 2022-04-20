import collections
import re

import requests


def format_new_updates(updates_info, stored_data):
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

    for release in list(updates_info):
        if release.get_name() not in stored_data["tweeted_today"]["new_updates"]:
            stored_data["tweeted_today"]["new_updates"].append(release.get_name())
        else:
            updates_info.remove(release)

    if not updates_info:
        return None

    tweet_text = []
    for release in updates_info:
        tweet_text.append(f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n")

    if len(updates_info) == 1:
        tweet_text.insert(0, ":collision: NEW UPDATE RELEASED :collision:\n\n")

        if updates_info[list(updates_info)[0]].get_release_notes_link():
            # if there is only one release, add its notes as a link
            tweet_text.append(updates_info[list(updates_info)[0]].get_release_notes_link())
    else:
        tweet_text.insert(0, ":collision: NEW UPDATES RELEASED :collision:\n\n")
        tweet_text.append("https://support.apple.com/en-us/HT201222")

    return tweet_text


def format_ios_modules(ios_info, stored_data):
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

    for release in list(ios_info):
        if release.get_name() not in stored_data["tweeted_today"]["ios_modules"]:
            stored_data["tweeted_today"]["ios_modules"] = release.get_name()
        else:
            ios_info.remove(release)

    if not ios_info:
        return None

    for release in ios_info:
        ios_release = requests.get(release.get_release_notes_link()).text
        ios_release = ios_release.split("Additional recognition", 1)[0]
        modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", ios_release)
        )
        modules = collections.OrderedDict(
            sorted(modules.items(), reverse=True, key=lambda t: t[1])
        )

        tweet_text = [f":hammer_and_pick: FIXED IN {release.get_name()} :hammer_and_pick:\n\n"]
        num_modules = 0

        for key, value in modules.items():
            if len(re.findall("bug", str(tweet_text))) <= 3:
                num_modules += value
                if value > 1:
                    tweet_text.append(f"- {value} bugs in {key}\n")
                else:
                    tweet_text.append(f"- {value} bug in {key}\n")

        num_modules -= release.get_num_of_bugs()

        if num_modules > 0:
            tweet_text.append(f"and {num_modules} other vulnerabilities fixed\n")

        tweet_text.append(f"{release.get_release_notes_link()}\n")

    return tweet_text

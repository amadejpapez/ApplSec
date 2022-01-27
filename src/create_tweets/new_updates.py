import re
from collections import Counter, OrderedDict

import requests

from twitter import tweet_or_make_a_thread


def tweet_new_updates(new_releases_info, stored_data):
    """
    -----------------------------
    💥 NEW UPDATES RELEASED 💥

    💻 macOS Big Sur 11.5.1 - 1 bug fixed
    📱 iOS and iPadOS 14.7.1 - 1 bug fixed
    https://support.apple.com/en-us/HT201222
    -----------------------------
    """

    for key, value in list(new_releases_info.items()):
        if key not in stored_data["tweeted_today"]["new_updates"]:
            stored_data["tweeted_today"]["new_updates"].append(key)
        else:
            del new_releases_info[key]

    if not new_releases_info:
        return

    results = []
    for key, value in new_releases_info.items():
        results.append(f"{value['emoji']} {key} - {value['num_of_bugs']}\n")

    if len(new_releases_info) > 1:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"
        results.append("https://support.apple.com/en-us/HT201222")
    else:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"
        # if there was only one release, add its release notes link
        results.append(
            new_releases_info[list(new_releases_info)[0]]["release_notes"]
        )

    tweet_or_make_a_thread(title, results)


def tweet_ios_modules(ios_info, stored_data):
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

    for key, _ in list(ios_info.items()):
        if key not in stored_data["tweeted_today"]["ios_parts"]:
            stored_data["tweeted_today"]["ios_parts"] = key
        else:
            del ios_info[key]

    if not ios_info:
        return

    for key, value in ios_info.items():
        ios_release = requests.get(value["release_notes"]).text
        ios_release = ios_release.split("Additional recognition", 1)[0]
        modules = Counter(re.findall(r"(?i)<strong>(.*)<\/strong>", ios_release))
        modules = OrderedDict(sorted(modules.items(), reverse=True, key=lambda t: t[1]))

        results = f":hammer_and_pick: FIXED IN {key} :hammer_and_pick:\n\n"
        num_modules = 0

        for key2, value2 in modules.items():
            if len(re.findall("bug", results)) <= 3:
                num_modules += value2
                if value2 > 1:
                    results += f"- {value2} bugs in {key2}\n"
                else:
                    results += f"- {value2} bug in {key2}\n"

        num_modules = int(re.findall(r"(\d+)", value["num_of_bugs"])[0]) - num_modules

        if num_modules > 0:
            results += f"and {num_modules} other vulnerabilities fixed\n"

        results += f"{value['release_notes']}\n"

    tweet_or_make_a_thread(first_tweet=results)

import re
from collections import Counter, OrderedDict

import requests
from create_tweets.twitter import tweetOrCreateAThread

"""
-----------------------------
💥 NEW UPDATES RELEASED 💥

💻 macOS Big Sur 11.5.1 - 1 bug fixed
📱 iOS and iPadOS 14.7.1 - 1 bug fixed
https://support.apple.com/en-us/HT201222
-----------------------------
"""


def tweetNewUpdates(updatesInfo):
    if len(updatesInfo) > 1:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"
    else:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"

    results = []
    for key, value in updatesInfo.items():
        results.append(f"{value['emojis']} {key} - {value['CVEs']}\n")

    tweetOrCreateAThread("tweetNewUpdates", title=title, results=results)


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


def tweetiOSParts(updatesInfo):
    for key, value in updatesInfo.items():
        page = requests.get(value["releaseNotes"]).text
        page = page.split("Additional recognition", 1)[0]
        parts = Counter(re.findall(r"<strong>(.*)<\/strong>", page))
        parts = OrderedDict(sorted(parts.items(), reverse=True, key=lambda t: t[1]))

        results = f":hammer_and_pick: FIXED IN {key} :hammer_and_pick:\n\n"
        numberParts = 0

        for key2, value2 in parts.items():
            if len(re.findall("bug", results)) <= 3:
                numberParts += value2
                if value2 > 1:
                    results += f"- {value2} bugs in {key2}\n"
                else:
                    results += f"- {value2} bug in {key2}\n"

        numberParts = int(re.findall(r"(\d+)", value["CVEs"])[0]) - numberParts

        if numberParts > 0:
            results += f"and {numberParts} other vulnerabilities fixed\n"

        results += f"{value['releaseNotes']}\n"

        tweetOrCreateAThread("tweetiOSParts", firstTweet=results)

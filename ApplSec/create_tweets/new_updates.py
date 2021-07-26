import re
from collections import Counter, OrderedDict

import requests
from create_tweets.post_on_twitter import tweetOrCreateAThread


# tweet that there were new updates released today
def tweetNewUpdates(updatesInfo):
    results = []

    if len(updatesInfo) == 1:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for key, value in updatesInfo.items():
        results.append(f"{value['emojis']} {key} - {value['CVEs']}\n")

    results = list(reversed(results))

    tweetOrCreateAThread("tweetNewUpdates", title=title, results=results)


# tweet top five parts that got bug fixes in the latest iOS update
def tweetiOSParts(updatesInfo, latestVersion):
    numberParts = 0
    results = ""

    for key, value in updatesInfo.items():
        if "iOS" in key and str(latestVersion["iOS"]) in key:
            page = requests.get(value["releaseNotes"]).text
            page = page.split("Additional recognition", 1)[0]
            parts = Counter(re.findall(r"<strong>(.*)<\/strong>", page))
            parts = OrderedDict(sorted(parts.items(), reverse=True, key=lambda t: t[1]))

            results = f":hammer_and_pick: FIXED IN {key} :hammer_and_pick:\n\n"

            for key2, value2 in parts.items():
                if len(re.findall("bug", results)) <= 3:
                    numberParts += value2
                    if value2 == 1:
                        results += f"- {value2} bug in {key2}\n"
                    else:
                        results += f"- {value2} bugs in {key2}\n"

            numberParts = int(re.findall(r"(\d+)", value["CVEs"])[0]) - numberParts

            if numberParts > 0:
                results += f"and {numberParts} other vulnerabilities fixed\n"

            results += f"{value['releaseNotes']}\n"

            tweetOrCreateAThread("tweetiOSParts", firstTweet=results)

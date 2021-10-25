import re

from create_tweets.post_on_twitter import tweetOrCreateAThread

"""
-----------------------------
🔄 4 SECURITY NOTES UPDATED 🔄

🌐 Safari 14.1.1 - 1 entry updated
💻 Security Update 2021-003 Catalina - 8 entries added
💻 Security Update 2021-004 Mojave - 6 entries added

💻 macOS Big Sur 11.4 - 8 entries added, 1 entry updated
-----------------------------
"""


def tweetEntryChanges(updatesInfo):
    results = []
    title = ""

    for key, value in updatesInfo.items():
        if value["added"] is not None or value["updated"] is not None:
            if value["added"] is None and value["updated"] is not None:
                results.append(f"{value['emojis']} {key} - {value['updated']}\n")
            elif value["added"] is not None and value["updated"] is None:
                results.append(f"{value['emojis']} {key} - {value['added']}\n")
            elif value["added"] is not None and value["updated"] is not None:
                results.append(
                    f"{value['emojis']} {key} - {value['added']}, {value['updated']}\n"
                )

    num = len(re.findall(r":[^:]+:", str(results)))

    if num > 1:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread("tweetEntryChanges", title=title, results=results)


def tweetReleaseNotesAvailable(updatesInfo):
    title = ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n"
    results = []

    for key, value in updatesInfo.items():
        results.append(f"{value['emojis']} {key} - {value['CVEs']}\n")

    tweetOrCreateAThread("tweetReleaseNotesAvailable", title=title, results=results)

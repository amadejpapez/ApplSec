# tweet if Apple updated or added anything to previous release notes

import json
import os
import re

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetEntryChanges(updatesInfo):
    results = []

    for key, value in updatesInfo.items():
        if value["added"] == None and value["updated"] != None:
            results.append(f"{value['emojis']} {key} - {value['updated']}\n")
        elif value["added"] != None and value["updated"] == None:
            results.append(f"{value['emojis']} {key} - {value['added']}\n")
        elif value["added"] != None and value["updated"] != None:
            results.append(f"{value['emojis']} {key} - {value['added']}, {value['updated']}\n")

    num = len(re.findall(r":[^:]+:", str(results)))

    if num == 1:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread("tweetEntryChanges", title=title, results=results)


def tweetReleaseNotesAvailable(updatesInfo):
    results = []
    dirPath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    with open(f"{dirPath}/stored_data.json", "r+", encoding="utf-8") as myFile:
        try:
            storedDataFile = json.load(myFile)
        except json.decoder.JSONDecodeError:
            myFile.seek(0)
            json.dump(
                {"zero_days": [], "details_available_soon": [], "todays_releases": {"date": "", "releases": []}}, myFile, indent=4
            )
            myFile.truncate()
            myFile.seek(0)
            storedDataFile = json.load(myFile)

        for key, value in updatesInfo.items():
            if key not in storedDataFile["details_available_soon"] and value["CVEs"] == "no details yet":
                storedDataFile["details_available_soon"].append(key)

            if key in storedDataFile["details_available_soon"] and value["releaseNotes"] != None:
                storedDataFile["details_available_soon"].remove(key)
                results.append(f"{value['emojis']} {key} - {value['CVEs']}\n")

        myFile.seek(0)
        json.dump(storedDataFile, myFile, indent=4)
        myFile.truncate()

    if results:
        title = ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n"
        tweetOrCreateAThread("tweetReleaseNotesAvailable", title=title, results=results)

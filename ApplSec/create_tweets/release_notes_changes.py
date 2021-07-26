# tweet if Apple updated or added anything to previous release notes

import re
import os
import json

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetEntryChanges(updatesInfo):
    results = []

    for key, value in updatesInfo.items():
        if value["added"] == None and value["updated"] != None:
            results.append(f'{value["emojis"]} {key} - {value["updated"]}\n')
        elif value["added"] != None and value["updated"] == None:
            results.append(f'{value["emojis"]} {key} - {value["added"]}\n')
        elif value["added"] != None and value["updated"] != None:
            results.append(f'{value["emojis"]} {key} - {value["added"]}, {value["updated"]}\n')

    num = len(re.findall(r":[^:]+:", str(results)))

    if num == 1:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread("tweetEntryChanges", title=title, results=results)


def tweetReleaseNotesAvailable(updatesInfo):
    results = []
    dirPath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))

    with open(f"{dirPath}/stored_data.json", "r+", encoding="utf-8") as myFile:
        try:
            json.load(myFile)
        except json.decoder.JSONDecodeError:
            json.dump({"zero_days":[], "details_available_soon":[]}, myFile, indent=4)

        myFile.seek(0)
        storedDataFile = json.load(myFile)

        for key, value in updatesInfo.items():
            if value["CVEs"] == "no details yet":
                storedDataFile["details_available_soon"].append(key)

            if key in storedDataFile["details_available_soon"] and value["releaseNotes"] != None:
                storedDataFile["details_available_soon"].remove(key)
                results.append(f'{value["emojis"]} {key} - {value["CVEs"]}\n')

        myFile.seek(0)
        json.dump(storedDataFile, myFile, indent=4)

    if results:
        title = ":collision: RELEASE NOTES AVAILABLE :collision:\n\n"
        tweetOrCreateAThread("tweetReleaseNotesAvailable", title=title, results=results)

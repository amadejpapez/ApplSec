import copy
import re
from datetime import date

import requests
from create_tweets.new_updates import tweetiOSParts, tweetNewUpdates
from create_tweets.release_notes_changes import tweetEntryChanges, tweetReleaseNotesAvailable
from create_tweets.web_server_fixes import tweetWebServerFixes
from create_tweets.yearly_report import tweetYearlyReport
from create_tweets.zero_days import tweetZeroDays
from get_data import getData
from save_data import readFile, saveData

mainPage = requests.get("https://support.apple.com/en-us/HT201222").text

releases = re.findall(r"(?<=<tr>)(?:.|\n)*?(?=<\/tr>)", mainPage)
releases.pop(0)  # remove first row
lastTwentyReleases = releases[:20]

lastTwentyReleaseNames = []
for release in lastTwentyReleases:
    lastTwentyReleaseNames.append(
        re.findall(r"(?<=<td>)(?:.|\n)*?(?=<\/td>)", release)[0]
    )

storedDataFile = readFile()


# if there are new releases, run tweetNewUpdates()
if len(str(date.today().day)) > 1:
    day = date.today().day
else:
    day = f"0{date.today().day}"

currentDateFormatOne = f"{day} {date.today().strftime('%b')} {date.today().year}"

newReleases = []
for release in lastTwentyReleases:
    if f"<td>{currentDateFormatOne}</td>" in release:
        newReleases.append(release)

updatesInfo = getData(newReleases)
newReleasesInfo = copy.copy(updatesInfo)

for key, value in list(newReleasesInfo.items()):
    if key not in storedDataFile["todays_tweets"]["tweetNewUpdates"]:
        storedDataFile["todays_tweets"]["tweetNewUpdates"].append(key)
    else:
        del newReleasesInfo[key]

if len(newReleasesInfo) > 0:
    tweetNewUpdates(newReleasesInfo)


# find the latest version of operating systems
latestVersion = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": ""}

for key, value in latestVersion.items():
    version = re.findall(rf"{key}\s(?:[a-z\s]+)?([0-9]+)", str(releases), re.IGNORECASE)

    version = list(map(int, version))
    version.sort(reverse=True)
    latestVersion[key] = int(version[0])

    if key == "macOS":
        # alongside of the version also get the macOS name
        latestVersion["macOS"] = re.findall(
            rf"{key}\s([a-z\s]+[0-9]+)", str(lastTwentyReleaseNames), re.IGNORECASE
        )[0]


# if the latest iOS series got an update, run tweetiOSParts()
iOSPartsInfo = {}

for key, value in updatesInfo.items():
    if (
        "iOS" in key
        and str(latestVersion["iOS"]) in key
        and value["CVEs"] != "no details yet"
    ):
        if value["zeroDays"]:
            if int(re.findall(r"\d+", value["CVEs"])[0]) != len(value["zeroDayCVEs"]):
                iOSPartsInfo[key] = value
        else:
            iOSPartsInfo[key] = value

for key, value in list(iOSPartsInfo.items()):
    if key not in storedDataFile["todays_tweets"]["tweetiOSParts"]:
        storedDataFile["todays_tweets"]["tweetiOSParts"] = key
    else:
        del iOSPartsInfo[key]

if len(iOSPartsInfo) > 0:
    tweetiOSParts(iOSPartsInfo)


# if there was a zero-day fixed, run tweetZeroDays()
zeroDaysInfo = {}

for key, value in updatesInfo.items():
    if value["zeroDays"]:
        zeroDaysInfo[key] = value

for key, value in list(zeroDaysInfo.items()):
    if (
        key in storedDataFile["todays_tweets"]["tweetZeroDays"].keys()
        and value["zeroDays"] == storedDataFile["todays_tweets"]["tweetZeroDays"][key]
    ):
        del zeroDaysInfo[key]
    else:
        storedDataFile["todays_tweets"]["tweetZeroDays"][key] = value["zeroDays"]

if len(zeroDaysInfo) > 0:
    tweetZeroDays(zeroDaysInfo)


# if there are any changes to the last 20 release notes, run tweetEntryChanges()
lastTwentyReleasesInfo = getData(lastTwentyReleases)
entryChangesInfo = {}

for key, value in lastTwentyReleasesInfo.items():
    if value["added"] or value["updated"]:
        entryChangesInfo[key] = value

for key, value in list(entryChangesInfo.items()):
    if (
        key in storedDataFile["todays_tweets"]["tweetEntryChanges"].keys()
        and value["added"]
        == storedDataFile["todays_tweets"]["tweetEntryChanges"][key][0]
        and value["updated"]
        == storedDataFile["todays_tweets"]["tweetEntryChanges"][key][1]
    ):
        del entryChangesInfo[key]
    else:
        storedDataFile["todays_tweets"]["tweetEntryChanges"][key] = [
            value["added"],
            value["updated"],
        ]

if len(entryChangesInfo) > 0:
    tweetEntryChanges(entryChangesInfo)


# if any releases got releases notes, run tweetReleaseNotesAvailable()
releaseNotesAvailableInfo = {}

for key, value in updatesInfo.items():
    if (
        key not in storedDataFile["details_available_soon"]
        and value["CVEs"] == "no details yet"
    ):
        storedDataFile["details_available_soon"].append(key)

    if (
        key in storedDataFile["details_available_soon"]
        and value["releaseNotes"] != None
    ):
        storedDataFile["details_available_soon"].remove(key)
        releaseNotesAvailableInfo[key] = value

if len(releaseNotesAvailableInfo) > 0:
    tweetReleaseNotesAvailable(releaseNotesAvailableInfo)


# if there was a new major release, run tweetYearlyReport()
for key, value in latestVersion.items():
    if f"{key} {value} " in str(lastTwentyReleaseNames) or f"{key} {value}.0 " in str(
        lastTwentyReleaseNames
    ):
        tweetYearlyReport(releases, key, value)


# if it is first day of the month, run tweetYearlyReport()
if date.today().day == 1:
    tweetWebServerFixes()

saveData(storedDataFile)

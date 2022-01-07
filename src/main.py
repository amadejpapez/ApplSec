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

storedDataFile = readFile()

mainPage = requests.get("https://support.apple.com/en-us/HT201222").text
releases = re.findall(r"(?<=<tr>)(?:.|\n)*?(?=<\/tr>)", mainPage)
releases.pop(0)  # remove first row
lastFiftyReleases = releases[:50]


# check if there are any new releases; tweetNewUpdates()
if len(str(date.today().day)) > 1:
    day = str(date.today().day)
else:
    day = f"0{date.today().day}"

currentDateFormatOne = f"{day} {date.today().strftime('%b')} {date.today().year}"  # 08 Jan 2022

newReleases = []
for release in lastFiftyReleases:
    if f"<td>{currentDateFormatOne}</td>" in release:
        newReleases.append(release)

newReleasesInfo = getData(newReleases)
newReleasesInfoCopy = copy.copy(newReleasesInfo)

for key, value in list(newReleasesInfoCopy.items()):
    if key not in storedDataFile["todays_tweets"]["tweetNewUpdates"]:
        storedDataFile["todays_tweets"]["tweetNewUpdates"].append(key)
    else:
        del newReleasesInfoCopy[key]

if len(newReleasesInfoCopy) > 0:
    tweetNewUpdates(newReleasesInfoCopy)


# find the latest version of each operating system
latestVersion = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": 0}

for key, value in latestVersion.items():
    version = re.findall(rf"{key}\s(?:[a-z\s]+)?([0-9]+)", str(releases), re.IGNORECASE)

    version = list(map(int, version))
    version.sort(reverse=True)
    latestVersion[key] = int(version[0])


# check if the latest iOS series got a new release; tweetiOSParts()
iOSPartsInfo = {}

for key, value in newReleasesInfoCopy.items():
    if (
        "iOS" in key and str(latestVersion["iOS"]) in key
        and value["CVEs"] != "no details yet"
        and value["releaseNotes"] != "None"
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

# if any releases got releases notes, run tweetReleaseNotesAvailable()
lastFiftyReleasesInfo = getData(lastFiftyReleases)
releaseNotesAvailableInfo = {}

for key, value in lastFiftyReleasesInfo.items():
    if (
        key not in storedDataFile["details_available_soon"]
        and value["CVEs"] == "no details yet"
    ):
        storedDataFile["details_available_soon"].append(key)

    if (
        key in storedDataFile["details_available_soon"]
        and value["releaseNotes"] is not None
    ):
        storedDataFile["details_available_soon"].remove(key)
        releaseNotesAvailableInfo[key] = value

if len(releaseNotesAvailableInfo) > 0:
    tweetReleaseNotesAvailable(releaseNotesAvailableInfo)

newReleasesInfo.update(releaseNotesAvailableInfo)

# if there was a zero-day fixed, run tweetZeroDays()
zeroDaysInfo = {}

for key, value in newReleasesInfo.items():
    if value["zeroDays"]:
        zeroDaysInfo[key] = value

for key, value in list(zeroDaysInfo.items()):
    if (
        key in storedDataFile["todays_tweets"]["tweetZeroDays"].keys()
    ) and value["zeroDays"] == storedDataFile["todays_tweets"]["tweetZeroDays"][key]:
        del zeroDaysInfo[key]
    else:
        storedDataFile["todays_tweets"]["tweetZeroDays"][key] = value["zeroDays"]

saveData(storedDataFile)

if len(zeroDaysInfo) > 0:
    tweetZeroDays(zeroDaysInfo)

storedDataFile = readFile()


# if there are any changes to the last 20 release notes, run tweetEntryChanges()
entryChangesInfo = {}

for key, value in lastFiftyReleasesInfo.items():
    if value["added"] or value["updated"]:
        entryChangesInfo[key] = value

for key, value in list(entryChangesInfo.items()):
    if (
        key in storedDataFile["todays_tweets"]["tweetEntryChanges"].keys()
        and value["added"] == storedDataFile["todays_tweets"]["tweetEntryChanges"][key][0]
        and value["updated"] == storedDataFile["todays_tweets"]["tweetEntryChanges"][key][1]
    ):
        del entryChangesInfo[key]
    else:
        storedDataFile["todays_tweets"]["tweetEntryChanges"][key] = [value["added"], value["updated"]]

if len(entryChangesInfo) > 0:
    tweetEntryChanges(entryChangesInfo)


# if there was a new major release, run tweetYearlyReport()
for key, value in latestVersion.items():
    if (
        f"{key} {value} " in str(newReleases) or f"{key} {value}.0 " in str(newReleases)
    ) and key not in storedDataFile["todays_tweets"]["tweetYearlyReport"]:
        tweetYearlyReport(releases, key, value)
        storedDataFile["todays_tweets"]["tweetYearlyReport"].append(key)


# if it is first day of the month, run tweetWebServerFixes()
if (
    date.today().day == 1
) and storedDataFile["todays_tweets"]["tweetWebServerFixes"] is False:
    tweetWebServerFixes()
    storedDataFile["todays_tweets"]["tweetWebServerFixes"] = True

saveData(storedDataFile)

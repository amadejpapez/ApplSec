import json
import os
import re
from datetime import date

import requests
from create_tweets.new_updates import tweetiOSParts, tweetNewUpdates
from create_tweets.release_notes_changes import tweetEntryChanges, tweetReleaseNotesAvailable
from create_tweets.web_server_fixes import tweetWebServerFixes
from create_tweets.yearly_report import tweetYearlyReport
from create_tweets.zero_days import tweetZeroDays
from get_data import getData

mainPage = requests.get("https://support.apple.com/en-us/HT201222").text
releases = re.findall(r"(?<=<tr>)(?:.|\n)*?(?=<\/tr>)", mainPage)
releases.pop(0)  # remove first row

lastTwentyReleases = releases[:20]
lastTwentyReleaseNames = []

for release in lastTwentyReleases:
    lastTwentyReleaseNames.append(re.findall(r"(?<=<td>)(?:.|\n)*?(?=<\/td>)", release)[0])


# if there are any new releases, run tweetNewUpdates()
if len(str(date.today().day)) == 1:
    # if day is only one number, add 0
    day = f"0{date.today().day}"
else:
    day = date.today().day

currentDateFormatOne = f"{day} {date.today().strftime('%b')} {date.today().year}"
newReleases = []

for release in lastTwentyReleases:
    if f"<td>{currentDateFormatOne}</td>" in release:
        newReleases.append(release)

updatesInfo = getData(newReleases)
dirPath = os.path.abspath(os.path.join(os.path.dirname(__file__)))

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

    if storedDataFile["todays_releases"]["date"] != str(date.today()):
        storedDataFile["todays_releases"]["date"] = str(date.today())
        storedDataFile["todays_releases"]["releases"] = []

    for key, value in list(updatesInfo.items()):
        if key not in storedDataFile["todays_releases"]["releases"]:
            storedDataFile["todays_releases"]["releases"].append(key)
        else:
            del updatesInfo[key]

    myFile.seek(0)
    json.dump(storedDataFile, myFile, indent=4)
    myFile.truncate()

if len(updatesInfo) > 0:
    tweetNewUpdates(updatesInfo)


# find the latest version of operating systems
latestVersion = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": ""}

for key, value in latestVersion.items():
    version = re.findall(rf"{key}\s(?:[a-z\s]+)?([0-9]+)", str(releases), re.IGNORECASE)

    version = list(map(int, version))
    version.sort(reverse=True)
    latestVersion[key] = int(version[0])

    if key == "macOS":
        # alongside of the version also get the macOS name
        latestVersion["macOS"] = re.findall(rf"{key}\s([a-z\s]+[0-9]+)", str(lastTwentyReleaseNames), re.IGNORECASE)[0]


# if there was an iOS release, run tweetiOSParts()
for key, value in updatesInfo.items():
    if "iOS" in key and value["CVEs"] != "no details yet":
        if int(re.findall(r"\d+", value["CVEs"])[0]) != len(value["zeroDayCVEs"]):
            # if all of the CVE fixes are zero days, do not run tweetiOSParts
            # as all of the info is in tweetZeroDay() tweet
            tweetiOSParts(updatesInfo, latestVersion)
            break

# if there was a zero-day fixed, run tweetZeroDays()
for key, value in updatesInfo.items():
    if value["zeroDays"]:
        tweetZeroDays(updatesInfo)
        break

# if there are any changes to the last 20 release notes, run tweetEntryChanges()
updatesInfo = getData(lastTwentyReleases)

for key, value in updatesInfo.items():
    if value["added"] or value["updated"]:
        tweetEntryChanges(updatesInfo)
        break

if len(newReleases) > 0:
    tweetReleaseNotesAvailable(updatesInfo)

# if there was a new major release, run tweetYearlyReport()
for key, value in latestVersion.items():
    if f"{key} {value} " in str(lastTwentyReleaseNames) or f"{key} {value}.0 " in str(lastTwentyReleaseNames):
        tweetYearlyReport(releases, key, value)

# if it is first day of the month, run tweetYearlyReport()
if date.today().day == 1:
    tweetWebServerFixes()

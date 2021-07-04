import re
from datetime import date

import requests
from create_tweets.entry_changes import tweetEntryChanges
from create_tweets.ios_parts import tweetiOSParts
from create_tweets.new_updates import tweetNewUpdates
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

currentDateFormatOne = f'{day} {date.today().strftime("%b")} {date.today().year}'
newReleases = []

for release in lastTwentyReleases:
    if f"<td>{currentDateFormatOne}</td>" in release:
        newReleases.append(release)

updatesInfo = getData(newReleases)

if len(newReleases) > 0:
    tweetNewUpdates(updatesInfo)

# find the latest version of operating systems
latestVersion = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": ""}

for key, value in latestVersion.items():
    version = re.findall(rf"{key}\s(?:[a-z\s]+)?([0-9]+)", str(releases), re.IGNORECASE)

    version = list(map(int, version))
    version.sort(reverse=True)
    version = int(version[0])
    latestVersion[key] = version

    if key == "macOS":
        # alongside of the version also get the macOS name
        latestVersion["macOS"] = re.findall(rf"{key}\s([a-z\s]+[0-9]+)", str(lastTwentyReleaseNames), re.IGNORECASE)[0]


# if there was an iOS release, run tweetiOSParts()
if "iOS" in str(updatesInfo):
    tweetiOSParts(updatesInfo, latestVersion)

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

# if there was a new major release, run tweetYearlyReport()
for key, value in latestVersion.items():
    if f"{key} {value} " in str(lastTwentyReleaseNames) or f"{key} {value}.0 " in str(lastTwentyReleaseNames):
        tweetYearlyReport(releases, key, value)

# if it is first day of the month, run tweetYearlyReport()
if date.today().day == 1:
    tweetWebServerFixes()

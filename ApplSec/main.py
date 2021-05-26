import re
import os
import requests
from datetime import date
from collections import Counter, OrderedDict
from make_a_tweet import tweetOrCreateAThread


# function to grab all the data from Apple's website
updatesInfo = {}

def getData(rows):
    for row in rows:
        if "href" in str(row):
            # if there are release notes, grab the whole page
            releaseNotes = re.findall(r'href="([^\']+)"', str(row))[0]
            page = requests.get(releaseNotes).text

            # grab the header from the page
            title = re.findall(r"<h2>(.*)<.h2>", page)[1]
            title = title.replace("*", "") # remove * from the title which is sometimes added for additional info
        else:
            # if there is no release notes, grab the title from the mainPage
            title = re.findall(r"(?i)\['([a-z0-9,\.\-\s]+)", str(row))[0]
            title = title.rstrip()
            page = None
            releaseNotes = None

        if "macOS" in title:
            # if macOS is in the title, take only the first part of the title
            title = title.split(",", 1)[0]
        if "iOS" in title and "iPadOS" in title:
            # if they are both in the title remove version number from iPadOS
            title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

        updatesInfo[title] = {}
        updatesInfo[title]["releaseNotes"] = releaseNotes


        # set emojis depending on the title
        if "iOS" in title:
            emojis = ":iphone:"
        elif "watchOS" in title:
            emojis = ":watch:"
        elif "tvOS" in title or "Apple TV" in title:
            emojis = ":tv:"
        elif "macOS" in title or "Security Update" in title:
            emojis = ":computer:"
        elif "iCloud" in title:
            emojis = ":cloud:"
        elif "Safari" in title:
            emojis = ":globe_with_meridians:"
        elif "iTunes" in title or "Shazam" in title or "GarageBand" in title or "Apple Music" in title:
            emojis = ":musical_note:"
        else:
            emojis = ":hammer_and_wrench:"

        updatesInfo[title]["emojis"] = emojis


        # grab the number of CVEs from the page
        CVEs = (len(re.findall("CVE", str(page))) - 1)

        if "soon" in str(row):
            CVEs = "no details yet"
        elif CVEs > 1:
            CVEs = f"{CVEs} bugs fixed"
        elif CVEs == 1:
            CVEs = f"{CVEs} bug fixed"
        else:
            CVEs = "no bugs fixed"

        updatesInfo[title]["CVEs"] = CVEs


        # search if there were any zero-day vulnerabilities fixed
        if "in the wild" in str(page) or "actively exploited" in str(page):
            num = len(re.findall("in the wild", page)) + len(re.findall("actively exploited", page))
            if num == 1:
                zeroDays = f"{num} zero-day"
            else:
                zeroDays = f"{num} zero-days"

            updatesInfo[title]["zeroDays"] = zeroDays

            # save all CVE numbers
            page = page.replace("<strong>", "▲").replace("</strong>", "▼").replace("/div", "◄")
            currentZeroDays = re.findall(r"▲[^▼]+▼([^▲◄]+actively exploited[^▲◄]+)", page)
            currentZeroDays = re.findall(r"CVE-[0-9]{4}-[0-9]{4,5}", str(currentZeroDays))
            updatesInfo[title]["zeroDayCVEs"] = currentZeroDays

        else:
            updatesInfo[title]["zeroDays"] = None
            updatesInfo[title]["zeroDayCVEs"] = None



        # check for any updated or added entries
        currentDateFormatTwo = f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
        num = (len(re.findall(f"Entry added {currentDateFormatTwo}", str(page))))

        if num == 1:
            added = f"{num} entry added"
        elif num > 1:
            added = f"{num} entries added"
        else:
            added = None

        updatesInfo[title]["added"] = added

        num = (len(re.findall(f"Entry updated {currentDateFormatTwo}", str(page))))
        if num == 1:
            updated = f"{num} entry updated"
        elif num > 1:
            updated = f"{num} entries updated"
        else:
            updated = None

        updatesInfo[title]["updated"] = updated



# tweet if there were any new updates released
def tweetNewUpdates(numberOfNewUpdates):
    updateResults = []

    if numberOfNewUpdates == 1:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for key, value in updatesInfo.items():
        updateResults.append(f'{value["emojis"]} {key} - {value["CVEs"]}\n')

    updateResults = list(reversed(updateResults))

    tweetOrCreateAThread("tweetNewUpdates", title, updateResults, "", "", "", None)


mainPage = requests.get("https://support.apple.com/en-us/HT201222").text
mainPage = mainPage.replace("\n", " ").replace("<td>", "▲").replace("</td>", "▼")
allTd = re.findall(r"▲([^▼]+)▼", str(mainPage))
allRows = list(map(list, zip(*[iter(allTd)]*3)))
latestRows = allRows[:20]
currentDateFormatOne = f"{date.today().day} {date.today().strftime('%b')} {date.today().year}"
newRows = []

for row in latestRows:
    if currentDateFormatOne in str(row):
        newRows.append(row)

if len(newRows) > 0:
    getData(newRows)
    tweetNewUpdates(len(newRows))



# tweet top five parts that got bug fixes in a new iOS update
def tweetiOSParts():
    numberParts = 0
    results = ""

    for key, value in updatesInfo.items():
        if "iOS" in key and str(latestVersion["iOS"]) in key:
            page = requests.get(value["releaseNotes"]).text
            page = page.replace("Additional recognition", "▲").split("▲", 1)[0]
            allStrong = Counter(re.findall(r"<strong>(.*)</strong>", str(page)))
            allStrong = OrderedDict(sorted(allStrong.items(), reverse=True, key=lambda t: t[1]))

            results = f':hammer_and_pick: FIXED IN {key} :hammer_and_pick:\n\n'
            CVEs = value["CVEs"]
            releaseNotes = value["releaseNotes"]

            for key, value in allStrong.items():
                if len(re.findall("bug", results)) <= 3:
                    numberParts += value
                    if value == 1:
                        results += f"- {value} bug in {key}\n"
                    else:
                        results += f"- {value} bugs in {key}\n"

            numberParts = int(re.findall(r"(\d+)", CVEs)[0]) - numberParts

            if numberParts > 0:
                results += f"and {numberParts} other vulnerabilities fixed\n"

            results += f"{releaseNotes}\n"

    tweetOrCreateAThread("tweetiOSParts", None, "", results, "", "", None)



# find the latest version of operating systems
latestVersion = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": ""}

for key, value in latestVersion.items():
    if key == "macOS":
        version = re.findall(rf"{key}\s[a-zA-Z\s]+([0-9]+)", str(allRows))
    else:
        version = re.findall(rf"{key}\s([0-9]+)", str(allRows))

    version = list(map(int, version))
    version.sort(reverse = True)
    version = int(version[0])
    latestVersion[key] = version

if "iOS" in str(updatesInfo):
    tweetiOSParts()



# tweet if there were any zero-day vulnerabilities fixed
def tweetZeroDays(numberOfZeroDayReleases):
    dirPath = os.path.dirname(os.path.realpath(__file__))
    zeroDayResults = []
    uniqueZeroDays = {}
    uniqueZeroDays["old"] = []
    uniqueZeroDays["new"] = []

    if numberOfZeroDayReleases == 1:
        title = ":mega: EMERGENCY UPDATE :mega:\n\n"
    else:
        title = ":mega: EMERGENCY UPDATES :mega:\n\n"

    for key, value in updatesInfo.items():
        if value["zeroDays"] != None:
            # if there were any zero-days fixed, add this to the results
            zeroDayResults.append(f'{value["zeroDays"]} fixed in {key}\n')

            for zeroDay in value["zeroDayCVEs"]:
                with open(f"{dirPath}/zeroDays.txt", "r") as zeroDays:
                    zeroDayFile = zeroDays.read()

                    if zeroDay in zeroDayFile and zeroDay not in uniqueZeroDays["old"]:
                        # if zero-day CVE is in the file, add it to the uniqueZeroDays if it is not already there
                        uniqueZeroDays["old"].append(zeroDay)

                    if zeroDay not in zeroDayFile:
                        # if zero-day CVE is not in the file, add it
                        if zeroDay not in uniqueZeroDays["new"]:
                            uniqueZeroDays["new"].append(zeroDay)
                        with open(f"{dirPath}/zeroDays.txt", "a") as zeroDays:
                            zeroDays.write(f"{zeroDay}\n")

    tweetOrCreateAThread("tweetZeroDays", title, zeroDayResults, "", "", "", uniqueZeroDays)


releasesWithZeroDays = 0
for key, value in updatesInfo.items():
    if value["zeroDays"] != None:
        releasesWithZeroDays += 1

if releasesWithZeroDays > 0:
    tweetZeroDays(releasesWithZeroDays)



# tweet if there are any changes to the last 20 release notes
def tweetEntryChanges():
    changedResults = []

    for key, value in updatesInfo.items():
        if value["added"] == None and value["updated"] != None:
            changedResults.append(f'{value["emojis"]} {key} - {value["updated"]}\n')
        if value["added"] != None and value["updated"] == None:
            changedResults.append(f'{value["emojis"]} {key} - {value["added"]}\n')
        if value["added"] != None and value["updated"] != None:
            changedResults.append(f'{value["emojis"]} {key} - {value["added"]}, {value["updated"]}\n')

    num = len(re.findall(r":[^:]+:", str(changedResults)))

    if num == 1:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread("tweetEntryChanges", title, changedResults, "", "", "", None)


entriesChanged = 0
for key, value in updatesInfo.items():
    if value["added"] != None or value["updated"] != None:
        entriesChanged += 1
if entriesChanged > 0:
    tweetEntryChanges()



# tweet how many security issues were fixed in Apple web servers in the previous month
if date.today().day == 1:
    lastMonth = int(date.today().strftime("%m")) - 1
    nameLastMonth = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][lastMonth - 1]
    lastMonth = f"0{lastMonth}"

    currentDateFormatThree = f"{date.today().year}-{lastMonth}"

    mainPage = "https://support.apple.com/en-us/HT201536"
    page = requests.get(mainPage).text
    numberOfFixes = len(re.findall(currentDateFormatThree, page))

    results = f"In {nameLastMonth}, Apple fixed {numberOfFixes} security issues in their web servers :globe_with_meridians:\n\n"

    allFixes = re.findall(rf"<em>{currentDateFormatThree}(.*)</em>", page)
    numberOfFixesOnAppleDotCom = len(re.findall(r"apple.com", str(allFixes)))
    numberOfFixesOnIcloudDotCom = len(re.findall(r"icloud.com", str(allFixes)))
    numberOfFixes = numberOfFixes - numberOfFixesOnAppleDotCom - numberOfFixesOnIcloudDotCom

    if numberOfFixesOnAppleDotCom >= 1:
        results += f":apple: {numberOfFixesOnAppleDotCom} of those on apple[.]com\n"
    if numberOfFixesOnIcloudDotCom >= 1:
        results += f":cloud: {numberOfFixesOnIcloudDotCom} of those on icloud[.]com\n"
    if numberOfFixes >= 1:
        results += f"and {numberOfFixes} on other domains\n"

    results += mainPage

    tweetOrCreateAThread("webServerFixes", None, "", results, "", "", None)



# tweet how many vulnerabilities were fixed in the four latest series of iOS/watchOS/tvOS/macOS if there is a new major update
def yearlyTotalReport(system, latestSystemVersion):
    info = {}

    # save previous three versions
    versions = []
    if system == "macOS":
        # macOS names are hard coded for now
        versions = ["11", "10.15", "10.14", "10.13"]
    else:
        num = latestSystemVersion
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    # get all the links of release notes, count CVEs and save all the info
    for version in versions:
        info[version] = {}
        info[version]["releaseNotes"] = ""
        info[version]["CVEs"] = 0
        info[version]["releases"] = 0
        info[version]["macosName"] = "None"

        if system == "macOS" and re.findall(rf"{system}\s([a-zA-Z\s]+){version}", str(allRows)) != []:
            # if system is macOS, take the name of the macOS version as Security Updates only contain names
            info[version]["macosName"] = re.findall(rf"{system}\s([a-zA-Z\s]+)\s{version}", str(allRows))[0]

        for row in allRows:
            row = str(row[0])

            if f"{system} {version}" in row or info[version]["macosName"] in row:
                if "href" in row:
                    # if there are release notes, count all the CVEs
                    info[version]["releaseNotes"] = re.findall(r'href="([^"]+)"', row)

                    page = requests.get(info[version]["releaseNotes"][0]).text
                    currentCVE = len(re.findall("CVE", page)) - 1
                    info[version]["CVEs"] += currentCVE

                info[version]["releases"] += 1

    secondVersion = list(info.keys())[0]

    results = f'{system} {latestSystemVersion} was released today. In {system} {secondVersion} series Apple fixed in total of {info[secondVersion]["CVEs"]} security issues over {info[secondVersion]["releases"]} releases. :locked_with_key:\n\n:bar_chart: COMPARED TO:\n'
    info.pop(secondVersion)

    for key, value in info.items():
        results += f'- {value["CVEs"]} fixed in {system} {key} over {value["releases"]} releases\n'

    if system == "macOS":
        # for macOS create a thread with additional info in the second tweet
        secondResults = "Numbers contain all Security and Supplemental Updates."
        tweetOrCreateAThread("yearlyTotalReport", None, "", results, secondResults, "", None)
    else:
        tweetOrCreateAThread("yearlyTotalReport", None, "", results, "", "", None)


for key, value in latestVersion.items():
    if f"{key} {value} " in str(latestRows) or f"{key} {value}.0 " in str(latestRows):
        # when there is new major version released in September, run yearlyTotalReport for that version
        yearlyTotalReport(key, value)
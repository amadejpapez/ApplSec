import re
import copy
import emoji
import tweepy
import requests
from datetime import date
from collections import Counter, OrderedDict

api_key = "x"
api_key_secret = "x"
access_token = "x"
access_token_secret = "x"

auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


mainLink = "https://support.apple.com/en-us/HT201222"
mainPage = requests.get(mainLink).text
mainPage = mainPage.replace("\n", " ").replace("<td>", "$*").replace("</td>", "*$")
allTd = re.findall(r"\$\*([^*$]+)\*\$", str(mainPage))
allRows = list(map(list, zip(*[iter(allTd)]*3)))
latestRows = allRows[:20]
allTd = list(map(list, zip(*[iter(allTd)]*3)))
currentDateFormatOne = f"{date.today().day} {date.today().strftime('%b')} {date.today().year}"

latestiosVersion = re.findall(r"iOS\s([0-9]+)", str(latestRows))
latestiosVersion = list(map(int, latestiosVersion))
latestiosVersion.sort(reverse = True)
latestiosVersion = int(latestiosVersion[0])


updatesInfo = {}
releasesWithZeroDays = 0
entriesChanged = 0

def getData(rows):
    for row in rows:
        if "href" in str(row):
            # if there are release notes grab the release notes page
            releaseNotes = re.findall(r'href="([^\']+)"', str(row))[0]
            page = requests.get(releaseNotes).text

            # grab the header from the page
            title = re.findall(r"<h2>(.*)<.h2>", page)[1]
            title = title.replace("*", "") # remove * from the title which is sometimes added for additional info
        else:
            title = re.findall(r"(?i)\['([a-z0-9,\.\-\s]+)", str(row))[0]
            title = title.rstrip()
            page = ""
            releaseNotes = ""

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
        elif "macOS" in title:
            emojis = ":computer:"
        elif "iCloud" in title:
            emojis = ":cloud:"
        elif "iTunes" in title:
            emojis = ":musical_note:"
        else:
            emojis = ":hammer_and_wrench:"

        updatesInfo[title]["emojis"] = emojis


        # grab the number of CVEs from the page
        CVEs = (len(re.findall("CVE", page)) - 1)

        if CVEs > 1:
            CVEs = f"{CVEs} bugs fixed"
        elif CVEs == 1:
            CVEs = f"{CVEs} bug fixed"
        elif "soon" in str(row):
            CVEs = "no details yet"
        else:
            CVEs = "no bugs fixed"

        updatesInfo[title]["CVEs"] = CVEs


        # search if there were any zero-day vulnerabilities fixed
        if "in the wild" in page or "actively exploited" in page:
            global releasesWithZeroDays
            releasesWithZeroDays += 1

            num = len(re.findall("in the wild", page)) + len(re.findall("actively exploited", page))
            if num == 1:
                zeroDays = f"{num} zero-day"
            else:
                zeroDays = f"{num} zero-days"

            updatesInfo[title]["zeroDays"] = zeroDays


        # check for any updated or added entries
        currentDateFormatTwo = f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
        num = (len(re.findall(f"Entry added {currentDateFormatTwo}", page)))
        global entriesChanged

        if num == 0:
            added = "none"
        elif num == 1:
            added = f"{num} entry added"
        elif num > 1:
            added = f"{num} entries added"

        if added != "none":
            entriesChanged += 1

        updatesInfo[title]["added"] = added

        num = (len(re.findall(f"Entry updated {currentDateFormatTwo}", page)))
        if num == 0:
            updated = "none"
        elif num == 1:
            updated = f"{num} entry updated"
        elif num > 1:
            updated = f"{num} entries updated"

        if updated != "none":
            entriesChanged += 1

        updatesInfo[title]["updated"] = updated



def tweetOrCreateAThread(title, functionResults):
    results = title
    if len(functionResults) <= 4:
        # if there are less than four releases put them all in one tweet
        for result in functionResults:
            results += result
        if functionResults == updateResults:
            # attached only to new updates released tweet
            results += f"{mainLink}\n"
        api.update_status(emoji.emojize(f"{results}", use_aliases=True))

    if len(functionResults) > 4:
        # if there are more than four releases create a thread
        secondResults = ""
        for result in functionResults:
            if len(re.findall("-", results)) <= 4:
                results += result
            else:
                secondResults += result
        if functionResults == updateResults:
            secondResults += f"{mainLink}\n"

        originalTweet = api.update_status(emoji.emojize(f"{results}", use_aliases=True))

        api.update_status(emoji.emojize(f"{secondResults}", use_aliases=True), in_reply_to_status_id=originalTweet.id, auto_populate_reply_metadata=True)



# tweet if there were any new updates released
if currentDateFormatOne in str(latestRows):
    newRows = []
    global updateResults
    updateResults = []

    # grab all the new rows
    for row in latestRows:
        if currentDateFormatOne in str(row):
            newRows.append(row)
    getData(newRows)

    if len(updatesInfo) == 1:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for key, value in updatesInfo.items():
        updateResults.append(f'{value["emojis"]} {key} - {value["CVEs"]}\n')

    tweetOrCreateAThread(title, updateResults)



# tweet top five parts that got bug fixes in a new iOS update
if "iOS" in str(updatesInfo):
    partUpdate = {}
    numberParts = 0

    for key, value in updatesInfo.items():
        if "iOS" in key and str(latestiosVersion) in key:
            partUpdate = copy.deepcopy(value)
            partUpdate["title"] = key

    page = requests.get(partUpdate["releaseNotes"]).text
    allStrong = Counter(re.findall(r"<strong>(.*)<.strong>", page))
    allStrong = OrderedDict(sorted(allStrong.items(), reverse=True, key=lambda t: t[1]))

    results = f':hammer_and_pick: FIXED IN {partUpdate["title"]} :hammer_and_pick:\n\n'

    for key, value in allStrong.items():
        if len(re.findall("-", results)) <= 3:
            numberParts += value
            if value == 1:
                results += f"- {value} bug in {key}\n"
            else:
                results += f"- {value} bugs in {key}\n"

    num = int(re.findall(r"(\d+)", partUpdate["CVEs"])[0])
    numberParts = num - numberParts

    if numberParts >= 1:
        results += f"and {numberParts} other vulnerabilities fixed\n"

    results += f'{partUpdate["releaseNotes"]}\n'
    api.update_status(emoji.emojize(f"{results}", use_aliases=True))



# tweet if there were any zero-day vulnerabilities fixed
if releasesWithZeroDays > 0:
    zeroDayReleases = {}
    zeroDayResults = []

    for key, value in updatesInfo.items():
        if "zeroDays" in updatesInfo[key]:
            zeroDayReleases[key] = value

    if releasesWithZeroDays == 1:
        title = ":mega: EMERGENCY UPDATE :mega:\n\n"
    else:
        title = ":mega: EMERGENCY UPDATES :mega:\n\n"

    for key, value in zeroDayReleases.items():
        zeroDayResults.append(f'{value["zeroDays"]} fixed in {key}\n')

    tweetOrCreateAThread(title, zeroDayResults)



# tweet if there are any changes to the last 20 release notes
if entriesChanged > 0:
    getData(latestRows)
    changedResults = []

    for key, value in updatesInfo.items():
        if value["added"] == "none" and value["updated"] != "none":
            changedResults.append(f'{value["emojis"]} {key} - {value["updated"]}\n')
        if value["added"] != "none" and value["updated"] == "none":
            changedResults.append(f'{value["emojis"]} {key} - {value["added"]}\n')
        if value["added"] != "none" and value["updated"] != "none":
            changedResults.append(f'{value["emojis"]} {key} - {value["added"]}, {value["updated"]}\n')

    num = len(re.findall("-", str(changedResults)))
    if num == 1:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread(title, changedResults)



# tweet how many security issues were fixed in Apple web servers in the previous month
if date.today().day == 1:
    lastMonth = int(date.today().strftime("%m")) - 1
    nameLastMonth = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][lastMonth - 1]
    lastMonth = f"0{lastMonth}"

    currentDateFormatThree = f"{date.today().year}-{lastMonth}"

    link = "https://support.apple.com/en-us/HT201536"
    page = requests.get(link).text
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
    results += f"{link}"

    api.update_status(emoji.emojize(f"{results}", use_aliases=True))


# tweet how many vulnerabilities were fixed in the four latest series of iOS if there is a new major iOS update
if f"iOS {latestiosVersion} " in str(latestRows) or f"iOS {latestiosVersion}.0 " in str(latestRows):
    iosInfo = {}

    # save previous three iOS versions
    iosVersions = [f"{latestiosVersion - 1}", f"{latestiosVersion - 2}", f"{latestiosVersion - 3}", f"{latestiosVersion - 4}"]

    # get all the links of release notes, count CVEs and save all the info to the nested directory
    for version in iosVersions:
        currentCVEs = 0
        iosInfo[version] = {}

        for row in allRows:
            if f"iOS {version}" in str(row[0]):
                iosInfo[version]["releaseNotes"] = re.findall(r'href="([^"]+)"', str(row[0]))

                for link in iosInfo[version]["releaseNotes"]:
                    page = requests.get(link).text
                    currentCVE = len(re.findall("CVE", page)) - 1
                    currentCVEs += currentCVE
                    iosInfo[version]["CVEs"] = currentCVEs

    secondiosVersion = list(iosInfo.keys())[0]
    results = f'iOS {latestiosVersion} was released today. In iOS {secondiosVersion} series Apple fixed in total of {iosInfo[secondiosVersion]["CVEs"]} security issues.\n\n:bar_chart: COMPARED TO:\n'
    iosInfo.pop(secondiosVersion)

    for key, value in iosInfo.items():
        results += f'- {value["CVEs"]} of issues fixed in iOS {key} series\n'

    api.update_status(emoji.emojize(f"{results}", use_aliases=True))
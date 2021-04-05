import re
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
latestRows = list(map(list, zip(*[iter(allTd)]*3)))[:20]
currentDateFormatOne = f"{date.today().day} {date.today().strftime('%b')} {date.today().year}"

latestiosVersion = re.findall(r"iOS\s([0-9]+)", str(allTd))
latestiosVersion = list(map(int, latestiosVersion))
latestiosVersion.sort(reverse = True)
latestiosVersion = int(latestiosVersion[0])

releasesWithZeroDays = 0
updatesInfo = {}
entriesChanged = 0

def getData(rows):
    for row in rows:
        if "href" in str(row):
            # if there are release notes
            releaseNotes = re.findall(r'href="([^\']+)"', str(row))[0]

            # grab the release notes page
            page = requests.get(releaseNotes).text

            # grab the header from the page
            title = re.findall(r"<h2>(.*)<.h2>", page)[1]
            title = title.replace("*", "") # remove * from the title which is sometimes added for additional info

            if "macOS" in title:
                # if macOS is in the title, take only the first part of the title
                title = title.split(",", 1)[0]
            if "iOS" in title and "iPadOS" in title:
                # if they are both in the title remove version number from iPadOS
                title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

            updatesInfo[title] = {}
            updatesInfo[title]["releaseNotes"] = releaseNotes


            # set emojis depending on the title and add it to the variable "emojis"
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
def tweetNewUpdates():
    global updateResults
    updateResults = []
    newRows = []

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


if currentDateFormatOne in str(latestRows):
    tweetNewUpdates()



# tweet top five parts that got bug fixes in a new iOS update
def tweetParts():
    partUpdate = {}
    
    for key, value in updatesInfo.items():
        if "iOS" in key and str(latestiosVersion) in key:
            partUpdate = value
            partUpdate["title"] = key

    page = requests.get(partUpdate["releaseNotes"]).text
    allStrong = Counter(re.findall(r"<strong>(.*)<.strong>", page))
    allStrong = OrderedDict(sorted(allStrong.items(), reverse=True, key=lambda t: t[1]))

    results = f':hammer_and_pick: FIXED IN {partUpdate["title"]} :hammer_and_pick:\n\n'

    numberParts = 0

    for key, value in allStrong.items():
        if len(re.findall("-", results)) <= 3:
            numberParts += value
            if value == 1:
                results += f"- {value} bug in {key}\n"
            else:
                results += f"- {value} bugs in {key}\n"

    number = re.findall(r"(\d+)", partUpdate["CVEs"])[0]
    numberParts = int(number) - numberParts

    if numberParts >= 1:
        results += f"and {numberParts} other vulnerabilities fixed\n"

    results += f'{partUpdate["releaseNotes"]}\n'
    api.update_status(emoji.emojize(f"{results}", use_aliases=True))


if "iOS" in str(updatesInfo):
    tweetParts()



# tweet if there were any zero-day vulnerabilities fixed
def tweetZeroDays():
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


if releasesWithZeroDays > 0:
    tweetZeroDays()



# tweet if there are any changes to the last 20 release notes
def tweetChanges():
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


if entriesChanged > 0:
    tweetChanges()



# tweet how many security issues were fixed in Apple web servers in the previous month
if date.today().day == 1:
    lastMonth = int(date.today().strftime('%m')) - 1
    if lastMonth < 10:
        lastMonth = f"0{lastMonth}"
    nameLastMonth = "January February March April May June July August September October November December".split()[int(lastMonth)-1]

    currentDateFormatThree = f"{date.today().year}-{lastMonth}"

    webLink = "https://support.apple.com/en-us/HT201536"
    webPage = requests.get(webLink).text
    numberOfFixes = len(re.findall(currentDateFormatThree, webPage))

    results = f"In {nameLastMonth}, Apple fixed {numberOfFixes} security issues in their websites :globe_with_meridians:\n\n"

    allFixes = re.findall(rf"<em>{currentDateFormatThree}(.*)</em>", webPage)
    numberOfFixesOnAppleDotCom = len(re.findall(r"apple.com", str(allFixes)))
    numberOfFixesOnIcloudDotCom = len(re.findall(r"icloud.com", str(allFixes)))
    numberOfOthers = numberOfFixes - numberOfFixesOnAppleDotCom - numberOfFixesOnIcloudDotCom

    if numberOfFixesOnAppleDotCom >= 1:
        results += f":apple: {numberOfFixesOnAppleDotCom} of them on apple[.]com\n"
    if numberOfFixesOnIcloudDotCom >= 1:
        results += f":cloud: {numberOfFixesOnIcloudDotCom} of them on icloud[.]com\n"
    if numberOfOthers >= 1:
        results += f"and {numberOfOthers} on other domains\n"
    results += f"{webLink}"

    api.update_status(emoji.emojize(f"{results}", use_aliases=True))



# tweet how many vulnerabilities were fixed in the four latest series of iOS
def iosTotalReport():
    # calculate previous three iOS versions and add them all to iosVersions variable
    iosVersions = []
    iosVersions.append(latestiosVersion)
    iosVersions.append(latestiosVersion - 1)
    iosVersions.append(latestiosVersion - 2)
    iosVersions.append(latestiosVersion - 3)

    # get all the links of release notes, count CVEs and save the results to allCVEs variable
    iosTd = {}
    alliosLinks = {}
    allCVEs = {}

    for version in iosVersions:
        regex = r"'[^']+iOS\s" + str(version) + "[^']+',"
        iosTd[f"{version}"] = re.findall(regex, str(allTd))

        alliosLinks[f"{version}"] = re.findall(r'href="([^"]+)', str(iosTd[f"{version}"]))

        currentCVEs = 0
        for link in alliosLinks[f"{version}"]:
            page = requests.get(link).text
            currentCVE = len(re.findall("CVE", page)) - 1
            currentCVEs += currentCVE
            allCVEs[f"{version}"] = currentCVEs

    results = f"iOS {iosVersions[0] + 1} was released today. In iOS {list(allCVEs.keys())[0]} series Apple fixed in total of {list(allCVEs.values())[0]} security issues. :hammer_and_pick:\n\nCOMPARED TO:\n"

    iosVersions.pop(0)

    for version in iosVersions:
        results += f"- {allCVEs[f'{version}']} of issues fixed in iOS {version} series\n"

    api.update_status(emoji.emojize(f"{results}", use_aliases=True))


# if there is new major iOS update run the iosTotalReport function
if re.compile("(%s|%s)" % (r"iOS\s\d+[^0-9a-z.]", r"iOS\s\d+\.0[^0-9a-z.]")).findall(str(latestRows)) != []:
    iosTotalReport()
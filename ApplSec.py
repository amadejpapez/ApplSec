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

headers = []
CVEs = []
changedLinks = []
added = []
updated = []
newLinks = []
iosCVEs = []
iosHeaders = []
iosLinks = []
zeroDaysHeader = []
zeroDays = []

def getData(listofLinks):
    headers.clear()
    for link in listofLinks:
        page = requests.get(link).text
        # grab the second title from the page and add it to variable "headers"
        currentHeader = re.findall(r"<h2>(.*)<.h2>", page)[1]
        currentHeader = currentHeader.replace("*", "")
        headers.append(currentHeader)

        # count CVEs on the page and add the number to the variable "CVEs"
        currentCVE = (len(re.findall("CVE", page)) - 1)
        if currentCVE > 1:
            CVEs.append(f"{currentCVE} bugs fixed")
        elif currentCVE == 1:
            CVEs.append(f"{currentCVE} bug fixed")
        else:
            CVEs.append("no bugs fixed")

        # search for any updated entries or any new added entries
        if listofLinks == changedLinks:
            number = (len(re.findall(entryAdded, page)))
            if number == 0:
                added.append("none")
            if number == 1:
                added.append(f"{number} entry added")
            elif number > 1:
                added.append(f"{number} entries added")

            number = (len(re.findall(entryUpdated, page)))
            if number == 0:
                updated.append("none")
            if number == 1:
                updated.append(f"{number} entry updated")
            elif number > 1:
                updated.append(f"{number} entries updated")


        if listofLinks == newLinks:
            # gather all iOS versions data so it can be used for tweeting which parts got the most fixes
            if "iOS" in currentHeader:
                global iosCVEs
                iosCVEs.append(currentCVE)
                global iosHeaders
                iosHeaders.append(currentHeader)
                global iosLinks
                iosLinks.append(link)

            # search if there were any zero-day vulnerabilities fixed
            if "in the wild" in page or "actively exploited" in page:
                zeroDaysHeader.append(currentHeader)
                number = len(re.findall("in the wild", page)) + len(re.findall("actively exploited", page))
                if number == 1:
                    number = f"{number} zero-day"
                else:
                    number = f"{number} zero-days"
                zeroDays.append(number)



# set emojis depending on the title and add it to the variable "emojis"
def setEmojis(x):
    global emojis
    emojis = []
    for header in x:
        if "iOS" in header:
            emojis.append(":iphone:")
            # if iOS is in the title, take only the first part; without iPadOS
            if x == iosHeaders:
                x[x.index(header)] = header.split("and", 1)[0].rstrip().replace("iOS", "iOS AND iPadOS")
            else:
                x[x.index(header)] = header.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")
        elif "watchOS" in header:
            emojis.append(":watch:")
        elif "tvOS" in header or "Apple TV" in header:
            emojis.append(":tv:")
        elif "macOS" in header:
            emojis.append(":computer:")
            # if macOS is in the title, take only the first part of the title
            x[x.index(header)] = header.split(",", 1)[0]
        elif "iCloud" in header:
            emojis.append(":cloud:")
        elif "iTunes" in header:
            emojis.append(":musical_note:")
        else:
            emojis.append(":hammer_and_wrench:")


mainLink = "https://support.apple.com/en-us/HT201222"
mainPage = requests.get(mainLink).text
mainPage = mainPage.replace("<br>", "</td>")
allTd = re.findall(r"<td>(.*)</td>", mainPage)[:20*3]
allLinks = re.findall(r'href="(https://support.apple.com/kb/[A-Z0-9]+)"', str(allTd))
currentDateFormatOne = f"{date.today().day} {date.today().strftime('%b')} {date.today().year}"

# tweet if there were any new updates released
def tweetNewUpdates():
    global mainPage
    global newLinks
    global headers
    numberOfUpdates = len(re.findall(currentDateFormatOne, mainPage))
    newTd = allTd[:numberOfUpdates*3]

    rows = [newTd[x:x+3] for x in range(0, len(newTd), 3)]
    emptyHeaders = []

    for row in rows:
        if "href" in str(row):
            newLinks.append(re.findall(r'href="(.*)"', str(row)))
        else:
            emptyHeaders.append(re.findall(r"'([a-zA-Z]*\s[a-zA-Z]*?\s?[a-zA-Z]*?\s?[0-9]*\.?[0-9]*?\.?[0-9]*?\s?[a-zA-Z]*?\s?[a-zA-Z]*?\s?[0-9]*?\.?[0-9]*?\.?[0-9]*?)',\s'[a-zA-Z]", str(row)))

    emptyHeaders = sum(emptyHeaders, [])
    newLinks = sum(newLinks, [])
    getData(newLinks)
    headers += emptyHeaders
    setEmojis(headers)

    def setTitleForNewUpdates(number):
        global results1
        if number == 1:
            results1 = ":collision: NEW UPDATE RELEASED :collision:\n\n"
        else:
            results1 = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    results2 = ""
    resultsT2 = ""

    for header, emoj in zip(headers, emojis):
        if len(re.findall("-", results2)) < 6:
            if len(CVEs) >= 1:
                results2 += f"{emoj} {header} - {CVEs[0]}\n"
                CVEs.pop(0)
            else:
                results2 += f"{emoj} {header} - no bugs fixed\n"
        else:
            if len(CVEs) >= 1:
                resultsT2 += f"{emoj} {header} - {CVEs[0]}\n"
                CVEs.pop(0)
            else:
                resultsT2 += f"{emoj} {header} - no bugs fixed\n"

    setTitleForNewUpdates(len(re.findall("-", results2)))
    results2 += f"{mainLink}\n"
    results = results1 + results2
    api.update_status(emoji.emojize(f"{results}", use_aliases=True))

    if resultsT2 != "":
        setTitleForNewUpdates(len(re.findall("-", resultsT2)))
        results = results1 + resultsT2
        api.update_status(emoji.emojize(f"{results}", use_aliases=True))

if currentDateFormatOne in allTd:
    tweetNewUpdates()



# tweet top five parts that got bug fixes in a new iOS update
def tweetParts():
    global iosHeaders
    setEmojis(iosHeaders)
    partHeader = sorted(iosHeaders, reverse=True)[0]
    partCVE = iosCVEs[iosHeaders.index(partHeader)]
    partLink = iosLinks[iosHeaders.index(partHeader)]

    page = requests.get(partLink).text
    allStrong = Counter(re.findall(r"<strong>(.*)<.strong>", page))
    allStrong = OrderedDict(sorted(allStrong.items(), reverse=True, key=lambda t: t[1]))

    results = f":hammer_and_pick: FIXED IN {partHeader} :hammer_and_pick:\n\n"

    numberParts = 0

    for key, value in allStrong.items():
        if len(re.findall("-", results)) <= 3:
            numberParts += value
            if value == 1:
                results += f"- {value} bug in {key}\n"
            else:
                results += f"- {value} bugs in {key}\n"

    numberParts = partCVE - numberParts
    if numberParts >= 1:
        results += f"and {numberParts} other vulnerabilities fixed\n"

    results += f"{partLink}\n"
    api.update_status(emoji.emojize(f"{results}", use_aliases=True))

if iosHeaders != []:
    tweetParts()



# tweet if there were any zero-day vulnerabilities fixed
def tweetZeroDays():
    setEmojis(zeroDaysHeader)

    global results
    def setTitleForZeroDays(number):
        global results
        if number == 1:
            results = ":mega: EMERGENCY UPDATE :mega:\n\n"
        else:
            results = ":mega: EMERGENCY UPDATES :mega:\n\n"

    setTitleForZeroDays(len(zeroDaysHeader))

    resultsT2 = ""
    for num, header in zip(zeroDays, zeroDaysHeader):
        if len(re.findall("fixed", results)) <= 4:
            results += f"{num} fixed in {header}\n"
        else:
            resultsT2 += f"{num} fixed in {header}\n"

    api.update_status(emoji.emojize(f"{results}", use_aliases=True))

    if resultsT2 != "":
        setTitleForZeroDays(len(re.findall("fixed", resultsT2)))
        results += resultsT2
        api.update_status(emoji.emojize(f"{results}", use_aliases=True))

if zeroDays != []:
    tweetZeroDays()



# tweet if there are any changes to the last 20 release notes
def tweetChanges(links):
    getData(changedLinks)
    setEmojis(headers)

    def setTitleForChangedReleases(number):
        global results1
        if number == 1:
            results1 = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
        else:
            results1 = f":arrows_counterclockwise: {number} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    results2 = ""
    resultsT2 = ""

    for emoj, header, add, update in zip(emojis, headers, added, updated):
        if len(re.findall("-", results2)) < 4:
            if add == "none" and update != "none":
                results2 += f"{emoj} {header} - {update}\n"
            if add != "none" and update == "none":
                results2 += f"{emoj} {header} - {add}\n"
            if add != "none" and update != "none":
                results2 += f"{emoj} {header} - {add}, {update}\n"
        else:
            if add == "none" and update != "none":
                resultsT2 += f"{emoj} {header} - {update}\n"
            if add != "none" and update == "none":
                resultsT2 += f"{emoj} {header} - {add}\n"
            if add != "none" and update != "none":
                resultsT2 += f"{emoj} {header} - {add}, {update}\n"

    setTitleForChangedReleases(len(re.findall("-", results2)))
    results = results1 + results2
    api.update_status(emoji.emojize(f"{results}", use_aliases=True))

    if resultsT2 != "":
        setTitleForChangedReleases(len(re.findall("-", resultsT2)))
        results = results1 + resultsT2
        api.update_status(emoji.emojize(f"{results}", use_aliases=True))


for link in allLinks:
    currentDateFormatTwo = f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
    entryAdded = f"Entry added {currentDateFormatTwo}"
    entryUpdated = f"Entry updated {currentDateFormatTwo}"
    page = requests.get(link).text

    if entryAdded in page or entryUpdated in page:
        changedLinks.append(link)

if changedLinks != []:
    tweetChanges(changedLinks)
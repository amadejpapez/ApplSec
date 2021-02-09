import re
import emoji
import tweepy
import requests
from datetime import date
from collections import Counter, OrderedDict

api_key = "NeqCGihR5p01SE2I35QppLYGP"
api_secret_key = "24FtTcjPMN4fukNTZzDvnsajsYieYoiPd40XWOZwC8HY4GsiR8"
access_token = "1357726978309259272-sgF1Ukjv7RNauDYak8GsoUl7pShAwz"
access_secret_key = "RbQDmSrzkJc39JgrnVFxHuECo9cLqxNJbOdDbYfJagz9X"

auth = tweepy.OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_secret_key)
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

def getData(link):
    for x in link:
        page = requests.get(x).text
        # grab the second title from the page and add it to variable "headers"
        currentHeader = re.findall(r"<h2>(.*)<.h2>", page)[1]
        headers.append(currentHeader)

        # count CVEs on the page and add the number to the variable "CVEs"
        currentCVE = (len(re.findall("CVE", page)) - 1)
        if currentCVE > 1:
            CVEs.append(str(currentCVE) + " bugs fixed")
        elif currentCVE == 1:
            CVEs.append(str(currentCVE) + " bug fixed")
        else:
            CVEs.append("no bugs fixed")

        # search for any updated entries or any new added entries
        if link == changedLinks:
            search = "Entry added " + str(currentDateFormatTwo)
            number = (len(re.findall(search, page)))
            if number == 1:
                added.append(str(number) + " entry added")
            elif number > 1:
                added.append(str(number) + " entries added")

            search = "Entry updated " + str(currentDateFormatTwo)
            number = (len(re.findall(search, page)))
            if number == 1:
                updated.append(str(number) + " entry updated")
            elif number > 1:
                updated.append(str(number) + " entries updated")


        if link == newLinks:
            # gather all iOS versions data so it can be used for tweeting which parts got the most fixes later
            if "iOS" in currentHeader:
                global iosCVEs
                iosCVEs.append(currentCVE)
                global iosHeaders
                iosHeaders.append(currentHeader)
                global iosLinks
                iosLinks.append(x)

            # search if there were any zero-day vulnerabilities fixed
            if "in the wild" in page or "actively exploited" in page:
                zeroDaysHeader.append(currentHeader)
                zeroDays.append(len(re.findall("in the wild", page)) + len(re.findall("actively exploited", page)))


# set emojis depending on the title and add it to the variable "emojis"
emojis = []
def setEmojis(names):
    emojis.clear()
    for x in names:
        if "iOS" in x:
            emojis.append(":iphone: ")
            # if iOS is in the title, take only the first part; without iPadOS
            names[names.index(x)] = x.split("and", 1)[0].rstrip()
        elif "watchOS" in x:
            emojis.append(":watch: ")
        elif "tvOS" in x or "Apple TV" in x:
            emojis.append(":tv: ")
        elif "macOS" in x:
            emojis.append(":computer: ")
            # if macOS is in the title, take only the first part of the title
            names[names.index(x)] = x.split(",", 1)[0]
        elif "iCloud" in x:
            emojis.append(":cloud: ")
        elif "iTunes" in x:
            emojis.append(":musical_note: ")
        else:
            emojis.append(":hammer_and_wrench: ")


# tweet if there were any new updates released
mainLink = "https://support.apple.com/en-us/HT201222"
mainPage = requests.get(mainLink).text
allLinks = re.findall(r'href="(https://support.apple.com/kb/[A-Z0-9]+)"', mainPage)
currentDateFormatOne = str(date.today().day) + " " + str(date.today().strftime("%B")[0:3]) + " " + str(date.today().year)

if currentDateFormatOne in mainPage:
    updates = len(re.findall(currentDateFormatOne, mainPage))
    mainPage = mainPage.replace("<br>", "</td>")
    allTd = re.findall(r"<td>(.*)</td>", mainPage)[:updates*3]
    rows = [allTd[x:x+3] for x in range(0, len(allTd), 3)]
    emptyHeaders = []

    for x in rows:
        if "href" in str(x):
            newLinks.append(re.findall(r'href="(.*)"', str(x)))
        else:
            emptyHeaders.append(re.findall(r"'([a-zA-Z]+.?[a-zA-Z]*?.?[0-9]+.?[0-9]*?.?[0-9]*?.?[a-z]*?.?[a-zA-Z]*?.[a-zA-Z]*?[0-9]*?.?[0-9]*?.?[0-9]*?.?)',", str(x)))

    emptyHeaders = sum(emptyHeaders, [])
    newLinks = sum(newLinks, [])
    getData(newLinks)
    headers += emptyHeaders
    setEmojis(headers)

    results2 = ""
    results3 = ""
    resultsV2 = ""
    for x in headers:
        if len(re.findall("-", results2)) < 6:
            if len(CVEs) >= 1:
                results2 += emojis[0] + x + " - " + CVEs[0] + "\n"
                CVEs.pop(0)
            else:
                results2 += emojis[0] + x + " - no bugs fixed\n"
            emojis.pop(0)
        else:
            if len(CVEs) >= 1:
                resultsV2 += emojis[0] + x + " - " + CVEs[0] + "\n"
                CVEs.pop(0)
            else:
                resultsV2 += emojis[0] + x + " - no bugs fixed\n"
            emojis.pop(0)

    def setTitle(number):
        global results1
        if number == 1:
            results1 = ":collision: NEW UPDATE RELEASED :collision:\n\n"
        else:
            results1 = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    results3 += mainLink + "\n"
    setTitle(len(re.findall("-", results2)))
    results = results1 + results2 + results3
    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))

    if resultsV2 != "":
        setTitle(len(re.findall("-", resultsV2)))
        results = results1 + resultsV2
        api.update_status(emoji.emojize("{}".format(results), use_aliases=True))


# tweet top five parts that got bug fixes in a new iOS update
if iosHeaders != []:
    iosHeaders = sorted(iosHeaders, reverse=True)
    setEmojis(iosHeaders)
    partHeader = iosHeaders[0]
    partCVE = iosCVEs[iosHeaders.index(partHeader)]
    iosLinks = iosLinks[iosHeaders.index(partHeader)]

    page = requests.get(iosLinks).text
    allStrong = Counter(re.findall(r"<strong>(.*)<.strong>", page))
    allStrong = OrderedDict(sorted(allStrong.items(), reverse=True, key=lambda t: t[1]))

    results = ":hammer_and_pick: FIXED IN " + partHeader + " :hammer_and_pick:\n\n"
    numberParts = 0

    for key, value in allStrong.items():
        if len(re.findall("-", results)) <= 3:
            numberParts += value
            if value == 1:
                results += "- " + str(value) + " bug in " + str(key) + "\n"
            else:
                results += "- " + str(value) + " bugs in " + str(key) + "\n"

    numberParts = partCVE - numberParts
    if numberParts >= 1:
        results += "and " + str(numberParts) + " other vulnerabilities fixed\n"

    results += iosLinks + "\n"
    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))


# tweet if there were any zero-day vulnerabilities fixed
if zeroDays != []:
    setEmojis(zeroDaysHeader)
    results2 = ""
    results3 = ""
    resultsV2 = ""

    for x in zeroDays:
        if len(re.findall("zero-day", results2)) < 4:
            if x == 1:
                results2 += str(x) + " zero-day fixed in " + zeroDaysHeader[0] + "\n"
            else:
                results2 += str(x) + " zero-days fixed in " + zeroDaysHeader[0] + "\n"
            zeroDaysHeader.pop(0)
        else:
            if x == 1:
                resultsV2 += str(x) + " zero-day fixed in " + zeroDaysHeader[0] + "\n"
            else:
                resultsV2 += str(x) + " zero-days fixed in " + zeroDaysHeader[0] + "\n"
            zeroDaysHeader.pop(0)

    def setTitle2(number):
        global results1
        if number == 1:
            results1 = ":mega: EMERGENCY UPDATE :mega:\n\n"
        else:
            results1 = ":mega: EMERGENCY UPDATES :mega:\n\n"

    setTitle2(len(re.findall("zero-day", results2)))
    results = results1 + results2
    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))

    if resultsV2 != "":
        setTitle2(len(re.findall("zero-day", resultsV2)))
        results = results1 + resultsV2
        api.update_status(emoji.emojize("{}".format(results), use_aliases=True))


# tweet if there are any changes to the last 20 release notes
for x in allLinks[:27]:
    currentDateFormatTwo = str(date.today().strftime("%B")) + " " + str(date.today().day) + ", " + str(date.today().year)
    entryAdded = "Entry added " + str(currentDateFormatTwo)
    entryUpdated = "Entry updated " + str(currentDateFormatTwo)
    page = requests.get(x).text

    if entryAdded in page or entryUpdated in page:
        changedLinks.append(x)

if changedLinks != []:
    headers.clear()
    getData(changedLinks)
    setEmojis(headers)
    results2 = ""
    results3 = ""
    resultsV2 = ""

    for x in headers:
        if len(re.findall("-", results2)) < 4:
            if len(added) == 0 and len(updated) >= 1:
                results2 += emojis[0] + x + " - " + str(updated[0]) + "\n"
            if len(added) >= 1 and len(updated) == 0:
                results2 += emojis[0] + x + " - " + str(added[0]) + "\n"
            if len(added) >= 1 and len(updated) >= 1:
                results2 += emojis[0] + x + " - " + str(added[0]) + ", " + str(updated[0]) + "\n"
        else:
            if len(added) == 0 and len(updated) >= 1:
                resultsV2 += emojis[0] + x + " - " + str(updated[0]) + "\n"
            if len(added) >= 1 and len(updated) == 0:
                resultsV2 += emojis[0] + x + " - " + str(added[0]) + "\n"
            if len(added) >= 1 and len(updated) >= 1:
                resultsV2 += emojis[0] + x + " - " + str(added[0]) + ", " + str(updated[0]) + "\n"

        if len(added) >= 1:
            added.pop(0)
        if len(updated) >= 1:
            updated.pop(0)
        emojis.pop(0)

    def setTitle3(number):
        global results1
        if number == 1:
            results1 = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
        else:
            results1 = ":arrows_counterclockwise: " + str(number) + " SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    setTitle3(len(re.findall("-", results2)))
    results = results1 + results2
    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))

    if resultsV2 != "":
        setTitle3(len(re.findall("-", resultsV2)))
        results = results1 + resultsV2
        api.update_status(emoji.emojize("{}".format(results), use_aliases=True))
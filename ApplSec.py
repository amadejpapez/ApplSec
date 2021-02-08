import re
import emoji
import tweepy
import requests
from datetime import date
from collections import Counter
from collections import OrderedDict
from bs4 import BeautifulSoup, SoupStrainer

api_key = "x"
api_secret_key = "x"
access_token = "x"
access_secret_key = "x"

auth = tweepy.OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_secret_key)
api = tweepy.API(auth)


headers = []
emojis = []
CVEs = []
added = []
updated = []
entriesAdded = []
entriesUpdated = []

def getData(link):
    zeroDays = 0
    results3 = ""
    for x in link:
        page = requests.get(x)
        soup = BeautifulSoup(page.content, "html.parser")

        # get data about title of the new version
        allHeaders = soup.find_all("h2")
        currentHeader = re.sub("<[^>]*?>","", str(allHeaders[1]))
        if "macOS" in currentHeader:
            # if macOS is in the title, take only the first part of the title
            currentHeader = currentHeader.split(",", 1)[0]
        if "iOS" in currentHeader:
            # if iOS is in the title, take only the first part; without iPadOS
            currentHeader = currentHeader.split("and", 1)[0].rstrip()
        headers.append(currentHeader)

        # set emojis specific to the title
        if "iOS" in currentHeader:
            emojis.append(":iphone: ")
        elif "watchOS" in currentHeader:
            emojis.append(":watch: ")
        elif "tvOS" in currentHeader:
            emojis.append(":tv: ")
        elif "macOS" in currentHeader:
            emojis.append(":computer: ")
        elif "iCloud" in currentHeader:
            emojis.append(":cloud: ")
        else:
            emojis.append(":hammer_and_wrench: ")

        # get data about the number of CVEs that were fixed
        numberCVE = (len(re.findall("CVE", str(soup))) - 1)
        if numberCVE == 1:
            text = str(numberCVE) + " bug fixed"
        else:
            text = str(numberCVE) + " bugs fixed"
        CVEs.append(text)

        # get data about which parts got bug fixes in the latest iOS update
        if "iOS 14" in currentHeader:
            allStrong = soup.find_all("strong")
            allStrong = re.sub("<[^>]*?>","", str(allStrong))
            allStrong = allStrong.strip('][').split(', ')
            global countStrong
            countStrong = Counter(allStrong)
            global partHeader
            partHeader = currentHeader
            global partLink
            partLink = x

        # get data if any entries were added
        if link == entriesAdded:
            search = "Entry added " + str(currentDateFormatTwo)
            number = (len(re.findall(search, str(soup))))
            if number == 1:
                text = str(number) + " entry added"
            else:
                text = str(number) + " entries added"
            added.append(text)

        # get data if any entries were updated
        if link == entriesUpdated:
            search = "Entry updated " + str(currentDateFormatTwo)
            number = (len(re.findall(search, str(soup))))
            if number == 1:
                text = str(text) + " entry updated"
            else:
                text = str(text) + " entries updated"
            updated.append(text)

        # get data if there were any zero-day vulnerabilities fixed
        if link == newLinks:
            if "iOS" in currentHeader:
                global iosCVE
                iosCVE = numberCVE

            if "in the wild" or "actively exploited" in soup:
                zeroDays = len(re.findall("in the wild", str(soup)))
                zeroDays += len(re.findall("actively exploited", str(soup)))
                if zeroDays == 1:
                    results3 += str(zeroDays) + " zero-day fixed in " + currentHeader + "\n"
                elif zeroDays > 1:
                    results3 += str(zeroDays) + " zero-days fixed in " + currentHeader + "\n"

    if zeroDays >= 1:
        if len(re.findall("zero-day", results3)) == 1:
            results2 = ":mega: EMERGENCY UPDATE :mega:\n\n"
        else:
            results2 = ":mega: EMERGENCY UPDATES :mega:\n\n"
        results = results2 + results3

        print(emoji.emojize("{}".format(results), use_aliases=True))


# get all the links from the page
allLinks = []
mainLink = "https://support.apple.com/en-us/HT201222"
mainPage = requests.get(mainLink).text
for link in BeautifulSoup(mainPage, features="html.parser", parse_only=SoupStrainer("a")):
    if link.has_attr("href"):
        allLinks.append(link["href"])

# check and tweet results if there are were new updates released
currentDateFormatOne = str(date.today().day) + " " + str(date.today().strftime("%B")[0:3]) + " " + str(date.today().year)
if currentDateFormatOne in mainPage:
    # get only the new links from the page
    newLinks = allLinks[22:len(re.findall(currentDateFormatOne, mainPage)) + 22]
    getData(newLinks)

    if len(headers) == 1:
        results = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        results = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for x in headers:
        results += emojis[0] + x + " - " + CVEs[0] + "\n"
        CVEs.pop(0)
        emojis.pop(0)

    results += mainLink + "\n"
    print(emoji.emojize("{}".format(results), use_aliases=True))


# tweet top 5 parts that got bug fixes in a new iOS update
if partHeader != "":
    numberParts = 0
    results = ":hammer_and_pick: FIXED IN " + partHeader + " :hammer_and_pick:\n\n"

    countStrong = OrderedDict(sorted(countStrong.items(), reverse=True, key=lambda t: t[1]))
    for key, value in countStrong.items():
        if len(re.findall("-", results)) <= 3:
            numberParts += value
            if value == 1:
                results += "- " + str(value) + " bug in " + str(key) + "\n"
            else:
                results += "- " + str(value) + " bugs in " + str(key) + "\n"

    numberParts = iosCVE - numberParts
    results += "and " + str(numberParts) + " other vulnerabilities patched!\n" + partLink + "\n"
    print(emoji.emojize("{}".format(results), use_aliases=True))


# check if there are any changes to the last 20 release pages and tweet the results
for x in allLinks[22:42]:
    currentDateFormatTwo = str(date.today().strftime("%B")) + " " + str(date.today().day) + ", " + str(date.today().year)
    page = requests.get(x).text

    search = "Entry added " + str(currentDateFormatTwo)
    if search in page:
        entriesAdded.append(x)

    search = "Entry updated " + str(currentDateFormatTwo)
    if search in page:
        entriesUpdated.append(x)

if entriesAdded != [] or entriesUpdated != []:
    headers.clear()
    getData(entriesAdded)
    getData(entriesUpdated)

    results3 = ""
    for x in headers:
        if len(added) == 0 and len(updated) >= 1:
            results3 += emojis[0] + x + " - " + str(updated[0]) + "\n"
        if len(added) >= 1 and len(updated) == 0:
            results3 += emojis[0] + x + " - " + str(added[0]) + "\n"
        if len(added) >= 1 and len(updated) >= 1:
            results3 += emojis[0] + x + " - " + str(added[0]) + ", " + str(updated[0]) + "\n"

        if len(added) >= 1:
            added.pop(0)
        if len(updated) >= 1:
            updated.pop(0)
        emojis.pop(0)

    if len(re.findall("-", results3)) == 1:
        results2 = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        results2 = ":arrows_counterclockwise: " + str(len(re.findall("-", results3))) + " SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    results = results2 + results3
    print(emoji.emojize("{}".format(results), use_aliases=True))
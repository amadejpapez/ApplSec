import re
import emoji
import tweepy
import requests
from datetime import date
from collections import Counter
from bs4 import BeautifulSoup, SoupStrainer

api_key = "x"
api_secret_key = "x"
access_token = "x"
access_secret_key = "x"

auth = tweepy.OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_secret_key)
api = tweepy.API(auth)


updatesPage = requests.get("https://support.apple.com/en-us/HT201222").text
currentDateFormatOne = str(date.today().day) + " " + str(date.today().strftime("%B")[0:3]) + " " + str(date.today().year)
currentDateFormatTwo = str(date.today().strftime("%B")) + " " + str(date.today().day) + ", " + str(date.today().year)

newHeader = []
newCVE = []
countStrong = []
newStrong = []
entriesAdded = []
entriesUpdated = []
numberOfAdded = []
numberOfUpdated = []
emojis = []
newAdded = []
newUpdated = []

def getData(link):
    number0Days = 0
    for x in link:
        newPage = requests.get(x)
        soup = BeautifulSoup(newPage.content, "html.parser")

        # get the title of the new version
        allHeaders = soup.find_all("h2")
        currentHeader = re.sub("<[^>]*?>","", str(allHeaders[1]))
        if "macOS" in currentHeader:
            # if macOS in the title take only the first part
            currentHeader = currentHeader.split(",", 1)[0]
        if "iOS" in currentHeader:
            # if iOS in the title take only the first part; without iPadOS
            currentHeader = currentHeader.split("and", 1)[0].rstrip()
        newHeader.append(currentHeader)

        # set emojis
        if "iOS" in currentHeader:
            emojis.append(":iphone: ")
        elif "watchOS" in currentHeader:
            emojis.append(":watch: ")
        elif "tvOS" in currentHeader:
            emojis.append(":tv: ")
        elif "macOS" in currentHeader:
            emojis.append(":computer: ")
        else:
            emojis.append(":hammer_and_wrench: ")

        # get the number of CVEs on the page
        numberCVE = (len(re.findall("CVE", str(soup))) - 1)
        if numberCVE == 1:
            numberCVE = str(numberCVE) + " bug fixed"
        else:
            numberCVE = str(numberCVE) + " bugs fixed"
        newCVE.append(numberCVE)

        # get topics
        allStrong = soup.find_all("strong")
        countStrong.append(Counter(allStrong).most_common)
        newStrong.append(re.sub("<[^>]*?>","", str(countStrong)))
        countStrong.clear()

        # search for added entries
        if link == entriesAdded:
            search = "Entry added " + str(currentDateFormatTwo)
            numberOfAdded = (len(re.findall(search, str(soup))))
            if numberOfAdded == 1:
                numberOfAdded = str(numberOfAdded) + " entry added"
            else:
                numberOfAdded = str(numberOfAdded) + " entries added"
            newAdded.append(numberOfAdded)

        # search for updated entries
        if link == entriesUpdated:
            search = "Entry updated " + str(currentDateFormatTwo)
            numberOfUpdated = (len(re.findall(search, str(soup))))
            if numberOfUpdated == 1:
                numberOfUpdated = str(numberOfUpdated) + " entry updated"
            else:
                numberOfUpdated = str(numberOfUpdated) + " entries updated"
            newUpdated.append(numberOfUpdated)

        # search if there were any zero-day vulnerabilities fixed
        if link == newLinks:
            if "in the wild" or "actively exploited" in soup:
                number0Days = len(re.findall("in the wild", str(soup)))
                number0Days += len(re.findall("actively exploited", str(soup)))
                results0Days3 = ""
                if number0Days == 1:
                    results0Days3 += str(number0Days) + " zero-day vulnerability fixed in " + currentHeader
                else:
                    results0Days3 += str(number0Days) + " zero-day vulnerabilities fixed in " + currentHeader

    if number0Days >= 1:
        if len(re.findall("zero-day", results0Days3)) == 1:
            results0Days2 = ":mega: EMERGENCY UPDATE :mega:\n\n"
        else:
            results0Days2 = ":mega: EMERGENCY UPDATES :mega:\n\n"
        results0Days1 = results0Days2 + results0Days3

        api.update_status(emoji.emojize("{}".format(results0Days1), use_aliases=True))


allLinks = []
for link in BeautifulSoup(updatesPage, features="html.parser", parse_only=SoupStrainer("a")):
    # get all the links from the page
    if link.has_attr("href"):
        allLinks.append(link["href"])


if currentDateFormatOne in updatesPage:
    # get only the new links from the page
    newLinks = allLinks[22:len(re.findall(currentDateFormatOne, updatesPage)) + 22]
    getData(newLinks)

    # api.update_status results
    if len(newHeader) == 1:
        results = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        results = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for x in newHeader:
        results += emojis[0] + x + " - " + newCVE[0] + "\n"
        newCVE.pop(0)
        emojis.pop(0)

    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))


for x in allLinks[22:42]:
    # check if the last 20 update pages got any new bug fixes added today
    page = requests.get(x).text

    search = "Entry added " + str(currentDateFormatTwo)
    if search in page:
        entriesAdded.append(x)

    search = "Entry updated " + str(currentDateFormatTwo)
    if search in page:
        entriesUpdated.append(x)

if entriesAdded != [] or entriesUpdated != []:
    # if any security notes were updated
    newHeader.clear()
    getData(entriesAdded)
    getData(entriesUpdated)

    newEntries = entriesAdded + entriesUpdated

    # api.update_status results
    results3 = ""
    for x in newHeader:
        if len(newAdded) == 0 and len(newUpdated) >= 1:
            results3 += emojis[0] + x + " - " + str(newUpdated[0]) + "\n"
        if len(newAdded) >= 1 and len(newUpdated) == 0:
            results3 += emojis[0] + x + " - " + str(newAdded[0]) + "\n"
        if len(newAdded) >= 1 and len(newUpdated) >= 1:
            results3 += emojis[0] + x + " - " + str(newAdded[0]) + ", " + str(newUpdated[0]) + "\n"

        if len(newAdded) >= 1:
            newAdded.pop(0)
        if len(newUpdated) >= 1:
            newUpdated.pop(0)
        emojis.pop(0)

    if len(re.findall("-", results3)) == 1:
        results2 = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        results2 = ":arrows_counterclockwise: " + str(len(re.findall("-", results3))) + " SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    results1 = results2 + results3

    api.update_status(emoji.emojize("{}".format(results1), use_aliases=True))
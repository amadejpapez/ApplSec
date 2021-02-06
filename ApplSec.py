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
numberCVE = []
countStrong = []
newStrong = []

def getData(link):
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

        # get the number of CVEs on the page
        numberCVE.append(len(re.findall("CVE", str(soup))) - 1)

        # search if there were any zero-day vulnerabilities fixed
        number0Days = 0
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
        if "iOS" in x:
            results += ":iphone: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "watchOS" in x:
            results += ":watch: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "tvOS" in x:
            results += ":tv: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "macOS" in x:
            results += ":computer: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        else:
            results += ":hammer_and_wrench: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        numberCVE.pop(0)

    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))


updatedLinks = []
for x in allLinks[22:42]:
    # check if the last 20 update pages got any changes today
    page = requests.get(x).text
    search = "Entry added " + str(currentDateFormatTwo)

    if search in page:
        updatedLinks.append(x)

if updatedLinks != []:
    # if any security notes were updated
    newHeader.clear()
    getData(updatedLinks)

    # api.update_status results
    if len(newHeader) == 1:
        results = ":arrows_counterclockwise: " + str(len(updatedLinks)) + " SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        results = ":arrows_counterclockwise: " + str(len(updatedLinks)) + " SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    for x in newHeader:
        if "iOS" in x:
            results += ":iphone: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "watchOS" in x:
            results += ":watch: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "tvOS" in x:
            results += ":tv: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        elif "macOS" in x:
            results += ":computer: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        else:
            results += ":hammer_and_wrench: " + x + " - " + str(numberCVE[0]) + " bugs fixed\n"
        numberCVE.pop(0)

    api.update_status(emoji.emojize("{}".format(results), use_aliases=True))
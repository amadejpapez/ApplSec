import re
import requests
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer

updatesPage = requests.get("https://support.apple.com/en-us/HT201222").text
currentDateFormatOne = str(date.today().day) + " " + str(date.today().strftime("%B")[0:3]) + " " + str(date.today().year)
currentDateFormatTwo = str(date.today().strftime("%B")) + " " + str(date.today().day) + ", " + str(date.today().year)


newHeader = []
numberCVE = []

def getData(link):
    for x in link:
        newPage = requests.get(x)
        soup = BeautifulSoup(newPage.content, "html.parser")

        # get the title of the new version
        allHeaders = soup.find_all("h2")
        newHeader.append(re.sub("<[^>]*?>","", str(allHeaders[1])))

        # get the number of CVEs on the page
        numberCVE.append(len(re.findall("CVE", str(soup))) - 1)

    for x in newHeader:
        # if there is macOS in the header take only the first part, not the full title
        if "macOS" in x:
            macosIsHere = newHeader.index(x)
            newHeader[macosIsHere] = x.split(",", 1)[0]


allLinks = []
for link in BeautifulSoup(updatesPage, features="html.parser", parse_only=SoupStrainer("a")):
    # get all the links from the page
    if link.has_attr("href"):
        allLinks.append(link["href"])


if currentDateFormatOne in updatesPage:
    # get only the new links from the page
    newLinks = allLinks[22:len(re.findall(currentDateFormatOne, updatesPage)) + 22]
    getData(newLinks)

    # print results
    results = "RELEASED TODAY:\n"
    for x in newHeader:
        results += x + " released with " + str(numberCVE[0]) + " security fixes\n"
        numberCVE.pop(0)
    print(results)


updatedLinks = []
for x in allLinks[22:42]:
    # check if the last 20 update pages got any changes today
    page = requests.get(x).text
    search = "Entry added " + str(currentDateFormatTwo)

    if search in page:
        updatedLinks.append(x)

if updatedLinks != []:
    newHeader.clear()
    getData(updatedLinks)

    # print results
    results = "UPDATED TODAY:\n"
    for x in newHeader:
        results += x + " was released " + str(numberCVE[0]) + " security fixes\n"
        numberCVE.pop(0)
    print(results)
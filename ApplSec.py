import re
import requests
import httplib2
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer


updatesPage = requests.get("https://support.apple.com/en-us/HT201222").text
# currentDate = str(date.today().day) + " " + str(date.today().strftime('%B')[0:3]) + " " + str(date.today().year)
currentDate = str(1) + " " + "Feb" + " " + str(date.today().year)


# checks if there was a new version added today or not
if currentDate in updatesPage:
    wasUpdated = True
else:
    wasUpdated = False


if (wasUpdated == True):
    # if there was an update scrape all the links
    allLinks = []
    http = httplib2.Http()
    status, response = http.request('https://support.apple.com/en-us/HT201222')

    for link in BeautifulSoup(response, features="html.parser", parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            allLinks.append(link['href'])

    # get only the new links
    searchResults = len(re.findall(currentDate, updatesPage)) + 22
    newLinks = allLinks[22:searchResults]

    # scrape new links and gather info from the links
    newHeader = []
    numberCVE = []

    for x in newLinks:
        newLink = requests.get(x)
        soup = BeautifulSoup(newLink.content, 'html.parser')

        # get the header of the new version
        allHeaders = soup.find_all('h2')
        newHeader.append(re.sub("<[^>]*?>","", str(allHeaders[1])))

        # search how many CVEs there are
        numberCVE.append(len(re.findall("CVE", str(soup))) - 1)

    for x in newHeader:
        # if there is macOS in the header take only the first part, not the full header
        if "macOS" in x:
            macosIsHere = newHeader.index(x)
            newHeader[macosIsHere] = x.split(',', 1)[0]

    # print results
    print("PATCH TIME!")
    for x in newHeader:
        print(x + " released with " + str(numberCVE[0]) + " security fixes")
        numberCVE.pop(0)
import re
import requests
import httplib2
from datetime import date
from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer

updatesPage = urlopen("https://support.apple.com/en-us/HT201222").read().decode('utf-8')
currentDate = str(date.today().day) + " " + str(date.today().strftime('%B')[0:3] + " " + str(date.today().year))
currentDat = str(1) + " " + str(date.today().strftime('%B')[0:3] + " " + str(date.today().year))


# stores if there was a new version added today or not
if currentDat in updatesPage:
    wasUpdated = True
else:
    wasUpdated = False


# scrape all links
links = []
if (wasUpdated == True):
    http = httplib2.Http()
    status, response = http.request('https://support.apple.com/en-us/HT201222')

    for link in BeautifulSoup(response, features="html.parser", parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            links.append(link['href'])


    # get new links
    searchResults = len(re.findall(currentDat, updatesPage)) + 22
    newVersion = links[22:searchResults]


    # scrape new versions
    newVersion1 = requests.get(newVersion[0])
    soup = BeautifulSoup(newVersion1.content, 'html.parser')
    # get the header of the new version
    header = soup.find_all('h2')
    header1 = re.sub("<[^>]*?>","", str(header[1]))
    # search how many CVEs there are
    numberCVE1 = len(re.findall("CVE", str(soup))) - 1

    newVersion2 = requests.get(newVersion[1])
    soup = BeautifulSoup(newVersion2.content, 'html.parser')
    # get the header of the new version
    header = soup.find_all('h2')
    header2 = re.sub("<[^>]*?>","", str(header[1]))
    # search how many CVEs there are
    numberCVE2 = len(re.findall("CVE", str(soup))) - 1

    newVersion3 = requests.get("https://support.apple.com/en-us/HT212146")
    soup = BeautifulSoup(newVersion3.content, 'html.parser')
    # get the header of the new version
    header = soup.find_all('h2')
    header3 = re.sub("<[^>]*?>","", str(header[1]))
    # search how many CVEs there are
    numberCVE3 = len(re.findall("CVE", str(soup))) - 1

    newVersion4 = requests.get("https://support.apple.com/en-us/HT212149")
    soup = BeautifulSoup(newVersion4.content, 'html.parser')
    # get the title of the new version
    header = soup.find_all('h2')
    header4 = re.sub("<[^>]*?>","", str(header[1]))
    # search how many CVEs there are
    numberCVE4 = len(re.findall("CVE", str(soup))) - 1

    newVersion5 = requests.get("https://support.apple.com/en-us/HT212148")
    soup = BeautifulSoup(newVersion5.content, 'html.parser')
    # get the title of the new version
    header = soup.find_all('h2')
    header5 = re.sub("<[^>]*?>","", str(header[1]))
    # search how many CVEs there are
    numberCVE5 = len(re.findall("CVE", str(soup))) - 1

    # print results
    print("PATCH TIME!")
    print(header1 + " released with " + str(numberCVE1) + " security fixes")
    print(header2[0:18] + " released with " + str(numberCVE2) + " security fixes")
    print(header3 + " released with " + str(numberCVE3) + " security fixes")
    print(header4 + " released with " + str(numberCVE4) + " security fixes")
    print(header5 + " released with " + str(numberCVE5) + " security fixes")
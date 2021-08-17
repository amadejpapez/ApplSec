import re
from datetime import date

import requests
from create_tweets.post_on_twitter import tweetOrCreateAThread


"""
In month of March Apple fixed 42 security issues in their websites 🌐

🍎 31 of them on apple[.]com
☁️ 1 of them on icloud[.]com
and 10 on other domains
"""

def tweetWebServerFixes():
    lastMonth = int(date.today().strftime("%m")) - 1
    nameLastMonth = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ][lastMonth - 1]

    if lastMonth < 10:
        lastMonth = f"0{lastMonth}"

    currentDateFormatThree = f"<em>{date.today().year}-{lastMonth}"

    mainPage = "https://support.apple.com/en-us/HT201536"
    page = requests.get(mainPage).text
    numberOfFixes = len(re.findall(currentDateFormatThree, page))

    results = f"In {nameLastMonth}, Apple fixed {numberOfFixes} security issues in their web servers. :globe_with_meridians:\n\n"

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

    results += mainPage

    tweetOrCreateAThread("webServerFixes", firstTweet=results)
# tweet how many vulnerabilities were fixed in the four latest series of iOS/watchOS/tvOS/macOS if there is a new major update
# this is only ran in September

import re

import requests
from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetYearlyReport(releases, system, latestSystemVersion):
    info = {}
    versions = []

    # save previous three versions
    if system == "macOS":
        # macOS names are hard coded for now
        versions = ["11", "10.15", "10.14", "10.13"]
    else:
        num = latestSystemVersion
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    # get all the links of release notes, count CVEs and save all the info
    for version in versions:
        info[version] = {"releaseNotes": "", "CVEs": 0, "releases": 0}

        if system == "macOS":
            # if system is macOS, take the name of the macOS version as Security Updates only contain names
            macOSName = re.findall(rf"{system}\s([a-z\s]+){version}", str(releases), re.IGNORECASE)[0]
        else:
            macOSName = "None"

        for release in releases:
            if f"{system} {version}" in release or macOSName in release:
                if "href" in release:
                    # if there are release notes, count all the CVEs
                    info[version]["releaseNotes"] = re.findall(r'href="([^"]+)"', release)
                    page = requests.get(info[version]["releaseNotes"][0]).text

                    currentCVE = len(re.findall("CVE", page)) - 1
                    info[version]["CVEs"] += currentCVE

                info[version]["releases"] += 1

    secondVersion = list(info.keys())[0]

    results = f"{system} {latestSystemVersion} was released today. In {system} {secondVersion} series Apple fixed in total of {info[secondVersion]['CVEs']} security issues over {info[secondVersion]['releases']} releases. :locked_with_key:\n\n:bar_chart: COMPARED TO:\n"
    info.pop(secondVersion)

    for key, value in info.items():
        results += f"- {value['CVEs']} fixed in {system} {key} over {value['releases']} releases\n"

    if system == "macOS":
        # for macOS create a thread with additional info in the second tweet
        secondResults = "Numbers also contain issues from Security and Supplemental Updates."
        tweetOrCreateAThread("tweetYearlyReport", firstTweet=results, secondTweet=secondResults)
    else:
        tweetOrCreateAThread("tweetYearlyReport", firstTweet=results)

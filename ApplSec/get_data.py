# grabs all data from Apple's website and saves it to updatesInfo

import re
from datetime import date

import requests


def getData(releases):
    updatesInfo = {}

    for release in releases:
        if "href" in str(release):
            # if there are release notes, grab the whole page
            releaseNotes = re.findall(r'href="([^\']+)"', str(release))[0]
            page = requests.get(releaseNotes).text

            # grab the header from the page
            title = re.findall(r"<h2>(.*)<.h2>", page)[1]
            title = title.replace("*", "") # remove * from the title which is sometimes added for additional info
        else:
            print(release)
            # if there is no release notes, grab the title from the mainPage
            title = re.findall(r"\['([a-z0-9,\.\-\s]+)", str(release), re.IGNORECASE)[0]
            title = title.rstrip()
            page = None
            releaseNotes = None

        if "macOS" in title:
            # if macOS is in the title, take only the first part of the title
            title = title.split(",", 1)[0]
        elif "iOS" in title and "iPadOS" in title:
            # if they are both in the title remove version number from iPadOS
            title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

        # set emojis depending on the title
        if "iOS" in title:
            emojis = ":iphone:"
        elif "watchOS" in title:
            emojis = ":watch:"
        elif "tvOS" in title or "Apple TV" in title:
            emojis = ":tv:"
        elif "macOS" in title or "Security Update" in title:
            emojis = ":computer:"
        elif "iCloud" in title:
            emojis = ":cloud:"
        elif "Safari" in title:
            emojis = ":globe_with_meridians:"
        elif "iTunes" in title or "Shazam" in title or "GarageBand" in title or "Apple Music" in title:
            emojis = ":musical_note:"
        else:
            emojis = ":hammer_and_wrench:"

        updatesInfo[title] = {"releaseNotes": releaseNotes, "emojis": emojis}

        # grab the number of CVEs from the page
        CVEs = (len(re.findall("CVE", str(page))) - 1)

        if "soon" in str(release):
            updatesInfo[title]["CVEs"] = "no details yet"
        elif CVEs > 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bugs fixed"
        elif CVEs == 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bug fixed"
        else:
            updatesInfo[title]["CVEs"] = "no bugs fixed"

        # search if there were any zero-day vulnerabilities fixed
        if "in the wild" in str(page) or "actively exploited" in str(page):
            num = len(re.findall("in the wild", page)) + len(re.findall("actively exploited", page))
            if num == 1:
                updatesInfo[title]["zeroDays"] = f"{num} zero-day"
            else:
                updatesInfo[title]["zeroDays"] = f"{num} zero-days"

            entries = re.findall(r"(?<=<strong>)(?:.|\n)*?(?=<strong>|<\/div)", page)
            zeroDayEntry = []

            for entry in entries:
                if "in the wild" in entry or "actively exploited" in entry:
                    zeroDayEntry.append(entry)

            updatesInfo[title]["zeroDayCVEs"] = re.findall(r"CVE-[0-9]{4}-[0-9]{4,5}", str(zeroDayEntry))

        else:
            updatesInfo[title]["zeroDays"] = None
            updatesInfo[title]["zeroDayCVEs"] = None

        # check for any updated or added entries
        currentDateFormatTwo = f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
        num = (len(re.findall(f"Entry added {currentDateFormatTwo}", str(page))))

        if num == 1:
            updatesInfo[title]["added"] = f"{num} entry added"
        elif num > 1:
            updatesInfo[title]["added"] = f"{num} entries added"
        else:
            updatesInfo[title]["added"] = None

        num = (len(re.findall(f"Entry updated {currentDateFormatTwo}", str(page))))

        if num == 1:
            updatesInfo[title]["updated"] = f"{num} entry updated"
        elif num > 1:
            updatesInfo[title]["updated"] = f"{num} entries updated"
        else:
            updatesInfo[title]["updated"] = None

    return updatesInfo
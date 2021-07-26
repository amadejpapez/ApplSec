# grabs all data from Apple's website and saves it to updatesInfo

import re
from datetime import date

import requests


def getData(releases):
    updatesInfo = {}

    for release in releases:
        title = re.findall(r"(?:<td>|\">)([^<]+)(?:<br>|<\/a>)", str(release.split("\n")[0]), re.IGNORECASE)[0]
        title = title.rstrip()

        if "href" in str(release):
            # if there are release notes, grab the whole page
            releaseNotesLink = re.findall(r'href="([^\']+)"', str(release))[0]
            releaseNotes = requests.get(releaseNotesLink).text
        else:
            # if there is no release notes
            releaseNotesLink = None
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

        updatesInfo[title] = {"releaseNotes": releaseNotesLink, "emojis": emojis}

        # grab the number of CVEs from the page
        CVEs = len(re.findall("CVE", str(releaseNotes))) - 1

        if "soon" in str(release):
            updatesInfo[title]["CVEs"] = "no details yet"
        elif CVEs > 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bugs fixed"
        elif CVEs == 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bug fixed"
        else:
            updatesInfo[title]["CVEs"] = "no bugs fixed"

        # search if there were any zero-day vulnerabilities fixed
        if "in the wild" in str(releaseNotes) or "actively exploited" in str(releaseNotes):
            num = len(re.findall("in the wild", releaseNotes)) + len(re.findall("actively exploited", releaseNotes))
            if num == 1:
                updatesInfo[title]["zeroDays"] = f"{num} zero-day"
            else:
                updatesInfo[title]["zeroDays"] = f"{num} zero-days"

            entries = re.findall(r"(?<=<strong>)(?:.|\n)*?(?=<strong>|<\/div)", releaseNotes)
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
        num = len(re.findall(f"Entry added {currentDateFormatTwo}", str(releaseNotes)))

        if num == 1:
            updatesInfo[title]["added"] = f"{num} entry added"
        elif num > 1:
            updatesInfo[title]["added"] = f"{num} entries added"
        else:
            updatesInfo[title]["added"] = None

        num = len(re.findall(f"Entry updated {currentDateFormatTwo}", str(releaseNotes)))

        if num == 1:
            updatesInfo[title]["updated"] = f"{num} entry updated"
        elif num > 1:
            updatesInfo[title]["updated"] = f"{num} entries updated"
        else:
            updatesInfo[title]["updated"] = None

    return updatesInfo

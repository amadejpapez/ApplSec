import re
from datetime import date

import requests

"""
Grabs all data from Apple's website and saves it to 'updatesInfo'.

Example:
-----------------------------
'iOS and iPadOS 14.7': {
    'releaseNotes': 'https://support.apple.com/kb/HT212623',
    'emojis': ':iphone:',
    'CVEs': '37 bugs fixed',
    'zeroDays': '3 zero-days',
    'zeroDayCVEs': {
        'CVE-2021-30761': 'WebKit',
        'CVE-2021-30762': 'WebKit',
        'CVE-2021-30713': 'TCC'
    },
    'added': '8 entries added',
    'updated': '1 entry updated'
}
-----------------------------
"""


def getData(releases):
    updatesInfo = {}

    for release in releases:
        title = re.findall(
            r"(?:<td>|\">)([^<]+)(?:<br>|<\/a>)",
            str(release.split("\n")[0]),
            re.IGNORECASE,
        )[0]
        title = title.rstrip()

        if "href" in str(release):
            # if there are release notes, grab the whole page
            releaseNotesLink = re.findall(r'href="([^\']+)"', str(release))[0]
            releaseNotes = requests.get(releaseNotesLink).text
        else:
            # if there is no release notes
            releaseNotesLink = "None"
            releaseNotes = "None"

        if "macOS" in title:
            # if macOS is in the title, take only the first part of the title
            title = title.split(",", 1)[0]
        elif "iOS" in title and "iPadOS" in title:
            # if they are both in the title remove version number from iPadOS
            title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

        # set an emoji depending on the title
        emojiDict = {
            "iOS": ":iphone:",
            "iPadOS": ":iphone:",
            "watchOS": ":watch:",
            "tvOS": ":tv:",
            "Apple TV": ":tv:",
            "macOS": ":computer:",
            "Security Update": ":computer:",
            "iCloud": ":cloud:",
            "Safari": ":globe_with_meridians:",
            "iTunes": ":musical_note:",
            "Shazam": ":musical_note:",
            "GarageBand": ":musical_note:",
            "Apple Music": ":musical_note:"
        }

        for key, value in emojiDict.items():
            if key in title:
                emojis = value
                break
            else:
                emojis = ":hammer_and_wrench:"

        updatesInfo[title] = {"releaseNotes": releaseNotesLink, "emojis": emojis}

        # grab the number of CVEs from the page
        CVEs = len(re.findall("CVE", releaseNotes)) - 1

        if "soon" in str(release):
            updatesInfo[title]["CVEs"] = "no details yet"
        elif CVEs > 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bugs fixed"
        elif CVEs == 1:
            updatesInfo[title]["CVEs"] = f"{CVEs} bug fixed"
        else:
            updatesInfo[title]["CVEs"] = "no bugs fixed"

        # search if there were any zero-day vulnerabilities fixed
        numberOfZeroDays = len(re.findall("in the wild", releaseNotes)) + len(
            re.findall("actively exploited", releaseNotes)
        )

        if numberOfZeroDays > 0:
            if numberOfZeroDays == 1:
                updatesInfo[title]["zeroDays"] = f"{numberOfZeroDays} zero-day"
            else:
                updatesInfo[title]["zeroDays"] = f"{numberOfZeroDays} zero-days"

            updatesInfo[title]["zeroDayCVEs"] = {}

            for entry in re.findall(
                r"((?<=<strong>)(?:.|\n)*?(?=<strong>|<\/div))", releaseNotes
            ):
                if "in the wild" in entry or "actively exploited" in entry:
                    zeroDayCVE = re.findall(r"CVE-[0-9]{4}-[0-9]{4,5}", entry)[0]
                    zeroDayLocation = re.findall(r"(.*)<\/strong>", entry)[0]
                    updatesInfo[title]["zeroDayCVEs"][zeroDayCVE] = zeroDayLocation

        else:
            updatesInfo[title]["zeroDays"] = None
            updatesInfo[title]["zeroDayCVEs"] = None

        # check for any updated or added entries
        currentDateFormatTwo = (
            f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
        )
        num = len(re.findall(f"Entry added {currentDateFormatTwo}", releaseNotes))

        if num == 1:
            updatesInfo[title]["added"] = f"{num} entry added"
        elif num > 1:
            updatesInfo[title]["added"] = f"{num} entries added"
        else:
            updatesInfo[title]["added"] = None

        num = len(re.findall(f"Entry updated {currentDateFormatTwo}", releaseNotes))

        if num == 1:
            updatesInfo[title]["updated"] = f"{num} entry updated"
        elif num > 1:
            updatesInfo[title]["updated"] = f"{num} entries updated"
        else:
            updatesInfo[title]["updated"] = None

    return updatesInfo

import datetime
import re

import requests


def set_emoji(title):
    """Return an emoji depending on the title."""

    emoji_dict = {
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
        "Apple Music": ":musical_note:",
    }

    for key, value in emoji_dict.items():
        if key in title:
            return value

    return ":hammer_and_wrench:"


def check_zero_days(release_notes):
    """Check for specific keywords to find any fixed zero-days."""

    entries = re.findall(r"(?i)(?<=<strong>).*?(?=<strong>|<\/div)", release_notes)
    list_zero_days = {}

    for entry in entries:
        if "in the wild" in entry or "actively exploited" in entry:
            cve = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]{4,5}", entry)[0]
            list_zero_days[cve] = re.findall(r"(?i).+?(?=<\/strong>)", entry)[0]

    count = len(list_zero_days)

    if count > 1:
        return f"{count} zero-days", list_zero_days
    if count == 1:
        return f"{count} zero-day", list_zero_days

    return None, {}


def count_bugs(release, release_notes):
    """Return number of CVEs in the release notes."""

    count = len(re.findall("CVE", release_notes)) - 1

    if count > 1:
        return f"{count} bugs fixed"
    if count == 1:
        return f"{count} bug fixed"
    if "soon" in release[0]:
        return "no details yet"

    return "no bugs fixed"


def check_notes_updates(release_notes):
    """Return if any entries were added or updated today."""

    previous_day = datetime.date.today() - datetime.timedelta(1)
    date_format_two = (
        f"{previous_day.strftime('%B')} {previous_day.day}, {previous_day.year}"
    )
    # tweet is made on the next day for any changes made on the previous day
    # Format: January 2, 2022

    num = len(re.findall(f"added {date_format_two}", release_notes))

    if num == 1:
        added = "1 entry added"
    elif num >= 1:
        added = f"{num} entries added"
    else:
        added = None

    num = len(re.findall(f"updated {date_format_two}", release_notes))

    if num == 1:
        updated = "1 entry updated"
    elif num >= 1:
        updated = f"{num} entries updated"
    else:
        updated = None

    return added, updated


def get_info(releases):
    """
    Gather all data about given releases from Apple's website.

    Input format:
    -----
    [
        [
            "<a href="https://support.apple.com/kb/HT213055">macOS Big Sur 11.6.3</a>",
            "macOS Big Sur",
            "26 Jan 2022"
        ]
    ]
    -----

    Return format:
    -----
    {
        "iOS and iPadOS 14.7": {
            "release_notes": "https://support.apple.com/kb/HT212623",
            "release_date": "26 Jan 2022",
            "emoji": ":iphone:",
            "num_of_bugs": "37 bugs fixed",
            "num_of_zero_days": "3 zero-days",
            "list_of_zero_days": {
                "CVE-2021-30761": "WebKit",
                "CVE-2021-30762": "WebKit",
                "CVE-2021-30713": "TCC"
            },
            "entries_added": "8 entries added",
            "entries_updated": "1 entry updated"
        }
    }
    -----
    """

    release_info = {}

    for release in releases:
        title = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release[0])[0]
        release_date = re.findall(r"(?i)(?<=[>])[^<]+|^[^<]+", release[2])[0]

        if "href" in release[0]:
            release_notes_link = re.findall(r'(?i)href="(.+?)"', release[0])[0]
            release_notes = requests.get(release_notes_link).text
            release_notes = release_notes.replace("\n", "").replace("&nbsp;", " ")
        else:
            release_notes_link = None
            release_notes = ""

        if "iOS" in title and "iPad" in title:
            # if they are both in the title remove version number from iPadOS
            # turn "iOS 15.3 and iPadOS 15.3" into shorter "iOS and iPadOS 15.3"
            title = title.split("and", 1)[0].strip().replace("iOS", "iOS and iPadOS")

        num_zero_days, list_zero_days = check_zero_days(release_notes)
        added, updated = check_notes_updates(release_notes)

        if title in list(release_info):
            # if title is already in, add * at the end
            # reason being Apple sometime re-releases updated (Safari 14.1)
            # which breaks checking on the second release
            # because there is already info with the same title
            title += "*"

        release_info[title] = {
            "release_notes": release_notes_link,
            "release_date": release_date,
            "emoji": set_emoji(title),
            "num_of_bugs": count_bugs(release, release_notes),
            "num_of_zero_days": num_zero_days,
            "list_of_zero_days": list_zero_days,
            "entries_added": added,
            "entries_updated": updated,
        }

    return release_info


def determine_latest_versions(ver_releases):
    """
    Return the latest major version number for each system.
    For macOS return its name alongside.
    """

    versions = {"iOS": [0], "tvOS": [0], "watchOS": [0], "macOS": [0, ""]}

    for system, ver in versions.items():
        version = re.findall(rf"(?i){system}[a-z\s]*\s([0-9]+)", str(ver_releases))

        version = list(map(int, version))
        version.sort(reverse=True)

        ver[0] = int(version[0])

    versions["macOS"][1] = re.findall(
        rf"(?i)(?<=macOS)[a-z\s]+(?={versions['macOS'][0]})", str(ver_releases)
    )[0].strip()

    versions["iOS and iPadOS"] = versions.pop("iOS")

    return versions

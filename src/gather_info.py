import re
from datetime import date

import requests


def set_emoji(title):
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


def check_zerodays(release_notes):
    num = len(re.findall("in the wild", release_notes)) + len(
        re.findall("actively exploited", release_notes)
    )

    if num > 0:
        if num == 1:
            num_zerodays = f"{num} zero-day"
        else:
            num_zerodays = f"{num} zero-days"

        list_zerodays = {}

        for entry in re.findall(
            r"(?i)((?<=<strong>)(?:.|\n)*?(?=<strong>|<\/div))", release_notes
        ):
            if "in the wild" in entry or "actively exploited" in entry:
                zeroday = re.findall(r"(?i)CVE-[0-9]{4}-[0-9]{4,5}", entry)[0]
                list_zerodays[zeroday] = re.findall(r"(?i)(.*)<\/strong>", entry)[0]

        return num_zerodays, list_zerodays

    return None, None


def count_bugs(release, release_notes):
    num = len(re.findall("CVE", release_notes)) - 1

    if "soon" in release[0]:
        return "no details yet"
    if num > 1:
        return f"{num} bugs fixed"
    if num == 1:
        return f"{num} bug fixed"

    return "no bugs fixed"


def check_notes_updates(release_notes):
    date_format_two = (
        f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"
    )
    # Example: January 19, 2022

    num = len(re.findall(f"Entry added {date_format_two}", release_notes))

    if num >= 1:
        added = f"{num} added"
    else:
        added = None

    num = len(re.findall(f"Entry updated {date_format_two}", release_notes))

    if num >= 1:
        updated = f"{num} updated"
    else:
        updated = None

    return added, updated


def get_data(releases):
    """
    Gather all data about given releases from Apple's website.

    Input example:
    ----------------------------
    [
        '<td><a href="https://support.apple.com/kb/HT213055">macOS Big Sur 11.6.3</a></td>',
        '<td>macOS Big Sur</td>',
        '<td>26 Jan 2022</td>'
    ]
    ----------------------------

    Return example:
    ----------------------------
    {
        'iOS and iPadOS 14.7': {
            'release_notes': 'https://support.apple.com/kb/HT212623',
            'emoji': ':iphone:',
            'num_of_bugs': '37 bugs fixed',
            'num_of_zerodays': '3 zero-days',
            'list_of_zerodays': {
                'CVE-2021-30761': 'WebKit',
                'CVE-2021-30762': 'WebKit',
                'CVE-2021-30713': 'TCC'
            },
            'entries_added': '8 entries added',
            'entries_updated': '1 entry updated'
        }
    }
    -----------------------------
    """

    release_info = {}

    for release in releases:
        title = re.findall(
            r"(?i)(?:<td>|\">)([^<]+)(?:<br>|<\/a>|<em>|<\/td>)",
            release[0],
        )[0].rstrip()

        if "href" in release[0]:
            release_notes_link = re.findall(r'(?i)href="([^\']+)"', release[0])[0]
            release_notes = requests.get(release_notes_link).text
        else:
            release_notes_link = None
            release_notes = ""

        if "macOS" in title:
            # if macOS is in the title, take only the first part of the title
            title = title.split(",", 1)[0]
        elif "iOS" in title and "iPad" in title:
            # if they are both in the title remove version number from iPadOS
            title = title.split("and", 1)[0].rstrip().replace("iOS", "iOS and iPadOS")

        num_zerodays, list_zerodays = check_zerodays(release_notes)
        added, updated = check_notes_updates(release_notes)

        release_info[title] = {
            "release_notes": release_notes_link,
            "emoji": set_emoji(title),
            "num_of_bugs": count_bugs(release, release_notes),
            "num_of_zerodays": num_zerodays,
            "list_of_zerodays": list_zerodays,
            "entries_added": added,
            "entries_updated": updated,
        }

    return release_info

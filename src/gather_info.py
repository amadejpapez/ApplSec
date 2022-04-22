import re

from Release import Release


def get_info(release_rows: list) -> list:
    """
    Gather all data about given releases from Apple's website.

    Input format (release row on the initial Security page):
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
    [
        Class Release (
            "name": "iOS and iPadOS 14.7",
            "emoji": ":iphone:",
            "release_notes_link": "https://support.apple.com/kb/HT212623",
            "release_date": "26 Jan 2022",
            "num_of_bugs": 37,
            "num_of_zero_days": 3,
            "zero_days": {
                "CVE-2021-30761": "WebKit",
                "CVE-2021-30762": "WebKit",
                "CVE-2021-30713": "TCC"
            },
            "num_entries_added": 8,
            "num_entries_updated": 1
        )
    ]
    -----
    """

    releases = []

    for row in release_rows:
        releases.append(Release(row))

    return releases


def determine_latest_versions(release_rows: list) -> dict:
    """
    Return the latest major version number for each system.
    For macOS also return its name.
    """

    versions = {
        "iOS": [0],
        "tvOS": [0],
        "watchOS": [0],
        "macOS": [0, ""],
    }

    for key, value in versions.items():
        search = re.findall(rf"(?i){key}[a-z\s]*\s([0-9]+)", str(release_rows))

        search = list(map(int, search))
        search.sort(reverse=True)

        value[0] = search[0]

    versions["macOS"][1] = re.findall(
        rf"(?i)(?<=macOS)[a-z\s]+(?={versions['macOS'][0]})", str(release_rows)
    )[0].strip()

    return versions

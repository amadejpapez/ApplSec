import re
from Release import Release


def get_info(releases: list) -> list:
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
            "release_notes": "https://support.apple.com/kb/HT212623",
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

    release_info = []

    for release_row in releases:
        release_info.append(Release(release_row))

        # if title in list(release_info):
        #     # if title is already in, add * at the end
        #     # reason being Apple sometime re-releases updated (Safari 14.1)
        #     # which breaks checking on the second release
        #     # because there is already info with the same title
        #     title += "*"

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

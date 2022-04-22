import re

from gather_info import get_info
from typing import Tuple


def get_versions(system: str, version: int, release_rows: list) -> Tuple[str, list]:
    """
    Get last four version numbers for that system.
    For macOS it gives version names instead.
    """

    versions = []

    if system == "macOS":
        # macOS versions are hard coded
        # get macOS name as Security Updates only contain names
        for x in ["12", "11", "10.15", "10.14"]:
            versions.append(
                re.findall(rf"(?i)(?<=macOS)[a-z\s]+(?={x})", str(release_rows))[0].strip()
            )
    else:
        num = version
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    return system, versions


def format_yearly_report(release_rows: list, system: str, version: int, stored_data: dict) -> list:
    """
    -----
    iOS 15 was released today. In iOS 14 series Apple fixed in total of 346 security issues over 16 releases. 🔐

    📊 COMPARED TO:
    - 301 fixed in iOS 13 over 18 releases
    - 339 fixed in iOS 12 over 33 releases
    - 310 fixed in iOS 11 over 17 releases
    -----
    """

    if system in stored_data["tweeted_today"]["yearly_report"]:
        return []

    stored_data["tweeted_today"]["yearly_report"].append(system)

    system, versions = get_versions(system, version, release_rows)

    # get all the links of release notes, count CVEs and save all the info
    info = {}
    for ver in versions:
        info[ver] = {"num_of_bugs": 0, "num_of_releases": 0}

        for release in release_rows:
            if system in release[0] and str(ver) in release[0]:
                if "href" in release[0]:
                    release_info = get_info([release])
                    num = release_info[0].get_num_of_bugs()

                    if num > 0:
                        info[ver]["num_of_bugs"] += num

                info[ver]["num_of_releases"] += 1

    second_version = list(info.keys())[0]

    tweet_text = [
        f"{system} {version} was released today. In {system} {second_version} series Apple fixed in total of {info[second_version]['num_of_bugs']} security issues over {info[second_version]['num_of_releases']} releases. :locked_with_key:\n\n:bar_chart: COMPARED TO:\n"
    ]

    del info[second_version]

    for key, value in info.items():
        tweet_text.append(
            f"- {value['num_of_bugs']} fixed in {system} {key} over {value['num_of_releases']} releases\n"
        )

    if system == "macOS":
        # for macOS create a thread with additional info in the second tweet
        tweet_text.append(
            "Numbers also contain issues from Security and Supplemental Updates."
        )

    return tweet_text

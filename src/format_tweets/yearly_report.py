import re

from gather_info import get_info


def get_versions(system, version, releases):
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
                re.findall(rf"(?i)(?<=macOS)[a-z\s]+(?={x})", str(releases))[0].strip()
            )
    else:
        num = version
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    if system == "iOS and iPadOS":
        system = "iOS"

    return system, versions


def format_yearly_report(releases, system, version, stored_data):
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
        return None

    stored_data["tweeted_today"]["yearly_report"].append(system)

    system, versions = get_versions(system, version, releases)

    # get all the links of release notes, count CVEs and save all the info
    info = {}
    for ver in versions:
        info[ver] = {"num_of_bugs": 0, "num_of_releases": 0}

        for release in releases:
            if system in release[0] and str(ver) in release[0]:
                if "href" in release[0]:
                    release_info = get_info([release])
                    num = re.findall(
                        r"\d+", release_info[list(release_info)[0]]["num_of_bugs"]
                    )

                    if num:
                        info[ver]["num_of_bugs"] += int(num[0])

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

import re

from gather_info import get_info
from twitter import tweet_or_make_a_thread


def tweet_yearly_report(releases, system, system_version, stored_data):
    """
    iOS 15 was released today. In iOS 14 series Apple fixed in total of 346 security issues over 16 releases. 🔐

    📊 COMPARED TO:
    - 301 fixed in iOS 13 over 18 releases
    - 339 fixed in iOS 12 over 33 releases
    - 310 fixed in iOS 11 over 17 releases
    """

    if system in stored_data["tweeted_today"]["yearly_report"]:
        return

    stored_data["tweeted_today"]["yearly_report"].append(system)

    # save previous three versions
    versions = []
    if system == "macOS":
        # macOS names are hard coded for now
        versions = ["12", "11", "10.15", "10.14"]
    else:
        num = system_version
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    if system == "iOS and iPadOS":
        system = "iOS"

    # get all the links of release notes, count CVEs and save all the info
    info = {}
    for version in versions:
        info[version] = {"num_of_bugs": 0, "num_of_releases": 0}

        if system == "macOS":
            # if system is macOS, take the name of the macOS version as Security Updates only contain names
            macos_name = re.findall(
                rf"(?i)macOS\s([a-z\s]+){version}", str(releases)
            )[0].rstrip()
        else:
            macos_name = "None"

        for release in releases:
            if f"{system} {version}" in release[0] or macos_name in release[0]:
                if "href" in release[0]:
                    release_info = get_info([release])
                    num = re.findall(
                        r"\d+", release_info[list(release_info)[0]]["num_of_bugs"]
                    )

                    if num:
                        info[version]["num_of_bugs"] += int(num[0])

                info[version]["num_of_releases"] += 1

    second_version = list(info.keys())[0]

    results = f"{system} {system_version} was released today. In {system} {second_version} series Apple fixed in total of {info[second_version]['num_of_bugs']} security issues over {info[second_version]['num_of_releases']} releases. :locked_with_key:\n\n:bar_chart: COMPARED TO:\n"

    del info[second_version]

    for key, value in info.items():
        results += f"- {value['num_of_bugs']} fixed in {system} {key} over {value['num_of_releases']} releases\n"

    if system == "macOS":
        # for macOS create a thread with additional info in the second tweet
        tweet_or_make_a_thread(
            first_tweet=results,
            second_tweet="Numbers also contain issues from Security and Supplemental Updates.",
        )

    else:
        tweet_or_make_a_thread(first_tweet=results)

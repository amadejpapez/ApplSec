"""
Post a report of bugs fixed in the previous major series, when a new major version is released.
"""

import lxml.html

import helpers.get_version_info as get_version_info
from helpers.posted_file import PostedFile
from release import Release


def get_new(new_sec_content: list[Release], latest_versions: dict[str, list]) -> list[list[str | int]]:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    new_yearly_report = []

    for key, value in latest_versions.items():
        if key in PostedFile.data["posts"]["yearly_report"]:
            continue

        PostedFile.data["posts"]["yearly_report"].append(key)

        for release in new_sec_content:
            if release.name in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
                new_yearly_report.append([key, value[0]])

            elif key == "macOS":
                if release.name in (
                    f"{key} {value[1]} {value[0]}",
                    f"{key} {value[1]} {value[0]}.0",
                ):
                    new_yearly_report.append([key, value[0]])

    return new_yearly_report


def format_report(release_rows: list[list[lxml.html.HtmlElement]], system: str, version: int) -> list[str]:
    """
    iOS 15 was released today. In iOS 14 series Apple fixed in total of 346 security issues over 16 releases. 🔐

    📊 COMPARED TO:
    - 301 fixed in iOS 13 over 18 releases
    - 339 fixed in iOS 12 over 33 releases
    - 310 fixed in iOS 11 over 17 releases
    """

    system, versions = get_version_info.latest_four(system, version, release_rows)

    info = {}
    for ver in versions:
        info[ver] = {"num_of_bugs": 0, "num_of_releases": 0}

        for row in release_rows:
            if system in row[0].text_content() and str(ver) in row[0].text_content():
                tmp = row[0].xpath(".//a/@href")

                if tmp != []:
                    release = Release.parse_from_table(row)

                    num = release.num_of_bugs

                    if num > 0:
                        info[ver]["num_of_bugs"] += num

                info[ver]["num_of_releases"] += 1

    second_version = list(info.keys())[0]

    post_text = [
        f"{system} {version} was released today. In {system} {second_version} series Apple fixed in total of {info[second_version]['num_of_bugs']} security issues over {info[second_version]['num_of_releases']} releases. 🔐\n\n📊 COMPARED TO:\n"
    ]

    del info[second_version]

    for key, value in info.items():
        post_text.append(f"- {value['num_of_bugs']} fixed in {system} {key} over {value['num_of_releases']} releases\n")

    if system == "macOS":
        # for macOS create a thread with additional info in the second post
        post_text.append("Numbers also contain issues from Security and Supplemental Updates.")

    return post_text

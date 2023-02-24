import collections
import re

import requests

import helpers.get_version_info as get_version_info
from Release import Release


def new_updates(releases: list) -> list:
    """
    -----
    💥 NEW UPDATES RELEASED 💥

    💻 macOS Monterey 12.2 - 13 bugs fixed
    📱 iOS and iPadOS 15.3 - 10 bugs fixed
    ⌚ watchOS 8.4 - 8 bugs fixed
    💻 macOS Big Sur 11.6.3 - 7 bugs fixed
    💻 Security Update 2022-001 Catalina - 5 bugs fixed
    🌐 Safari 15.3 - 4 bugs fixed
    https://support.apple.com/en-us/HT201222
    -----
    """
    post_text = []

    releases.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    for release in releases:
        post_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    if len(releases) == 1:
        post_text.insert(0, ":collision: NEW UPDATE RELEASED :collision:\n\n")

        # if there is only one release, add its notes as a link instead
        if releases[0].get_security_content_link():
            post_text.append(releases[0].get_security_content_link())
    else:
        post_text.insert(0, ":collision: NEW UPDATES RELEASED :collision:\n\n")
        post_text.append("https://support.apple.com/en-us/HT201222")

    return post_text


def top_ios_modules(releases: list) -> list:
    """
    -----
    ⚒ FIXED IN iOS 14.7 ⚒

    - 4 bugs in WebKit
    - 3 bugs in FontParser
    - 3 bugs in Model I/O
    - 2 bugs in CoreAudio
    and 25 other vulnerabilities fixed
    https://support.apple.com/en-us/HT212601
    -----
    """
    post_text = []

    for release in releases:
        sec_content_html = requests.get(release.get_security_content_link(), timeout=60).text
        sec_content_html = sec_content_html.split("Additional recognition", 1)[0]

        search_modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", sec_content_html)
        )
        modules = collections.OrderedDict(
            sorted(search_modules.items(), reverse=True, key=lambda x: x[1])
        )

        post_text = [f":hammer_and_pick: FIXED IN {release.get_name()} :hammer_and_pick:\n\n"]
        num_bugs = 0

        for key, value in modules.items():
            if len(post_text) < 5:
                if value > 1:
                    post_text.append(f"- {value} bugs in {key}\n")
                else:
                    post_text.append(f"- {value} bug in {key}\n")

                num_bugs += value

        num_bugs = release.get_num_of_bugs() - num_bugs

        if num_bugs > 0:
            post_text.append(f"and {num_bugs} other vulnerabilities fixed\n")
        elif num_bugs == 1:
            post_text.append("and 1 other vulnerability fixed\n")

        post_text.append(f"{release.get_security_content_link()}\n")

    return post_text


def get_zero_days_start_text(zero_days: dict) -> str:
    """Return text for the start of the zero day post."""

    num_new = 0
    num_old = 0

    for _, value in zero_days.items():
        if value["status"] == "new":
            num_new += 1
        else:
            num_old += 1

    text = ""

    if num_new == 1 and num_old == 0:
        text = "Apple pushed updates for a new zero-day that may have been actively exploited."

    elif num_new == 0 and num_old == 1:
        text = "Apple pushed additional updates for a zero-day that may have been actively exploited."

    elif num_new == 1 and num_old == 1:
        text = "Apple pushed updates for a new zero-day that may have been actively exploited and additional updates for one zero-day."

    elif num_new > 1 and num_old == 0:
        text = f"Apple pushed updates for {num_new} new zero-days that may have been actively exploited."

    elif num_new == 0 and num_old > 1:
        text = f"Apple pushed additional updates for {num_old} zero-days that may have been actively exploited."

    elif num_new == 1 and num_old > 1:
        text = f"Apple pushed updates for 1 new zero-day that may have been actively exploited and additional updates for {num_old} zero-days."

    elif num_new > 1 and num_old == 1:
        text = f"Apple pushed updates for {num_new} new zero-days that may have been actively exploited and additional updates for 1 zero-day."

    else:
        text = f"Apple pushed updates for {num_new} new zero-days that may have been actively exploited and additional updates for {num_old} zero-days."

    return text


def zero_days(releases: list, stored_data: dict) -> list:
    """
    -----
    📣 EMERGENCY UPDATES 📣

    Apple pushed updates for 3 new zero-days that may have been actively exploited and additional updates for 1 zero-day.

    🐛 CVE-2021-30869 (XNU) additional patches:
    - Security Update 2021-006 Catalina
    - iOS 12.5.5

    🐛 CVE-2021-30860 (CoreGraphics):
    - iOS 12.5.5

    🐛 CVE-2021-31010 (Core Telephony):
    - iOS 12.5.5

    🐛 CVE-2021-30858 (WebKit):
    - iOS 12.5.5
    -----
    """
    zero_days = {}

    for release in releases:
        for cve, module in release.get_zero_days().items():
            if not zero_days.get(cve):
                zero_days[cve] = {
                    "status": "old",
                    "module": module,
                    "releases": [release.get_name()],
                }
            else:
                zero_days[cve]["releases"].append(release.get_name())

            # if zero-day was not fixed in any previous releases
            if cve not in stored_data["zero_days"]:
                stored_data["zero_days"].append(cve)
                zero_days[cve]["status"] = "new"

    post_text = []

    if len(zero_days) == 1:
        post_text.append(":mega: EMERGENCY UPDATE :mega:\n\n")
    else:
        post_text.append(":mega: EMERGENCY UPDATES :mega:\n\n")

    post_text.append(get_zero_days_start_text(zero_days))

    for key, value in zero_days.items():
        if value["status"] == "new":
            post_text.append("\n\n:bug: " + key + " (" + value["module"] + "):")
        else:
            post_text.append("\n\n:bug: " + key + " (" + value["module"] + ") additional patches:")

        for release in value["releases"]:
            post_text[-1] += "\n- " + release

    return post_text


def entry_changes(releases: list) -> list:
    """
    -----
    🔄 24 ENTRY CHANGES 🔄

    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    💻 Security Update 2021-003 Catalina - 8 added
    💻 Security Update 2021-004 Mojave - 6 added
    🌐 Safari 14.1.1 - 1 updated
    -----
    """
    post_text = []
    changes_count = 0

    releases.sort(
        key=lambda x: (x.get_num_entries_added() + x.get_num_entries_updated()),
        reverse=True,
    )

    for release in releases:
        name = f"{release.get_emoji()} {release.get_name()}"

        changes_count += release.get_num_entries_added() + release.get_num_entries_updated()

        if release.get_num_entries_added() > 0:
            if release.get_num_entries_updated() > 0:
                post_text.append(
                    f"{name} - {release.get_format_num_entries_added()}, {release.get_format_num_entries_updated()}\n"
                )
            else:
                post_text.append(f"{name} - {release.get_format_num_entries_added()}\n")

        elif release.get_num_entries_updated() > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_updated()}\n")

    if changes_count == 1:
        post_text.insert(
            0,
            ":arrows_counterclockwise: 1 ENTRY CHANGE :arrows_counterclockwise:\n\n",
        )
    else:
        post_text.insert(
            0,
            f":arrows_counterclockwise: {changes_count} ENTRY CHANGES :arrows_counterclockwise:\n\n",
        )

    return post_text


def security_content_available(releases: list) -> list:
    """
    -----
    🗒 SECURITY CONTENT AVAILABLE 🗒

    💻 macOS Monterey 12.0.1 - 40 bugs fixed
    💻 macOS Big Sur 11.6.1 - 24 bugs fixed
    📱 iOS and iPadOS 15.1 - 22 bugs fixed
    💻 Security Update 2021-007 Catalina - 21 bugs fixed
    ⌚ watchOS 8.1 - 16 bugs fixed
    -----
    """

    releases.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    post_text = [
        ":spiral_notepad: SECURITY CONTENT AVAILABLE :spiral_notepad:\n\n",
    ]

    for release in releases:
        post_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    return post_text


def yearly_report(release_rows: list, system: str, version: int) -> list:
    """
    -----
    iOS 15 was released today. In iOS 14 series Apple fixed in total of 346 security issues over 16 releases. 🔐

    📊 COMPARED TO:
    - 301 fixed in iOS 13 over 18 releases
    - 339 fixed in iOS 12 over 33 releases
    - 310 fixed in iOS 11 over 17 releases
    -----
    """

    system, versions = get_version_info.latest_four(system, version, release_rows)

    info = {}
    for ver in versions:
        info[ver] = {"num_of_bugs": 0, "num_of_releases": 0}

        for row in release_rows:
            if system in row[0].text_content() and str(ver) in row[0].text_content():
                tmp = row[0].xpath(".//a/@href")

                if tmp != []:
                    release = Release(row)

                    num = release.get_num_of_bugs()

                    if num > 0:
                        info[ver]["num_of_bugs"] += num

                info[ver]["num_of_releases"] += 1

    second_version = list(info.keys())[0]

    post_text = [
        f"{system} {version} was released today. In {system} {second_version} series Apple fixed in total of {info[second_version]['num_of_bugs']} security issues over {info[second_version]['num_of_releases']} releases. :locked_with_key:\n\n:bar_chart: COMPARED TO:\n"
    ]

    del info[second_version]

    for key, value in info.items():
        post_text.append(
            f"- {value['num_of_bugs']} fixed in {system} {key} over {value['num_of_releases']} releases\n"
        )

    if system == "macOS":
        # for macOS create a thread with additional info in the second post
        post_text.append("Numbers also contain issues from Security and Supplemental Updates.")

    return post_text

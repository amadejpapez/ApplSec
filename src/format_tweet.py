import collections
import re

import requests

import gather_info
from Release import Release


def new_updates(releases_info: list) -> list:
    """
    -----
    💥 NEW UPDATES RELEASED 💥

    💻 macOS Monterey 12.2 - 13 bugs fixed
    📱 iOS and iPadOS 15.3 - 10 bugs fixed
    ⌚ watchOS 8.4 - 8 bugs fixed
    💻 macOS Big Sur 11.6.3 - 7 bugs fixed
    -----
    💻 Security Update 2022-001 Catalina - 5 bugs fixed
    🌐 Safari 15.3 - 4 bugs fixed
    https://support.apple.com/en-us/HT201222
    -----
    """

    tweet_text = []

    releases_info.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    if len(releases_info) == 1:
        tweet_text.insert(0, ":collision: NEW UPDATE RELEASED :collision:\n\n")

        if releases_info[0].get_security_content_link():
            # if there is only one release, add its notes as a link
            tweet_text.append(releases_info[0].get_security_content_link())
    else:
        tweet_text.insert(0, ":collision: NEW UPDATES RELEASED :collision:\n\n")
        tweet_text.append("https://support.apple.com/en-us/HT201222")

    return tweet_text


def top_ios_modules(releases_info: list) -> list:
    """
    -----------------------------
    ⚒ FIXED IN iOS 14.7 ⚒

    - 4 bugs in WebKit
    - 3 bugs in FontParser
    - 3 bugs in Model I/O
    - 2 bugs in CoreAudio
    and 25 other vulnerabilities fixed
    https://support.apple.com/kb/HT212601
    -----------------------------
    """
    tweet_text = []

    for release in releases_info:
        sec_content_html = requests.get(release.get_security_content_link(), timeout=60).text
        sec_content_html = sec_content_html.split("Additional recognition", 1)[0]

        search_modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", sec_content_html)
        )
        modules = collections.OrderedDict(
            sorted(search_modules.items(), reverse=True, key=lambda x: x[1])
        )

        tweet_text = [
            f":hammer_and_pick: FIXED IN {release.get_name()} :hammer_and_pick:\n\n"
        ]
        num_bugs = 0

        for key, value in modules.items():
            if len(tweet_text) < 5:
                num_bugs += value
                if value > 1:
                    tweet_text.append(f"- {value} bugs in {key}\n")
                else:
                    tweet_text.append(f"- {value} bug in {key}\n")

        num_bugs = release.get_num_of_bugs() - num_bugs

        if num_bugs > 0:
            tweet_text.append(f"and {num_bugs} other vulnerabilities fixed\n")
        elif num_bugs == 1:
            tweet_text.append("and 1 other vulnerability fixed\n")

        tweet_text.append(f"{release.get_security_content_link()}\n")

    return tweet_text


def get_zero_days_first_tweet(zero_days: dict) -> str:
    """Return text for the start of the zero day tweet."""

    num_new = 0
    num_old = 0

    for _, value in zero_days.items():
        if value["status"] == "new":
            num_new += 1
        else:
            num_old += 1

    text = ""

    if num_new == 1 and num_old == 0:
        text = f"Apple pushed updates for a new zero-day that may have been actively exploited."

    elif num_new == 0 and num_old == 1:
        text = f"Apple pushed additional updates for a zero-day that may have been actively exploited."

    elif num_new == 1 and num_old == 1:
        text = f"Apple pushed updates for a new zero-day that may have been actively exploited and additional updates for one zero-day."

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


def zero_days(releases_info: list, stored_data: dict) -> list:
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

    for release in releases_info:
        for cve, module in release.get_zero_days().items():
            if not zero_days.get(cve):
                zero_days[cve] = {"status": "old", "module": module, "releases": [release.get_name()]}
            else:
                zero_days[cve]["releases"].append(release.get_name())

            # if zero-day was not fixed in any previous releases
            if cve not in stored_data["zero_days"]:
                stored_data["zero_days"].append(cve)
                zero_days[cve]["status"] = "new"

    tweet_text = []

    if len(zero_days) == 1:
        tweet_text.append(":mega: EMERGENCY UPDATE :mega:\n\n")
    else:
        tweet_text.append(":mega: EMERGENCY UPDATES :mega:\n\n")

    tweet_text.append(get_zero_days_first_tweet(zero_days))

    for key, value in zero_days.items():
        if value["status"] == "new":
            tweet_text.append("\n\n:bug: " + key + " (" + value["module"] + "):")
        else:
            tweet_text.append("\n\n:bug: " + key + " (" + value["module"] + ") additional patches:")

        for release in value["releases"]:
            tweet_text[-1] += ("\n- " + release)

    return tweet_text


def entry_changes(releases_info: list) -> list:
    """
    -----
    🔄 24 ENTRY CHANGES 🔄

    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    💻 Security Update 2021-003 Catalina - 8 added
    💻 Security Update 2021-004 Mojave - 6 added
    🌐 Safari 14.1.1 - 1 updated
    -----
    """

    tweet_text = []
    changes_count = 0

    releases_info.sort(
        key=lambda x: (x.get_num_entries_added() + x.get_num_entries_updated()),
        reverse=True,
    )

    for release in releases_info:
        name = f"{release.get_emoji()} {release.get_name()}"

        changes_count += release.get_num_entries_added() + release.get_num_entries_updated()

        if release.get_num_entries_added() > 0:
            if release.get_num_entries_updated() > 0:
                tweet_text.append(
                    f"{name} - {release.get_format_num_entries_added()}, {release.get_format_num_entries_updated()}\n"
                    )
            else:
                tweet_text.append(f"{name} - {release.get_format_num_entries_added()}\n")

        elif release.get_num_entries_updated() > 0:
            tweet_text.append(f"{name} - {release.get_format_num_entries_updated()}\n")

    if changes_count > 1:
        tweet_text.insert(
            0,
            f":arrows_counterclockwise: {changes_count} ENTRY CHANGES :arrows_counterclockwise:\n\n",
        )
    else:
        tweet_text.insert(
            0,
            ":arrows_counterclockwise: 1 ENTRY CHANGE :arrows_counterclockwise:\n\n",
        )

    return tweet_text


def security_content_available(releases_info: list) -> list:
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

    releases_info.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    tweet_text = [
        ":spiral_notepad: SECURITY CONTENT AVAILABLE :spiral_notepad:\n\n",
    ]

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    return tweet_text


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

    system, versions = gather_info.latest_four_versions(system, version, release_rows)

    info = {}
    for ver in versions:
        info[ver] = {"num_of_bugs": 0, "num_of_releases": 0}

        for release in release_rows:
            if (
                system in release[0].text_content()
                and str(ver) in release[0].text_content()
            ):
                tmp = release[0].xpath('.//a/@href')

                if tmp != []:
                    sec_content = Release(release)

                    num = sec_content.get_num_of_bugs()

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

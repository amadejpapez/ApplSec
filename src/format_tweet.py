import collections
import re

import requests

from gather_info import determine_latest_four_versions, get_info


def new_updates(releases_info: list, stored_data: dict) -> list:
    """
    -----
    💥 NEW UPDATES RELEASED 💥

    🌐 Safari 15.3 - 4 bugs fixed
    💻 Security Update 2022-001 Catalina - 5 bugs fixed
    💻 macOS Big Sur 11.6.3 - 7 bugs fixed
    💻 macOS Monterey 12.2 - 13 bugs fixed
    -----
    📱 iOS and iPadOS 15.3 - 10 bugs fixed
    ⌚ watchOS 8.4 - 8 bugs fixed
    https://support.apple.com/en-us/HT201222
    -----
    """

    tweet_text = []

    for release in list(releases_info):
        if release.get_name() in stored_data["tweeted_today"]["new_updates"]:
            releases_info.remove(release)
        else:
            stored_data["tweeted_today"]["new_updates"].append(release.get_name())

    if not releases_info:
        return []

    releases_info.sort(key=lambda x: x.get_num_of_bugs(), reverse=True)

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    if len(releases_info) == 1:
        tweet_text.insert(0, ":collision: NEW UPDATE RELEASED :collision:\n\n")

        if releases_info[0].get_release_notes_link():
            # if there is only one release, add its notes as a link
            tweet_text.append(releases_info[0].get_release_notes_link())
    else:
        tweet_text.insert(0, ":collision: NEW UPDATES RELEASED :collision:\n\n")
        tweet_text.append("https://support.apple.com/en-us/HT201222")

    return tweet_text


def top_ios_modules(releases_info: list, stored_data: dict) -> list:
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

    for release in list(releases_info):
        if release.get_name() in stored_data["tweeted_today"]["ios_modules"]:
            releases_info.remove(release)
        else:
            stored_data["tweeted_today"]["ios_modules"] = release.get_name()

    if not releases_info:
        return []

    for release in releases_info:
        release_note = requests.get(release.get_release_notes_link()).text
        release_note = release_note.split("Additional recognition", 1)[0]

        search_modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", release_note)
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

        tweet_text.append(f"{release.get_release_notes_link()}\n")

    return tweet_text


def get_zero_days_first_tweet(unique_zero_days: dict) -> str:
    """Return text for the start of the zero day tweet."""

    length_old = len(unique_zero_days["old"])
    length_new = len(unique_zero_days["new"])

    if length_old > 0:
        text_old = ", ".join(unique_zero_days["old"])
        zero_day_module = unique_zero_days["old"][list(unique_zero_days["old"].keys())[0]]

    if length_new > 0:
        text_new = ", ".join(unique_zero_days["new"])
        zero_day_module = unique_zero_days["new"][list(unique_zero_days["new"].keys())[0]]

    if length_new == 1 and length_old == 0:
        return f"Apple pushed updates for a new {zero_day_module} zero-day ({text_new}) that may have been actively exploited."

    if length_new == 0 and length_old == 1:
        return f"Apple pushed additional updates for {zero_day_module} zero-day ({text_old}) that may have been actively exploited."

    if length_new == 1 and length_old == 1:
        return f"Apple pushed updates for a new {zero_day_module} zero-day ({text_new}) that may have been actively exploited and additional updates for {text_old}."

    if length_new > 1 and length_old == 0:
        return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited."

    if length_new == 0 and length_old > 1:
        return f"Apple pushed additional updates for {length_old} zero-days that may have been actively exploited."

    if length_new == 1 and length_old > 1:
        return f"Apple pushed updates for {length_new} new zero-day that may have been actively exploited and additional updates for {length_old} zero-days."

    if length_new > 1 and length_old == 1:
        return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited and additional updates for {length_old} zero-day."

    return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited and additional updates for {length_old} zero-days."


def zero_days(releases_info: list, stored_data: dict) -> list:
    """
    -----
    📣 EMERGENCY UPDATE 📣

    Apple pushed updates for 3 new zero-days that may have been actively exploited.
    -----
    🐛 ZERO-DAY DETAILS:

    - CVE-2021-30869 in XNU
    - CVE-2021-30860 in CoreGraphics
    - CVE-2021-30858 in WebKit
    -----
    ⚠️ PATCHES:

    1 zero-day in Security Update 2021-006 Catalina
    3 zero-days in iOS 12.5.5
    -----
    """

    for release in list(releases_info):
        if (
            release.get_name() in stored_data["tweeted_today"]["zero_days"].keys()
            and release.get_num_of_zero_days()
            == stored_data["tweeted_today"]["zero_days"][release.get_name()]
        ):
            # if release was tweeted with the same number of zero-days
            releases_info.remove(release)
            continue

        stored_data["tweeted_today"]["zero_days"][release.get_name()] = release.get_num_of_zero_days()

    if not releases_info:
        return []

    tweet_text = [[], [":bug: ZERO-DAY DETAILS:\n\n"], [":warning: PATCHES:\n\n"], []]
    zero_days = {}
    sorted_zero_days: dict = {"old": {}, "new": {}}

    for release in releases_info:
        tweet_text[2].append(f"{release.get_format_num_of_zero_days()} in {release.get_name()}\n")
        zero_days.update(release.get_zero_days())

    for key, value in zero_days.items():
        if key in stored_data["zero_days"]:
            # if zero day is in the file, add it to "old"
            sorted_zero_days["old"][key] = value
        else:
            # if zero day is not in the file, add it to file and "new"
            sorted_zero_days["new"][key] = value
            stored_data["zero_days"].append(key)

        tweet_text[1].append(f"- {key} in {value}\n")

    if len(tweet_text[2]) == 2:
        tweet_text[0].append(":mega: EMERGENCY UPDATE :mega:\n\n")
    else:
        tweet_text[0].append(":mega: EMERGENCY UPDATES :mega:\n\n")

    tweet_text[0].append(get_zero_days_first_tweet(sorted_zero_days))

    if len(sorted_zero_days["new"]) in (0, 1) and len(sorted_zero_days["old"]) in (0, 1):
        # if CVEs are already in the first tweet, do not do a separate DETAILS tweet
        tweet_text[1] = tweet_text[2]
        tweet_text[2] = tweet_text[3]

    return list(filter(None, tweet_text))


def entry_changes(releases_info: list) -> list:
    """
    -----
    🔄 4 SECURITY NOTES UPDATED 🔄

    🌐 Safari 14.1.1 - 1 entry updated
    💻 Security Update 2021-003 Catalina - 8 entries added
    💻 Security Update 2021-004 Mojave - 6 entries added
    💻 macOS Big Sur 11.4 - 8 entries added, 1 entry updated
    -----
    """

    tweet_text = []

    for release in releases_info:
        name = f"{release.get_emoji()} {release.get_name()}"
        added = release.get_format_num_entries_added()
        updated = release.get_format_num_entries_updated()

        if not added and updated:
            tweet_text.append(f"{name} - {updated}\n")
        elif added and not updated:
            tweet_text.append(f"{name} - {added}\n")
        elif added and updated:
            tweet_text.append(f"{name} - {added}, {updated}\n")

    if len(tweet_text) > 1:
        tweet_text.insert(
            0,
            f":arrows_counterclockwise: {len(tweet_text)} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n",
        )
    else:
        tweet_text.insert(
            0,
            ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n",
        )

    return tweet_text


def release_notes_available(releases_info: list, stored_data: dict) -> list:
    """
    -----
    🗒 RELEASE NOTES AVAILABLE 🗒

    💻 macOS Monterey 12.0.1 - 40 bugs fixed
    💻 macOS Big Sur 11.6.1 - 24 bugs fixed
    💻 Security Update 2021-007 Catalina - 21 bugs fixed
    ⌚ watchOS 8.1 - 16 bugs fixed
    📱 iOS and iPadOS 15.1 - 22 bugs fixed
    -----
    """

    for release in list(releases_info):
        if (
            release.get_name() in stored_data["details_available_soon"]
            and release.get_release_notes_link() is not None
        ):
            stored_data["details_available_soon"].remove(release.get_name())

        elif (
            release.get_name() not in stored_data["details_available_soon"]
            and release.get_format_num_of_bugs() == "no details yet"
        ):
            stored_data["details_available_soon"].append(release.get_name())
            releases_info.remove(release)

    if not releases_info:
        return []

    tweet_text = [
        ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n",
    ]

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    return tweet_text


def yearly_report(release_rows: list, system: str, version: int, stored_data: dict) -> list:
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

    system, versions = determine_latest_four_versions(system, version, release_rows)

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
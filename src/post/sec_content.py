import collections
import re

import lxml.html
import requests

import helpers.get_version_info as get_version_info
from helpers.posted_file import PostedFile
from release import Release


def retrieve_page() -> list:
    main_page = lxml.html.document_fromstring(
        requests.get("https://support.apple.com/en-us/HT201222", timeout=60).text
    )

    table = main_page.xpath("//table/tbody")[0].findall("tr")
    all_release_rows = []

    for row in table[1:]:
        all_release_rows.append(list(row.getchildren()))

    return all_release_rows


def get_new(all_release_rows: list) -> list[Release]:
    """Return new security content listings that have not been posted yet."""
    new_sec_content = []

    for row in all_release_rows:
        if Release.parse_name(row) in PostedFile.data["posts"]["new_sec_content"]:
            break

        new_sec_content.append(Release.parse_from_table(row))

        assert (
            len(new_sec_content) < 20
        ), "ERROR: More than 20 new security contents found. Something may not be right. Verify posted_data.json[posts][new_sec_content]."

    for release in new_sec_content:
        PostedFile.data["posts"]["new_sec_content"].append(release.name)

        if (
            release.name not in PostedFile.data["details_available_soon"]
            and release.get_format_num_of_bugs() == "no details yet"
        ):
            # save releases with "no details yet"
            PostedFile.data["details_available_soon"].append(release.name)

    return new_sec_content


def get_if_available(all_release_rows: list) -> list[Release]:
    """Return releases that said "no details yet" but have it available now."""
    checked = 0
    must_check = len(PostedFile.data["details_available_soon"])
    new_sec_content = []

    for row in all_release_rows:
        if checked == must_check:
            break

        release_obj = Release.parse_from_table(row)

        if release_obj.name in PostedFile.data["details_available_soon"]:
            if release_obj.security_content_link != "":
                new_sec_content.append(release_obj)
                PostedFile.data["details_available_soon"].remove(release_obj.name)

            checked += 1

    return new_sec_content


def format_new_sec_content(releases: list[Release]) -> list:
    """
    🐛 NEW SECURITY CONTENT 🐛

    📱 iOS and iPadOS 16.5 - 39 bugs fixed
    ⌚ watchOS 9.5 - 32 bugs fixed
    📺 tvOS 16.5 - 1 bug fixed
    ⌚ watchOS 9.5.1 - no CVE entries
    https://support.apple.com/en-us/HT201222
    """

    releases.sort(key=lambda x: (x.num_of_bugs, x.name), reverse=True)

    post_text = [
        "🐛 NEW SECURITY CONTENT 🐛\n\n",
    ]

    for release in releases:
        post_text.append(f"{release.emoji} {release.name} - {release.get_format_num_of_bugs()}\n")

    # if there is only one release, add its notes as a link instead
    if len(releases) == 1:
        if releases[0].security_content_link:
            post_text.append(releases[0].security_content_link)
    else:
        post_text.append("https://support.apple.com/kb/HT201222")

    return post_text


def get_new_ios_release(new_sec_content: list[Release], latest_versions: dict) -> list[Release]:
    """
    If the latest iOS series got a new release.
    Do not post if all bugs are zero-days, as does are already in a post.
    """
    latest_ios_ver = str(latest_versions["iOS"][0])

    for release in new_sec_content:
        if (
            "iOS" in release.name
            and latest_ios_ver in release.name
            and release.name not in PostedFile.data["posts"]["ios_modules"]
            and release.security_content_link != ""
            and release.num_of_bugs != len(release.zero_days)
        ):
            PostedFile.data["posts"]["ios_modules"].append(release.name)
            return [release]

    return []


def format_ios_release(releases: list[Release]) -> list:
    """
    ⚒️ FIXED IN iOS 14.7 ⚒️

    - 4 bugs in WebKit
    - 3 bugs in FontParser
    - 3 bugs in Model I/O
    - 2 bugs in CoreAudio
    and 25 other vulnerabilities fixed
    https://support.apple.com/en-us/HT212601
    """
    post_text = []

    for release in releases:
        sec_content_html = requests.get(release.security_content_link, timeout=60).text
        sec_content_html = sec_content_html.split("Additional recognition", 1)[0]

        search_modules = collections.Counter(
            re.findall(r"(?<=<strong>).*?(?=<\/strong>)", sec_content_html)
        )
        modules = collections.OrderedDict(
            sorted(search_modules.items(), reverse=True, key=lambda x: x[1])
        )

        post_text = [f"⚒️ FIXED IN {release.name} ⚒️\n\n"]
        num_bugs = 0

        for key, value in modules.items():
            if len(post_text) < 5:
                if value > 1:
                    post_text.append(f"- {value} bugs in {key}\n")
                else:
                    post_text.append(f"- {value} bug in {key}\n")

                num_bugs += value

        num_bugs = release.num_of_bugs - num_bugs

        if num_bugs > 0:
            post_text.append(f"and {num_bugs} other vulnerabilities fixed\n")
        elif num_bugs == 1:
            post_text.append("and 1 other vulnerability fixed\n")

        post_text.append(f"{release.security_content_link}\n")

    return post_text


def get_new_zero_days(new_sec_content: list[Release]) -> list[Release]:
    zero_day_releases = []

    for release in new_sec_content:
        if (
            release.num_of_zero_days > 0
            and release.name not in PostedFile.data["posts"]["zero_days"].keys()
        ):
            zero_day_releases.append(release)
            PostedFile.data["posts"]["zero_days"][release.name] = release.num_of_zero_days

    return zero_day_releases


def format_zero_days_start_text(zero_days: dict) -> str:
    """Return text for the start of the zero day post."""
    num_new = 0
    num_old = 0
    text = ""

    for _, value in zero_days.items():
        if value["status"] == "new":
            num_new += 1
        else:
            num_old += 1

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


def format_zero_days(releases: list[Release]) -> list:
    """
    📣 EMERGENCY UPDATES 📣

    Apple pushed updates for 1 new zero-day that may have been actively exploited and additional updates for 1 zero-day.

    🐛 CVE-2021-30869 (XNU) additional patches:
    - Security Update 2021-006 Catalina
    - iOS 12.5.5

    🐛 CVE-2021-30860 (CoreGraphics):
    - iOS 12.5.5
    """
    zero_days = {}

    for release in releases:
        for cve, module in release.zero_days.items():
            if not zero_days.get(cve):
                zero_days[cve] = {
                    "status": "old",
                    "module": module,
                    "releases": [release.name],
                }
            else:
                zero_days[cve]["releases"].append(release.name)

            # if zero-day was not fixed in any previous releases
            if cve not in PostedFile.data["zero_days"]:
                PostedFile.data["zero_days"].append(cve)
                zero_days[cve]["status"] = "new"

    post_text = []

    if len(zero_days) == 1:
        post_text.append("📣 EMERGENCY UPDATE 📣\n\n")
    else:
        post_text.append("📣 EMERGENCY UPDATES 📣\n\n")

    post_text.append(format_zero_days_start_text(zero_days))

    for key, value in zero_days.items():
        if value["status"] == "new":
            post_text.append("\n\n🐛 " + key + " (" + value["module"] + "):")
        else:
            post_text.append("\n\n🐛 " + key + " (" + value["module"] + ") additional patches:")

        for release in value["releases"]:
            post_text[-1] += "\n- " + release

    return post_text


def get_entry_changes(all_release_rows: list) -> list[Release]:
    """
    Check for security content changes made on the previous day.
    Because of checking all of the security notes, it is only called at midnight.
    """
    changed_releases = []

    for row in all_release_rows:
        release = Release.parse_from_table(row)

        if release.num_entries_added > 0 or release.num_entries_updated > 0:
            changed_releases.append(release)

    return changed_releases


def format_entry_changes(releases: list[Release]) -> list:
    """
    🔄 24 ENTRY CHANGES 🔄

    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    💻 Security Update 2021-003 Catalina - 8 added
    💻 Security Update 2021-004 Mojave - 6 added
    🌐 Safari 14.1.1 - 1 updated
    """
    post_text = []
    changes_count = 0

    releases.sort(
        key=lambda x: (x.num_entries_added + x.num_entries_updated, x.name),
        reverse=True,
    )

    for release in releases:
        name = f"{release.emoji} {release.name}"

        changes_count += release.num_entries_added + release.num_entries_updated

        if release.num_entries_added > 0:
            if release.num_entries_updated > 0:
                post_text.append(
                    f"{name} - {release.get_format_num_entries_added()}, {release.get_format_num_entries_updated()}\n"
                )
            else:
                post_text.append(f"{name} - {release.get_format_num_entries_added()}\n")

        elif release.num_entries_updated > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_updated()}\n")

    if changes_count == 1:
        post_text.insert(
            0,
            "🔄 1 ENTRY CHANGE 🔄\n\n",
        )
    else:
        post_text.insert(
            0,
            f"🔄 {changes_count} ENTRY CHANGES 🔄\n\n",
        )

    return post_text


def get_yearly_report(new_sec_content: list[Release], latest_versions: dict) -> list:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    new_yearly_report = []

    for key, value in latest_versions.items():
        if key in PostedFile.data["posts"]["yearly_report"]:
            return []

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


def yearly_report(release_rows: list, system: str, version: int) -> list:
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
        post_text.append(
            f"- {value['num_of_bugs']} fixed in {system} {key} over {value['num_of_releases']} releases\n"
        )

    if system == "macOS":
        # for macOS create a thread with additional info in the second post
        post_text.append("Numbers also contain issues from Security and Supplemental Updates.")

    return post_text

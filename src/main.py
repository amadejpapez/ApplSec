import sys

import lxml.html
import requests

import format_tweet
import gather_info
import get_date
import json_file
from Release import Release

if "pytest" not in sys.modules:
    from posting import post


def retrieve_main_page() -> list:
    main_page = lxml.html.document_fromstring(
        requests.get("https://support.apple.com/en-us/HT201222", timeout=300).text
    )

    table = main_page.xpath("//table/tbody")[0].findall("tr")
    all_releases = []

    for row in table[1:]:
        all_releases.append(list(row.getchildren()))

    return all_releases


def check_latest_ios_release(coll: dict, stored_data: dict, release: Release, lat_ios_ver: str) -> None:
    """
    If the latest iOS series (currently iOS 16) got a new release.

    Do not tweet if all bugs are zero-days, as does are already in a tweet.
    """
    if (
        "iOS" in release.get_name()
        and lat_ios_ver in release.get_name()
        and release.get_name() not in stored_data["tweeted_today"]["ios_modules"]
        and release.get_security_content_link() != ""
        and release.get_num_of_bugs() != len(release.get_zero_days())
    ):
        coll["ios_release"].append(release)

        stored_data["tweeted_today"]["ios_modules"] = release.get_name()


def check_sec_content_available(coll: dict, stored_data: dict, release: Release) -> None:
    """
    Check if any releases that said "no details yet", got sec content now available.

    Also check if any new "no details yet" releases appeared and save them.
    """
    if (
        release.get_name() in stored_data["details_available_soon"]
        and release.get_security_content_link() != ""
    ):
        coll["sec_content_available"].append(release)

        stored_data["details_available_soon"].remove(release.get_name())

    if (
        release.get_name() not in stored_data["details_available_soon"]
        and release.get_format_num_of_bugs() == "no details yet"
    ):
        stored_data["details_available_soon"].append(release.get_name())


def check_for_new_releases(coll: dict, stored_data: dict, latest_versions: dict, date_format_one: str) -> None:
    lat_ios_ver = str(latest_versions["iOS"][0])

    for release in coll["last_twenty"]:
        if release.get_release_date() == date_format_one:
            if release.get_name() not in stored_data["tweeted_today"]["new_updates"]:
                coll["new_releases"].append(release)

                stored_data["tweeted_today"]["new_updates"].append(release.get_name())

            if "iOS" in release.get_name():
                check_latest_ios_release(coll, stored_data, release, lat_ios_ver)

        check_sec_content_available(coll, stored_data, release)


def check_for_zero_day_releases(coll: dict, stored_data: dict) -> None:
    """
    Look if there are any releases, containing zero-days.
    """
    check_tmp = coll["new_releases"] + coll["sec_content_available"]

    for release in check_tmp:
        if (
            release.get_num_of_zero_days() > 0
            and release.get_name() not in stored_data["tweeted_today"]["zero_days"].keys()
        ):
            coll["zero_day_releases"].append(release)

            stored_data["tweeted_today"]["zero_days"][release.get_name()] = release.get_num_of_zero_days()


def check_for_entry_changes(coll: dict, all_releases: list) -> None:
    """
    On midnight check for security content changes made on the previous day.
    Because of checking so many releases and to not make too much requests,
    it is only doing this once per day.
    """

    all_releases_info = coll["last_twenty"]

    for row in all_releases[20:]:
        all_releases_info.append(Release(row))

    for release in all_releases_info:
        if release.get_num_entries_added() > 0 or release.get_num_entries_updated() > 0:
            coll["changed_releases"].append(release)


def check_for_yearly_report(coll: dict, stored_data: dict, latest_versions: dict) -> None:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    for key, value in latest_versions.items():
        if key in stored_data["tweeted_today"]["yearly_report"]:
            return

        stored_data["tweeted_today"]["yearly_report"].append(key)

        for release in coll["new_releases"]:
            if release.get_name() in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
                coll["yearly_report"].append([key, value[0]])

            elif key == "macOS":
                if release.get_name() in (
                    f"{key} {value[1]} {value[0]}",
                    f"{key} {value[1]} {value[0]}.0",
                ):
                    coll["yearly_report"].append([key, value[0]])


def main():
    stored_data = json_file.read()

    all_releases = retrieve_main_page()
    releases = all_releases[:20]
    releases_info = []

    for row in releases:
        releases_info.append(Release(row))

    coll = {
        "last_twenty": releases_info,
        "new_releases": [],
        "ios_release": [],
        "changed_releases": [],
        "sec_content_available": [],
        "zero_day_releases": [],
        "yearly_report": [],
    }

    latest_versions = gather_info.latest_version(releases)

    check_for_new_releases(coll, stored_data, latest_versions, get_date.format_one())
    check_for_zero_day_releases(coll, stored_data)

    if get_date.is_midnight():
        check_for_entry_changes(coll, all_releases)

    # check_for_yearly_report(coll, stored_data, latest_versions) # DISABLED AS NOT TESTED ENOUGH

    if coll["ios_release"]:
        post(format_tweet.top_ios_modules(coll["ios_release"]))

    if coll["zero_day_releases"]:
        post(format_tweet.zero_days(coll["zero_day_releases"], stored_data))

    if coll["changed_releases"]:
        post(format_tweet.entry_changes(coll["changed_releases"]))

    if coll["sec_content_available"]:
        post(format_tweet.security_content_available(coll["sec_content_available"]))

    # if coll["yearly_report"]:
    #    post(format_tweet.yearly_report(all_releases, key, value[0]))

    # new updates should be tweeted last, after all of the other tweets
    if coll["new_releases"]:
        post(format_tweet.new_updates(coll["new_releases"]))

    json_file.save(stored_data)


if __name__ == "__main__":
    main()

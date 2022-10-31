import re

import requests

import format_tweet
import gather_info
import get_date
import json_file
from Release import Release
from twitter import tweet


def retrieve_main_page() -> list:
    MAIN_PAGE_HTML = (
        requests.get("https://support.apple.com/en-us/HT201222")
        .text.replace("\n", "")
        .replace("&nbsp;", " ")
    )
    all_releases = re.findall(r"(?<=<tr>).*?(?=<\/tr>)", MAIN_PAGE_HTML)[1:]

    for i, _ in enumerate(all_releases):
        all_releases[i] = re.findall(r"(?<=<td)(?:[^>]*>)(.*?)(?=<\/td>)", all_releases[i])

    return all_releases


def check_for_new_releases(coll: dict, stored_data: dict, latest_versions: dict) -> None:
    date_format_one = get_date.format_one()

    for release in coll["last_twenty"]:
        if release.get_release_date() == date_format_one:
            coll["new_releases"].append(release)

            # if the latest iOS series got a new release
            if (
                "iOS" in release.get_name()
                and str(latest_versions["iOS"][0]) in release.get_name()
            ):
                coll["ios_release"].append(release)

        # if any releases that said "soon" got security content available
        if (
            release.get_name() in stored_data["details_available_soon"]
            and release.get_security_content_link() != ""
        ):
            coll["sec_content_available"].append(release)

        # or if any new releases say "no details yet"
        if release.get_format_num_of_bugs() == "no details yet":
            coll["sec_content_available"].append(release)


def check_for_zero_day_releases(coll: dict) -> None:
    """
    Look if there are any releases, containing zero-days.
    """
    check_tmp = coll["new_releases"] + coll["sec_content_available"]

    for release in check_tmp:
        if release.get_num_of_zero_days() > 0:
            coll["zero_day_releases"].append(release)


def check_for_entry_changes(coll: dict, all_releases: list) -> None:
    """
    On midnight check for security content changes made on the previous day.
    Because of checking so many releases and to not make too much requests,
    it is only doing this once per day.
    """
    if not get_date.is_midnight():
        return

    all_releases_info = coll["last_twenty"]

    for row in all_releases[20:]:
        all_releases_info.append(Release(row))

    for release in all_releases_info:
        if release.get_num_entries_added() > 0 or release.get_num_entries_updated() > 0:
            coll["changed_releases"].append(release)


def check_for_yearly_report(coll: dict, latest_versions: dict) -> None:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    for key, value in latest_versions.items():
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
        "yearly_report": []
    }

    latest_versions = gather_info.latest_version(releases)

    check_for_new_releases(coll, stored_data, latest_versions)
    check_for_entry_changes(coll, all_releases)
    check_for_zero_day_releases(coll)
    # check_for_yearly_report(coll, latest_versions) # DISABLED AS NOT TESTED ENOUGH

    if coll["ios_release"]:
        tweet(format_tweet.top_ios_modules(coll["ios_release"], stored_data))

    if coll["zero_day_releases"]:
        tweet(format_tweet.zero_days(list(coll["zero_day_releases"]), stored_data))

    if coll["changed_releases"]:
        tweet(format_tweet.entry_changes(coll["changed_releases"]))

    if coll["sec_content_available"]:
        tweet(
            format_tweet.security_content_available(
                list(coll["sec_content_available"]), stored_data
            )
        )

    # if coll["yearly_report"]:
    #    tweet(format_tweet.yearly_report(all_releases, key, value[0], stored_data))

    # new updates should be tweeted last, after all of the other tweets
    if coll["new_releases"]:
        tweet(format_tweet.new_updates(list(coll["new_releases"]), stored_data))

    json_file.save(stored_data)


if __name__ == "__main__" :
    main()

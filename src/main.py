import lxml.html
import requests

import helpers.get_date as get_date
import helpers.get_version_info as get_version_info
import helpers.manage_posted_data as manage_posted_data
import post_format
from post_make import post
from Release import Release, create_name


def retrieve_main_page() -> list:
    main_page = lxml.html.document_fromstring(
        requests.get("https://support.apple.com/en-us/HT201222", timeout=60).text
    )

    table = main_page.xpath("//table/tbody")[0].findall("tr")
    all_releases_rows = []

    for row in table[1:]:
        all_releases_rows.append(list(row.getchildren()))

    return all_releases_rows


def check_latest_ios_release(
    coll: dict[str, list[Release]], posted_data: dict, release: Release, lat_ios_ver: str
) -> None:
    """
    If the latest iOS series (currently iOS 16) got a new release.

    Do not post if all bugs are zero-days, as does are already in a post.
    """
    if (
        "iOS" in release.name
        and lat_ios_ver in release.name
        and release.name not in posted_data["posts"]["ios_modules"]
        and release.security_content_link != ""
        and release.num_of_bugs != len(release.zero_days)
    ):
        coll["ios_release"].append(release)

        posted_data["posts"]["ios_modules"].append(release.name)


def save_sec_content_no_details_yet(posted_data: dict, release: Release) -> None:
    """
    Receives releases with "no details yet" from check_for_new_releases()
    and saves them.
    """
    if (
        release.name not in posted_data["details_available_soon"]
        and release.get_format_num_of_bugs() == "no details yet"
    ):
        posted_data["details_available_soon"].append(release.name)


def check_if_sec_content_available(coll: dict[str, list[Release]], posted_data: dict, all_releases_rows: list) -> None:
    """
    Check if any releases that said "no details yet", got security content available now.
    """
    checked = 0
    must_check = len(posted_data["details_available_soon"])

    for row in all_releases_rows:
        if checked == must_check:
            break

        release_obj = Release(row)

        if release_obj.name in posted_data["details_available_soon"]:
            if release_obj.security_content_link != "":
                coll["sec_content_available"].append(release_obj)
                posted_data["details_available_soon"].remove(release_obj.name)

            checked += 1


def check_new_releases(
    coll: dict[str, list[Release]], posted_data: dict, latest_versions: dict, new_releases: list[Release]
) -> None:
    latest_ios_ver = str(latest_versions["iOS"][0])

    for release in new_releases:
        if release.name not in posted_data["posts"]["new_updates"]:
            coll["new_releases"].append(release)

            posted_data["posts"]["new_updates"].append(release.name)

        if "iOS" in release.name:
            check_latest_ios_release(coll, posted_data, release, latest_ios_ver)

        if release.security_content_link == "":
            save_sec_content_no_details_yet(posted_data, release)


def check_for_zero_day_releases(coll: dict[str, list[Release]], posted_data: dict) -> None:
    """
    Look if there are any releases, containing zero-days.
    """
    check_tmp = coll["new_releases"] + coll["sec_content_available"]

    for release in check_tmp:
        if (
            release.num_of_zero_days > 0
            and release.name not in posted_data["posts"]["zero_days"].keys()
        ):
            coll["zero_day_releases"].append(release)

            posted_data["posts"]["zero_days"][
                release.name
            ] = release.num_of_zero_days


def check_for_entry_changes(coll: dict[str, list[Release]], all_releases_rows: list) -> None:
    """
    On midnight check for security content changes made on the previous day.
    Because of checking so many releases and to not make too much requests,
    it is only doing this once per day.
    """
    for row in all_releases_rows:
        release = Release(row)

        if release.num_entries_added > 0 or release.num_entries_updated > 0:
            coll["changed_releases"].append(release)


def check_for_yearly_report(coll: dict[str, list[Release]], coll_yearly_report: list, posted_data: dict, latest_versions: dict) -> None:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    for key, value in latest_versions.items():
        if key in posted_data["posts"]["yearly_report"]:
            return

        posted_data["posts"]["yearly_report"].append(key)

        for release in coll["new_releases"]:
            if release.name in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
                coll_yearly_report.append([key, value[0]])

            elif key == "macOS":
                if release.name in (
                    f"{key} {value[1]} {value[0]}",
                    f"{key} {value[1]} {value[0]}.0",
                ):
                    coll_yearly_report.append([key, value[0]])


def main():
    posted_data = manage_posted_data.read()
    all_releases_rows = retrieve_main_page()
    latest_versions = get_version_info.latest(all_releases_rows[:20])

    new_releases = []

    for row in all_releases_rows:
        if create_name(row) in posted_data["posts"]["new_updates"]:
            break

        new_releases.insert(0, Release(row))

    coll = {
        "new_releases": [],
        "ios_release": [],
        "changed_releases": [],
        "sec_content_available": [],
        "zero_day_releases": [],
    }
    coll_yearly_report = []

    check_new_releases(coll, posted_data, latest_versions, new_releases)
    check_for_zero_day_releases(coll, posted_data)
    check_if_sec_content_available(coll, posted_data, all_releases_rows)

    if get_date.is_midnight():
        check_for_entry_changes(coll, all_releases_rows)

    # check_for_yearly_report(coll, coll_yearly_report, posted_data, latest_versions) # DISABLED AS NOT TESTED ENOUGH

    if coll["ios_release"]:
        post(post_format.top_ios_modules(coll["ios_release"]))

    if coll["zero_day_releases"]:
        post(post_format.zero_days(coll["zero_day_releases"], posted_data))

    if coll["changed_releases"]:
        post(post_format.entry_changes(coll["changed_releases"]))

    if coll["sec_content_available"]:
        post(post_format.security_content_available(coll["sec_content_available"]))

    # if coll_yearly_report:
    #    post(format_post.yearly_report(all_releases, key, value[0]))

    # new updates should be posted last, after all of the other posts
    if coll["new_releases"]:
        post(post_format.new_updates(coll["new_releases"]))

    manage_posted_data.save(posted_data)


if __name__ == "__main__":
    main()

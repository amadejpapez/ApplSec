import lxml.etree
import lxml.html
import requests

import helpers.get_date as get_date
import helpers.get_version_info as get_version_info
import helpers.post_format as post_format
from helpers.post_make import post
from helpers.PostedFile import PostedFile
from Release import Release


def retrieve_security_page() -> list:
    main_page = lxml.html.document_fromstring(
        requests.get("https://support.apple.com/en-us/HT201222", timeout=60).text
    )

    table = main_page.xpath("//table/tbody")[0].findall("tr")
    all_releases_rows = []

    for row in table[1:]:
        all_releases_rows.append(list(row.getchildren()))

    return all_releases_rows


def retrieve_releases_page() -> lxml.etree._ElementTree:
    rss_feed = requests.get(
        "https://developer.apple.com/news/releases/rss/releases.rss", timeout=60
    ).text.encode("utf-8")
    xml_tree = lxml.etree.fromstring(rss_feed, None)

    return xml_tree


def check_new_releases(
    coll: dict[str, list[Release]], xml_tree: lxml.etree._ElementTree
) -> None:
    new_releases = []

    for el in xml_tree.xpath("//item"):
        name = el.xpath("title")[0].text
        emoji = Release.parse_emoji(name)

        if name in PostedFile.data["posts"]["new_releases"]:
            break

        # skip releases that do not have an emoji in parse_emoji()
        # specifically to skip updates for App Store Connect, TestFlight and so on
        if emoji == "🛠️":
            continue

        new_releases.insert(0, Release.from_rss_release(el))

        assert len(new_releases) < 20, "ERROR: More than 20 new releases detected. Something may not be right. Verify posted_data.json[posts][new_releases]."

    for release in new_releases:
        if release.emoji != "" and release.name not in PostedFile.data["posts"]["new_releases"]:
            coll["new_releases"].append(release)

            PostedFile.data["posts"]["new_releases"].append(release.name)


def check_latest_ios_release(
    coll: dict[str, list[Release]], release: Release, lat_ios_ver: str
) -> None:
    """
    If the latest iOS series (currently iOS 16) got a new release.

    Do not post if all bugs are zero-days, as does are already in a post.
    """
    if (
        "iOS" in release.name
        and lat_ios_ver in release.name
        and release.name not in PostedFile.data["posts"]["ios_modules"]
        and release.security_content_link != ""
        and release.num_of_bugs != len(release.zero_days)
    ):
        coll["ios_release"].append(release)

        PostedFile.data["posts"]["ios_modules"].append(release.name)


def save_sec_content_no_details_yet(release: Release) -> None:
    """
    Receives releases with "no details yet" from check_for_new_releases()
    and saves them.
    """
    if (
        release.name not in PostedFile.data["details_available_soon"]
        and release.get_format_num_of_bugs() == "no details yet"
    ):
        PostedFile.data["details_available_soon"].append(release.name)


def check_if_sec_content_available(
    coll: dict[str, list[Release]], all_releases_rows: list
) -> None:
    """
    Check if any releases that said "no details yet", got security content available now.
    """
    checked = 0
    must_check = len(PostedFile.data["details_available_soon"])

    for row in all_releases_rows:
        if checked == must_check:
            break

        release_obj = Release.parse_from_table(row)

        if release_obj.name in PostedFile.data["details_available_soon"]:
            if release_obj.security_content_link != "":
                coll["new_sec_content"].append(release_obj)
                PostedFile.data["details_available_soon"].remove(release_obj.name)

            checked += 1


def check_new_security_content(
    coll: dict[str, list[Release]],
    latest_versions: dict,
    all_releases_rows: list,
) -> None:
    latest_ios_ver = str(latest_versions["iOS"][0])
    new_sec_content = []

    for row in all_releases_rows:
        if Release.parse_name(row) in PostedFile.data["posts"]["new_sec_content"]:
            break

        new_sec_content.insert(0, Release.parse_from_table(row))

        assert len(new_sec_content) < 20, "ERROR: More than 20 new security contents found. Something may not be right. Verify posted_data.json[posts][new_sec_content]."

    for release in new_sec_content:
        if release.name not in PostedFile.data["posts"]["new_sec_content"]:
            coll["new_sec_content"].append(release)

            PostedFile.data["posts"]["new_sec_content"].append(release.name)

        if "iOS" in release.name:
            check_latest_ios_release(coll, release, latest_ios_ver)

        if release.security_content_link == "":
            save_sec_content_no_details_yet(release)


def check_for_zero_day_releases(coll: dict[str, list[Release]]) -> None:
    """
    Look if there are any releases, containing zero-days.
    """
    for release in coll["new_sec_content"]:
        if (
            release.num_of_zero_days > 0
            and release.name not in PostedFile.data["posts"]["zero_days"].keys()
        ):
            coll["zero_day_releases"].append(release)

            PostedFile.data["posts"]["zero_days"][release.name] = release.num_of_zero_days


def check_for_entry_changes(coll: dict[str, list[Release]], all_releases_rows: list) -> None:
    """
    On midnight check for security content changes made on the previous day.
    Because of checking so many releases and to not make too much requests,
    it is only doing this once per day.
    """
    for row in all_releases_rows:
        release = Release.parse_from_table(row)

        if release.num_entries_added > 0 or release.num_entries_updated > 0:
            coll["changed_releases"].append(release)


def check_for_yearly_report(
    coll: dict[str, list[Release]],
    coll_yearly_report: list,
    latest_versions: dict,
) -> None:
    """
    If there is a new major upgrade. Report how many bugs Apple fixed
    in the last 4 major series releases.
    """
    for key, value in latest_versions.items():
        if key in PostedFile.data["posts"]["yearly_report"]:
            return

        PostedFile.data["posts"]["yearly_report"].append(key)

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
    PostedFile.read()
    all_releases_rows = retrieve_security_page()
    releases_page = retrieve_releases_page()
    latest_versions = get_version_info.latest(all_releases_rows[:20])

    coll = {
        "new_releases": [],
        "new_sec_content": [],
        "ios_release": [],
        "changed_releases": [],
        "zero_day_releases": [],
    }
    # coll_yearly_report = []

    check_new_releases(coll, releases_page)

    check_new_security_content(coll, latest_versions, all_releases_rows)
    check_for_zero_day_releases(coll)
    check_if_sec_content_available(coll, all_releases_rows)

    if get_date.is_midnight():
        check_for_entry_changes(coll, all_releases_rows)

    # check_for_yearly_report(coll, coll_yearly_report, latest_versions) # DISABLED AS NOT TESTED ENOUGH

    if coll["ios_release"]:
        post(post_format.top_ios_modules(coll["ios_release"]))

    if coll["zero_day_releases"]:
        post(post_format.zero_days(coll["zero_day_releases"]))

    if coll["changed_releases"]:
        post(post_format.entry_changes(coll["changed_releases"]))

    # if coll_yearly_report:
    #    post(format_post.yearly_report(all_releases, key, value[0]))

    # new updates should be posted last, after all of the other posts
    if coll["new_releases"]:
        post(post_format.new_updates(coll["new_releases"]))

    if coll["new_sec_content"]:
        post(post_format.new_security_content(coll["new_sec_content"]))

    PostedFile.save()


if __name__ == "__main__":
    main()

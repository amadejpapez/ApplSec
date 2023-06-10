import lxml.html
import requests

from helpers.PostedFile import PostedFile
from Release import Release


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

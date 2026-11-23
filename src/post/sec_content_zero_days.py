"""
Post zero-days fixed in new security content, grouped by releases they were fixed in.
"""

from helpers.posted_file import PostedFile
from release import Release


def get_new(new_sec_content: list[Release]) -> list[Release]:
    zero_day_releases = []

    for release in new_sec_content:
        if release.num_of_zero_days > 0 and release.name not in PostedFile.data["posts"]["zero_days"].keys():
            zero_day_releases.append(release)

    zero_day_releases.reverse()
    for release in zero_day_releases:
        PostedFile.data["posts"]["zero_days"][release.name] = release.num_of_zero_days

    return zero_day_releases


def _format_start_text(zero_days: dict[str, dict]) -> str:
    """Return text for the start of the zero day post."""
    num_new = 0
    num_old = 0
    text = ""

    for _, value in zero_days.items():
        if value["details"]["status"] == "new":
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


def format_releases(releases: list[Release]) -> list[str]:
    """
    📣 EMERGENCY UPDATES 📣

    Apple pushed updates for 3 new zero-days that may have been actively exploited
    and additional updates for 1 zero-day.

    🐛 CVE-2021-30869 (XNU) additional patches:
    - Security Update 2021-006 Catalina
    - iOS 12.5.5

    🐛 CVE-2021-30860 (CoreGraphics),
    🐛 CVE-2021-31010 (Core Telephony),
    🐛 CVE-2021-30858 (WebKit):
    - iOS 12.5.5"
    """
    if not releases:
        return []

    # group releases by CVE, determine if CVE new or old
    zero_days: dict[str, dict] = {}
    for release in releases:
        for cve, module in release.zero_days.items():
            if not zero_days.get(cve):
                zero_days[cve] = {
                    "releases": [release.name],
                    "details": {"status": "old", "module": module},
                }
            else:
                zero_days[cve]["releases"].append(release.name)

            # if zero-day was not fixed in any previous releases
            if cve not in PostedFile.data["zero_days"]:
                PostedFile.data["zero_days"].append(cve)
                zero_days[cve]["details"]["status"] = "new"

    # group set of releases if they share multiple CVEs together
    release_groups: list[dict] = []
    for key, value in zero_days.items():
        for item in release_groups:
            if item["releases"] == value["releases"]:
                item["zero_days"][key] = value["details"]
                break
        else:
            release_groups.append({"releases": value["releases"], "zero_days": {key: value["details"]}})

    post_text = []

    if len(zero_days) == 1:
        post_text.append("📣 EMERGENCY UPDATE 📣\n\n")
    else:
        post_text.append("📣 EMERGENCY UPDATES 📣\n\n")

    post_text.append(_format_start_text(zero_days))

    for group in release_groups:
        text = "\n"

        for cve, value in group["zero_days"].items():
            if value["status"] == "new":
                text += "\n🐛 " + cve + " (" + value["module"] + "),"
            else:
                text += "\n🐛 " + cve + " (" + value["module"] + ") additional patches,"

        text = text[:-1] + ":"

        group["releases"].sort(key=str.lower)
        for rel in group["releases"]:
            text += "\n- " + rel

        post_text.append(text)

    return post_text

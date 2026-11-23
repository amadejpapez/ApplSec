"""
Post the modules with the most bugs fixed in a new release of the latest iOS series.
"""

import collections
import re

from helpers.posted_file import PostedFile
from helpers.session import session
from release import Release


def get_new(new_sec_content: list[Release], latest_versions: dict[str, list]) -> list[Release]:
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


def format_release(releases: list[Release]) -> list[str]:
    """
    ⚒️ FIXED IN iOS 14.7 ⚒️

    - 4 bugs in WebKit
    - 3 bugs in FontParser
    - 3 bugs in Model I/O
    - 2 bugs in CoreAudio
    and 25 other vulnerabilities fixed
    https://support.apple.com/kb/HT212601
    """
    if not releases:
        return []

    release = releases[0]

    response = session.get(release.security_content_link, timeout=60)
    response.raise_for_status()
    sec_content_html = response.text
    modules_html = Release.get_html_entries(sec_content_html)

    modules: dict[str, int] = {}

    for entry in modules_html:
        module_name = Release.get_html_entry_title(entry)
        cve_count = len(re.findall(r"(?i)CVE-[0-9]{4}-[0-9]+", entry))

        if module_name not in modules:
            modules[module_name] = cve_count
        else:
            modules[module_name] += cve_count

    modules = collections.OrderedDict(sorted(modules.items(), reverse=True, key=lambda x: x[1]))

    post_text = [f"⚒️ FIXED IN {release.name} ⚒️\n\n"]
    num_bugs = 0

    for key, value in modules.items():
        if len(post_text) >= 5:
            break

        if value > 1:
            post_text.append(f"- {value} bugs in {key}\n")
        else:
            post_text.append(f"- {value} bug in {key}\n")

        num_bugs += value

    num_bugs = release.num_of_bugs - num_bugs

    if num_bugs == 1:
        post_text.append("and 1 other vulnerability fixed\n")
    elif num_bugs > 0:
        post_text.append(f"and {num_bugs} other vulnerabilities fixed\n")

    post_text.append(f"{release.security_content_link}\n")

    return post_text

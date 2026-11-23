"""
Post new security content listings and ones whose details became available later.
"""

import lxml.html

from helpers.posted_file import PostedFile
from release import Release


def get_new(all_release_rows: list[list[lxml.html.HtmlElement]]) -> list[Release]:
    """Return new security content listings that have not been posted yet."""
    new_sec_content = []

    for i, row in enumerate(all_release_rows):
        name = Release.parse_name(row)

        if name in PostedFile.data["posts"]["new_sec_content"]:
            # handle if Apple adds new release but not at the top
            # i should be less than the number of saved items in case of reordering
            if i >= 19:
                break
            continue

        new_sec_content.append(Release.parse_from_table(row))

        assert (
            len(new_sec_content) < 20
        ), "ERROR: More than 20 new security contents found. Something may not be right. Verify posted_data.json[posts][new_sec_content]."

    new_sec_content.reverse()
    for release in new_sec_content:
        PostedFile.data["posts"]["new_sec_content"].append(release.name)

        if (
            release.name not in PostedFile.data["details_available_soon"]
            and release.get_format_num_of_bugs() == "no details yet"
        ):
            # save releases with "no details yet"
            PostedFile.data["details_available_soon"].append(release.name)

    return new_sec_content + get_if_available(all_release_rows)


def get_if_available(all_release_rows: list[list[lxml.html.HtmlElement]]) -> list[Release]:
    """Return releases that said "no details yet" but have it available now."""
    checked = 0
    must_check = len(PostedFile.data["details_available_soon"])
    new_sec_content = []

    for row in all_release_rows:
        if checked == must_check:
            break

        release_name = Release.parse_name(row)
        release_security_link = Release.parse_security_content_link(row)

        if release_name in PostedFile.data["details_available_soon"]:
            if release_security_link != "":
                release_obj = Release.parse_from_table(row)

                new_sec_content.append(release_obj)
                PostedFile.data["details_available_soon"].remove(release_obj.name)

            checked += 1

    return new_sec_content


def format_mastodon(releases: list[Release]) -> list[str]:
    """
    🐛 NEW SECURITY CONTENT 🐛

    📱 iOS and iPadOS 16.5 - 39 bugs fixed
    https://support.apple.com/kb/HT213757
    ⌚ watchOS 9.5 - 32 bugs fixed
    https://support.apple.com/kb/HT213764
    📺 tvOS 16.5 - 1 bug fixed
    https://support.apple.com/kb/HT213761
    ⌚ watchOS 9.5.1 - no CVE entries
    """
    if not releases:
        return []

    releases.sort(key=lambda x: (x.num_of_bugs, x.name), reverse=True)

    post_text = [
        "🐛 NEW SECURITY CONTENT 🐛\n\n",
    ]

    for release in releases:
        post_text.append(f"{release.emoji} {release.name} - {release.get_format_num_of_bugs()}\n")

        if release.security_content_link:
            post_text[-1] += f"{release.security_content_link}\n"

    return post_text


def format_twitter(releases: list[Release]) -> list[str]:
    """
    🐛 NEW SECURITY CONTENT 🐛

    📱 iOS and iPadOS 16.5 - 39 bugs fixed
    ⌚ watchOS 9.5 - 32 bugs fixed
    📺 tvOS 16.5 - 1 bug fixed
    ⌚ watchOS 9.5.1 - no CVE entries
    https://support.apple.com/en-us/HT201222
    """
    if not releases:
        return []

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
        post_text.append("https://support.apple.com/en-us/100100")

    return post_text

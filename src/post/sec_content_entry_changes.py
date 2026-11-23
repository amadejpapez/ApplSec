"""
Post entries added or updated on the previous day across all security content.
"""

import lxml.html

from release import Release


def get_changed(all_release_rows: list[list[lxml.html.HtmlElement]]) -> list[Release]:
    """
    Check for security content changes made on the previous day.
    Because of checking all of the security notes, it is only called at midnight.
    """
    changed_releases = []

    for row in all_release_rows:
        # Checks hundreds of pages, so one failing should not skip changes of all others
        release = Release.parse_from_table(row, skip_failed_fetch=True)

        if release.num_entries_added > 0 or release.num_entries_updated > 0:
            changed_releases.append(release)

    return changed_releases


def format_mastodon(releases: list[Release]) -> list[str]:
    """
    🔄 24 ENTRY CHANGES 🔄

    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    https://support.apple.com/kb/HT212529
    💻 Security Update 2021-003 Catalina - 8 added
    https://support.apple.com/kb/HT212530
    💻 Security Update 2021-004 Mojave - 6 added
    https://support.apple.com/kb/HT212531
    🌐 Safari 14.1.1 - 1 updated
    https://support.apple.com/kb/HT212534
    """
    if not releases:
        return []

    post_text = []
    changes_count = 0

    releases.sort(
        key=lambda x: (x.num_entries_added + x.num_entries_updated, x.name),
        reverse=True,
    )

    for release in releases:
        name = f"{release.emoji} {release.name}"

        changes_count += release.num_entries_added + release.num_entries_updated

        if release.num_entries_added > 0 and release.num_entries_updated > 0:
            post_text.append(
                f"{name} - {release.get_format_num_entries_added()}, {release.get_format_num_entries_updated()}\n"
            )
        elif release.num_entries_added > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_added()}\n")
        elif release.num_entries_updated > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_updated()}\n")

        if release.num_entries_added > 0 or release.num_entries_updated > 0:
            if release.security_content_link != "":
                post_text[-1] += f"{release.security_content_link}\n"

    if changes_count == 1:
        post_text.insert(0, "🔄 1 ENTRY CHANGE 🔄\n\n")
    else:
        post_text.insert(0, f"🔄 {changes_count} ENTRY CHANGES 🔄\n\n")

    return post_text


def format_twitter(releases: list[Release]) -> list[str]:
    """
    🔄 24 ENTRY CHANGES 🔄

    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    💻 Security Update 2021-003 Catalina - 8 added
    💻 Security Update 2021-004 Mojave - 6 added
    🌐 Safari 14.1.1 - 1 updated
    """
    if not releases:
        return []

    post_text = []
    changes_count = 0

    releases.sort(
        key=lambda x: (x.num_entries_added + x.num_entries_updated, x.name),
        reverse=True,
    )

    for release in releases:
        name = f"{release.emoji} {release.name}"

        changes_count += release.num_entries_added + release.num_entries_updated

        if release.num_entries_added > 0 and release.num_entries_updated > 0:
            post_text.append(
                f"{name} - {release.get_format_num_entries_added()}, {release.get_format_num_entries_updated()}\n"
            )
        elif release.num_entries_added > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_added()}\n")
        elif release.num_entries_updated > 0:
            post_text.append(f"{name} - {release.get_format_num_entries_updated()}\n")

    if changes_count == 1:
        post_text.insert(0, "🔄 1 ENTRY CHANGE 🔄\n\n")
    else:
        post_text.insert(0, f"🔄 {changes_count} ENTRY CHANGES 🔄\n\n")

    return post_text

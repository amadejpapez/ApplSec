def format_entry_changes(releases_info: list) -> list:
    """
    -----
    🔄 4 SECURITY NOTES UPDATED 🔄

    🌐 Safari 14.1.1 - 1 entry updated
    💻 Security Update 2021-003 Catalina - 8 entries added
    💻 Security Update 2021-004 Mojave - 6 entries added
    💻 macOS Big Sur 11.4 - 8 entries added, 1 entry updated
    -----
    """

    tweet_text = []

    for release in releases_info:
        name = f"{release.get_emoji()} {release.get_name()}"
        added = release.get_format_num_entries_added()
        updated = release.get_format_num_entries_updated()

        if not added and updated:
            tweet_text.append(f"{name} - {updated}\n")
        elif added and not updated:
            tweet_text.append(f"{name} - {added}\n")
        elif added and updated:
            tweet_text.append(f"{name} - {added}, {updated}\n")

    if len(tweet_text) > 1:
        tweet_text.insert(
            0,
            f":arrows_counterclockwise: {len(tweet_text)} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n",
        )
    else:
        tweet_text.insert(
            0,
            ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n",
        )

    return tweet_text


def format_release_notes_available(releases_info: list, stored_data: dict) -> list:
    """
    -----
    🗒 RELEASE NOTES AVAILABLE 🗒

    💻 macOS Monterey 12.0.1 - 40 bugs fixed
    💻 macOS Big Sur 11.6.1 - 24 bugs fixed
    💻 Security Update 2021-007 Catalina - 21 bugs fixed
    ⌚ watchOS 8.1 - 16 bugs fixed
    📱 iOS and iPadOS 15.1 - 22 bugs fixed
    -----
    """

    for release in list(releases_info):
        if (
            release.get_name() in stored_data["details_available_soon"]
            and release.get_release_notes_link() is not None
        ):
            stored_data["details_available_soon"].remove(release.get_name())

        elif (
            release.get_name() not in stored_data["details_available_soon"]
            and release.get_format_num_of_bugs() == "no details yet"
        ):
            stored_data["details_available_soon"].append(release.get_name())
            releases_info.remove(release)

    if not releases_info:
        return []

    tweet_text = [
        ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n",
    ]

    for release in releases_info:
        tweet_text.append(
            f"{release.get_emoji()} {release.get_name()} - {release.get_format_num_of_bugs()}\n"
        )

    return tweet_text

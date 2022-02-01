import re


def format_entry_changes(changes_info):
    """
    -----
    🔄 4 SECURITY NOTES UPDATED 🔄

    🌐 Safari 14.1.1 - 1 updated
    💻 Security Update 2021-003 Catalina - 8 added
    💻 Security Update 2021-004 Mojave - 6 added
    💻 macOS Big Sur 11.4 - 8 added, 1 updated
    -----
    """

    tweet_text = []
    for key, value in changes_info.items():
        added = value["entries_added"]
        updated = value["entries_updated"]

        if added is None and updated is not None:
            tweet_text.append(f"{value['emoji']} {key} - {updated}\n")
        elif added is not None and updated is None:
            tweet_text.append(f"{value['emoji']} {key} - {added}\n")
        elif added is not None and updated is not None:
            tweet_text.append(f"{value['emoji']} {key} - {added}, {updated}\n")

    num_updates = len(re.findall(r":[^:]+:", str(tweet_text)))

    if num_updates == 1:
        tweet_text.insert(
            0,
            ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n",
        )
    else:
        tweet_text.insert(
            0,
            f":arrows_counterclockwise: {num_updates} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n",
        )

    return tweet_text


def format_release_notes_available(notes_releases_info, stored_data):
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

    for key, value in list(notes_releases_info.items()):
        if (
            key in stored_data["details_available_soon"]
            and value["release_notes"] is not None
        ):
            stored_data["details_available_soon"].remove(key)

        elif (
            key not in stored_data["details_available_soon"]
            and value["num_of_bugs"] == "no details yet"
        ):
            stored_data["details_available_soon"].append(key)
            del notes_releases_info[key]

    if not notes_releases_info:
        return None

    tweet_text = [
        ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n",
    ]

    for key, value in notes_releases_info.items():
        tweet_text.append(f"{value['emoji']} {key} - {value['num_of_bugs']}\n")

    return tweet_text

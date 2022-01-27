import re

from twitter import tweet_or_make_a_thread


def tweet_entry_changes(releases_info, stored_data):
    """
    -----------------------------
    🔄 4 SECURITY NOTES UPDATED 🔄

    🌐 Safari 14.1.1 - 1 entry updated
    💻 Security Update 2021-003 Catalina - 8 entries added
    💻 Security Update 2021-004 Mojave - 6 entries added

    💻 macOS Big Sur 11.4 - 8 entries added, 1 entry updated
    -----------------------------
    """

    for key, value in list(releases_info.items()):
        if (
            key in stored_data["todays_tweets"]["tweetEntryChanges"].keys()
            and value["added"] == stored_data["todays_tweets"]["tweetEntryChanges"][key][0]
            and value["updated"] == stored_data["todays_tweets"]["tweetEntryChanges"][key][1]
        ):
            del releases_info[key]
        else:
            stored_data["todays_tweets"]["tweetEntryChanges"][key] = [value["added"], value["updated"]]

    results = []
    title = ""

    for key, value in releases_info.items():
        added = value["entries_added"]
        updated = value["entries_updated"]

        if added is not None or updated is not None:
            if added is None and updated is not None:
                results.append(f"{value['emoji']} {key} - {updated}\n")
            elif added is not None and updated is None:
                results.append(f"{value['emoji']} {key} - {added}\n")
            elif added is not None and updated is not None:
                results.append(f"{value['emoji']} {key} - {added}, {updated}\n")

    num = len(re.findall(r":[^:]+:", str(results)))

    if num > 1:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"

    tweet_or_make_a_thread("tweet_entry_changes", title=title, results=results)


def tweet_release_notes_available(stored_data, releases_info):
    """
    🗒 RELEASE NOTES AVAILABLE 🗒

    💻 macOS Monterey 12.0.1 - 40 bugs fixed
    💻 macOS Big Sur 11.6.1 - 24 bugs fixed
    💻 Security Update 2021-007 Catalina - 21 bugs fixed
    ⌚ watchOS 8.1 - 16 bugs fixed
    📱 iOS and iPadOS 15.1 - 22 bugs fixed
    """

    release_notes_available = {}

    for key, value in releases_info.items():
        if (
            key not in stored_data["details_available_soon"]
            and value["num_of_bugs"] == "no details yet"
        ):
            stored_data["details_available_soon"].append(key)

        if (
            key in stored_data["details_available_soon"]
            and value["release_notes"] is not None
        ):
            stored_data["details_available_soon"].remove(key)
            release_notes_available[key] = value

    if release_notes_available == {}:
        return

    title = ":spiral_notepad: RELEASE NOTES AVAILABLE :spiral_notepad:\n\n"
    results = []

    for key, value in release_notes_available.items():
        results.append(f"{value['emoji']} {key} - {value['num_of_bugs']}\n")

    tweet_or_make_a_thread("tweet_release_notes_available", title=title, results=results)

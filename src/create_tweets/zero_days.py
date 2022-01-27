import re

from twitter import tweet_or_make_a_thread


def make_first_tweet(unique_zerodays, all_zerodays):
    length_new = len(unique_zerodays["new"])
    length_old = len(unique_zerodays["old"])

    if length_new > 0:
        text_new = ", ".join(unique_zerodays["new"])
    if length_old > 0:
        text_old = ", ".join(unique_zerodays["old"])

    zero_day_module = all_zerodays[list(all_zerodays.keys())[0]]

    if length_new == 1 and length_old == 0:
        return f"Today, Apple pushed updates for one new zero-day ({text_new}) in {zero_day_module} that was already used to attack users."

    if length_new == 0 and length_old == 1:
        return f"Today, Apple pushed additional updates for {text_old} zero-day in {zero_day_module} that was already used to attack users."

    if length_new == 1 and length_old == 1:
        return f"Today, Apple pushed updates for one new zero-day ({text_new}) in {zero_day_module} that was already used to attack users and additional updates for {text_old} zero-day in {zero_day_module}."

    if length_new > 1 and length_old == 0:
        return f"Today, Apple pushed updates for {length_new} new zero-days that had already been used to attack users."

    if length_new == 0 and length_old > 1:
        return f"Today, Apple pushed additional updates for {length_old} zero-days that had already been used to attack users."

    if length_new > 1 and length_old > 1:
        return f"Today, Apple pushed updates for {length_new} new zero-days that had already been used to attack users and additional updates for {length_new} zero-days."


def tweet_zerodays(releases_info, stored_data):
    """
    -----------------------------
    📣 EMERGENCY UPDATE 📣

    Today, Apple pushed updates for one new zero-day (CVE-2021-30807) in IOMobileFrameBuffer that was already used to attack users.
    -----------------------------

    -----------------------------
    ⚠️ PATCHED TODAY:

    1 zero-day fixed in iOS and iPadOS 14.7.1
    1 zero-day fixed in macOS Big Sur 11.5.1
    -----------------------------
    """

    for key, value in list(releases_info.items()):
        if (
            key in stored_data["tweeted_today"]["zero_days"].keys()
            and value["num_of_zerodays"] == stored_data["tweeted_today"]["zero_days"][key]
        ):
            del releases_info[key]
        else:
            stored_data["tweeted_today"]["zero_days"][key] = value["num_of_zerodays"]

    if not releases_info:
        return

    second_tweet = ":bug: ZERO-DAY DETAILS:\n\n"
    third_tweet = ":warning: PATCHED TODAY:\n\n"
    fourth_tweet = ""
    all_zerodays = {}

    for key, value in releases_info.items():
        if value["num_of_zerodays"]:
            if len(re.findall("fixed in", third_tweet)) <= 4:
                third_tweet += f"{value['num_of_zerodays']} in {key}\n"
            else:
                fourth_tweet += f"{value['num_of_zerodays']} in {key}\n"

            all_zerodays.update(value["list_of_zerodays"])

    unique_zerodays = {"old": {}, "new": {}}
    for key, value in all_zerodays.items():
        if len(stored_data["zero_days"]) > 10:
            # if there are more than 10 zero days in a file, remove the last 5
            del stored_data["zero_days"][:-5]

        if key in stored_data["zero_days"]:
            # if zero day is already in the file, add it to "old"
            unique_zerodays["old"][key] = value
        else:
            # if zero day is not in the file, add it and add it to "new"
            unique_zerodays["new"][key] = value
            stored_data["zero_days"].append(key)

        second_tweet += f"- {key} in {value}\n"

    if len(re.findall("fixed in", third_tweet)) == 1:
        first_tweet = ":mega: EMERGENCY UPDATE :mega:\n\n"
    else:
        first_tweet = ":mega: EMERGENCY UPDATES :mega:\n\n"

    first_tweet += make_first_tweet(unique_zerodays, all_zerodays)

    if len(all_zerodays) == 1:
        # if there is only one zero day, do not print a separate tweet for zero days
        second_tweet = third_tweet
        third_tweet = fourth_tweet

    tweet_or_make_a_thread(
        first_tweet=first_tweet,
        second_tweet=second_tweet,
        third_tweet=third_tweet,
        fourth_tweet=fourth_tweet
    )

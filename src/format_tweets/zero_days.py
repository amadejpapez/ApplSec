def format_first_tweet(unique_zero_days, all_zero_days):
    """Return text for the start of the zero day tweet."""

    length_new = len(unique_zero_days["new"])
    length_old = len(unique_zero_days["old"])

    if length_new > 0:
        text_new = ", ".join(unique_zero_days["new"])
    if length_old > 0:
        text_old = ", ".join(unique_zero_days["old"])

    zero_day_module = all_zero_days[list(all_zero_days.keys())[0]]

    if length_new == 1 and length_old == 0:
        return f"Apple pushed updates for a new {zero_day_module} zero-day ({text_new}) that may have been actively exploited."

    if length_new == 0 and length_old == 1:
        return f"Apple pushed additional updates for {zero_day_module} zero-day ({text_old}) that may have been actively exploited."

    if length_new == 1 and length_old == 1:
        return f"Apple pushed updates for a new {zero_day_module} zero-day ({text_new}) that may have been actively exploited and additional updates for {text_old}."

    if length_new > 1 and length_old == 0:
        return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited."

    if length_new == 0 and length_old > 1:
        return f"Apple pushed additional updates for {length_old} zero-days that may have been actively exploited."

    if length_new == 1 and length_old > 1:
        return f"Apple pushed updates for {length_new} new zero-day that may have been actively exploited and additional updates for {length_old} zero-days."

    if length_new > 1 and length_old == 1:
        return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited and additional updates for {length_old} zero-day."

    if length_new > 1 and length_old > 1:
        return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited and additional updates for {length_old} zero-days."


def format_zero_days(zero_day_releases_info, stored_data):
    """
    -----
    📣 EMERGENCY UPDATE 📣

    Apple pushed updates for 3 new zero-days that may have been actively exploited.
    -----
    🐛 ZERO-DAY DETAILS:

    - CVE-2021-30869 in XNU
    - CVE-2021-30860 in CoreGraphics
    - CVE-2021-30858 in WebKit
    -----
    ⚠️ PATCHES:

    1 zero-day in Security Update 2021-006 Catalina
    3 zero-days in iOS 12.5.5
    -----
    """

    tweet_text = [[], [":bug: ZERO-DAY DETAILS:\n\n"], [":warning: PATCHES:\n\n"], []]
    all_zero_days = {}

    for key, value in list(zero_day_releases_info.items()):
        if (
            key in stored_data["tweeted_today"]["zero_days"].keys()
            and value["num_of_zero_days"]
            == stored_data["tweeted_today"]["zero_days"][key]
        ):
            # if release was tweeted with the same number of zero-days
            del zero_day_releases_info[key]
            continue

        stored_data["tweeted_today"]["zero_days"][key] = value["num_of_zero_days"]

        tweet_text[2].append(f"{value['num_of_zero_days']} in {key}\n")
        all_zero_days.update(value["list_of_zero_days"])

    if not zero_day_releases_info:
        return None

    unique_zero_days = {"old": {}, "new": {}}
    for key, value in all_zero_days.items():
        if key in stored_data["zero_days"]:
            # if zero day is in the file, add it to "old"
            unique_zero_days["old"][key] = value
        else:
            # if zero day is not in the file, add it and add it to "new"
            unique_zero_days["new"][key] = value
            stored_data["zero_days"].append(key)

        tweet_text[1].append(f"- {key} in {value}\n")

    if len(tweet_text[2]) == 2:
        tweet_text[0].append(":mega: EMERGENCY UPDATE :mega:\n\n")
    else:
        tweet_text[0].append(":mega: EMERGENCY UPDATES :mega:\n\n")

    tweet_text[0].append(format_first_tweet(unique_zero_days, all_zero_days))

    if len(unique_zero_days["new"]) in (0, 1) and len(unique_zero_days["old"]) in (0, 1):
        # if CVEs are already in the first tweet, do not do a separate DETAILS tweet
        tweet_text[1] = tweet_text[2]
        tweet_text[2] = tweet_text[3]

    return list(filter(None, tweet_text))

def format_first_tweet(unique_zero_days: dict) -> str:
    """Return text for the start of the zero day tweet."""

    length_old = len(unique_zero_days["old"])
    length_new = len(unique_zero_days["new"])

    if length_old > 0:
        text_old = ", ".join(unique_zero_days["old"])
        zero_day_module = unique_zero_days["old"][list(unique_zero_days["old"].keys())[0]]

    if length_new > 0:
        text_new = ", ".join(unique_zero_days["new"])
        zero_day_module = unique_zero_days["new"][list(unique_zero_days["new"].keys())[0]]

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

    return f"Apple pushed updates for {length_new} new zero-days that may have been actively exploited and additional updates for {length_old} zero-days."


def format_zero_days(releases_info: list, stored_data: dict) -> list:
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

    for release in list(releases_info):
        if (
            release.get_name() in stored_data["tweeted_today"]["zero_days"].keys()
            and release.get_num_of_zero_days()
            == stored_data["tweeted_today"]["zero_days"][release.get_name()]
        ):
            # if release was tweeted with the same number of zero-days
            releases_info.remove(release)
            continue

        stored_data["tweeted_today"]["zero_days"][release.get_name()] = release.get_num_of_zero_days()

    if not releases_info:
        return []

    tweet_text = [[], [":bug: ZERO-DAY DETAILS:\n\n"], [":warning: PATCHES:\n\n"], []]
    zero_days = {}
    sorted_zero_days: dict = {"old": {}, "new": {}}

    for release in releases_info:
        tweet_text[2].append(f"{release.get_format_num_of_zero_days()} in {release.get_name()}\n")
        zero_days.update(release.get_zero_days())

    for key, value in zero_days.items():
        if key in stored_data["zero_days"]:
            # if zero day is in the file, add it to "old"
            sorted_zero_days["old"][key] = value
        else:
            # if zero day is not in the file, add it to file and "new"
            sorted_zero_days["new"][key] = value
            stored_data["zero_days"].append(key)

        tweet_text[1].append(f"- {key} in {value}\n")

    if len(tweet_text[2]) == 2:
        tweet_text[0].append(":mega: EMERGENCY UPDATE :mega:\n\n")
    else:
        tweet_text[0].append(":mega: EMERGENCY UPDATES :mega:\n\n")

    tweet_text[0].append(format_first_tweet(sorted_zero_days))

    if len(sorted_zero_days["new"]) in (0, 1) and len(sorted_zero_days["old"]) in (0, 1):
        # if CVEs are already in the first tweet, do not do a separate DETAILS tweet
        tweet_text[1] = tweet_text[2]
        tweet_text[2] = tweet_text[3]

    return list(filter(None, tweet_text))

import re

import requests

import format_tweet
import gather_info
import get_date
import json_file
from Release import Release
from twitter import tweet

MAIN_PAGE_HTML = (
    requests.get("https://support.apple.com/en-us/HT201222")
    .text.replace("\n", "")
    .replace("&nbsp;", " ")
)
all_releases = re.findall(r"(?<=<tr>).*?(?=<\/tr>)", MAIN_PAGE_HTML)[1:]

for i, _ in enumerate(all_releases):
    all_releases[i] = re.findall(r"(?<=<td)(?:[^>]*>)(.*?)(?=<\/td>)", all_releases[i])

releases = all_releases[:20]
releases_info = []

for row in releases:
    releases.append(Release(row))

stored_data = json_file.read()

date_format_one = get_date.format_one()

latest_versions = gather_info.latest_versions(releases)


new_releases_info = []
ios_release_info = []
sec_content_available_info = []

for release in releases_info:
    if release.get_release_date() == date_format_one:
        new_releases_info.append(release)

        # if the latest iOS series got a new release
        if (
            "iOS" in release.get_name()
            and str(latest_versions["iOS"][0]) in release.get_name()
            and release.get_security_content_link() != ""
            and release.get_num_of_bugs() != len(release.get_zero_days())
        ):
            ios_release_info.append(release)

    # if any releases that said "soon" got security content available
    if (
        release.get_name() in stored_data["details_available_soon"]
        and release.get_security_content_link() != ""
    ):
        sec_content_available_info.append(release)

    # or if any new releases say "no details yet"
    if release.get_format_num_of_bugs() == "no details yet":
        sec_content_available_info.append(release)


if ios_release_info:
    tweet(format_tweet.top_ios_modules(ios_release_info, stored_data))


# if there were any zero-days fixed
check_zero_days_info = new_releases_info + sec_content_available_info
zero_day_releases_info = []

for release in check_zero_days_info:
    if release.get_num_of_zero_days() > 0:
        zero_day_releases_info.append(release)

if zero_day_releases_info:
    tweet(format_tweet.zero_days(list(zero_day_releases_info), stored_data))


# on midnight check for security content changes made on the previous day
if get_date.is_midnight():
    all_releases_info = releases_info

    for row in all_releases[20:]:
        all_releases_info.append(Release(row))

    changed_releases_info = []
    for release in all_releases_info:
        if release.get_num_entries_added() > 0 or release.get_num_entries_updated() > 0:
            changed_releases_info.append(release)

    if changed_releases_info:
        tweet(format_tweet.entry_changes(changed_releases_info))

if sec_content_available_info:
    tweet(
        format_tweet.security_content_available(
            list(sec_content_available_info), stored_data
        )
    )

# new updates should be tweeted last, after all of the other tweets
if new_releases_info:
    tweet(format_tweet.new_updates(list(new_releases_info), stored_data))


# DISABLED AS NOT TESTED ENOUGH

# if there was a new major release
#for key, value in latest_versions.items():
#    for release in new_releases_info:
#        if release.get_name() in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
#            tweet(format_tweet.yearly_report(all_releases, key, value[0], stored_data))
#
#        elif key == "macOS":
#            if release.get_name() in (
#                f"{key} {value[1]} {value[0]}",
#                f"{key} {value[1]} {value[0]}.0",
#            ):
#                tweet(
#                    format_tweet.yearly_report(all_releases, key, value[0], stored_data)
#                )

json_file.save(stored_data)

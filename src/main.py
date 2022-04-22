import datetime
import re

import requests

import format_tweet
from gather_info import determine_latest_versions, get_info
from save_data import read_file, save_file
from twitter import tweet

MAIN_PAGE = requests.get("https://support.apple.com/en-us/HT201222").text.replace("\n", "").replace("&nbsp;", " ")
all_releases = re.findall(r"(?<=<tr>).*?(?=<\/tr>)", MAIN_PAGE)[1:]

for i, _ in enumerate(all_releases):
    all_releases[i] = re.findall(r"(?<=<td>).*?(?=<\/td>)", all_releases[i])

releases = all_releases[:20]
releases_info = get_info(releases)

stored_data, midnight = read_file()

if midnight:
    # on midnight do checks with the previous date to not miss any
    # changes made between 11pm and 12pm
    check_date = datetime.date.today() - datetime.timedelta(1)
else:
    check_date = datetime.date.today()

date_format_one = f"{check_date.day:02d} {check_date.strftime('%b')} {check_date.year}"
# Format: 08 Jan 2022

latest_versions = determine_latest_versions(releases)


new_releases_info = []
ios_releases_info = []
notes_releases_info = []

for release in releases_info:
    if release.get_release_date() == date_format_one:
        new_releases_info.append(release)

    # if the latest iOS series got a new release
    if (
        "iOS" in release.get_name()
        and str(latest_versions["iOS"][0]) in release.get_name()
        and release.get_release_notes_link() is not None
        and release.get_num_of_bugs() != len(release.get_zero_days())
    ):
        ios_releases_info.append(release)

    # if any releases that said "soon" got releases notes
    if (
        release.get_name() in stored_data["details_available_soon"]
        and release.get_release_notes_link() is not None
    ):
        notes_releases_info.append(release)

    # or if any new releases say "no details yet"
    if release.get_format_num_of_bugs() == "no details yet":
        notes_releases_info.append(release)


if ios_releases_info:
    tweet(format_tweet.top_ios_modules(ios_releases_info, stored_data))

if notes_releases_info:
    tweet(format_tweet.release_notes_available(list(notes_releases_info), stored_data))


# if there were any zero-days fixed
check_zero_days_info = new_releases_info + notes_releases_info
zero_day_releases_info = []

for release in check_zero_days_info:
    if release.get_num_of_zero_days() > 0:
        zero_day_releases_info.append(release)

if zero_day_releases_info:
    tweet(format_tweet.zero_days(list(zero_day_releases_info), stored_data))


# on midnight check for release note changes made on the previous day
if midnight:
    check_changes_info = releases_info + get_info(all_releases[20:])

    changes_releases_info = []
    for release in check_changes_info:
        if release.get_num_entries_added() > 0 or release.get_num_entries_updated() > 0:
            changes_releases_info.append(release)

    if changes_releases_info:
        tweet(format_tweet.entry_changes(changes_releases_info))


# new updates should be tweeted last, after all of the other tweets
if new_releases_info:
    tweet(format_tweet.new_updates(list(new_releases_info), stored_data))


# if there was a new major release
for key, value in latest_versions.items():
    for release in new_releases_info:
        if release.get_name() in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
            tweet(format_tweet.yearly_report(all_releases, key, value[0], stored_data))

        elif key == "macOS":
            if release.get_name() in (
                f"{key} {value[1]} {value[0]}",
                f"{key} {value[1]} {value[0]}.0",
            ):
                tweet(format_tweet.yearly_report(all_releases, key, value[0], stored_data))

save_file(stored_data, midnight)
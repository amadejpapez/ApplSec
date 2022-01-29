import re
from datetime import date

import requests

from create_tweets.new_updates import tweet_ios_modules, tweet_new_updates
from create_tweets.release_notes_changes import tweet_entry_changes, tweet_release_notes_available
from create_tweets.yearly_report import tweet_yearly_report
from create_tweets.zero_days import tweet_zerodays
from gather_info import get_info
from save_data import read_file, save_file
from twitter import tweet_or_make_a_thread


def determine_latest_versions(releases):
    versions = {"iOS": [0], "tvOS": [0], "watchOS": [0], "macOS": [0, ""]}

    for key, value in versions.items():
        version = re.findall(rf"(?i){key}\s(?:[a-z\s]+)?([0-9]+)", str(releases))

        version = list(map(int, version))
        version.sort(reverse=True)

        value[0] = int(version[0])

    versions["macOS"][1] = re.findall(
        rf"(?i)macOS\s([a-z\s]+){versions['macOS'][0]}", str(releases)
    )[0].rstrip()

    versions["iOS and iPadOS"] = versions.pop("iOS")

    return versions


stored_data = read_file()

main_page = requests.get("https://support.apple.com/en-us/HT201222").text
all_releases = re.findall(r"<tr>(.*?)<\/tr>", main_page.replace("\n", ""))[1:]

for i, _ in enumerate(all_releases):
    all_releases[i] = re.findall(r"<td>(.*?)<\/td>", all_releases[i])

# var releases is storing only the last hundred releases
releases = all_releases[:100]
releases_info = get_info(releases)


# get all new releases
date_format_one = (
    f"{date.today().day:02d} {date.today().strftime('%b')} {date.today().year}"
)
# Format: 08 Jan 2022

new_releases_info = {}
for key, value in releases_info.items():
    if value["release_date"] == date_format_one:
        new_releases_info[key] = value


# if the latest iOS series got a new release
latest_versions = determine_latest_versions(releases)
ios_releases_info = {}

for key, value in new_releases_info.items():
    if (
        "iOS" in key
        and str(latest_versions["iOS and iPadOS"][0]) in key
        and value["num_of_bugs"] != "no details yet"
        and value["release_notes"] is not None
        and int(re.findall(r"\d+", value["num_of_bugs"])[0])
        != len(value["list_of_zerodays"])
    ):
        ios_releases_info[key] = value

if ios_releases_info:
    tweet_ios_modules(ios_releases_info, stored_data)
    save_file(stored_data)


# if any releases that said "soon" got releases notes
if (
    stored_data["details_available_soon"] != []
    or str(releases_info) != "no details yet"
):
    tweet_release_notes_available(dict(releases_info), stored_data)
    save_file(stored_data)


# if there were any zero-days fixed
zeroday_releases_info = {}

for key, value in new_releases_info.items():
    if value["num_of_zerodays"]:
        zeroday_releases_info[key] = value

if len(zeroday_releases_info) > 0:
    tweet_zerodays(dict(zeroday_releases_info), stored_data)
    save_file(stored_data)


# if there were any changes in the release notes
changes_releases_info = {}

for key, value in releases_info.items():
    if value["entries_added"] or value["entries_updated"]:
        changes_releases_info[key] = value

if len(changes_releases_info) > 0:
    tweet_entry_changes(changes_releases_info, stored_data)
    save_file(stored_data)


# if new updates were released
# should be tweeted the last, after all of the above
if new_releases_info:
    tweet_new_updates(dict(new_releases_info), stored_data)
    save_file(stored_data)


# if there was a new major release
for key, value in latest_versions.items():
    for key2, _ in new_releases_info.items():
        if key2 in (
            f"{key} {value[0]}",
            f"{key} {value[0]}.0"
        ):
            tweet_yearly_report(all_releases, key, value[0], stored_data)

        elif key == "macOS":
            if key2 in (
                f"{key} {value[1]} {value[0]}",
                f"{key} {value[1]} {value[0]}.0"
            ):
                tweet_yearly_report(all_releases, key, value[0], stored_data)

save_file(stored_data)

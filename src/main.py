import re
from datetime import date

import requests
from create_tweets.new_updates import tweet_ios_modules, tweet_new_updates
from create_tweets.release_notes_changes import tweet_entry_changes, tweet_release_notes_available
from create_tweets.web_server_fixes import tweet_webserver_fixes
from create_tweets.yearly_report import tweet_yearly_report
from create_tweets.zero_days import tweet_zerodays
from get_data import get_data
from save_data import read_file, save_file


def determine_latest_versions(releases):
    versions = {"iOS": 0, "tvOS": 0, "watchOS": 0, "macOS": 0}

    for key, _ in versions.items():
        version = re.findall(rf"(?i){key}\s(?:[a-z\s]+)?([0-9]+)", str(releases))

        version = list(map(int, version))
        version.sort(reverse=True)
        versions[key] = int(version[0])

    return versions


stored_data = read_file()

main_page = requests.get("https://support.apple.com/en-us/HT201222").text
all_releases = re.findall(r"(?<=<tr>)(?:.|\n)*?(?=<\/tr>)", main_page)
# var releases is storing only the previous fifty releases
releases = all_releases[1:50]

date_format_one = f"{date.today().day:02d} {date.today().strftime('%b')} {date.today().year}"
# 08 Jan 2022

new_releases = []
for i, _ in enumerate(releases):
    releases[i] = releases[i].rstrip().split("\n")

    if f"<td>{date_format_one}</td>" in releases[i]:
        new_releases.append(releases[i])

new_releases_info = get_data(new_releases)

if new_releases != []:
    tweet_new_updates(new_releases_info, stored_data)

latest_versions = determine_latest_versions(releases)

# check if the latest iOS series got a new release; tweetiOSParts()
ios_info = {}
for key, value in new_releases_info.items():
    if (
        "iOS" in key and str(latest_versions["iOS"]) in key
        and value["num_of_bugs"] != "no details yet"
        and value["release_notes"] != "None"
        and int(re.findall(r"\d+", value["num_of_bugs"])[0]) != len(value["list_of_zerodays"])
    ):
        ios_info[key] = value

if ios_info != {}:
    tweet_ios_modules(ios_info, stored_data)


# if any releases got releases notes, run tweetReleaseNotesAvailable()
releases_info = get_data(releases)

if (
    stored_data["details_available_soon"] != []
    or str(releases_info) != "no details yet"
):
    tweet_release_notes_available(stored_data, releases_info)


# if there was a zero-day fixed, run tweetZeroDays()
zeroday_releases_info = {}

for key, value in new_releases_info.items():
    if value["num_of_zerodays"]:
        zeroday_releases_info[key] = value

if len(zeroday_releases_info) > 0:
    tweet_zerodays(zeroday_releases_info, stored_data)


# if there are any changes to the last 20 release notes, run tweetEntryChanges()
changes_releases_info = {}

for key, value in releases_info.items():
    if value["entries_added"] or value["entries_updated"]:
        changes_releases_info[key] = value

if len(changes_releases_info) > 0:
    tweet_entry_changes(changes_releases_info, stored_data)


# if there was a new major release, run tweetYearlyReport()
for key, value in latest_versions.items():
    if (
        f"{key} {value} " in str(new_releases) or f"{key} {value}.0 " in str(new_releases)
    ) and key not in stored_data["tweeted_today"]["yearly_report"]:
        tweet_yearly_report(releases, key, value)
        stored_data["tweeted_today"]["yearly_report"].append(key)


# if it is first day of the month, run tweetWebServerFixes()
if (
    date.today().day == 1
) and stored_data["tweeted_today"]["webserver_fixes"] is False:
    tweet_webserver_fixes()
    stored_data["tweeted_today"]["webserver_fixes"] = True

save_file(stored_data)

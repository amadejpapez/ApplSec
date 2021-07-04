# tweet if Apple updated or added anything to previous release notes

import re

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetEntryChanges(updatesInfo):
    results = []

    for key, value in updatesInfo.items():
        if value["added"] == None and value["updated"] != None:
            results.append(f'{value["emojis"]} {key} - {value["updated"]}\n')
        elif value["added"] != None and value["updated"] == None:
            results.append(f'{value["emojis"]} {key} - {value["added"]}\n')
        elif value["added"] != None and value["updated"] != None:
            results.append(f'{value["emojis"]} {key} - {value["added"]}, {value["updated"]}\n')

    num = len(re.findall(r":[^:]+:", str(results)))

    if num == 1:
        title = ":arrows_counterclockwise: 1 SECURITY NOTE UPDATED :arrows_counterclockwise:\n\n"
    else:
        title = f":arrows_counterclockwise: {num} SECURITY NOTES UPDATED :arrows_counterclockwise:\n\n"

    tweetOrCreateAThread("tweetEntryChanges", title = title, results = results)
# tweet that there were new updates released today

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetNewUpdates(updatesInfo):
    results = []

    if len(updatesInfo) == 1:
        title = ":collision: NEW UPDATE RELEASED :collision:\n\n"
    else:
        title = ":collision: NEW UPDATES RELEASED :collision:\n\n"

    for key, value in updatesInfo.items():
        results.append(f'{value["emojis"]} {key} - {value["CVEs"]}\n')

    results = list(reversed(results))

    tweetOrCreateAThread("tweetNewUpdates", title=title, results=results)

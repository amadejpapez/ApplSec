import json
import os

import emoji
import tweepy

LOC = os.path.abspath(os.path.join(__file__, "../../../auth_secrets.json"))
with open(LOC, "r", encoding="utf-8") as auth_file:
    KEYS = json.load(auth_file)

API = tweepy.Client(
    consumer_key=KEYS["ApplSec"]["api_key"],
    consumer_secret=KEYS["ApplSec"]["api_key_secret"],
    access_token=KEYS["ApplSec"]["access_token"],
    access_token_secret=KEYS["ApplSec"]["access_token_secret"],
    return_type=dict,
)


def arrange_elements(tweet_text, item):
    """
    Arranges elements so that each element in tweet_text is under 240
    characters. Each tweet_text element presents each tweet in a thread.
    """

    if len(emoji.emojize(tweet_text[-1] + item, use_aliases=True)) < 240:
        tweet_text[-1] += item
    else:
        tweet_text.append(item)


def tweet(results):
    """
    Accepts a Python list of text that has to be tweeted. It
    arranges the list into one tweet or a thread, as appropriate
    and sends it to Twitter.

    ["1", "2", "3", "4", "5", "6", "7"]

    Arrange elements into a tweet as they fit or extend to a thread.

    If input list contains a list, it is sorted separately, so each
    list strictly starts in a new thread tweet.

    ["1", "2", "3", ["4", "5"], ["6", "7"]]

    Arrange first three elements. Add new tweet and arrange the list.
    Add another tweet and arrange the second list.
    """

    if not results:
        return

    tweet_text = [""]
    for group in results:
        if isinstance(group, list):
            tweet_text.append("")

            for element in group:
                arrange_elements(tweet_text, element)

        else:
            arrange_elements(tweet_text, group)

    tweet_text = list(filter(None, tweet_text))
    tweet_id = []

    for text in tweet_text:
        if tweet_text.index(text) == 0:
            # first tweet
            tweet_id.append(
                API.create_tweet(
                    text=emoji.emojize(text, use_aliases=True),
                )
            )
        else:
            # others in the thread
            tweet_id.append(
                API.create_tweet(
                    in_reply_to_tweet_id=tweet_id[-1]["data"]["id"],
                    text=emoji.emojize(text, use_aliases=True),
                )
            )

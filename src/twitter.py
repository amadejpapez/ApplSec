"""
Handles the tweeting part.

API keys are stored in a separate 'auth_secrets.json' file.
It is located outside of the ApplSec project folder.
File structure:
-----------------------------
{
    "ApplSec" : {
        "api_key"               : "x",
        "api_key_secret"        : "x",
        "access_token"          : "x",
        "access_token_secret"   : "x"
    }
}
-----------------------------
"""

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


def tweet_or_make_a_thread(
    title="",
    results="",
    first_tweet="",
    second_tweet="",
    third_tweet="",
    fourth_tweet="",
):
    if results != "":
        max_length = 275

        for result in results:
            if len(first_tweet + result + title) < max_length:
                first_tweet += result

            elif len(second_tweet + result) < max_length:
                second_tweet += result

            elif len(third_tweet + result) < max_length:
                third_tweet += result

    if title != "":
        first_tweet = str(title + first_tweet)

    if first_tweet != "":
        first_tweet = API.create_tweet(
            text=emoji.emojize(first_tweet, use_aliases=True),
        )

    if second_tweet != "":
        second_tweet = API.create_tweet(
            in_reply_to_tweet_id=first_tweet["data"]["id"],
            text=emoji.emojize(second_tweet, use_aliases=True),
        )

    if third_tweet != "":
        third_tweet = API.create_tweet(
            in_reply_to_tweet_id=second_tweet["data"]["id"],
            text=emoji.emojize(third_tweet, use_aliases=True),
        )

    if fourth_tweet != "":
        API.create_tweet(
            in_reply_to_tweet_id=third_tweet["data"]["id"],
            text=emoji.emojize(fourth_tweet, use_aliases=True),
        )

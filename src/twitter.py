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


LOCATION = os.path.abspath(os.path.join(__file__, "../../../auth_secrets.json"))
with open(LOCATION, "r", encoding="utf-8") as myFile:
    keys = json.load(myFile)

API = tweepy.Client(
    consumer_key=keys["ApplSec"]["api_key"],
    consumer_secret=keys["ApplSec"]["api_key_secret"],
    access_token=keys["ApplSec"]["access_token"],
    access_token_secret=keys["ApplSec"]["access_token_secret"],
    return_type=dict,
)


def tweet_or_make_a_thread(what_function, **kwargs):
    """
    Arguments: what_function, title, results, first_tweet, second_tweet, third_tweet, fourth_tweet
    """

    if "results" in kwargs:
        max_length = 250 if what_function == "tweet_new_updates" else 275
        kwargs["first_tweet"] = ""
        kwargs["second_tweet"] = ""
        kwargs["third_tweet"] = ""

        for result in kwargs["results"]:
            if len(kwargs["first_tweet"] + result + kwargs["title"]) < max_length:
                kwargs["first_tweet"] += result

            elif len(kwargs["second_tweet"] + result) < max_length:
                kwargs["second_tweet"] += result

            elif len(kwargs["third_tweet"] + result) < max_length:
                kwargs["third_tweet"] += result

        if what_function == "tweet_new_updates":
            kwargs["first_tweet"] += "https://support.apple.com/en-us/HT201222"

    if "title" in kwargs:
        kwargs["first_tweet"] = str(kwargs["title"] + kwargs["first_tweet"])

    for key, value in list(kwargs.items()):
        if not value:
            del kwargs[key]

    if "first_tweet" in kwargs:
        first_tweet = API.create_tweet(
            text=emoji.emojize(kwargs["first_tweet"], use_aliases=True)
        )

    if "second_tweet" in kwargs:
        second_tweet = API.create_tweet(
            in_reply_to_tweet_id=first_tweet["data"]["id"],
            text=emoji.emojize(kwargs["second_tweet"], use_aliases=True)
        )

    if "third_tweet" in kwargs:
        thirdTweet = API.create_tweet(
            in_reply_to_tweet_id=second_tweet["data"]["id"],
            text=emoji.emojize(kwargs["third_tweet"], use_aliases=True)
        )

    if "fourth_tweet" in kwargs:
        API.create_tweet(
            in_reply_to_tweet_id=thirdTweet["data"]["id"],
            text=emoji.emojize(kwargs["fourth_tweet"], use_aliases=True)
        )

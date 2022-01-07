import json
import os

import emoji
import tweepy

"""
Handle the tweeting part.

tweetOrCreateAThread() accepts the following:
whatFunction, title, results, firstTweet, secondTweet, thirdTweet, fourthTweet

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

location = os.path.abspath(os.path.join(__file__, "../../../auth_secrets.json"))
with open(location, "r", encoding="utf-8") as myFile:
    keys = json.load(myFile)

API = tweepy.Client(
    consumer_key=keys["ApplSec"]["api_key"],
    consumer_secret=keys["ApplSec"]["api_key_secret"],
    access_token=keys["ApplSec"]["access_token"],
    access_token_secret=keys["ApplSec"]["access_token_secret"],
    return_type=dict,
)


def tweetOrCreateAThread(whatFunction, **kwargs):
    if "results" in kwargs:
        maxLength = 250 if whatFunction == "tweetNewUpdates" else 275
        kwargs["firstTweet"] = ""
        kwargs["secondTweet"] = ""
        kwargs["thirdTweet"] = ""

        for result in kwargs["results"]:
            if len(kwargs["firstTweet"] + result + kwargs["title"]) < maxLength:
                kwargs["firstTweet"] += result

            elif len(kwargs["secondTweet"] + result) < maxLength:
                kwargs["secondTweet"] += result

            elif len(kwargs["thirdTweet"] + result) < maxLength:
                kwargs["thirdTweet"] += result

        if whatFunction == "tweetNewUpdates":
            kwargs["firstTweet"] += "https://support.apple.com/en-us/HT201222"

    if "title" in kwargs:
        kwargs["firstTweet"] = str(kwargs["title"] + kwargs["firstTweet"])

    for key, value in list(kwargs.items()):
        if not value:
            del kwargs[key]

    if "firstTweet" in kwargs:
        firstTweet = API.create_tweet(
            text=emoji.emojize(kwargs["firstTweet"], use_aliases=True)
        )

    if "secondTweet" in kwargs:
        secondTweet = API.create_tweet(
            in_reply_to_tweet_id=firstTweet["data"]["id"],
            text=emoji.emojize(kwargs["secondTweet"], use_aliases=True)
        )

    if "thirdTweet" in kwargs:
        thirdTweet = API.create_tweet(
            in_reply_to_tweet_id=secondTweet["data"]["id"],
            text=emoji.emojize(kwargs["thirdTweet"], use_aliases=True)
        )

    if "fourthTweet" in kwargs:
        API.create_tweet(
            in_reply_to_tweet_id=thirdTweet["data"]["id"],
            text=emoji.emojize(kwargs["fourthTweet"], use_aliases=True)
        )

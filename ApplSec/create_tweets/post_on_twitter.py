import re

import emoji
import tweepy
from auth_secrets import keys

api_key = keys["ApplSec"]["api_key"]
api_key_secret = keys["ApplSec"]["api_key_secret"]
access_token = keys["ApplSec"]["access_token"]
access_token_secret = keys["ApplSec"]["access_token_secret"]

auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def tweetOrCreateAThread(whatFunction, **kwargs):
    # ACCEPTS: whatFunction, title, results, firstTweet, secondTweet, thirdTweet
    mainLink = "https://support.apple.com/en-us/HT201222"

    if "results" in kwargs and whatFunction != "tweetZeroDays":
        kwargs["firstTweet"] = ""

        if len(kwargs["results"]) <= 4:
            # if there are less than four releases put them all in one tweet
            for result in kwargs["results"]:
                kwargs["firstTweet"] += result

        if len(kwargs["results"]) > 4:
            # if there are more than four releases create a thread
            kwargs["secondTweet"] = ""

            if whatFunction != "changedResults":
                regex = "-"
            else:
                regex = ":[^:]+:"

            for result in kwargs["results"]:
                if int(len(re.findall(regex, kwargs["firstTweet"])) + 1) <= 4:
                    kwargs["firstTweet"] += result
                else:
                    kwargs["secondTweet"] += result

        # attach a link to new updates released tweet
        if whatFunction == "tweetNewUpdates":
            kwargs["firstTweet"] += f"{mainLink}\n"

    if whatFunction == "tweetZeroDays":
        kwargs["firstTweet"] = f'{kwargs["title"]} :rotating_light:\n\nRELEASED UPDATES:\n'

        if len(kwargs["results"]) >= 2:
            kwargs["secondTweet"] = ""

        for zeroDay in kwargs["results"]:
            if len(re.findall("in", kwargs["firstTweet"])) <= 2:
                kwargs["firstTweet"] += zeroDay
            else:
                kwargs["secondTweet"] += zeroDay

    else:
        if "title" in kwargs:
            kwargs["firstTweet"] = str(kwargs["title"] + kwargs["firstTweet"])

    firstTweet = api.update_status(emoji.emojize(kwargs["firstTweet"], use_aliases=True))

    if "secondTweet" in kwargs:
        secondTweet = api.update_status(emoji.emojize(kwargs["secondTweet"], use_aliases=True), in_reply_to_status_id=firstTweet.id, auto_populate_reply_metadata=True)

    if "thirdTweet" in kwargs:
        api.update_status(emoji.emojize(kwargs["thirdTweet"], use_aliases=True), in_reply_to_status_id=secondTweet.id, auto_populate_reply_metadata=True)

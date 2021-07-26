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
    # ACCEPTS: whatFunction, title, results, firstTweet, secondTweet, thirdTweet, fourthTweet

    if "results" in kwargs:
        maxLength = 250 if whatFunction == "tweetNewUpdates" else 275
        kwargs["firstTweet"] = ""
        kwargs["secondTweet"] = ""
        kwargs["thirdTweet"] = ""

        for result in kwargs["results"]:
            if len(emoji.emojize(kwargs["firstTweet"], use_aliases=True) + result + kwargs["title"]) < maxLength:
                kwargs["firstTweet"] += result

            elif len(emoji.emojize(kwargs["secondTweet"], use_aliases=True) + result) < maxLength:
                kwargs["secondTweet"] += result

            elif len(emoji.emojize(kwargs["thirdTweet"], use_aliases=True) + result) < maxLength:
                kwargs["thirdTweet"] += result

        if whatFunction == "tweetNewUpdates":
            kwargs["firstTweet"] += "https://support.apple.com/en-us/HT201222"

    if "title" in kwargs:
        kwargs["firstTweet"] = str(kwargs["title"] + kwargs["firstTweet"])

    for key, value in list(kwargs.items()):
        if value == "":
            del kwargs[key]


    firstTweet = api.update_status(emoji.emojize(kwargs["firstTweet"], use_aliases=True))

    if "secondTweet" in kwargs:
        secondTweet = api.update_status(emoji.emojize(kwargs["secondTweet"], use_aliases=True), in_reply_to_status_id=firstTweet.id, auto_populate_reply_metadata=True)

    if "thirdTweet" in kwargs:
        thirdTweet = api.update_status(emoji.emojize(kwargs["thirdTweet"], use_aliases=True), in_reply_to_status_id=secondTweet.id, auto_populate_reply_metadata=True)

    if "fourthTweet" in kwargs:
        api.update_status(emoji.emojize(kwargs["fourthTweet"], use_aliases=True), in_reply_to_status_id=thirdTweet.id, auto_populate_reply_metadata=True)

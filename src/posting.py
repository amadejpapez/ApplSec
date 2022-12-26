import json
import os

import emoji
import requests
import tweepy

LOC = os.path.abspath(os.path.join(__file__, "../../../auth_secrets.json"))
with open(LOC, "r", encoding="utf-8") as auth_file:
    KEYS = json.load(auth_file)

TWITTER_API = tweepy.Client(
    consumer_key=KEYS["Twitter_ApplSec"]["api_key"],
    consumer_secret=KEYS["Twitter_ApplSec"]["api_key_secret"],
    access_token=KEYS["Twitter_ApplSec"]["access_token"],
    access_token_secret=KEYS["Twitter_ApplSec"]["access_token_secret"],
    return_type=type(dict),
)

MASTODON_API = {
    "access_token": ("Bearer " + KEYS["Mastodon_ApplSec"]["access_token"]),
}


def arrange_post(results: list, MAX_CHAR: int) -> list:
    """
    ["1", "2", "3", "4", "5", "6", "7"]

    Accepts and returns a list of strings. Each element represents a "section"
    inside of a post.

    Function evaluates each element's length. If element can be fully added
    to the previous one and still respect the character limit, it will do that.

    At return each element represents a post inside of a thread.
    """
    arranged = [""]

    for item in results:
        if len(emoji.emojize(arranged[-1] + item, language="alias")) < MAX_CHAR:
            arranged[-1] += item
        else:
            arranged.append(item)

    return arranged


def tweet(results: list) -> None:
    """Handle posting to Twitter."""
    MAX_CHAR = 250

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = TWITTER_API.create_tweet(
                text=emoji.emojize(text, language="alias"),
            )

            post_ids.append(response["data"]["id"])
        else:
            # other posts in a thread
            response = TWITTER_API.create_tweet(
                in_reply_to_tweet_id=post_ids[-1],
                text=emoji.emojize(text, language="alias"),
            )

            post_ids.append(response["data"]["id"])


def toot(results: list) -> None:
    """Handle posting to Mastodon."""
    MAX_CHAR = 500
    API_URL = "https://mastodon.social/api/v1/statuses"

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                API_URL,
                json={"status": emoji.emojize(text, language="alias")},
                headers={"Authorization": MASTODON_API["access_token"]},
                timeout=60
            )

            post_ids.append(response.json()["id"])
        else:
            # other posts in a thread
            response = requests.post(
                API_URL,
                json={
                    "status": emoji.emojize(text, language="alias"),
                    "in_reply_to_id": post_ids[-1],
                },
                headers={"Authorization": MASTODON_API["access_token"]},
                timeout=60
            )

            post_ids.append(response.json()["id"])


def post(results: list) -> None:
    if not results:
        return

    tweet(results)
    toot(results)

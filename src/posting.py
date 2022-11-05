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
    return_type=dict,
)

MASTODON_API = {
    "access_token": ("Bearer " + KEYS["Mastodon_ApplSec"]["access_token"]),
}


def join_or_split(arranged: list, item: str, MAX_CHAR: int) -> None:
    """
    If character limit is reached, add it as a new thread post. Else join.
    """

    if len(emoji.emojize(arranged[-1] + item, language="alias")) < MAX_CHAR:
        arranged[-1] += item
    else:
        arranged.append(item)


def arrange_post(results: list, MAX_CHAR: int) -> list:
    """
    ["1", "2", "3", "4", "5", "6", "7"]

    This is how the passed in post and returned post look like. This is one
    thread and each element represents a post inside of it.

    Passed in list is not yet correctly sorted as it does not respect the
    character limits per post. That is this function's job to take care of.

    Each element gets evaluated and if it exceeds the character limit, it
    will be split into more posts. If it has less, it will be joined together
    with previous text, if possible.

    ["1", "2", "3", ["4", "5"], ["6", "7"]]

    To prevent joining, you can already pass in a list instead of a string. The
    list element will then strictly start in a new post inside of a thread and
    will not be joined with the text before.
    """

    arranged = [""]

    for item in results:
        if isinstance(item, list):
            arranged.append("")

            for elem in item:
                join_or_split(arranged, elem, MAX_CHAR)

        else:
            join_or_split(arranged, item, MAX_CHAR)

    arranged = list(filter(None, arranged))

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

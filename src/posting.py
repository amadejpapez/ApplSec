import os

import emoji
import requests
import tweepy

TWITTER_API = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_API_KEY"),
    consumer_secret=os.environ.get("TWITTER_API_KEY_SECRET"),
    access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
    return_type=type(dict),
)

MASTODON_KEY = "Bearer " + os.environ.get("MASTODON_ACCESS_TOKEN", "")


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

            post_ids.append(getattr(response, "data")["id"])
        else:
            # other posts in a thread
            response = TWITTER_API.create_tweet(
                in_reply_to_tweet_id=post_ids[-1],
                text=emoji.emojize(text, language="alias"),
            )

            post_ids.append(getattr(response, "data")["id"])


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
                headers={"Authorization": MASTODON_KEY},
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
                headers={"Authorization": MASTODON_KEY},
                timeout=60
            )

            post_ids.append(response.json()["id"])


def post(results: list) -> None:
    if not results:
        return

    try:
        tweet(results)
    except Exception as e:
        print("TWITTER FAILED TO POST: " + str(results) + "\n" + str(e) + "\n")

    try:
        toot(results)
    except Exception as e:
        print("MASTODON FAILED TO POST: " + str(results) + "\n" + str(e) + "\n")

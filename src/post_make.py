import os
import sys

import requests
import tweepy

TWITTER_API = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_TEST_API_KEY"),
    consumer_secret=os.environ.get("TWITTER_TEST_API_KEY_SECRET"),
    access_token=os.environ.get("TWITTER_TEST_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("TWITTER_TEST_ACCESS_TOKEN_SECRET"),
    return_type=type(dict),
)

MASTODON_KEY = "Bearer " + os.environ.get("MASTODON_TEST_ACCESS_TOKEN", "")


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
        if len(arranged[-1] + item) < MAX_CHAR:
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
                text=text,
            )

            post_ids.append(getattr(response, "data")["id"])
        else:
            # other posts in a thread
            response = TWITTER_API.create_tweet(
                in_reply_to_tweet_id=post_ids[-1],
                text=text,
            )

            post_ids.append(getattr(response, "data")["id"])


def toot(results: list) -> None:
    """Handle posting to Mastodon."""
    MAX_CHAR = 500
    # API_URL = "https://mastodon.social/api/v1/statuses"
    API_URL = "https://mas.to/api/v1/statuses"

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                API_URL,
                json={"status": text},
                headers={"Authorization": MASTODON_KEY},
                timeout=60,
            )

            post_ids.append(response.json()["id"])
        else:
            # other posts in a thread
            response = requests.post(
                API_URL,
                json={
                    "status": text,
                    "in_reply_to_id": post_ids[-1],
                },
                headers={"Authorization": MASTODON_KEY},
                timeout=60,
            )

            post_ids.append(response.json()["id"])


def post(results: list) -> None:
    if not results:
        return

    try:
        toot(results)
    except Exception as e:
        print("ERROR: Mastodon failed to post\n" + str(results) + "\n" + str(e) + "\n")
        sys.exit(1)

    try:
        tweet(results)
    except Exception as e:
        print("ERROR: Twitter failed to post\n" + str(results) + "\n" + str(e) + "\n")
        sys.exit(1)

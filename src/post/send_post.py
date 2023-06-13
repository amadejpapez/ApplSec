import os
import sys

import requests
import tweepy

from helpers.posted_file import PostedFile

TWITTER_API = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_API_KEY"),
    consumer_secret=os.environ.get("TWITTER_API_KEY_SECRET"),
    access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
    return_type=type(dict),
)

TWITTER_API_TEST = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_API_KEY_TEST"),
    consumer_secret=os.environ.get("TWITTER_API_KEY_SECRET_TEST"),
    access_token=os.environ.get("TWITTER_ACCESS_TOKEN_TEST"),
    access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET_TEST"),
    return_type=type(dict),
)

MASTODON_KEY = "Bearer " + os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_KEY_TEST = "Bearer " + os.environ.get("MASTODON_ACCESS_TOKEN_TEST", "")


def arrange_post(results: list[str], MAX_CHAR: int) -> list[str]:
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


def tweet(results: list[str], API: tweepy.Client) -> None:
    """Handle posting to Twitter."""
    MAX_CHAR = 280

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = API.create_tweet(
                text=text,
            )

            post_ids.append(getattr(response, "data")["id"])
        else:
            # other posts in a thread
            response = API.create_tweet(
                in_reply_to_tweet_id=post_ids[-1],
                text=text,
            )

            post_ids.append(getattr(response, "data")["id"])


def toot(results: list[str], API_KEY: str) -> None:
    """Handle posting to Mastodon."""
    MAX_CHAR = 11_000
    API_URL = "https://infosec.exchange/api/v1/statuses"

    results.append("\n\n#apple #cybersecurity #infosec #security #ios")

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                API_URL,
                json={"status": text},
                headers={"Authorization": API_KEY},
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
                headers={"Authorization": API_KEY},
                timeout=60,
            )

            post_ids.append(response.json()["id"])


def post(results_mastodon: list[str], results_twitter: list[str] = []) -> None:
    if not results_mastodon and not results_twitter:
        return

    # if results_twitter is not submitted, do the same post on Twitter as on Mastodon
    if not results_twitter:
        results_twitter = results_mastodon

    try:
        toot(list(results_mastodon), MASTODON_KEY_TEST)
    except Exception as e:
        print("ERROR: Mastodon failed to post\n" + str(results_mastodon) + "\n" + str(e) + "\n")
        sys.exit(1)

    try:
        tweet(list(results_twitter), TWITTER_API_TEST)
    except Exception as e:
        print("ERROR: Twitter failed to post\n" + str(results_twitter) + "\n" + str(e) + "\n")
        sys.exit(1)

    PostedFile.save()

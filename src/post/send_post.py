import datetime
import os
import re
import sys

import requests

from helpers.posted_file import PostedFile
from requests_oauthlib import OAuth1

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_KEY_SECRET = os.environ.get("TWITTER_API_KEY_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

TWITTER_API_KEY_TEST = os.environ.get("TWITTER_API_KEY_TEST", "")
TWITTER_API_KEY_SECRET_TEST = os.environ.get("TWITTER_API_KEY_SECRET_TEST", "")
TWITTER_ACCESS_TOKEN_TEST = os.environ.get("TWITTER_ACCESS_TOKEN_TEST", "")
TWITTER_ACCESS_TOKEN_SECRET_TEST = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET_TEST", "")

MASTODON_KEY = os.environ.get("MASTODON_ACCESS_TOKEN", "")
MASTODON_KEY_TEST = os.environ.get("MASTODON_ACCESS_TOKEN_TEST", "")

BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD", "")


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


def tweet(results: list[str], use_test_account: bool) -> None:
    """Handle posting to Twitter."""
    MAX_CHAR = 270
    API_URL = "https://api.twitter.com"

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids: list[str] = []

    oauth = None
    if not use_test_account:
        oauth = OAuth1(
            client_key=TWITTER_API_KEY,
            client_secret=TWITTER_API_KEY_SECRET,
            resource_owner_key=TWITTER_ACCESS_TOKEN,
            resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )
    else:
        oauth = OAuth1(
            client_key=TWITTER_API_KEY_TEST,
            client_secret=TWITTER_API_KEY_SECRET_TEST,
            resource_owner_key=TWITTER_ACCESS_TOKEN_TEST,
            resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET_TEST,
        )

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                url=API_URL + "/2/tweets",
                json={
                    "text": text,
                },
                auth=oauth,
            )
        else:
            # other posts in a thread
            response = requests.post(
                url=API_URL + "/2/tweets",
                json={
                    "text": text,
                    "reply": {
                        "in_reply_to_tweet_id": post_ids[-1],
                    }
                },
                auth=oauth,
            )

        if response.status_code != 201:
            raise Exception(f"Received status is {response.status_code}\nError:{response.text}")

        post_ids.append(response.json()["data"]["id"])


def toot(results: list[str], use_test_account: bool) -> None:
    """Handle posting to Mastodon."""
    MAX_CHAR = 11_000
    API_URL = "https://infosec.exchange/api"

    results.append("\n\n#apple #cybersecurity #infosec #security #ios")

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids: list[str] = []

    api_key = MASTODON_KEY_TEST if use_test_account else MASTODON_KEY

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                url=API_URL + "/v1/statuses",
                json={"status": text},
                headers={"Authorization": "Bearer " + api_key},
                timeout=60,
            )
        else:
            # other posts in a thread
            response = requests.post(
                url=API_URL + "/v1/statuses",
                json={
                    "status": text,
                    "in_reply_to_id": post_ids[-1],
                },
                headers={"Authorization": "Bearer " + api_key},
                timeout=60,
            )

        if response.status_code != 200:
            raise Exception(f"Received status is {response.status_code}\nError:{response.text}")

        post_ids.append(response.json()["id"])


def postBluesky(results: list[str], use_test_account: bool) -> None:
    """Handle posting to Bluesky."""
    MAX_CHAR = 300
    API_URL = "https://bsky.social/"

    if use_test_account:
        return

    loginResponse = requests.post(
        url=API_URL + "xrpc/com.atproto.server.createSession",
        json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_PASSWORD},
        timeout=60,
    )

    if loginResponse.status_code != 200:
        raise Exception(f"Failed to login. Received status is {loginResponse.status_code}\nError:{loginResponse.text}")

    access_token = loginResponse.json()["accessJwt"]

    results.append("\n\n#apple #infosec")

    posts_list = arrange_post(results, MAX_CHAR)

    post_ids: list[dict] = []

    for text in posts_list:
        if posts_list.index(text) == 0:
            # individual post or start of a thread
            response = requests.post(
                url=API_URL + "xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": "Bearer " + access_token},
                json={
                    "repo": BLUESKY_HANDLE,
                    "collection": "app.bsky.feed.post",
                    "record": {
                        "text": text,
                        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "facets": getBlueskyFacets(text)
                    }},
                timeout=60,
            )
        else:
            # other posts in a thread
            response = requests.post(
                url=API_URL + "xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": "Bearer " + access_token},
                json={
                    "repo": BLUESKY_HANDLE,
                    "collection": "app.bsky.feed.post",
                    "record": {
                        "text": text,
                        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "reply": {
                            "root": {
                                "uri": post_ids[0]["uri"],
                                "cid": post_ids[0]["cid"],
                            },
                            "parent": {
                                "uri": post_ids[-1]["uri"],
                                "cid": post_ids[-1]["cid"],
                            },
                        },
                        "facets": getBlueskyFacets(text)
                    }},
                timeout=60,
            )

        if response.status_code != 200:
            raise Exception(f"Received status is {response.status_code}\nError:{response.text}")

        post_ids.append({"cid": response.json()["cid"], "uri": response.json()["uri"]})


def post(results_mastodon: list[str], results_twitter: list[str] = [], use_test_account: bool = False) -> None:
    if not results_mastodon and not results_twitter:
        return

    # if results_twitter is not submitted, do the same post on Twitter as on Mastodon
    if not results_twitter:
        results_twitter = results_mastodon

    try:
        toot(list(results_mastodon), use_test_account)
    except Exception as e:
        print("ERROR: Mastodon failed to post\n" + str(results_mastodon) + "\n" + str(e) + "\n")
        sys.exit(1)

    try:
        tweet(list(results_twitter), use_test_account)
    except Exception as e:
        print("ERROR: Twitter failed to post\n" + str(results_twitter) + "\n" + str(e) + "\n")
        # sys.exit(1)

    try:
        postBluesky(list(results_twitter), use_test_account)
    except Exception as e:
        print("ERROR: Bluesky failed to post\n" + str(results_twitter) + "\n" + str(e) + "\n")
        # sys.exit(1)

    PostedFile.save()


def getBlueskyFacets(text: str) -> list:
    facets = []

    links = re.finditer(r"https?[^\s\n]*", text)

    for link in links:
        facets.append({
            "index": {
                "byteStart": len(text[:link.start()].encode("utf-8")),
                "byteEnd": len(text[:link.end()].encode("utf-8")),
            },
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": link.group(0)
                }
            ]
        })

    hashtags = re.finditer(r"#[^\s\n]*", text)

    for tag in hashtags:
        facets.append({
            "index": {
                "byteStart": len(text[:tag.start()].encode("utf-8")),
                "byteEnd": len(text[:tag.end()].encode("utf-8")),
            },
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#tag",
                    "tag": tag.group(0)[1:]
                }
            ]
        })

    return facets

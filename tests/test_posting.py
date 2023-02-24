import os
import time

import pytest
import requests
import tweepy

TWITTER_API_TEST = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_TEST_API_KEY"),
    consumer_secret=os.environ.get("TWITTER_TEST_API_KEY_SECRET"),
    access_token=os.environ.get("TWITTER_TEST_ACCESS_TOKEN"),
    access_token_secret=os.environ.get("TWITTER_TEST_ACCESS_TOKEN_SECRET"),
    return_type=type(dict),
)

MASTODON_KEY_TEST = "Bearer " + os.environ.get("MASTODON_TEST_ACCESS_TOKEN", "")


@pytest.mark.skip
def test_mastodon_posting():
    API_URL = "https://mas.to/api/v1/statuses"

    response_c = requests.post(
        API_URL,
        json={"status": "THIS IS A TEST"},
        headers={"Authorization": MASTODON_KEY_TEST},
        timeout=60,
    )

    assert response_c.status_code == 200

    time.sleep(10)

    response_d = requests.delete(
        API_URL + "/" + response_c.json()["id"],
        headers={"Authorization": MASTODON_KEY_TEST},
        timeout=60,
    )

    assert response_d.status_code == 200


@pytest.mark.skip
def test_twitter_posting():
    response_c = TWITTER_API_TEST.create_tweet(
        text="THIS IS A TEST",
    )

    time.sleep(10)

    response_d = TWITTER_API_TEST.delete_tweet(
        id=getattr(response_c, "data")["id"],
    )

    assert getattr(response_d, "data")["deleted"] is True

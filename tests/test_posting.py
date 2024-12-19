from helpers_test import read_examples

from post.send_post import arrange_post

examples = read_examples("posts_sec")

def test_post_splitting1() -> None:
    mastodon_post = arrange_post(examples["new_sec_content_post_mastodon"], 11_000)
    assert mastodon_post ==examples["new_sec_content_post_mastodon_split"]

    twitter_post = arrange_post(examples["new_sec_content_post_twitter"], 270)
    assert twitter_post == examples["new_sec_content_post_twitter_split"]

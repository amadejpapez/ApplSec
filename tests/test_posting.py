from helpers_test import read_examples

from post.send_post import arrange_post, remove_links

examples = read_examples("posts_sec")

def test_post_splitting1() -> None:
    mastodon_post = arrange_post(examples["new_sec_content_post_mastodon"], 11_000)
    assert mastodon_post ==examples["new_sec_content_post_mastodon_split"]

    twitter_post = arrange_post(examples["new_sec_content_post_twitter"], 270)
    assert twitter_post == examples["new_sec_content_post_twitter_split"]


def test_remove_links() -> None:
    """Verify links are removed from posts for Twitter."""
    assert remove_links(examples["ios_modules_post"]) == examples["ios_modules_post"][:-1]
    assert remove_links(examples["new_sec_content_post_twitter"]) == examples["new_sec_content_post_twitter"][:-1]

    removed = remove_links(examples["new_sec_content_post_mastodon"])
    assert removed[:3] == [
        "🐛 NEW SECURITY CONTENT 🐛\n\n",
        "💻 macOS Ventura 13.6.8 - 46 bugs fixed\n",
        "💻 macOS Monterey 12.7.6 - 42 bugs fixed\n",
    ]
    assert len(removed) == len(examples["new_sec_content_post_mastodon"])
    assert not any("http" in item for item in removed)

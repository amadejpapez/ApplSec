import pytest
from freezegun import freeze_time
from helpers_test import failing_get, read_examples, row_to_lxml

import helpers.run_errors as run_errors
import post.sec_content_entry_changes as sec_content_entry_changes

examples = read_examples("posts_sec")


@freeze_time("2024-07-30")
def test_entry_changes() -> None:
    """Test that both first and Additional Recognition sections are checked."""
    releases = row_to_lxml(examples["entry_changes_table"])
    releases_obj = sec_content_entry_changes.get_changed(releases)

    post = sec_content_entry_changes.format_mastodon(releases_obj)
    assert post == examples["entry_changes_post_mastodon"]
    post = sec_content_entry_changes.format_twitter(releases_obj)
    assert post == examples["entry_changes_post_twitter"]


@freeze_time("2024-07-30")
def test_entry_changes_only_one() -> None:
    releases = row_to_lxml(examples["entry_changes_one_table"])
    releases_obj = sec_content_entry_changes.get_changed(releases)

    post = sec_content_entry_changes.format_mastodon(releases_obj)
    assert post == examples["entry_changes_one_post_mastodon"]
    post = sec_content_entry_changes.format_twitter(releases_obj)
    assert post == examples["entry_changes_one_post_twitter"]


def test_entry_changes_failed_fetch_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that a failed fetch in the entry changes check is skipped and collected as a run error."""
    monkeypatch.setattr("release.session.get", failing_get)
    rows = row_to_lxml(examples["last_one_year_table"][6:8])

    assert sec_content_entry_changes.get_changed(rows) == []
    # skipped, but the run should still fail at the end
    assert len(run_errors.errors) == 2
    run_errors.errors.clear()

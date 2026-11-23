from helpers_test import compare, info_to_release, read_examples, row_to_lxml, row_to_release

import post.sec_content_new as sec_content_new
import post.sec_content_zero_days as sec_content_zero_days
from helpers.posted_file import PostedFile

examples = read_examples("posts_sec")


def test_zero_day_many_new() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()

    new_releases = sec_content_new.get_new(releases_obj)
    compare(new_releases, examples["zero_day_releases_info"])

    new_zero_days = sec_content_zero_days.get_new(new_releases)
    post = sec_content_zero_days.format_releases(new_zero_days)

    assert post == examples["zero_day_releases_many_new_post"]

    assert PostedFile.data == examples["zero_day_releases_posted_data"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content_new.get_new(releases_obj)
    assert new_releases == []


def test_zero_day_many_old() -> None:
    releases_obj = row_to_release(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2024-23225", "CVE-2024-23296"]

    new_zero_days = sec_content_zero_days.get_new(releases_obj)
    post = sec_content_zero_days.format_releases(new_zero_days)

    assert post == examples["zero_day_releases_many_old_post"]


def test_zero_day_one_new_one_old() -> None:
    releases_obj = row_to_release(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2024-23296"]

    new_zero_days = sec_content_zero_days.get_new(releases_obj)
    post = sec_content_zero_days.format_releases(new_zero_days)

    assert post == examples["zero_day_releases_one_new_one_old_post"]


def test_zero_day_one_new() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["posts"]["new_sec_content"] = ["iOS and iPadOS 17.4"]
    PostedFile.data["zero_days"] = ["CVE-2024-23296"]

    new_releases = sec_content_new.get_new(releases_obj)
    new_zero_days = sec_content_zero_days.get_new(new_releases)
    post = sec_content_zero_days.format_releases(new_zero_days)

    assert post == examples["zero_day_releases_one_new_post"]


def test_zero_day_one_old() -> None:
    releases_obj = row_to_lxml(examples["zero_day_releases_table"])

    PostedFile.reset()
    PostedFile.data["posts"]["new_sec_content"] = ["iOS and iPadOS 17.4"]
    PostedFile.data["zero_days"] = ["CVE-2024-23225"]

    new_releases = sec_content_new.get_new(releases_obj)
    new_zero_days = sec_content_zero_days.get_new(new_releases)
    post = sec_content_zero_days.format_releases(new_zero_days)

    assert post == examples["zero_day_releases_one_old_post"]


def test_zero_day_many_new_one_old() -> None:
    releases_obj = info_to_release(examples["zero_day_many_releases_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2023-42916"]

    new_zero_days = sec_content_zero_days.get_new(releases_obj)

    post = sec_content_zero_days.format_releases(new_zero_days)
    assert post == examples["zero_day_releases_many_new_one_old_post"]


def test_zero_day_one_new_many_old() -> None:
    releases_obj = info_to_release(examples["zero_day_many_releases_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2024-23225", "CVE-2021-30860", "CVE-2024-23296"]

    new_zero_days = sec_content_zero_days.get_new(releases_obj)

    post = sec_content_zero_days.format_releases(new_zero_days)
    assert post == examples["zero_day_releases_one_new_many_old_post"]


def test_zero_day_many_new_many_old() -> None:
    releases_obj = info_to_release(examples["zero_day_many_releases_info"])

    PostedFile.reset()
    PostedFile.data["zero_days"] = ["CVE-2024-23225", "CVE-2024-23296"]

    new_zero_days = sec_content_zero_days.get_new(releases_obj)

    post = sec_content_zero_days.format_releases(new_zero_days)
    assert post == examples["zero_day_releases_many_new_many_old_post"]

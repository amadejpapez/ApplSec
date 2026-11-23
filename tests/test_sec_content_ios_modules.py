from helpers_test import compare, info_to_release, read_examples, row_to_lxml, row_to_release

import helpers.get_version_info as get_version_info
import post.sec_content_ios_modules as sec_content_ios_modules
from helpers.posted_file import PostedFile

examples = read_examples("posts_sec")

latest_versions = get_version_info.latest(row_to_lxml(examples["last_one_year_table"][:50]))


def test_ios_modules() -> None:
    releases_obj = row_to_release(examples["ios_modules_table"])
    PostedFile.reset()

    compare(releases_obj, examples["ios_modules_info"])

    new_releases = sec_content_ios_modules.get_new(releases_obj, latest_versions)

    post = sec_content_ios_modules.format_release(new_releases)
    assert post == examples["ios_modules_post"]

    # test again after posting and verify it returns nothing
    new_releases = sec_content_ios_modules.get_new(releases_obj, latest_versions)

    post = sec_content_ios_modules.format_release(new_releases)
    assert post == []


def test_ios_modules_no_other_vulnerabilities() -> None:
    releases_obj = row_to_release(examples["ios_modules_no_other_table"])
    PostedFile.reset()

    new_releases = sec_content_ios_modules.get_new(releases_obj, latest_versions)

    post = sec_content_ios_modules.format_release(new_releases)
    assert post == examples["ios_modules_no_other_post"]


def test_ios_modules_one_other_vulnerability() -> None:
    # uses iTunes release as it was the only one easy to find with bugs in 5 modules
    releases_obj = info_to_release(examples["ios_modules_one_other_info"])
    PostedFile.reset()

    post = sec_content_ios_modules.format_release(releases_obj)
    assert post == examples["ios_modules_one_other_post"]

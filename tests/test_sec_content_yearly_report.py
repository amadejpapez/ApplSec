import pytest
from helpers_test import read_examples, row_to_lxml, row_to_release

import post.sec_content_yearly_report as sec_content_yearly_report
from helpers.posted_file import PostedFile

examples = read_examples("posts_sec")


@pytest.mark.skip(reason="not tested for accuracy enough, needs updated example data")
def test_yearly_report() -> None:
    latest_versions: dict[str, list] = {"iOS and iPadOS": [15], "macOS": [12, "Monterey"], "tvOS": [15], "watchOS": [8]}
    releases_obj = row_to_release(examples["yearly_report_table"])
    PostedFile.reset()

    data = sec_content_yearly_report.get_new(releases_obj, latest_versions)

    assert data == [["iOS and iPadOS", 15], ["macOS", 12], ["tvOS", 15], ["watchOS", 8]]
    data.remove(["iOS and iPadOS", 15])
    data.append(["iOS", 15])

    for item in data:
        post = sec_content_yearly_report.format_report(
            row_to_lxml(examples["last_one_year_table"]),
            str(item[0]),
            int(item[1]),
        )

        assert post[0] == examples["yearly_report_" + str(item[0]) + "_post"][0]

    assert PostedFile.data["posts"]["yearly_report"] == ["iOS and iPadOS", "macOS", "tvOS", "watchOS"]

    # try again, should return empty
    data = sec_content_yearly_report.get_new(releases_obj, latest_versions)
    assert data == []

    # try again with one being be removed from the PostedFile
    PostedFile.data["posts"]["yearly_report"] = ["iOS and iPadOS", "macOS", "tvOS"]
    data = sec_content_yearly_report.get_new(releases_obj, latest_versions)
    assert data == [["watchOS", 8]]

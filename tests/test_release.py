import lxml.html
from helpers_test import read_examples, row_to_release

from release import Release

examples = read_examples("posts_sec")


def test_release_class_parsing() -> None:
    """Verify that parsing does not a fail with a big number of releases."""
    releases = examples["last_one_year_table"]
    releases_obj = row_to_release(releases)

    # check if Release returned the correct number of releases
    assert len(releases) == len(list(releases_obj))

    # check if titles match
    # useful for seeing which ones are missing if the above assert fails
    for i, _ in enumerate(releases):
        assert Release.parse_name([lxml.html.document_fromstring(releases[i][0])]) == releases_obj[i].name


def test_release_name_software_version() -> None:
    """Verify "software version" is shortened to "software"."""
    row = [lxml.html.fragment_fromstring('<td><a href="https://support.apple.com/x">HomeView software version 1.2</a></td>')]
    assert Release.parse_name(row) == "HomeView software 1.2"
    assert Release.parse_emoji("HomeView software 1.2") == "🏠"

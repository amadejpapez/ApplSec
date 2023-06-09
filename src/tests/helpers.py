import json

import lxml.html

from Release import Release


def read_examples(name: str) -> dict:
    with open("src/tests/" + name + ".json", "r", encoding="utf-8") as my_file:
        return json.load(my_file)


def compare(release_obj: list[Release], example: dict):
    for release, (_, expected) in zip(release_obj, example.items()):
        assert release.name == expected["name"]
        assert release.emoji == expected["emoji"], release.name
        assert release.release_date == expected["release_date"], release.name
        assert release.security_content_link == expected["security_content_link"], release.name
        assert release.zero_days == expected["zero_days"], release.name
        assert release.num_of_bugs == expected["num_of_bugs"], release.name
        assert release.num_of_zero_days == expected["num_of_zero_days"], release.name
        assert release.num_entries_added == expected["num_entries_added"], release.name
        assert release.num_entries_updated == expected["num_entries_updated"], release.name


def row_to_lxml(release_rows: list) -> list:
    releases_tmp = []

    for row in release_rows:
        tmp = []
        for x in row:
            tmp.append(lxml.html.document_fromstring(x))

        releases_tmp.append(tmp)

    return releases_tmp


def row_to_release(release_rows: list) -> list:
    releases_obj = []

    for row in row_to_lxml(release_rows):
        releases_obj.append(Release.parse_from_table(row))

    return releases_obj


def info_to_release(release_info: dict) -> list:
    releases_class = []

    for _, value in release_info.items():
        release_notes_link = value["release_notes_link"] if ("release_notes_link" in value) else ""

        releases_class.append(
            Release(
                value["name"],
                value["emoji"],
                release_notes_link,
                value["security_content_link"],
                value["release_date"],
                value["zero_days"],
                value["num_of_bugs"],
                value["num_of_zero_days"],
                value["num_entries_added"],
                value["num_entries_updated"],
            )
        )

    return releases_class

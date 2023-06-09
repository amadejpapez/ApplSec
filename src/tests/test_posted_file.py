import os

import pytest

from helpers.PostedFile import PostedFile

posted_data_test = {
    "zero_days": [
        "CVE-2021-30869"
    ],
    "details_available_soon": [],
    "posts": {
        "new_releases": [
            "iOS 16.6 beta 2 (20G5037d)"
        ],
        "new_sec_content": [
            "Safari 16.3"
        ],
        "ios_modules": [],
        "zero_days": {},
        "yearly_report": []
    }
}

FILE_LOC = "src/posted_data.json"


def test_posted_data_create():
    if os.path.exists(FILE_LOC):
        os.remove(FILE_LOC)

    # verify that it fails because "new_releases" is empty
    with pytest.raises(AssertionError):
        PostedFile.read()

    assert os.path.isfile(FILE_LOC) is True
    assert PostedFile.data == PostedFile.FILE_STRUCTURE


def test_posted_data_invalid_file():
    with open(FILE_LOC, "w", encoding="utf-8") as json_file:
        json_file.write("{")

    with open(FILE_LOC, "r", encoding="utf-8") as json_file:
        assert json_file.read() == "{"

    # verify that it fails because "new_releases" is empty
    with pytest.raises(AssertionError):
        PostedFile.read()

    assert os.path.isfile(FILE_LOC) is True
    assert PostedFile.data == PostedFile.FILE_STRUCTURE


def test_posted_data_save_read():
    test_posted_data_create()

    PostedFile.data = posted_data_test
    PostedFile.save()
    PostedFile.data = {}

    PostedFile.read()

    assert PostedFile.data == posted_data_test

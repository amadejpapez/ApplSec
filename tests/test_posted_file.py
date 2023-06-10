import os

import pytest
from helpers_test import read_examples

from helpers.posted_file import PostedFile

posted_data_test = read_examples("posted_file")["posted_data_test"]

FILE_LOC = "src/posted_data.json"


def test_posted_data_create() -> None:
    if os.path.exists(FILE_LOC):
        os.remove(FILE_LOC)

    # verify that it fails because "new_releases" is empty
    with pytest.raises(AssertionError):
        PostedFile.read()

    assert os.path.isfile(FILE_LOC) is True
    assert PostedFile.data == PostedFile.FILE_STRUCTURE


def test_posted_data_invalid_file() -> None:
    with open(FILE_LOC, "w", encoding="utf-8") as json_file:
        json_file.write("{")

    with open(FILE_LOC, "r", encoding="utf-8") as json_file:
        assert json_file.read() == "{"

    # verify that it fails because "new_releases" is empty
    with pytest.raises(AssertionError):
        PostedFile.read()

    assert os.path.isfile(FILE_LOC) is True
    assert PostedFile.data == PostedFile.FILE_STRUCTURE


def test_posted_data_save_read() -> None:
    test_posted_data_create()

    PostedFile.data = posted_data_test
    PostedFile.save()
    PostedFile.data = {}

    PostedFile.read()

    assert PostedFile.data == posted_data_test

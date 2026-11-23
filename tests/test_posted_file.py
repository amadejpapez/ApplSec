import json
import os

import pytest
from helpers_test import read_examples

from helpers.posted_file import PostedFile

posted_data_test = read_examples("posted_file")["posted_data_test"]


def test_posted_data_create() -> None:
    if os.path.exists(PostedFile._LOC):
        os.remove(PostedFile._LOC)

    # verify that it fails because "new_sec_content" is empty
    with pytest.raises(AssertionError):
        PostedFile.read()

    assert os.path.isfile(PostedFile._LOC) is True
    assert PostedFile.data == PostedFile.FILE_STRUCTURE


def test_posted_data_invalid_file() -> None:
    with open(PostedFile._LOC, "w", encoding="utf-8") as json_file:
        json_file.write("{")

    with open(PostedFile._LOC, "r", encoding="utf-8") as json_file:
        assert json_file.read() == "{"

    # verify that it fails and does not overwrite the invalid file
    with pytest.raises(json.JSONDecodeError):
        PostedFile.read()

    with open(PostedFile._LOC, "r", encoding="utf-8") as json_file:
        assert json_file.read() == "{"


def test_posted_data_save_read() -> None:
    test_posted_data_create()

    PostedFile.data = posted_data_test
    PostedFile.save()
    PostedFile.data = {}

    PostedFile.read()

    assert PostedFile.data == posted_data_test

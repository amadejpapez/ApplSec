"""
Save and read data in src/posted_data.json

File is used to store:
    - what was posted today
    - 10 last zero-day CVEs, for "new" and "additional" patch text
    - releases for which Apple says "no details yet"
"""

from __future__ import annotations

import copy
import json
import os

import helpers.get_date as get_date


class PostedFile:
    _LOC = os.path.abspath(os.path.join(__file__, "../../posted_data.json"))
    FILE_STRUCTURE = {
        "zero_days": [],
        "details_available_soon": [],
        "posts": {
            "new_releases": [],
            "new_sec_content": [],
            "ios_modules": [],
            "zero_days": {},
            "yearly_report": [],
        },
    }
    # data is a class variable, so that it does not have to be saved/read between different modules
    data: dict

    @staticmethod
    def read() -> None:
        try:
            with open(PostedFile._LOC, "r", encoding="utf-8") as json_file:
                PostedFile.data = json.load(json_file)
        except Exception:
            PostedFile.data = copy.deepcopy(PostedFile.FILE_STRUCTURE)
            PostedFile.save()

        assert (
            PostedFile.data["posts"]["new_sec_content"] != []
        ), "ERROR: 'new_sec_content' list inside of posted_data.json is empty. This is used to recognize that releases published before them are new. Add at least last 3 release names there."

        assert (
            PostedFile.data["posts"]["new_releases"] != []
        ), "ERROR: 'new_releases' list inside of posted_data.json is empty. This is used to recognize that releases published before them are new. Add at least last 3 release names there."

    @staticmethod
    def save() -> None:
        with open(PostedFile._LOC, "w", encoding="utf-8") as json_file:
            json.dump(PostedFile._clear_old_data(PostedFile.data), json_file, indent=4)

    @staticmethod
    def reset() -> None:
        PostedFile.data = copy.deepcopy(PostedFile.FILE_STRUCTURE)

    @staticmethod
    def _clear_old_data(new_data: dict) -> dict:
        while len(new_data["posts"]["new_releases"]) > 15:
            new_data["posts"]["new_releases"].pop(0)

        while len(new_data["posts"]["new_sec_content"]) > 15:
            new_data["posts"]["new_sec_content"].pop(0)

        while len(new_data["posts"]["ios_modules"]) > 3:
            new_data["posts"]["ios_modules"].pop(0)

        while len(new_data["zero_days"]) > 10:
            new_data["zero_days"].pop(0)

        if get_date.is_midnight():
            new_data["posts"]["zero_days"] = {}
            new_data["posts"]["yearly_report"] = []

        return new_data

"""
Functions for saving and reading data from src/posted_data.json

File is storing all of the recent posts. It also contains last 10 zero-days,
which is used for saying "new" or "additional" patch. Alongside it stores all of
the releases, for which Apple says "no details yet".
"""

import json
import os

import helpers.get_date as get_date

LOC = os.path.abspath(os.path.join(__file__, "../../posted_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "posts": {
        "new_updates": [],
        "new_sec_content": [],
        "ios_modules": [],
        "zero_days": {},
        "yearly_report": [],
    },
}


def read() -> dict:
    try:
        with open(LOC, "r", encoding="utf-8") as json_file:
            posted_data_json = json.load(json_file)

    except (json.JSONDecodeError, FileNotFoundError):
        save(FILE_STRUCTURE)
        posted_data_json = read()

    assert posted_data_json["posts"]["new_sec_content"] != [], "ERROR: 'new_sec_content' list inside of posted_data.json is empty. This is used to recognize that releases published before them are new. Add at least last 3 release names there."

    return posted_data_json


def clear_old_data(new_data: dict) -> dict:
    while len(new_data["posts"]["new_updates"]) > 15:
        new_data["posts"]["new_updates"].pop(0)

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


def save(new_data: dict) -> None:
    with open(LOC, "w", encoding="utf-8") as json_file:
        json.dump(clear_old_data(new_data), json_file, indent=4)

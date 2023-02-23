"""
Functions for saving and reading data from src/posted_data.json

File is storing all of the posts from today. It also contains last 10 zero-days,
which is used for saying "new" or "additional" patch. Alongside it stores all of
the releases, for which Apple says "no details yet".
"""

import json
import os

import helpers.get_date as get_date

LOC = os.path.abspath(os.path.join(__file__, "../posted_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "posted_today": {
        "new_updates": [],
        "ios_modules": "",
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

    while len(posted_data_json["zero_days"]) > 10:
        del posted_data_json["zero_days"][-1]

    return posted_data_json


def save(new_data: dict) -> None:
    if get_date.is_midnight():
        new_data["posted_today"] = FILE_STRUCTURE["posted_today"]

    with open(LOC, "w", encoding="utf-8") as json_file:
        json.dump(new_data, json_file, indent=4)

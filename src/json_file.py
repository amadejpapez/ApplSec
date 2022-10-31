"""
Save and read data from stored_data.json

File is storing last 10 zero-days, releases that do not have
security content available yet and data that was tweeted today.
"""

import json
import os

import get_date

LOC = os.path.abspath(os.path.join(__file__, "../stored_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "todays_date": str(get_date.current_date()),
    "tweeted_today": {
        "new_updates": [],
        "ios_modules": "",
        "zero_days": {},
        "yearly_report": [],
    },
}


def read() -> dict:
    try:
        with open(LOC, "r", encoding="utf-8") as json_file:
            stored_data = json.load(json_file)

    except (json.JSONDecodeError, FileNotFoundError):
        save(FILE_STRUCTURE)
        stored_data = read()

    while len(stored_data["zero_days"]) > 10:
        del stored_data["zero_days"][-1]

    return stored_data


def save(new_data: dict) -> None:
    if get_date.is_midnight():
        new_data["tweeted_today"] = FILE_STRUCTURE["tweeted_today"]
        new_data["todays_date"] = str(get_date.current_date())

    with open(LOC, "w", encoding="utf-8") as json_file:
        json.dump(new_data, json_file, indent=4)

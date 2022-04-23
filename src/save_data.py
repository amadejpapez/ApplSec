"""
Save and read data from stored_data.json.

File is storing:
- 10 last fixed zero-days
- releases that do not have security content available yet
- data tweeted on the current day to prevent tweeting the same thing twice
"""

import datetime
import json
import os
from typing import Tuple

LOC = os.path.abspath(os.path.join(__file__, "../stored_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "todays_date": str(datetime.date.today()),
    "tweeted_today": {
        "new_updates": [],
        "ios_modules": "",
        "zero_days": {},
        "yearly_report": [],
    },
}


def read_file() -> Tuple[dict, bool]:
    """
    Return contents of stored_data.json and if it is a start
    of a new day.
    """

    try:
        with open(LOC, "r", encoding="utf-8") as stored_file:
            stored_data = json.load(stored_file)

    except (json.JSONDecodeError, FileNotFoundError):
        save_file(FILE_STRUCTURE, False)
        stored_data, _ = read_file()

    if len(stored_data["zero_days"]) > 10:
        # if there are more than 10 zero days in a file, remove the last 3
        del stored_data["zero_days"][:-3]

    if stored_data["todays_date"] != str(datetime.date.today()):
        return stored_data, True

    return stored_data, False


def save_file(modified_data: dict, midnight: bool) -> None:
    """Save data to stored_data.json."""

    if midnight:
        modified_data["tweeted_today"] = FILE_STRUCTURE["tweeted_today"]
        modified_data["todays_date"] = str(datetime.date.today())

    with open(LOC, "w", encoding="utf-8") as stored_file:
        json.dump(modified_data, stored_file, indent=4)

"""
Save and read data from stored_data.json.

File is storing:
  - 10 last fixed zero-days
  - releases that do not have release notes yet
  - data tweeted that day to not tweet things twice
"""

import datetime
import json
import os

LOC = os.path.abspath(os.path.join(__file__, "../stored_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "todays_date": "",
    "tweeted_today": {
        "new_updates": [],
        "ios_modules": "",
        "zero_days": {},
        "yearly_report": [],
    },
}


def read_file():
    """
    Return contents of stored_data.json and if it is a start
    of a new day.
    """

    try:
        with open(LOC, "r", encoding="utf-8") as stored_file:
            stored_data = json.load(stored_file)

    except (json.JSONDecodeError, FileNotFoundError):
        save_file(FILE_STRUCTURE)
        stored_data, _ = read_file()

    new_day = False
    if stored_data["todays_date"] != str(datetime.date.today()):
        stored_data["tweeted_today"] = FILE_STRUCTURE["tweeted_today"]
        stored_data["todays_date"] = str(datetime.date.today())
        new_day = True

    if len(stored_data["zero_days"]) > 10:
        # if there are more than 10 zero days in a file, remove the last 3
        del stored_data["zero_days"][:-3]

    return stored_data, new_day


def save_file(modified_data):
    """Save data to stored_data.json."""

    with open(LOC, "w", encoding="utf-8") as stored_file:
        json.dump(modified_data, stored_file, indent=4)

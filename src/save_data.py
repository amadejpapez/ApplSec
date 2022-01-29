"""
Save and read data from the 'stored_data.json' file.

File is storing:
  - last 10 zero-days
  - releases that do not have release notes yet
  - data tweeted that day to not tweet things twice
"""

import json
import os
from datetime import date

LOC = os.path.abspath(os.path.join(__file__, "../stored_data.json"))

FILE_STRUCTURE = {
    "zero_days": [],
    "details_available_soon": [],
    "today_date": "",
    "tweeted_today": {
        "new_updates": [],
        "ios_parts": "",
        "entry_changes": {},
        "zero_days": {},
        "yearly_report": [],
    },
}


def read_file():
    try:
        with open(LOC, "r", encoding="utf-8") as stored_file:
            stored_data = json.load(stored_file)

    except (json.JSONDecodeError, FileNotFoundError):
        save_file(FILE_STRUCTURE)
        stored_data = read_file()

    if stored_data["today_date"] != str(date.today()):
        stored_data["tweeted_today"] = FILE_STRUCTURE["tweeted_today"]
        stored_data["today_date"] = str(date.today())

    return stored_data


def save_file(modified_data):
    with open(LOC, "w", encoding="utf-8") as stored_file:
        json.dump(modified_data, stored_file, indent=4)

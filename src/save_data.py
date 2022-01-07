import json
import os
from datetime import date

"""
Saves and reads data from the 'stored_data.json' file, so
the bot can use the data next time.

File stores:
- last 10 zero-days, so the bot knows if a zero-day is new
or if it is just an additional update.
- releases that do not have release notes yet
- all of the data tweeted that day to not tweet things twice
"""

LOCATION = os.path.abspath(os.path.join(__file__, "../stored_data.json"))

fileStructure = {
    "zero_days": [],
    "details_available_soon": [],
    "todays_tweets": {
        "date": "",
        "tweetNewUpdates": [],
        "tweetiOSParts": "",
        "tweetEntryChanges": {},
        "tweetZeroDays": {},
        "tweetYearlyReport": [],
        "tweetWebServerFixes": False,
    },
}


def readFile():
    try:
        with open(LOCATION, "r+", encoding="utf-8") as myFile:
            storedDataFile = json.load(myFile)
    except Exception:
        with open(LOCATION, "w+", encoding="utf-8") as myFile2:
            myFile2.seek(0)
            json.dump(fileStructure, myFile2, indent=4)
            myFile2.truncate()
            myFile2.seek(0)
            storedDataFile = json.load(myFile2)

    if storedDataFile["todays_tweets"]["date"] != str(date.today()):
        storedDataFile["todays_tweets"] = {
            "date": str(date.today()),
            "tweetNewUpdates": [],
            "tweetiOSParts": "",
            "tweetEntryChanges": {},
            "tweetZeroDays": {},
            "tweetYearlyReport": [],
            "tweetWebServerFixes": False,
        }

    return storedDataFile


def saveData(storedDataModified):
    with open(LOCATION, "w+", encoding="utf-8") as myFile:
        myFile.seek(0)
        json.dump(storedDataModified, myFile, indent=4)
        myFile.truncate()

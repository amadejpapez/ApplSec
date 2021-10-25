import json
import os
from datetime import date

"""
Saves and reads data from the 'stored_data.json' file, so
the bot can use the data next time.
"""

DIRPATH = os.path.abspath(os.path.join(os.path.dirname(__file__)))

fileStructure = {
    "zero_days": [],
    "details_available_soon": [],
    "todays_tweets": {
        "date": "",
        "tweetNewUpdates": [],
        "tweetiOSParts": "",
        "tweetEntryChanges": {},
        "tweetZeroDays": {},
    },
}


def readFile():
    try:
        with open(f"{DIRPATH}/stored_data.json", "r+", encoding="utf-8") as myFile:
            storedDataFile = json.load(myFile)
    except FileNotFoundError:
        with open(f"{DIRPATH}/stored_data.json", "w+", encoding="utf-8") as myFile2:
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
        }

    return storedDataFile


def saveData(storedDataModified):
    with open(f"{DIRPATH}/stored_data.json", "w+", encoding="utf-8") as myFile:
        myFile.seek(0)
        json.dump(storedDataModified, myFile, indent=4)
        myFile.truncate()

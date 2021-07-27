# tweet which, where and how many zero-day vulnerabilities were fixed

import json
import os
import re

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetZeroDays(updatesInfo):
    allZeroDays = {}
    dirPath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uniqueZeroDays = {"old": {}, "new": {}}
    secondTweet = ":bug: ZERO-DAY DETAILS:\n\n"
    thirdTweet = ":hammer_and_pick: RELEASED TODAY:\n\n"
    fourthTweet = ""

    for key, value in updatesInfo.items():
        if value["zeroDays"]:
            if len(re.findall("fixed in", thirdTweet)) <= 4:
                thirdTweet += f"{value['zeroDays']} fixed in {key}\n"
            else:
                fourthTweet += f"{value['zeroDays']} fixed in {key}\n"

            allZeroDays.update(value["zeroDayCVEs"])

    for zeroDay in allZeroDays:
        with open(f"{dirPath}/stored_data.json", "r+", encoding="utf-8") as myFile:
            try:
                storedDataFile = json.load(myFile)
            except json.decoder.JSONDecodeError:
                myFile.seek(0)
                json.dump(
                    {"zero_days": [], "details_available_soon": [], "todays_releases": {"date": "", "releases": []}}, myFile, indent=4
                )
                myFile.truncate()
                myFile.seek(0)
                storedDataFile = json.load(myFile)

            if len(storedDataFile["zero_days"]) > 10:
                # if there are more than 10 zero days in a file, remove the last 5
                del storedDataFile["zero_days"][:-5]

            if zeroDay in storedDataFile["zero_days"]:
                # if zero day is already in the file, add it to "old"
                uniqueZeroDays["old"][zeroDay] = allZeroDays[zeroDay]
            else:
                # if zero day is not in the file, add it and add it to "new"
                uniqueZeroDays["new"][zeroDay] = allZeroDays[zeroDay]
                storedDataFile["zero_days"].append(zeroDay)

            myFile.seek(0)
            json.dump(storedDataFile, myFile, indent=4)
            myFile.truncate()

        secondTweet += f"- {zeroDay} in {allZeroDays[zeroDay]}\n"

    if len(re.findall("fixed in", thirdTweet)) == 1:
        firstTweet = ":mega: EMERGENCY UPDATE :mega:\n\n"
    else:
        firstTweet = ":mega: EMERGENCY UPDATES :mega:\n\n"

    lengthNew = len(uniqueZeroDays["new"])
    lengthOld = len(uniqueZeroDays["old"])

    if lengthNew > 0:
        textNew = ", ".join(uniqueZeroDays["new"])
    if lengthOld > 0:
        textOld = ", ".join(uniqueZeroDays["old"])

    if lengthNew == 1 and lengthOld == 0:
        firstTweet += f"Today, Apple pushed updates for one new zero-day ({textNew}) in {allZeroDays[list(allZeroDays.keys())[0]]} that was already used to attack users."
    elif lengthNew == 0 and lengthOld == 1:
        firstTweet += f"Today, Apple pushed additional updates for {textOld} zero-day in {allZeroDays[list(allZeroDays.keys())[0]]} that was already used to attack users."
    elif lengthNew == 1 and lengthOld == 1:
        firstTweet += f"Today, Apple pushed updates for one new zero-day ({textNew}) in {allZeroDays[list(allZeroDays.keys())[0]]} that was already used to attack users and additional updates for {textOld} zero-day in {allZeroDays[list(allZeroDays.keys())[0]]}."
    elif lengthNew > 1 and lengthOld == 0:
        firstTweet += f"Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users."
    elif lengthNew == 0 and lengthOld > 1:
        firstTweet += f"Today, Apple pushed additional updates for {lengthOld} zero-days that had already been used to attack users."
    elif lengthNew > 1 and lengthOld > 1:
        firstTweet += f"Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users and additional updates for {lengthNew} zero-days."

    if len(allZeroDays) == 1:
        # if there is only one zero day, do not print a separate tweet for zero days
        secondTweet = thirdTweet
        thirdTweet = fourthTweet

    tweetOrCreateAThread("tweetZeroDays", firstTweet=firstTweet, secondTweet=secondTweet, thirdTweet=thirdTweet, fourthTweet=fourthTweet)

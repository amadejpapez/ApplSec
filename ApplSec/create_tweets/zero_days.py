# tweet which, where and how many zero-day vulnerabilities were fixed

import json
import os

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetZeroDays(updatesInfo):
    results = []
    uniqueZeroDays = {"old": [], "new": []}
    dirPath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))

    for key, value in updatesInfo.items():
        if value["zeroDays"]:
            # if there were any zero-days fixed, add this to the results
            results.append(f'{value["zeroDays"]} fixed in {key}\n')

            with open(f"{dirPath}/stored_data.json", "r+", encoding="utf-8") as myFile:
                try:
                    json.load(myFile)
                except json.decoder.JSONDecodeError:
                    json.dump({"zero_days":[], "details_available_soon":[]}, myFile, indent=4)

                myFile.seek(0)
                zeroDayStoredData = json.load(myFile)

                for zeroDay in value["zeroDayCVEs"]:
                    if zeroDay in zeroDayStoredData["zero_days"] and zeroDay not in uniqueZeroDays["old"]:
                        # if zero-day CVE is already in the file, add it to "old"
                        uniqueZeroDays["old"].append(zeroDay)

                    if zeroDay not in zeroDayStoredData["zero_days"] and zeroDay not in uniqueZeroDays["new"]:
                        # if zero-day CVE is not in the file, add it to the file and to "new"
                        uniqueZeroDays["new"].append(zeroDay)
                        zeroDayStoredData["zero_days"].append(zeroDay)

                myFile.seek(0)
                json.dump(zeroDayStoredData, myFile, indent=4)

    if len(results) == 1:
        title = ":mega: EMERGENCY UPDATE :mega:\n\n"
    else:
        title = ":mega: EMERGENCY UPDATES :mega:\n\n"

    lengthNew = len(uniqueZeroDays["new"])
    lengthOld = len(uniqueZeroDays["old"])

    if lengthNew > 0:
        uniqueZeroDays["new"] = ", ".join(uniqueZeroDays["new"])
    if lengthOld > 0:
        uniqueZeroDays["old"] = ", ".join(uniqueZeroDays["old"])

    if lengthNew == 1 and lengthOld == 0:
        title += f'Today, Apple pushed updates for one new zero-day ({uniqueZeroDays["new"]}) that was already used to attack users.'
    elif lengthNew == 0 and lengthOld == 1:
        title += f'Today, Apple pushed additional updates for one zero-day ({uniqueZeroDays["old"]}) that was already used to attack users.'
    elif lengthNew == 1 and lengthOld == 1:
        title += f'Today, Apple pushed updates for one new zero-day ({uniqueZeroDays["new"]}) that was already used to attack users and additional updates for one zero-day ({uniqueZeroDays["old"]}).'
    elif lengthNew > 1 and lengthOld == 0:
        title += f'Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users - {uniqueZeroDays["new"]}.'
    elif lengthNew == 0 and lengthOld > 1:
        title += f'Today, Apple pushed additional updates for {lengthOld} zero-days that had already been used to attack users - {uniqueZeroDays["old"]}.'
    elif lengthNew > 1 and lengthOld > 1:
        title += f"Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users and additional updates for {lengthNew} zero-days."

    tweetOrCreateAThread("tweetZeroDays", title=title, results=results)

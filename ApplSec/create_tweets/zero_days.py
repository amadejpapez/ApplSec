# tweet which, where and how many zero-day vulnerabilities were fixed

import os

from create_tweets.post_on_twitter import tweetOrCreateAThread


def tweetZeroDays(updatesInfo):
    results = []
    uniqueZeroDays = {"old": [], "new": []}
    dirPath = os.path.dirname(os.path.realpath(__file__))

    for key, value in updatesInfo.items():
        if value["zeroDays"]:
            # if there were any zero-days fixed, add this to the results
            results.append(f'{value["zeroDays"]} fixed in {key}\n')

            for zeroDay in value["zeroDayCVEs"]:
                if not os.path.exists(f"{dirPath}/zeroDays.txt"):
                    with open(f"{dirPath}/zeroDays.txt", "w") as file:
                        file.write("")

                with open(f"{dirPath}/zeroDays.txt", "r+") as file:
                    zeroDayFile = file.read()

                    if zeroDay in zeroDayFile and zeroDay not in uniqueZeroDays["old"]:
                        # if zero-day CVE is already in the file, add it to "old"
                        uniqueZeroDays["old"].append(zeroDay)

                    if zeroDay not in zeroDayFile:
                        # if zero-day CVE is not in the file, add it to the file and to "new"
                        if zeroDay not in uniqueZeroDays["new"]:
                            uniqueZeroDays["new"].append(zeroDay)
                        file.write(f"{zeroDay}\n")

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

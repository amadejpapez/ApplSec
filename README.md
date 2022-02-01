<h1 align="center">ApplSec</h1>
<br>
<p align="center"><b>Twitter bot written in Python 🐍</b></p>
<p align="center"><b>Checking for the latest updates to Apple's ecosystem every hour 🔐</b></p>
<p align="center"><b>Running on <a href="https://twitter.com/applsec">@ApplSec</a> since February 6, 2021</b></p>
<p align="center"><img src="images/ApplSec.png" width=100></p>


## Keeps you up to date with the following info:
* 💥 new software releases,
* 🔒 how many vulnerabilities Apple fixed in each update,
* 💉 five iOS modules that got the most security fixes in the latest update,
* ⚠️ fixes for any new, or previous zero-day vulnerabilities,
* 🔄 if Apple updated or added any new entries to previous release notes,
* and more!

<p align="center"><img src="images/img1_dark.jpg" width=340></p>
<p align="center"><img src="images/img2_dark.jpg" width=340></p>
<p align="center"><img src="images/img3_dark.jpg" width=340></p>
<p align="center"><img src="images/img4_dark.jpg" width=340></p>
<p align="center"><img src="images/img6_dark.jpg" width=340></p>

## 🦾 How does it work?
First, it creates a current day format and searches for it on the [Apple Security Updates](https://support.apple.com/en-us/HT201222) page. If a new update is available, it starts gathering data from its security release notes. The bot counts how many security issues were fixed in each release, checks for zero-days and other needed data. It arranges gathered data into a tweet or into a thread if there is more.

If Apple says "no details yet", the bot will save the release and tweet that info is not available yet. Next time it will check for it and tweet when release note becomes available with data it contains.

The bot is checking for changes every hour. To avoid tweeting the same thing twice, it is saving all of the tweeted info for the current day in a JSON file.

At the start of the day, it also checks if Apple updated any release notes in the previous day. On January 19th 2022 Apple updated 25 security release notes. They added and updated entries all the way back to releases from two years ago.

<br>

For communication with Twitter it is using Python library [Tweepy](https://www.tweepy.org/), and for running the bot a Tasks feature on the [PythonAnywhere](https://www.pythonanywhere.com/) website, where you can set how often you want to run your code.

The bot is often updated as new ideas appear and to keep with changes to Apple's website.

<br>

*Apple, Apple logo, iCloud, watchOS, tvOS and macOS are trademarks of Apple Inc., registered in the U.S. and other countries and regions.*

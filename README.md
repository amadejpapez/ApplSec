# ApplSec
**Twitter bot written in Python that tweets how many vulnerabilities were patched in the new updates to Apple's operating systems.**

**Bot has been running on Twitter account @ApplSec since February 6, 2021.**

### What does the bot do?
Bot checks Apple security update page for any new updates released to their operating systems. If it finds any new it will gather new links to the releases and gather information like the title, so it knows which update it is and it will count how many security vulnerabilities were fixed. If the update has no security updates, bot will also detect it and add it to the list of new updates. Depending on the system that got the update, it will assign an emoji to the title. Bot can also detect if there are zero-days fixed and it will tweet where and how many zero-days were fixed. Each time it will also check last 20 updates if they got any new bug fixes added or updated.

<p align="center"><img src="images/image1.jpg" width=350><p>
<p align="center"><img src="images/image2.jpg" width=350><p>
<p align="center"><img src="images/image3.jpg" width=350><p>
<p align="center"><img src="images/image4.jpg" width=350><p>

### How does it work?
Bot is written in Python and the code is often updated as new ideas appear. It uses a Python library called __Tweepy__. Tweepy is open-source on GitHub and enables communication between Python and Twitter API. You can find more about Tweepy on their [official page](https://www.tweepy.org/) or on their [GitHub repository](https://github.com/tweepy/tweepy).

This Python code is hosted on __PythonAnywhere__, which offers hosting Python code in the cloud. PythonAnywhere has a feature called Tasks, which enables you to upload your Python code and set the time when you want to run it. You can find more about PythonAnywhere on their [official page](https://www.pythonanywhere.com/).

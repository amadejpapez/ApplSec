# ApplSec
**Twitter bot written in Python that tweets how many vulnerabilities were patched in the new updates to Apple's operating systems.**

### What does the bot do?
Bot checks Apple security update page for any new security updates released to their operating systems on the current day. If it finds any it will gather new links to the releases and gather information like the title, so it knows which update it is and it will count how many security vulnerabilities were fixed. It will then combine gathered data and tweet it.

Bot also checks if Apple added any new entries to the old releases. If it detects any new changes it will count the vulnerabilities again and tweet that there are new changes.

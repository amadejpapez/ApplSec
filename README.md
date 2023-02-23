# posted_data.json

This branch is used to store posted_data.json. File contains important data, which is needed by the bot at every run, such as what has already been posted.

Since moving to running the bot in a GitHub Action, I had to find a good way for storing it. Each run retrieves it, moves it into src/ and then it might modify it. This changes then have to be available at the next run. For hourly scheduling I am using cron.

What else do I need? I want to see changes the bot is making to the file. And if I want to change or for it to not post something (I sometimes run the bot locally before the full hour), I can easily modify the file.

Using a special branch might not be the best way, but it should solve my problem. :D

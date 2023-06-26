# Changelog

## [15.1] - 2023-06-26

### Changed

- in zero-day posts, each CVE will now have releases sorted alphabetically

### Fixed

- upgrade security content links from `http` to `https`
- remove `&nbsp;` character from release names

### Code

- more and improved tests

## [15.0] - 2023-06-13

### Added

- Bot now follows [Apple Developer - Releases](https://developer.apple.com/news/releases/) page. This allows for quicker posts about updates, before security contents is published. Posts about new updates should now be posted sooner, contain build numbers and beta software!
- New Security Content and Entry Changes posts now contain, below each release name, a link to their security content. This should make it easier to access the said security content. For now only enabled for Mastodon, as it makes the post too long and then splits it into many tweets with each having around 2 or 3 releases.

### Changed

- New Releases or New Security Content post will now be made first, followed by others. Previously, everything was before (zero-days,...) and then New Security Content was the last post.
- If a set of releases share multiple zero-days, they will be grouped together. Meaning CVE information separated by coma and then listed releases. This avoids same set of releases being repeated by different CVEs.
- "NEW UPDATES RELEASED" posts now contain releases from RSS with build numbers. Previous "NEW UPDATES RELEASED" with "x bugs fixed" have been moved to "NEW SECURITY CONTENT".

### Fixed

- Twitter posts are now up to 280 characters, as previously it was set at max 250

### Code

- more and improved testing
- various other moving around, renames and more

## [14.0] - 2023-04-12

### Added

- catch releases with non-today release date, Apple sometimes adds security content for a release a day or more later
- automatically add hashtags to Mastodon posts

### Changed

- run bot more often at the time when Apple usually releases updates, so it should catch them quicker
- sort releases both by number of bugs and then by name

### Fixed

- do not skip over Additional Recognition section and catch entry changes there, this is a regression and a new test has been added
- strip "(details available soon)" from release names

### Code

- run bot as a GitHub Action cron job, previously it was on PythonAnywhere
- add test-requirements.txt for test dependencies
- use emojis directly, remove emoji package dependency
- store API keys inside of environmental variables, instead of a JSON file
- various other moving around, renames and more

## [13.0] - 2022-12-26

### Added

- bot is now also available on Mastodon

### Changed

- new releases are now sorted by the number of bugs, so release with the most bug fixes is now at the top
- update wording "zero-day may have been actively exploited" to align with Apple's wording
- re-format zero-day tweet to make more clear which zero-days are new, old and what zero-days are in each release
- update multiple tweet wordings
- also sort releases by number of bugs/changes in Security Content Available and Entry Changes

### Fixed

- if all iOS bugs were fixed in top four modules except 1, it would say "and 1 other vulnerabilities fixed"

### Code

- use lxml package for more html parsing, rely less on regex
- make a Release class
- do not request all data of the last 20 releases at every run
- a lot of other code changes and moving around
- better testing
- use type hints
- add CHANGELOG.md
- add Dependabot

## [12.0] - 2022-02-11

### Added

- if there is only one new release, tweet with its release notes link instead of the main page link
- a few small tweet rewording changes, mostly on a zero-day tweet
- remove tweeting of [Apple Web Server](https://support.apple.com/en-us/HT201536) fixes. It stopped working in September 2021 when Apple reformatted the website. Text from every entry saying on which domain the issue was reported got removed. Because no entries were added in two months, I think these tweets are no longer useful.
- On January 19th 2022 Apple updated 25 release notes, all the way back to two years ago, causing the bot to not catch all of them. Checking for release note entry changes is now done once per day, on midnight. It is checking for added/updated entries on the previous day and on a lot more release notes than before.

### Fixed

- Apple sometimes re-releases versions with the same release name but with a different build number (mostly Safari), causing two releases to have the same title. Bot now recognizes this because otherwise it messed with checking.
- if Apple updated a release note entry twice, the bot did not catch the second change
- Because the bot is running hourly and checking for changes with the current date, it did not catch changes made between 11pm and 12am. On midnight it now does checking with the previous date.

### Code

- move to Twitter API v2
- a lot of code refactoring, regex updates and style changes in this release
- add pytest testing and add GitHub Action check for it on each commit push!

## [11.0] - 2021-11-07

### Added

- Bot is now running every hour! This enables it to catch more changes and quicker.
- Before if security content is not available yet, the bot would tweet that in the New Releases. Now when release notes become available a new tweet will be made.
- tweetZeroDay() now tweets which part of the OS had the zero-day

### Changed

- if all of the bugs in the new release are zero-days, do not run tweetiOSParts() as all of the info is now tweetZeroDay() tweet
- rewritten tweeting function, now creating tweets checks if twet is 280 characters long and creates a thread
- save all of the tweeted info into `stored_data.json`, as the bot is running hourly this prevents tweeting same info twice
- lastTwentyReleases has been changed to lastFiftyReleases as the bot did not catch some of the changes Apple made

### Fixed

- tweetZeroDays(): may tweet one zero day twice
- tweetiOSParts(): do not run if there are no release notes yet and updated regex
- getData(): releases with release notes but no bugs fixed would cause an error
- tweetWebServerFixes(): only tweet if there are any fixes as Apple is not updating this page regularly
- tweetYearlyReport(): run on newReleases instead of lastTwentyReleases

## [10.2] - 2021-07-04

### Fixed

- tweetEntryChanges() only ran on new releases instead of last 20 releases

### Code

- moved all tweeting functions to separate files, which will make it a lot easier to read, maintain and to add new features
- improved regex

## [10.1] - 2021-06-18

### Changed

- new releases are now tweeted in the reverse order as more important updates are usually pushed first

### Fixed

- if `tweetiOSParts()` failed it would still try to tweet the results as that part was not indented right
- if a month number was 12, the bot would search `2021-012` on Apple website, which would obviously fail - zero is now added only if a number is under 10
- as zero-day CVEs are stored in `zeroDay.txt`, the bot now creates this file if it does not exist instead of failing
- there was an issue with the bot picking other dates from the Apple Web Server Notifications page

### Code

- API authentication keys are now stored in `auth_secrets.py` file (which is in `.gitignore`)
- moved scripts to a separate file, separated tweeting function into its own file
- ran `isort` on files

## [10.0] - 2021-05-09

### Added

- alongside of a "new zero-days fixed" tweet:
  - it will tweet how many unique zero-days were fixed that day as Apple fixes same vulnerabilities over different systems
  - now it will check how many zero-days are actually new, and how many were fixed before as Apple may for example release a zero-day fix for iOS, and the next day a fix for the same zero-day in macOS. It will then tweet if a zero-day is new, or if it is an additional update for a previous zero-day. The bot will save zero-day CVEs to a separate file, and check it when new a release with zero-day fixes is released
- iosYearlyReport function that tweets how many security issues Apple fixed in previous 4 versions:
  - was extended to macOS, watchOS and tvOS
  - now also counts and tweets how many releases each series had

### Fixed

- if Apple added or updated any entries on previous release notes, the changes would not get tweeted as it was only checking this on new releases instead of last 20 releases
- if Apple thanked a researcher for assistance with Kernel under "Additional recognition", it would count it as a Kernel bug when tweeting which parts of the iOS got the most bug fixes
- other improvements to regex and counting

## [9.2] - 2021-04-27

### Changed

- added new emojis for Safari, Shazam, GarageBand, Apple Music for Android and macOS Security Updates for previous versions
- fixed grammar and changed wording in some tweets

## [9.1] - 2021-04-25

### Changed

- when Apple says that release notes will be available soon, it will say "no details yet" instead of "no bugs fixed"

### Fixed

- if new update had no release notes, it would not be tweeted

## [9.0] - 2021-04-06

### Added

- when new iOS starts in September, the bot will count all the vulnerabilities fixed in the previous four iOS series
- the bot now creates threads if the original tweet is too long instead of creating two separate tweets

### Fixed

- if there was only an update for iOS, the bot would still tweet "iOS and iPadOS"

### Code

- rewrote all the functions as all the info about updates is now stored in a nested dictionary instead of individual variables

## [8.1] - 2021-04-02

### Changed

- changed wording of a "how many security issues did Apple fix in their websites" tweet

## [8.0] - 2021-03-20

### Added

- on the first day of the month the bot will check [Apple web server notifications](https://support.apple.com/en-us/HT201536) and print how many security fixes Apple fixed on their websites. The bot will also print how many fixes were made to _apple.com_, how many to _icloud.com_ and others.

## [7.5] - 2021-03-09

### Changed

- it will say "iOS and iPadOS" in the title instead of cutting out iPadOS and just saying iOS

### Fixed

- if Apple added an additional comment to the title, the * alongside the header would be tweeted alongside the title
- adjusting the title for iOS, iPadOS and macOS did not work for all the functions

## [7.4] - 2021-02-16

### Fixed

- updated regex that gets the titles for updates that do not have release notes as the title was sometimes wrong

## [7.3] - 2021-02-16

### Fixed

- if there was only one update released it would say "new updates released" instead of "new update released"

## [7.2] - 2021-02-16

### Fixed

- if there was only one update released and if it did not have release notes, it would not be tweeted
- updated regex that gets the titles for updates that do not have release notes as the title was sometimes wrong

## [7.1] - 2021-02-13

### Fixed

- if there was one release updated with new entries and another with only updated entries, it would cause wrong data to be tweeted

### Code

- started using `zip()` function in for loops to loop over multiple variables
- started using f-strings

## [7.0] - 2021-02-09

### Added

- added an emoji for software updates to Apple TV and iTunes

### Fixed

- if there was only one update released, it would not be tweeted
- if there was one update released without release notes, it would cause wrong data to be tweeted alongside the release
- if there was one release with new entries added and old entries updated, it would tweet it twice
- if there is only one bug fixed in the latest iOS version, it will no longer add "and 0 other vulnerabilities fixed"
- if there were more than 5 updates released, tweet would be too long and it would cause an error; this was fixed by adding additional checks to all tweeting functions and if one tweet is too long it will now make another tweet

## CODE

- started using regex
- removed module `BeautifulSoup`

## [6.0] - 2021-02-08

### Added

- the bot now also tweets about releases that do not have any security fixes

### Changed

- changed wording of tweets

## [5.1] - 2021-02-08

### Changed

- added Apple Security Updates page link to the tweet about new updates released
- added release notes link to the tweet that tweets which parts of the iOS got the most bug fixes
- changed wording of tweets

## [5.0] - 2021-02-07

### Added

- tweet top five parts of the iOS that got the most security bugs fixed

### Fixed

- if there were more updates released with a zero-day vulnerabilities fixed, it would tweet only one release
- if there were new updates released, it would not tweet them

## [4.1] - 2021-02-07

### Added

- when Apple makes any changes to the already released release notes, the bot will tweet the release, how many new entries were added and how many previous ones were updated

### Changed

- new checks, so for example if there is only 1 bug fixed it does not tweet with "1 bugs fixed" anymore

## [4.0] - 2021-02-07

### Added

- tweet if there were any zero-days fixed
- new emojis depending on which operating system got the update

### Changed

- reworded tweets
- if there is iOS in the title, now it only takes the iOS version, without iPadOS

### Cod

- added `Counter` module

## [3.1] - 2021-02-06

### Added

- connecting and sending a tweet to Twitter

### Code

- added modules `emoji` and `tweepy`

## [3.0] - 2021-02-05

### Changed

- tweet if Apple added any new entries to old security notes

### Code

- remove `httplib2` module

## [2.1] - 2021-02-03

### Changed

- results are now printed with only one print function so that it will all be in one tweet later

## [2.0] - 2021-02-03

### Changed

- if there is macOS in the title, it only takes the first part not the whole title

### Code

- removed `urlopen` module
- started using for loops

## [1.0] - 2021-02-03

- Initial release

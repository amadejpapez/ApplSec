import re
from datetime import date

import requests

from twitter import tweet_or_make_a_thread


def tweet_webserver_fixes():
    """
    In month of March Apple fixed 42 security issues in their websites 🌐

    🍎 31 of them on apple[.]com
    ☁️ 1 of them on icloud[.]com
    and 10 on other domains
    """

    last_month = int(date.today().strftime("%m")) - 1
    last_month_name = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ][last_month - 1]

    date_format_three = f"<em>{date.today().year}-{last_month}"

    main_page = "https://support.apple.com/en-us/HT201536"
    page = requests.get(main_page).text
    num_of_fixes = len(re.findall(date_format_three, page))

    results = f"In {last_month_name}, Apple fixed {num_of_fixes} security issues in their web servers. :globe_with_meridians:\n\n"

    all_fixes = re.findall(rf"<em>{date_format_three}(.*)</em>", page)
    num_on_apple_com = len(re.findall(r"apple.com", str(all_fixes)))
    num_on_icloud_com = len(re.findall(r"icloud.com", str(all_fixes)))

    num_of_fixes = num_of_fixes - num_on_apple_com - num_on_icloud_com

    if num_on_apple_com >= 1:
        results += f":apple: {num_on_apple_com} of those on apple[.]com\n"
    if num_on_icloud_com >= 1:
        results += f":cloud: {num_on_icloud_com} of those on icloud[.]com\n"
    if num_of_fixes >= 1:
        results += f"and {num_of_fixes} on other domains\n"

    results += main_page

    if all_fixes:
        tweet_or_make_a_thread(first_tweet=results)

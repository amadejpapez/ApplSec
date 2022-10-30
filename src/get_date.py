import datetime


def current_date() -> datetime:
    return datetime.date.today()


def check_date() -> datetime:
    """
    On midnight, do checks with the previous date,
    to not miss any changes made between 11pm and 12pm.
    """

    if is_midnight():
        return current_date() - datetime.timedelta(1)

    return current_date()


def is_midnight() -> bool:
    return datetime.datetime.now().hour == 0


def format_one() -> str:
    """
    Return date in a format: 08 Jan 2022
    Used on the main page.
    """

    tmp_date = check_date()

    date_format = f"{tmp_date.day:02d} {tmp_date.strftime('%b')} {tmp_date.year}"

    return date_format


def format_two() -> str:
    """
    Return date in a format: January 2, 2022
    Used on the security content pages, when Apple says "Entry added/updated: ..."
    """

    tmp_date = check_date()

    date_format = f"{tmp_date.strftime('%B')} {tmp_date.day}, {tmp_date.year}"

    return date_format

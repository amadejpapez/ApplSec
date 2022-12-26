import re
from typing import Tuple


def latest_version(release_rows: list) -> dict:
    """
    Return the latest major version number for each system.
    For macOS also return its name.
    """

    versions = {
        "iOS": [0],
        "tvOS": [0],
        "watchOS": [0],
        "macOS": [0, ""],
    }

    release_names = []
    for row in release_rows:
        release_names.append(row[0].text_content())

    for key, value in versions.items():
        search = re.findall(rf"(?i){key}[a-z\s]*\s([0-9]+)", str(release_names))

        search = list(map(int, search))
        search.sort(reverse=True)

        value[0] = search[0]

    versions["macOS"][1] = re.findall(
        rf"(?i)(?<=macOS)[a-z\s]+(?={versions['macOS'][0]})", str(release_names)
    )[0].strip()

    return versions


def latest_four_versions(system: str, version: int, release_rows: list) -> Tuple[str, list]:
    """
    Get last four version numbers for that system.
    For macOS it gives version names instead.
    """

    versions = []

    release_names = []
    for row in release_rows:
        release_names.append(row[0].text_content())

    if system == "macOS":
        # macOS versions are hard coded
        # get macOS name as Security Updates only contain names
        for ver in ["12", "11", "10.15", "10.14"]:
            versions.append(
                re.findall(rf"(?i)(?<=macOS)[a-z\s]+(?={ver})", str(release_names))[0].strip()
            )
    else:
        num = version
        while len(versions) <= 3:
            num -= 1
            versions.append(num)

    return system, versions

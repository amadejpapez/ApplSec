"""
Detect new stable releases from Pallas, so they are posted without waiting for security content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import helpers.pallas as pallas
import helpers.run_errors as run_errors
from helpers.posted_file import PostedFile
from helpers.session import session
from release import Release


@dataclass(frozen=True)
class StableRelease:
    build: str
    version: str | None
    os_names: set[str]
    # True if from PublicAssetSets, the releases offered to everyone now, so ones we post.
    # False if only from AssetSets, which also has older releases managed devices can still
    # install, like 27.0 and 27.1 after 27.2.1 is out. Those are not posted, but their builds
    # are still stable, so a beta channel serving one is not posted as an RC.
    public: bool


_PMV_IOS_DEVICE_FAMILIES = {
    "iPhone": "iOS",
    "iPad": "iPadOS",
    "AppleTV": "tvOS",
    "Watch": "watchOS",
    "AudioAccessory": "HomePod Software",
}
_PMV_OS_KEYS = ["macOS", "visionOS"]


def _get_os_names_for_release(pmv_key: str, entry: dict, version: str) -> set[str]:
    """
    Return set of OS names for a release.
    A release 27.2.1 with same build number can be for both iPad and iPhone for example. We need to post for each one.
    """
    # These are correctly marked
    if pmv_key in _PMV_OS_KEYS:
        return {pmv_key}

    # Everything else we need is under "iOS", we need to split its device name and parse which one out

    if pmv_key != "iOS":
        return set()

    os_names = set()
    before_ipados = pallas.split_version_into_key(version) < (13,)

    for device in entry["SupportedDevices"]:
        # "iPhone18,1" -> "iPhone"
        family = re.split(r"\d", device, maxsplit=1)[0]

        if family not in _PMV_IOS_DEVICE_FAMILIES:
            continue

        os_name = _PMV_IOS_DEVICE_FAMILIES[family]

        # iPad ran iOS before iPadOS 13
        if os_name == "iPadOS" and before_ipados:
            os_name = "iOS"

        os_names.add(os_name)

    return os_names


def _request_pmv() -> dict:
    """Return the list of stable releases Apple offers to all devices."""
    response = session.get(pallas.URL + "/pmv", verify=pallas.APPLE_ROOT_CA, timeout=60)
    response.raise_for_status()

    return response.json()


def _parse_stable_releases(pmv: dict) -> list[StableRelease]:
    """Parse and return a stable release model for every PMV entry."""
    releases = []

    for public, asset_sets in [(True, pmv["PublicAssetSets"]), (False, pmv["AssetSets"])]:
        for pmv_key, entries in asset_sets.items():
            for entry in entries:
                if not entry.get("Build"):
                    print(f"ERROR: Pallas stable release is missing its build, skipping it\n{entry}\n")
                    run_errors.errors.append(ValueError(f"Pallas stable release is missing its build: {entry}"))
                    continue

                try:
                    # "27.0" -> "27".
                    version = entry["ProductVersion"].removesuffix(".0")
                    os_names = _get_os_names_for_release(pmv_key, entry, version)
                except (KeyError, TypeError, AttributeError) as e:
                    print(f"ERROR: Pallas stable release {entry['Build']} is missing its version or devices\n" + repr(e) + "\n")
                    run_errors.errors.append(e)
                    version, os_names = None, set()

                releases.append(StableRelease(entry["Build"], version, os_names, public))

    return releases


def get_stable_releases() -> list[StableRelease]:
    """Return all stable releases."""
    return _parse_stable_releases(_request_pmv())


def get_latest_versions(stable_releases: list[StableRelease]) -> dict[str, dict[str, str]]:
    """Return the newest public version per OS and major: {"iOS": {"18": "18.7.12", "27": "27.2.1"}}."""
    versions: dict[str, dict[str, str]] = {}

    for release in stable_releases:
        if not release.public or release.version is None:
            continue

        for os_name in release.os_names:
            latest = versions.setdefault(os_name, {})
            major_number = release.version.split(".")[0]

            if major_number not in latest or pallas.split_version_into_key(release.version) > pallas.split_version_into_key(latest[major_number]):
                latest[major_number] = release.version

    return versions


def get_new(latest_versions: dict[str, dict[str, str]]) -> list[Release]:
    """Return stable releases that have not been posted yet for each OS."""
    new_releases: list[Release] = []

    for os_name, latest in latest_versions.items():
        posted = PostedFile.data["posts"]["stable_releases"].setdefault(os_name, {})

        for major, version in latest.items():
            if major not in posted or pallas.split_version_into_key(version) > pallas.split_version_into_key(posted[major]):
                posted[major] = version
                new_releases.append(Release.from_name(f"{os_name} {version}"))

    return new_releases


def format_releases(releases: list[Release]) -> list[str]:
    """
    🎉 NEW STABLE RELEASES 🎉

    📱 iOS 27.2.1
    📱 iPadOS 27.2.1
    💻 macOS 27.2.1
    """
    if not releases:
        return []

    post_text = []

    releases.sort(key=lambda x: (x.name.lower()))

    for release in releases:
        post_text.append(f"{release.emoji} {release.name}\n")

    plural = "S" if len(releases) > 1 else ""
    post_text.insert(0, f"🎉 NEW STABLE RELEASE{plural} 🎉\n\n")

    return post_text

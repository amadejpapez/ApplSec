"""
Detect new beta and RC releases from Pallas (gdmf.apple.com), the server Apple devices check for updates.
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import NotRequired, TypedDict

from helpers.posted_file import PostedFile
from helpers.session import session
from release import Release

_URL = "https://gdmf.apple.com/v2"
# gdmf.apple.com uses Apple's own CA, which is not included in the default certificate bundle
_APPLE_ROOT_CA = os.path.abspath(os.path.join(__file__, "../../../certs/apple_root_ca.pem"))

_ASSET_TYPE = "com.apple.MobileAsset.SoftwareUpdate"
_ASSET_TYPE_MAC = "com.apple.MobileAsset.MacSoftwareUpdate"

# Needs updating when new iOS versions pop up in summer, also below in OS_TARGETS for other OS betas
_IOS_BETAS = [
    "a5f921db-50af-448c-8f7e-3f093ca2c954",  # 27
    "da1941f6-9822-4347-b771-fb09c3509052",  # 26
]

# Version the device reports to be on, Apple only offers newer releases. The same iOS
# build is intentionally sent for all OSes, it still returns betas for current and next major versions
_PRODUCT_VERSION = "26.0"
_BUILD_VERSION = "23A341"


class OSTarget(TypedDict):
    name: str
    product_type: str
    hw_model: str
    asset_type: str
    beta_audiences: list[str]
    release_audience: NotRequired[str]


# Devices we request betas for, we only get betas for these devices
# Prefer devices that are not the newest, as a device released with a new major version does not get betas of the previous one
OS_TARGETS: list[OSTarget] = [
    {
        "name": "iOS",
        "product_type": "iPhone18,1",  # iPhone 17 Pro (2025)
        "hw_model": "V53AP",
        "asset_type": _ASSET_TYPE,
        "beta_audiences": _IOS_BETAS,
    },
    {
        "name": "iPadOS",
        "product_type": "iPad17,1",  # iPad Pro 11" M5 (2025)
        "hw_model": "J817AP",
        "asset_type": _ASSET_TYPE,
        "beta_audiences": _IOS_BETAS,
    },
    {
        "name": "macOS",
        "product_type": "Mac17,2",  # MacBook Pro 14" M5 (2025)
        "hw_model": "J704AP",
        "asset_type": _ASSET_TYPE_MAC,
        "beta_audiences": [
            "621ba5ab-54b6-4a71-891a-425ac0ce4551",  # 27
            "832afda4-7283-41da-a95b-75f4a151e473",  # 26
        ],
    },
    {
        "name": "tvOS",
        "product_type": "AppleTV14,1",  # Apple TV 4K 3rd generation (2022)
        "hw_model": "J255AP",
        "asset_type": _ASSET_TYPE,
        "release_audience": "356d9da0-eee4-4c6c-bbe5-99b60eadddf0",
        "beta_audiences": [
            "6ca2978e-e976-48b5-9b85-cba646d5dea8",  # 27
        ],
    },
    {
        "name": "watchOS",
        "product_type": "Watch7,17",  # Apple Watch Series 11 (2025)
        "hw_model": "N227sAP",
        "asset_type": _ASSET_TYPE,
        "release_audience": "b82fcf9c-c284-41c9-8eb2-e69bf5a5269f",
        "beta_audiences": [
            "973a069a-8d0c-4247-8239-9493f14ee56e",  # 27
        ],
    },
    {
        "name": "visionOS",
        "product_type": "RealityDevice17,1",  # Apple Vision Pro M5 (2025)
        "hw_model": "N301aAP",
        "asset_type": _ASSET_TYPE,
        "beta_audiences": [
            "3796f01d-bf07-45c2-8df6-ad7300055ed9",  # 27
            "6cc62786-ab10-4911-bbc3-ebb7815972f6",  # 26
        ],
    },
]


def retrieve_assets() -> tuple[list[tuple[str, dict]], set[str] | None]:
    """
    Return all assets from beta channels as (OS name, asset) and builds of public
    releases. A failed request does not stop the bot, as the next run will retry it.
    """
    assets = []

    for target in OS_TARGETS:
        for audience in target["beta_audiences"]:
            try:
                assets += [(target["name"], asset) for asset in _request_assets(target, audience)]
            except Exception as e:
                print(f"ERROR: Pallas request failed for {target['name']} ({audience})\n" + str(e) + "\n")

    try:
        return assets, _request_final_builds()
    except Exception as e:
        print("ERROR: Pallas request for public releases failed\n" + str(e) + "\n")
        return assets, None


def _request_assets(target: OSTarget, audience: str) -> list[dict]:
    """Return what the target device is offered on the given channel."""
    response = session.post(
        url=_URL + "/assets",
        json={
            "ClientVersion": 2,
            "AssetType": target["asset_type"],
            "AssetAudience": audience,
            "ProductType": target["product_type"],
            "HWModelStr": target["hw_model"],
            "ProductVersion": _PRODUCT_VERSION,
            "BuildVersion": _BUILD_VERSION,
            "CompatibilityVersion": 20,
        },
        verify=_APPLE_ROOT_CA,
        timeout=30,
    )
    response.raise_for_status()

    return _decode_response(response.text)["Assets"]


def _decode_response(jws: str) -> dict:
    """Response is a signed JWS in the format of "header.payload.signature"."""
    payload = jws.split(".")[1]
    payload += "=" * (-len(payload) % 4)

    return json.loads(base64.urlsafe_b64decode(payload))


def _request_final_builds() -> set[str]:
    """Return builds of all public releases."""
    response = session.get(_URL + "/pmv", verify=_APPLE_ROOT_CA, timeout=60)
    response.raise_for_status()

    builds = set()

    # read both lists, so a public build is never mistaken for an RC if it is only in one of them
    data = response.json()
    for asset_set in [*data["PublicAssetSets"].values(), *data["AssetSets"].values()]:
        builds.update(asset["Build"] for asset in asset_set)

    for target in OS_TARGETS:
        if release_audience := target.get("release_audience"):
            builds.update(asset["Build"] for asset in _request_assets(target, release_audience))

    return builds


def _parse_version(asset: dict) -> str:
    """Return version in the format used by Apple: "9.9.27.3" -> "27.3" and "27.0" -> "27"."""
    return asset["OSVersion"].removeprefix("9.9.").removesuffix(".0")


def _parse_beta_number(asset: dict) -> int | None:
    """Return the beta number from a documentation ID: "iOS273Beta1" -> 1."""
    beta_number = re.search(r"Beta(\d+)$", asset.get("SUDocumentationID", ""))

    return int(beta_number.group(1)) if beta_number else None


def _is_beta(asset: dict) -> bool:
    return asset.get("RestoreVersionInfo", {}).get("IsSeed", False)


def get_new(assets: list[tuple[str, dict]], final_builds: set[str] | None) -> list[Release]:
    """
    Return new beta and RC releases that have not been posted yet.

    Beta channels also serve final releases and RCs do not have the beta flag, so
    anything without it is an RC only if the build was not publicly released.
    If public releases are not known (None), skip RCs to avoid posting final releases as RC.
    """
    beta_releases: list[Release] = []

    for os_name, asset in assets:
        try:
            version = _parse_version(asset)
            build = asset["Build"]
        except (KeyError, AttributeError) as e:
            print(f"ERROR: Pallas asset for {os_name} is missing its version or build, skipping it\n" + repr(e) + "\n")
            continue

        if _is_beta(asset):
            # tvOS has no beta number in its documentation ID ("PreRelease"), so it is just "beta"
            release_type, beta_number = "beta", _parse_beta_number(asset)
        elif final_builds is None or build in final_builds:
            continue
        else:
            release_type, beta_number = "RC", None

        # posted once per build and type, so an RC build can later also be posted as final
        posted = PostedFile.data["posts"]["beta_releases"].setdefault(os_name, [])
        if any(record["build"] == build and record["type"] == release_type for record in posted):
            continue

        record: dict = {"version": version, "type": release_type}
        if beta_number is not None:
            record["beta"] = beta_number
        record["build"] = build
        posted.append(record)

        label = release_type if beta_number is None else f"{release_type} {beta_number}"
        name = f"{os_name} {version} {label} ({build})"
        beta_releases.append(Release(name, Release.parse_emoji(name), "", "", "", {}, 0, 0, 0, 0))

    return beta_releases


def format_releases(releases: list[Release]) -> list[str]:
    """
    🧪 NEW BETA RELEASES 🧪

    📱 iOS 16.6 beta 2 (20G5037d)
    📱 iPadOS 16.6 beta 2 (20G5037d)
    💻 macOS 13.5 beta 2 (22G5038d)
    """
    if not releases:
        return []

    post_text = []

    releases.sort(key=lambda x: (x.name.lower()))

    for release in releases:
        post_text.append(f"{release.emoji} {release.name}\n")

    if len(releases) == 1:
        post_text.insert(0, "🧪 NEW BETA RELEASE 🧪\n\n")
    else:
        post_text.insert(0, "🧪 NEW BETA RELEASES 🧪\n\n")

    return post_text

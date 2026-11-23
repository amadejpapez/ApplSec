"""
Detect new beta and RC releases from Pallas beta channels.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

import helpers.pallas as pallas
from helpers.posted_file import PostedFile
from helpers.session import session
from post.pallas_stable_releases import StableRelease
from release import Release

# Updates are split into types or catalogs. macOS is the only special one with its own catalog.
_ASSET_TYPE = "com.apple.MobileAsset.SoftwareUpdate"
_ASSET_TYPE_MAC = "com.apple.MobileAsset.MacSoftwareUpdate"

# Version the device reports to be on, Apple only offers newer releases. The same iOS
# build is intentionally sent for all OSes, it still returns betas for current and next major versions
_PRODUCT_VERSION = "26.0"
_BUILD_VERSION = "23A341"


@dataclass(frozen=True)
class DeviceTarget:
    name: str
    product_type: str
    hw_model: str
    beta_audiences: list[str]
    asset_type: str = _ASSET_TYPE


# Devices we request betas for, we only get betas for these devices
# Prefer devices that are not the newest, as a device released with a new major version does not get betas of the previous one
_DEVICE_TARGETS: list[DeviceTarget] = [
    DeviceTarget(
        name="iOS",
        product_type="iPhone18,1",  # iPhone 17 Pro (2025)
        hw_model="V53AP",
        beta_audiences=[
            "a5f921db-50af-448c-8f7e-3f093ca2c954",  # 27
            "da1941f6-9822-4347-b771-fb09c3509052",  # 26
        ],
    ),
    DeviceTarget(
        name="iPadOS",
        product_type="iPad17,1",  # iPad Pro 11" M5 (2025)
        hw_model="J817AP",
        beta_audiences=[
            "a5f921db-50af-448c-8f7e-3f093ca2c954",  # 27
            "da1941f6-9822-4347-b771-fb09c3509052",  # 26
        ],
    ),
    DeviceTarget(
        name="macOS",
        product_type="Mac17,2",  # MacBook Pro 14" M5 (2025)
        hw_model="J704AP",
        asset_type=_ASSET_TYPE_MAC,
        beta_audiences=[
            "621ba5ab-54b6-4a71-891a-425ac0ce4551",  # 27
            "832afda4-7283-41da-a95b-75f4a151e473",  # 26
        ],
    ),
    DeviceTarget(
        name="tvOS",
        product_type="AppleTV14,1",  # Apple TV 4K 3rd generation (2022)
        hw_model="J255AP",
        beta_audiences=[
            "6ca2978e-e976-48b5-9b85-cba646d5dea8",  # 27
        ],
    ),
    DeviceTarget(
        name="watchOS",
        product_type="Watch7,17",  # Apple Watch Series 11 (2025)
        hw_model="N227sAP",
        beta_audiences=[
            "973a069a-8d0c-4247-8239-9493f14ee56e",  # 27
        ],
    ),
    DeviceTarget(
        name="visionOS",
        product_type="RealityDevice17,1",  # Apple Vision Pro M5 (2025)
        hw_model="N301aAP",
        beta_audiences=[
            "3796f01d-bf07-45c2-8df6-ad7300055ed9",  # 27
            "6cc62786-ab10-4911-bbc3-ebb7815972f6",  # 26
        ],
    ),
]


def _decode_response(jws: str) -> dict:
    """Asset response is a signed JWS in the format of "header.payload.signature"."""
    payload = jws.split(".")[1]
    payload += "=" * (-len(payload) % 4)

    return json.loads(base64.urlsafe_b64decode(payload))


def _get_offered_beta_updates_for_device(device_target: DeviceTarget, audience: str) -> list[dict]:
    """Return what the target device is offered on the given channel."""
    response = session.post(
        url=pallas.URL + "/assets",
        json={
            "ClientVersion": 2,
            "AssetType": device_target.asset_type,
            "AssetAudience": audience,
            "ProductType": device_target.product_type,
            "HWModelStr": device_target.hw_model,
            "ProductVersion": _PRODUCT_VERSION,
            "BuildVersion": _BUILD_VERSION,
            "CompatibilityVersion": 20,
        },
        verify=pallas.APPLE_ROOT_CA,
        timeout=30,
    )
    response.raise_for_status()

    return _decode_response(response.text)["Assets"]


def get_beta_updates() -> list[tuple[str, dict]]:
    """Return all assets from beta channels for target devices as (OS name, asset)."""
    beta_assets = []

    for target in _DEVICE_TARGETS:
        for audience in target.beta_audiences:
            try:
                beta_assets += [(target.name, asset) for asset in _get_offered_beta_updates_for_device(target, audience)]
            except Exception as e:
                print(f"ERROR: Pallas request failed for {target.name} ({audience})\n" + repr(e) + "\n")

    return beta_assets


def _get_beta_key(record: dict) -> tuple:
    """Return beta or RC of the same version for sorting: betas before RCs, then by build."""
    # Split into parts for comparison: "24C5037i" -> ((24, ""), (-1, "C"), (5037, ""), (-1, "i")).
    build_key = tuple((int(part), "") if part.isdigit() else (-1, part) for part in re.findall(r"\d+|\D+", record["build"]))

    return record["type"] == "RC", build_key


def _parse_beta_number(asset: dict) -> int | None:
    """Return the beta number from a documentation ID: "iOS273Beta1" -> 1."""
    beta_number = re.search(r"Beta(\d+)$", asset.get("SUDocumentationID", ""))

    return int(beta_number.group(1)) if beta_number else None


def get_new(beta_assets: list[tuple[str, dict]], stable_releases: list[StableRelease]) -> list[Release]:
    """Return new beta and RC releases that have not been posted yet."""
    stable_build_numbers = {release.build for release in stable_releases}
    latest_returned: dict[tuple[str, str], dict] = {}

    for os_name, asset in beta_assets:
        try:
            # "9.9.27.3" -> "27.3" and "27.0" -> "27"
            version = asset["OSVersion"].removeprefix("9.9.").removesuffix(".0")
            build = asset["Build"]
        except (KeyError, AttributeError) as e:
            print(f"ERROR: Pallas asset for {os_name} is missing its version or build, skipping it\n" + repr(e) + "\n")
            continue

        # If not marked as public seed -> is beta
        if asset.get("RestoreVersionInfo", {}).get("IsSeed", False):
            # tvOS has no beta number in its documentation ID, just "PreRelease", so leave it as just "beta"
            release_type, beta_number = "beta", _parse_beta_number(asset)
        elif not stable_build_numbers or build in stable_build_numbers:
            # Beta channels also contain stable releases and RCs do not have the beta flag, so anything not in stable release from PVM is considered an RC.
            # If build is in stable builds skip it. Also skip if stable builds failed and is empty.
            continue
        else:
            # Not in stable builds and not marked as a beta, assume it is RC
            release_type, beta_number = "RC", None

        record: dict = {"type": release_type}
        if beta_number is not None:
            record["beta"] = beta_number
        record["build"] = build

        returned = latest_returned.get((os_name, version))
        if not returned or _get_beta_key(record) > _get_beta_key(returned):
            latest_returned[(os_name, version)] = record

    beta_releases: list[Release] = []

    for (os_name, version), record in latest_returned.items():
        posted = PostedFile.data["posts"]["beta_releases"].setdefault(os_name, {})
        latest = posted.get(version)
        if latest and _get_beta_key(latest) >= _get_beta_key(record):
            continue

        posted[version] = record

        label = record["type"] if "beta" not in record else f"{record['type']} {record['beta']}"
        beta_releases.append(Release.from_name(f"{os_name} {version} {label} ({record['build']})"))

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

    plural = "S" if len(releases) > 1 else ""
    post_text.insert(0, f"🧪 NEW BETA RELEASE{plural} 🧪\n\n")

    return post_text

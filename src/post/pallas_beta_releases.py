"""
Detect new beta and RC releases from Pallas beta channels.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

import helpers.pallas as pallas
import helpers.run_errors as run_errors
from helpers.posted_file import PostedFile
from helpers.session import session
from post.pallas_stable_releases import StableRelease
from release import Release

# Updates are split into types or catalogs. macOS is the only special one with its own catalog.
_ASSET_TYPE = "com.apple.MobileAsset.SoftwareUpdate"
_ASSET_TYPE_MAC = "com.apple.MobileAsset.MacSoftwareUpdate"


@dataclass(frozen=True)
class DeviceTarget:
    name: str
    product_type: str
    hw_model: str
    # Version the device reports to be on. Apple only offers newer releases, and betas of an older major
    # only to a device on it, so report the oldest major. Newer majors are still offered from their channels.
    product_version: str
    build_version: str
    beta_audiences: list[str]
    asset_type: str = _ASSET_TYPE


# Devices we request betas for, we only get betas for these devices
# Use devices that run the oldest major and still get the newest one, as a device released with a newer major
# cannot report the older one, and one dropped from a newer major does not get its betas
_DEVICE_TARGETS: list[DeviceTarget] = [
    DeviceTarget(
        name="iOS",
        product_type="iPhone17,1",  # iPhone 16 Pro (2024)
        hw_model="D93AP",
        product_version="18.0",
        build_version="22A3354",
        beta_audiences=[
            "a5f921db-50af-448c-8f7e-3f093ca2c954",  # 27
            "da1941f6-9822-4347-b771-fb09c3509052",  # 26
            "9953ae7e-ec38-48d6-9d3c-5c1a15a536dc",  # 18.x
        ],
    ),
    DeviceTarget(
        name="iPadOS",
        product_type="iPad16,3",  # iPad Pro 11" M4 (2024)
        hw_model="J717AP",
        product_version="18.0",
        build_version="22A3354",
        beta_audiences=[
            "a5f921db-50af-448c-8f7e-3f093ca2c954",  # 27
            "da1941f6-9822-4347-b771-fb09c3509052",  # 26
            "9953ae7e-ec38-48d6-9d3c-5c1a15a536dc",  # 18.x
        ],
    ),
    DeviceTarget(
        name="macOS",
        product_type="Mac15,3",  # MacBook Pro 14" M3 (2023)
        hw_model="J504AP",
        product_version="15.0",
        build_version="24A335",
        asset_type=_ASSET_TYPE_MAC,
        beta_audiences=[
            "621ba5ab-54b6-4a71-891a-425ac0ce4551",  # 27
            "832afda4-7283-41da-a95b-75f4a151e473",  # 26
            "98df7800-8378-4469-93bf-5912da21a1e1",  # 15
        ],
    ),
    DeviceTarget(
        name="tvOS",
        product_type="AppleTV14,1",  # Apple TV 4K 3rd generation (2022)
        hw_model="J255AP",
        product_version="18.0",
        build_version="22J357",
        beta_audiences=[
            "6ca2978e-e976-48b5-9b85-cba646d5dea8",  # 27
            "69cc7bd5-9ff2-4f5e-8b4f-30955542a81d",  # 26
            "98847ed4-1c37-445c-9e7b-5b95d29281f2",  # 18
        ],
    ),
    DeviceTarget(
        name="watchOS",
        product_type="Watch7,1",  # Apple Watch Series 9 (2023)
        hw_model="N207sAP",
        product_version="11.0",
        build_version="22R349",
        beta_audiences=[
            "973a069a-8d0c-4247-8239-9493f14ee56e",  # 27
            "e73d2741-8003-45cd-b909-86b9840f2ea2",  # 26
            "23d7265b-1000-47cf-8d0a-07144942db9e",  # 11
        ],
    ),
    DeviceTarget(
        name="visionOS",
        product_type="RealityDevice14,1",  # Apple Vision Pro (2024)
        hw_model="N301AP",
        product_version="2.0",
        build_version="22N320",
        beta_audiences=[
            "3796f01d-bf07-45c2-8df6-ad7300055ed9",  # 27
            "6cc62786-ab10-4911-bbc3-ebb7815972f6",  # 26
            "0bef3239-79ad-4d2a-99c3-2c05df2becf8",  # 2
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
            "ProductVersion": device_target.product_version,
            "BuildVersion": device_target.build_version,
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
                run_errors.errors.append(e)

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


def _is_older_than_stable(latest_versions: dict[str, dict[str, str]], os_name: str, version: str) -> bool:
    """
    Return True if a version is not newer than the latest stable of its major.
    Apple keep serving old betas and stable releases long after, which are not in stable releases from PMV anymore.
    """
    latest = latest_versions.get(os_name)
    if not latest:
        return False

    major = version.split(".")[0]
    if major in latest:
        return pallas.split_version_into_key(version) <= pallas.split_version_into_key(latest[major])

    # A major older than the newest released one that is not released anymore, like tvOS 18 when only 26 and 27 are
    return int(major) < max(int(latest_major) for latest_major in latest)


def get_new(beta_assets: list[tuple[str, dict]], stable_releases: list[StableRelease], latest_stable_versions: dict[str, dict[str, str]]) -> list[Release]:
    """Return new beta and RC releases that have not been posted yet."""
    stable_build_numbers = {release.build for release in stable_releases}
    latest_returned: dict[tuple[str, str], dict] = {}

    for os_name, asset in beta_assets:
        try:
            # "9.9.27.3" -> "27.3" and "27.0" -> "27"
            version = asset["OSVersion"].removeprefix("9.9.").removesuffix(".0")
            build = asset["Build"]
            older_than_stable = _is_older_than_stable(latest_stable_versions, os_name, version)
        except (KeyError, AttributeError, ValueError) as e:
            print(f"ERROR: Pallas asset for {os_name} is missing its version or build, skipping it\n" + repr(e) + "\n")
            run_errors.errors.append(e)
            continue

        if older_than_stable:
            continue

        # If not marked as public seed -> is beta
        if asset.get("RestoreVersionInfo", {}).get("IsSeed", False):
            # tvOS has no beta number in its documentation ID, just "PreRelease", so leave it as just "beta"
            release_type, beta_number = "beta", _parse_beta_number(asset)
        elif not stable_build_numbers or build in stable_build_numbers:
            # Beta channels also contain stable releases and RCs do not have the beta flag, so anything not in stable release from PVM is considered an RC.
            # If build is in stable builds skip it. Also skip if there are no stable builds to compare with.
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

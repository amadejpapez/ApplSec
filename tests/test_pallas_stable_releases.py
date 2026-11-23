import copy

from helpers_test import read_examples

import helpers.run_errors as run_errors
import post.pallas_stable_releases as pallas_stable_releases
from helpers.posted_file import PostedFile
from post.pallas_stable_releases import StableRelease

examples = read_examples("posts_pallas")


def test_pallas_stable_download() -> None:
    """Verify successful download, including Apple's certificate, and that all OSes are returned."""
    stable_releases = pallas_stable_releases.get_stable_releases()
    os_names = {"iOS", "iPadOS", "macOS", "tvOS", "watchOS", "visionOS", "HomePod Software", "HomeView Software"}

    assert set(pallas_stable_releases.get_latest_versions(stable_releases)) == os_names


def test_pallas_stable_releases() -> None:
    """Verify the post of new stable releases and that they are not returned again."""
    PostedFile.reset()
    latest_versions = pallas_stable_releases.get_latest_versions(pallas_stable_releases._parse_stable_releases(examples["pmv"]))

    new_releases = pallas_stable_releases.get_new(latest_versions)

    post = pallas_stable_releases.format_releases(new_releases)
    assert post == examples["stable_releases_post"]

    assert PostedFile.data["posts"]["stable_releases"]["iOS"] == {"12": "12.5.8", "26": "26.7.3", "27": "27.2.1"}

    # test again after posting and verify it returns nothing
    assert pallas_stable_releases.get_new(latest_versions) == []


def test_pallas_stable_releases_only_greater() -> None:
    """Verify that only versions greater than the posted one of the same major are returned and stored."""
    PostedFile.reset()

    PostedFile.data["posts"]["stable_releases"] = {"iOS": {"18": "18.7.5", "27": "27.2.1"}}

    new_releases = pallas_stable_releases.get_new({"iOS": {"18": "18.7.6", "26": "26.7.3", "27": "27.2"}})

    assert [release.name for release in new_releases] == ["iOS 18.7.6", "iOS 26.7.3"]
    assert PostedFile.data["posts"]["stable_releases"]["iOS"] == {"18": "18.7.6", "26": "26.7.3", "27": "27.2.1"}


def test_pallas_stable_versions_newest_per_major() -> None:
    """Verify that only the newest version of a major is kept, if Apple still lists an older one."""
    stable_releases = [
        StableRelease("22H124", "18.7.6", {"iOS"}, public=True),
        StableRelease("22H100", "18.7.4", {"iOS"}, public=True),
    ]

    assert pallas_stable_releases.get_latest_versions(stable_releases) == {"iOS": {"18": "18.7.6"}}


def test_pallas_stable_versions_only_public() -> None:
    """Verify that versions only listed in AssetSets, which has older releases, are not posted."""
    stable_releases = [
        StableRelease("24B156", "27.2.1", {"iOS"}, public=True),
        StableRelease("24C100", "27.3", {"iOS"}, public=False),
        StableRelease("23H100", "26.7", {"iOS"}, public=False),
    ]

    assert pallas_stable_releases.get_latest_versions(stable_releases) == {"iOS": {"27": "27.2.1"}}


def test_pallas_stable_releases_malformed() -> None:
    """Verify that an entry missing its devices still returns its build, and the other entries their versions."""
    pmv = copy.deepcopy(examples["pmv"])
    # the only iPadOS 27.2.1 entry, iOS 27.2.1 is also listed by another entry
    del pmv["PublicAssetSets"]["iOS"][0]["SupportedDevices"]

    stable_releases = pallas_stable_releases._parse_stable_releases(pmv)
    latest_versions = pallas_stable_releases.get_latest_versions(stable_releases)

    assert "24B156" in {release.build for release in stable_releases}
    assert "iPadOS" not in latest_versions
    assert latest_versions["iOS"]["27"] == "27.2.1"
    # skipped, but the run should still fail at the end
    assert len(run_errors.errors) == 1
    run_errors.errors.clear()

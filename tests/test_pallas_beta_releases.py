import copy

from helpers_test import read_examples

import post.pallas_beta_releases as pallas_beta_releases
import post.pallas_stable_releases as pallas_stable_releases
from helpers.posted_file import PostedFile
from post.pallas_stable_releases import StableRelease

examples = read_examples("posts_pallas")

beta_assets = examples["beta_assets"]
stable_releases = [StableRelease(build, None, set(), public=True) for build in examples["stable_builds"]]


def test_pallas_beta_download() -> None:
    """Verify successful download and decoding, including Apple's certificate, and that all OSes are returned."""
    os_names = {target.name for target in pallas_beta_releases._DEVICE_TARGETS}

    assert {os_name for os_name, _ in pallas_beta_releases.get_beta_updates()} == os_names


def test_decode_response() -> None:
    """Verify decoding of a JWS, where base64 padding was removed by Apple."""
    assert pallas_beta_releases._decode_response("header.eyJBc3NldHMiOiBbXX0.signature") == {"Assets": []}


def test_pallas_beta_releases() -> None:
    """Verify names of betas and RCs, while stable releases from beta channels are skipped."""
    PostedFile.reset()

    beta_releases = pallas_beta_releases.get_new(beta_assets, stable_releases)

    post = pallas_beta_releases.format_releases(beta_releases)
    assert post == examples["beta_releases_post"]

    assert PostedFile.data["posts"]["beta_releases"] == examples["beta_releases_posted"]

    # test again after posting and verify it returns nothing
    beta_releases = pallas_beta_releases.get_new(beta_assets, stable_releases)

    post = pallas_beta_releases.format_releases(beta_releases)
    assert post == []


def test_pallas_beta_releases_only_one() -> None:
    """Verify that all except one being posted returns only that one."""
    PostedFile.reset()

    PostedFile.data["posts"]["beta_releases"] = copy.deepcopy(examples["beta_releases_posted"])
    del PostedFile.data["posts"]["beta_releases"]["iOS"]

    beta_releases = pallas_beta_releases.get_new(beta_assets, stable_releases)

    post = pallas_beta_releases.format_releases(beta_releases)
    assert post == examples["beta_releases_one_post"]


def test_pallas_beta_releases_only_later() -> None:
    """Verify that only releases later than the posted one of the same version are returned and stored."""
    PostedFile.reset()

    tvos_beta = {"OSVersion": "27.3", "Build": "24K5286g", "RestoreVersionInfo": {"IsSeed": True}}
    PostedFile.data["posts"]["beta_releases"] = {
        "iOS": {"27.3": {"type": "beta", "beta": 2, "build": "24C5047e"}},
        "tvOS": {"27.3": {"type": "beta", "build": "24K5296a"}},
    }

    # older betas returned again
    assert pallas_beta_releases.get_new(beta_assets[:1] + [("tvOS", tvos_beta)], stable_releases) == []

    # a later build of the same version, as tvOS has no beta number, and then an RC
    beta_releases = pallas_beta_releases.get_new([("tvOS", tvos_beta | {"Build": "24K5306b"})], stable_releases)
    assert [release.name for release in beta_releases] == ["tvOS 27.3 beta (24K5306b)"]

    beta_releases = pallas_beta_releases.get_new([("tvOS", tvos_beta | {"Build": "24K40", "RestoreVersionInfo": {}})], stable_releases)
    assert [release.name for release in beta_releases] == ["tvOS 27.3 RC (24K40)"]

    assert PostedFile.data["posts"]["beta_releases"]["tvOS"] == {"27.3": {"type": "RC", "build": "24K40"}}


def test_pallas_beta_releases_latest_in_run() -> None:
    """Verify that of several builds of one version in the same run only the latest is returned, in any order."""
    beta_2 = ("iOS", beta_assets[0][1] | {"Build": "24C5047e", "SUDocumentationID": "iOS273Beta2"})
    beta_3 = ("iOS", beta_assets[0][1] | {"Build": "24C5057a", "SUDocumentationID": "iOS273Beta3"})

    for run in [[beta_2, beta_3], [beta_3, beta_2]]:
        PostedFile.reset()

        beta_releases = pallas_beta_releases.get_new(run, stable_releases)

        assert [release.name for release in beta_releases] == ["iOS 27.3 beta 3 (24C5057a)"]


def test_pallas_beta_releases_two_beta_cycles() -> None:
    """Verify that a beta of a lower version is returned while a higher version of the same major is also in beta."""
    PostedFile.reset()

    posted_27_4 = {"type": "beta", "beta": 1, "build": "24E5207f"}
    PostedFile.data["posts"]["beta_releases"] = {"iOS": {"27.4": posted_27_4}}

    beta_releases = pallas_beta_releases.get_new(beta_assets[:1], stable_releases)

    assert [release.name for release in beta_releases] == ["iOS 27.3 beta 1 (24C5037i)"]
    assert PostedFile.data["posts"]["beta_releases"]["iOS"] == {"27.4": posted_27_4} | examples["beta_releases_posted"]["iOS"]


def test_pallas_beta_releases_stable_builds_unknown() -> None:
    """Verify that with stable releases unknown betas are returned, but nothing is treated as an RC."""
    PostedFile.reset()

    beta_releases = pallas_beta_releases.get_new(beta_assets, [])

    assert "macOS 26.7.3 RC (25G416)" not in [release.name for release in beta_releases]
    assert "iOS 27.3 beta 1 (24C5037i)" in [release.name for release in beta_releases]


def test_pallas_beta_releases_malformed_asset() -> None:
    """Verify that an asset without a version or build is skipped and the rest are still returned."""
    PostedFile.reset()

    malformed = [["iOS", {"Build": "24C5037i"}], ["tvOS", {"OSVersion": "27.3"}]]
    beta_releases = pallas_beta_releases.get_new(malformed + beta_assets[:1], stable_releases)

    assert [release.name for release in beta_releases] == ["iOS 27.3 beta 1 (24C5037i)"]


def test_pallas_beta_releases_stable_only_in_asset_sets() -> None:
    """Verify that a build only listed in AssetSets is not posted as an RC."""
    PostedFile.reset()
    pmv_releases = pallas_stable_releases._parse_stable_releases(examples["pmv"])

    assert pallas_beta_releases.get_new([("iOS", {"OSVersion": "9.9.27.2", "Build": "24B100"})], pmv_releases) == []

import copy

from helpers_test import read_examples

import post.pallas_releases as pallas_releases
from helpers.posted_file import PostedFile

examples = read_examples("posts_pallas")

assets = examples["assets"]
final_builds = set(examples["final_builds"])


def test_pallas_download() -> None:
    """Verify successful download and decoding, including Apple's certificate, and that all OSes are returned."""
    downloaded_assets, downloaded_builds = pallas_releases.retrieve_assets()

    assert {os_name for os_name, _ in downloaded_assets} == {target["name"] for target in pallas_releases.OS_TARGETS}
    assert downloaded_builds


def test_decode_response() -> None:
    """Verify decoding of a JWS, where base64 padding was removed by Apple."""
    assert pallas_releases._decode_response("header.eyJBc3NldHMiOiBbXX0.signature") == {"Assets": []}


def test_pallas_releases() -> None:
    """Verify names of betas and RCs, while final releases from beta channels are skipped."""
    PostedFile.reset()

    beta_releases = pallas_releases.get_new(assets, final_builds)

    post = pallas_releases.format_releases(beta_releases)
    assert post == examples["beta_releases_post"]

    assert PostedFile.data["posts"]["beta_releases"] == examples["beta_releases_posted"]

    # test again after posting and verify it returns nothing
    beta_releases = pallas_releases.get_new(assets, final_builds)

    post = pallas_releases.format_releases(beta_releases)
    assert post == []


def test_pallas_releases_only_one() -> None:
    """Verify that all except one being posted returns only that one."""
    PostedFile.reset()

    PostedFile.data["posts"]["beta_releases"] = copy.deepcopy(examples["beta_releases_posted"])
    del PostedFile.data["posts"]["beta_releases"]["iOS"]

    beta_releases = pallas_releases.get_new(assets, final_builds)

    post = pallas_releases.format_releases(beta_releases)
    assert post == examples["beta_releases_one_post"]


def test_pallas_releases_duplicates() -> None:
    """Verify that the same build returned multiple times is returned once."""
    PostedFile.reset()

    beta_releases = pallas_releases.get_new(assets[:1] * 2, final_builds)

    assert [release.name for release in beta_releases] == ["iOS 27.3 beta 1 (24C5037i)"]


def test_pallas_releases_posted_by_build() -> None:
    """Verify that an already posted build is not posted again, even if its version or beta number changed."""
    PostedFile.reset()

    PostedFile.data["posts"]["beta_releases"] = {"iOS": [{"version": "27.3", "type": "beta", "beta": 2, "build": "24C5037i"}]}

    beta_releases = pallas_releases.get_new(assets[:1], final_builds)

    assert beta_releases == []


def test_pallas_releases_cleared_per_os() -> None:
    """Verify that only the oldest releases of an OS with too many are removed."""
    PostedFile.reset()

    PostedFile.data["posts"]["beta_releases"] = {
        "iOS": [{"version": "27.3", "type": "beta", "beta": i, "build": str(i)} for i in range(25)],
        "tvOS": [{"version": "27.3", "type": "beta", "build": "24K5286g"}],
    }

    cleared = PostedFile._clear_old_data(PostedFile.data)["posts"]["beta_releases"]

    assert [record["build"] for record in cleared["iOS"]] == [str(i) for i in range(5, 25)]
    assert len(cleared["tvOS"]) == 1


def test_pallas_releases_final_builds_unknown() -> None:
    """Verify that with public releases unknown betas are returned, but nothing is treated as an RC."""
    PostedFile.reset()

    beta_releases = pallas_releases.get_new(assets, None)

    assert "macOS 26.7.3 RC (25G416)" not in [release.name for release in beta_releases]
    assert "iOS 27.3 beta 1 (24C5037i)" in [release.name for release in beta_releases]


def test_pallas_releases_malformed_asset() -> None:
    """Verify that an asset without a version or build is skipped and the rest are still returned."""
    PostedFile.reset()

    malformed = [["iOS", {"Build": "24C5037i"}], ["tvOS", {"OSVersion": "27.3"}]]
    beta_releases = pallas_releases.get_new(malformed + assets[:1], final_builds)

    assert [release.name for release in beta_releases] == ["iOS 27.3 beta 1 (24C5037i)"]


def test_pallas_version_format() -> None:
    assert pallas_releases._parse_version({"OSVersion": "9.9.27.3"}) == "27.3"
    assert pallas_releases._parse_version({"OSVersion": "27.0"}) == "27"
    assert pallas_releases._parse_version({"OSVersion": "26.7.3"}) == "26.7.3"

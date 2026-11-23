from pathlib import Path
from typing import Iterator

import pytest

import helpers.run_errors as run_errors
from helpers.posted_file import PostedFile


@pytest.fixture(autouse=True)
def temp_posted_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read and save posted_data.json in a temporary directory, so tests never touch the real src/posted_data.json."""
    monkeypatch.setattr(PostedFile, "_LOC", str(tmp_path / "posted_data.json"))


@pytest.fixture(autouse=True)
def no_run_errors() -> Iterator[None]:
    """
    Fail every test that collected run errors, as in a real run they would fail it at the end.
    Tests that expect errors must assert and clear them.
    """
    run_errors.errors.clear()
    yield
    assert run_errors.errors == [], f"test collected unexpected run errors: {run_errors.errors!r}"

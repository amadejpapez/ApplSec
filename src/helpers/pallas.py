"""
Shared constants for Pallas (gdmf.apple.com), the server Apple devices check for updates.
"""

import os

URL = "https://gdmf.apple.com/v2"
# Pallas uses Apple's own CA, which is not included in the default certificate bundle
APPLE_ROOT_CA = os.path.abspath(os.path.join(__file__, "../../../certs/apple_root_ca.pem"))


def split_version_into_key(version: str) -> tuple[int, ...]:
    """Return version key for sorting: "27.2.1" -> (27, 2, 1)."""
    return tuple(int(part) for part in version.split(".") if part.isdigit())

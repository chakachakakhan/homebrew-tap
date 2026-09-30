"""Update only Thorium's stable version and both official asset checksums."""

import json
import re
import subprocess
from pathlib import Path

ORIGIN = "https://github.com/edrlab/thorium-reader/releases/download"
CASK = Path("Casks/thorium-reader-linux.rb")


def update_cask(original, release):
    tag = release.get("tag_name", "")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Only published stable releases are accepted")
    if not re.fullmatch(r"v\d+(?:\.\d+)+", tag):
        raise ValueError(f"Unexpected stable release tag: {tag!r}")
    version = tag[1:]
    current = re.findall(r'^  version "(\d+(?:\.\d+)+)"$', original, re.MULTILINE)
    if len(current) != 1:
        raise ValueError("Expected exactly one numeric cask version")
    if tuple(map(int, version.split("."))) < tuple(map(int, current[0].split("."))):
        raise ValueError("Refusing to downgrade the cask")

    checksums = {}
    for arch in ("arm64", "x86_64"):
        name = f"Thorium-{version}-{arch}.AppImage"
        assets = [a for a in release.get("assets", []) if a.get("name") == name]
        if len(assets) != 1:
            raise ValueError(f"Expected one {name}; wait for complete upstream publication")
        asset = assets[0]
        if asset.get("browser_download_url") != f"{ORIGIN}/{tag}/{name}":
            raise ValueError(f"Unexpected download origin for {arch}")
        if asset.get("state") != "uploaded" or asset.get("size", 0) <= 0:
            raise ValueError(f"Incomplete asset for {arch}")
        digest = asset.get("digest") or ""
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError(f"Missing or invalid GitHub SHA-256 digest for {arch}")
        checksums[arch] = digest.removeprefix("sha256:")

    updated = original
    replacements = (
        (r'^  version "[^\"]+"$', f'  version "{version}"'),
        (r'^  sha256 arm64_linux:  "[0-9a-f]{64}",$',
         f'  sha256 arm64_linux:  "{checksums["arm64"]}",'),
        (r'^         x86_64_linux: "[0-9a-f]{64}"$',
         f'         x86_64_linux: "{checksums["x86_64"]}"'),
    )
    for pattern, replacement in replacements:
        updated, count = re.subn(pattern, replacement, updated, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"Expected exactly one metadata stanza: {pattern}")
    if current[0] == version and updated != original:
        raise ValueError("Same-version rebuilds require manual review")
    return updated


if __name__ == "__main__":
    response = subprocess.check_output([
        "curl", "--proto", "=https", "--tlsv1.2", "--fail", "--silent",
        "--show-error", "--location", "--retry", "3", "--max-time", "60",
        "https://api.github.com/repos/edrlab/thorium-reader/releases/latest",
    ], text=True)
    original = CASK.read_text()
    updated = update_cask(original, json.loads(response))
    if updated != original:
        CASK.write_text(updated)
        print("Updated Thorium Reader's stable version and architecture checksums")
    else:
        print("Thorium Reader is current")

"""Update OMP Desktop from the publisher's complete stable Linux release."""

import json
import re
import subprocess
from pathlib import Path

CASK = Path("Casks/omp-desktop.rb")
ORIGIN = "https://github.com/apoc/omp-desktop/releases/download"
VERSION = r'^  version "(\d+(?:\.\d+)+)"$'
CHECKSUM = r'^  sha256 "([0-9a-f]{64})"$'


def package_version(content):
    matches = re.findall(VERSION, content, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Expected exactly one numeric cask version")
    return matches[0]


def normalized(content):
    package_version(content)
    content = re.sub(VERSION, "<version>", content, flags=re.MULTILINE)
    content, count = re.subn(CHECKSUM, "<checksum>", content, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Expected exactly one SHA-256 checksum")
    return content


def metadata_only(before, after):
    try:
        return (before != after
                and tuple(map(int, package_version(after).split(".")))
                > tuple(map(int, package_version(before).split(".")))
                and normalized(before) == normalized(after))
    except ValueError:
        return False


def update_cask(original, release):
    normalized(original)
    tag = release.get("tag_name", "")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Only published stable releases are accepted")
    if not re.fullmatch(r"v\d+(?:\.\d+)+", tag):
        raise ValueError(f"Unexpected stable release tag: {tag!r}")
    version = tag[1:]
    current = package_version(original)
    if tuple(map(int, version.split("."))) < tuple(map(int, current.split("."))):
        raise ValueError("Refusing to downgrade OMP Desktop")
    name = f"OMP.Desktop_{version}_amd64.AppImage"
    assets = [asset for asset in release.get("assets", []) if asset.get("name") == name]
    if len(assets) != 1:
        raise ValueError(f"Expected one {name}; wait for complete publication")
    asset = assets[0]
    if asset.get("browser_download_url") != f"{ORIGIN}/{tag}/{name}":
        raise ValueError("Unexpected asset download origin")
    if asset.get("state") != "uploaded" or asset.get("size", 0) <= 0:
        raise ValueError("The Linux AppImage is incomplete")
    digest = asset.get("digest") or ""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Missing or invalid GitHub SHA-256 digest")
    updated = re.sub(VERSION, f'  version "{version}"', original, flags=re.MULTILINE)
    updated = re.sub(CHECKSUM, f'  sha256 "{digest[7:]}"', updated, flags=re.MULTILINE)
    if current == version and updated != original:
        raise ValueError("Same-version rebuilds require manual review")
    return updated


if __name__ == "__main__":
    response = subprocess.check_output([
        "curl", "--proto", "=https", "--tlsv1.2", "--fail", "--silent",
        "--show-error", "--location", "--retry", "3", "--max-time", "60",
        "https://api.github.com/repos/apoc/omp-desktop/releases/latest",
    ], text=True)
    original = CASK.read_text()
    updated = update_cask(original, json.loads(response))
    if updated != original:
        CASK.write_text(updated)
        print("Updated OMP Desktop's stable version and official SHA-256 digest")
    else:
        print("OMP Desktop is current")

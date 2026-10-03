"""Keep both Homebrew packages on one complete official OpenCodex release."""

import json
import re
import subprocess
from pathlib import Path

ORIGIN = "https://github.com/lidge-jun/opencodex/releases/download"
PACKAGE_ASSETS = {
    "Formula/opencodex.rb": (
        "ocx-{version}-bun-darwin-arm64.tar.gz",
        "ocx-{version}-bun-darwin-x64.tar.gz",
        "ocx-{version}-bun-linux-arm64.tar.gz",
        "ocx-{version}-bun-linux-x64.tar.gz",
    ),
    "Casks/opencodex-desktop.rb": (
        # Homebrew has separate Intel/ARM checksum fields for the same universal DMG.
        "OpenCodex-{version}-macos.dmg",
        "OpenCodex-{version}-macos.dmg",
        "OpenCodex-{version}-linux-x86_64.AppImage",
    ),
}
VERSION = r'^  version "(\d+(?:\.\d+)+)"$'
CHECKSUM = r'^((?: +sha256(?: +arm:)?| +(?:intel|x86_64_linux):) +)"([0-9a-f]{64})"(,?)$'


def package_version(content):
    versions = re.findall(VERSION, content, re.MULTILINE)
    if len(versions) != 1:
        raise ValueError("Expected exactly one numeric package version")
    return versions[0]


def version_tuple(version):
    return tuple(map(int, version.split(".")))


def normalize_metadata(content, path):
    package_version(content)
    content = re.sub(VERSION, "<version>", content, flags=re.MULTILINE)
    content, count = re.subn(CHECKSUM, lambda match: f'{match[1]}"<checksum>"{match[3]}',
                             content, flags=re.MULTILINE)
    if count != len(PACKAGE_ASSETS[path]):
        raise ValueError("Unexpected checksum count or malformed metadata")
    return content


def metadata_only(before, after, path):
    try:
        return (
            before != after
            and version_tuple(package_version(after)) > version_tuple(package_version(before))
            and normalize_metadata(before, path) == normalize_metadata(after, path)
        )
    except (KeyError, ValueError):
        return False


def update_packages(originals, release):
    if set(originals) != set(PACKAGE_ASSETS):
        raise ValueError("Both OpenCodex packages must be updated together")
    tag = release.get("tag_name", "")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Only published stable releases are accepted")
    if not re.fullmatch(r"v\d+(?:\.\d+)+", tag):
        raise ValueError(f"Unexpected stable release tag: {tag!r}")
    version = tag[1:]
    current = {package_version(content) for content in originals.values()}
    if len(current) != 1:
        raise ValueError("The CLI and desktop versions must agree")
    old_version = current.pop()
    if version_tuple(version) < version_tuple(old_version):
        raise ValueError("Refusing to downgrade OpenCodex")

    updated = {}
    for path, names in PACKAGE_ASSETS.items():
        original = originals[path]
        normalize_metadata(original, path)
        digests = []
        for template in names:
            name = template.format(version=version)
            matches = [asset for asset in release.get("assets", []) if asset.get("name") == name]
            if len(matches) != 1:
                raise ValueError(f"Expected one {name}; wait for complete upstream publication")
            asset = matches[0]
            if asset.get("browser_download_url") != f"{ORIGIN}/{tag}/{name}":
                raise ValueError(f"Unexpected download origin for {name}")
            if asset.get("state") != "uploaded" or asset.get("size", 0) <= 0:
                raise ValueError(f"Incomplete asset: {name}")
            digest = asset.get("digest") or ""
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError(f"Missing or invalid GitHub SHA-256 digest: {name}")
            digests.append(digest.removeprefix("sha256:"))
        checksums = iter(digests)
        content = re.sub(VERSION, f'  version "{version}"', original, flags=re.MULTILINE)
        content = re.sub(CHECKSUM, lambda match: f'{match[1]}"{next(checksums)}"{match[3]}',
                         content, flags=re.MULTILINE)
        if old_version == version and content != original:
            raise ValueError("Same-version rebuilds require manual review")
        updated[path] = content
    return updated


if __name__ == "__main__":
    response = subprocess.check_output([
        "curl", "--proto", "=https", "--tlsv1.2", "--fail", "--silent",
        "--show-error", "--location", "--retry", "3", "--max-time", "60",
        "https://api.github.com/repos/lidge-jun/opencodex/releases/latest",
    ], text=True)
    originals = {path: Path(path).read_text() for path in PACKAGE_ASSETS}
    updated = update_packages(originals, json.loads(response))
    for path, content in updated.items():
        if content != originals[path]:
            Path(path).write_text(content)
            print(f"Updated {path}")
    if updated == originals:
        print("OpenCodex is current")

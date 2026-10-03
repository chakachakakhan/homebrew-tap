"""Track GNU stable source releases; let Homebrew build and publish bottles."""

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

FORMULA = "Formula/emacs-pgtk.rb"
CASK = "Casks/emacs-pgtk-linux.rb"
PACKAGES = {FORMULA, CASK}
GNU = "https://ftp.gnu.org/gnu/emacs/"
VERSION = r"\d+\.[1-9]\d*(?:\.\d+)?"
FORMULA_URL = rf'^  url "https://ftpmirror\.gnu\.org/emacs/emacs-({VERSION})\.tar\.xz"$'
CASK_VERSION = rf'^  version "({VERSION})"$'
CHECKSUM = r'^  sha256 "([0-9a-f]{64})"$'
BOTTLE = r'^  bottle do\n(?:(?!^  end$).)*^  end\n\n'


def one(pattern, content):
    matches = re.findall(pattern, content, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Expected exactly one well-formed metadata field")
    return matches[0]


def package_version(content, path):
    return one(FORMULA_URL if path == FORMULA else CASK_VERSION, content)


def version_tuple(version):
    if not re.fullmatch(VERSION, version):
        raise ValueError(f"Not a stable GNU version: {version!r}")
    return tuple(map(int, version.split(".")))


def latest_release(index):
    versions = set(re.findall(rf'href=["\']emacs-({VERSION})\.tar\.xz["\']', index))
    if not versions:
        raise ValueError("GNU's index contained no stable Emacs source archives")
    return max(versions, key=version_tuple)


def without_bottle(content):
    if len(re.findall(r'^  bottle do$', content, re.MULTILINE)) > 1:
        raise ValueError("Multiple bottle blocks")
    result, count = re.subn(BOTTLE, "", content, flags=re.MULTILINE | re.DOTALL)
    if "  bottle do" in result:
        raise ValueError("Unrecognized bottle block")
    return result


def update_packages(originals, version, digest):
    if set(originals) != PACKAGES or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Both packages and a valid SHA-256 are required")
    current = {package_version(content, path) for path, content in originals.items()}
    checksums = {one(CHECKSUM, content) for content in originals.values()}
    if len(current) != 1 or len(checksums) != 1:
        raise ValueError("The formula and cask must describe the same GNU source release")
    old = current.pop()
    if version_tuple(version) < version_tuple(old):
        raise ValueError("Refusing to downgrade Emacs")
    if version == old:
        if checksums != {digest}:
            raise ValueError("A same-version source replacement requires manual review")
        return originals.copy()
    result = {}
    for path, original in originals.items():
        content = original
        if path == FORMULA:
            content = without_bottle(content)
            # A newer source release starts again at revision zero.
            content = re.sub(r'^  revision [1-9]\d*\n', "", content, flags=re.MULTILINE)
            one(FORMULA_URL, content)
            mirror = f'  mirror "{GNU}emacs-{old}.tar.xz"'
            if content.count(mirror) != 1:
                raise ValueError("Expected the matching official GNU mirror")
            content = re.sub(FORMULA_URL,
                             f'  url "https://ftpmirror.gnu.org/emacs/emacs-{version}.tar.xz"',
                             content, flags=re.MULTILINE)
            content = content.replace(mirror, f'  mirror "{GNU}emacs-{version}.tar.xz"')
        else:
            content = re.sub(CASK_VERSION, f'  version "{version}"', content, flags=re.MULTILINE)
        content = re.sub(CHECKSUM, f'  sha256 "{digest}"', content, flags=re.MULTILINE)
        result[path] = content
    return result


def metadata_only(before, after):
    """Require the exact deterministic source bump, with stale bottles removed."""
    try:
        version = package_version(after[FORMULA], FORMULA)
        digest = one(CHECKSUM, after[FORMULA])
        return (version_tuple(version) > version_tuple(package_version(before[FORMULA], FORMULA))
                and update_packages(before, version, digest) == after)
    except (KeyError, ValueError):
        return False


def download(url, destination=None):
    command = ["curl", "--proto", "=https", "--proto-redir", "=https", "--tlsv1.2",
               "--fail", "--silent", "--show-error", "--location", "--retry", "3",
               "--max-time", "180", url]
    if destination is not None:
        subprocess.run(command + ["--output", str(destination)], check=True)
        return None
    return subprocess.check_output(command, text=True)


def main():
    originals = {path: Path(path).read_text() for path in PACKAGES}
    version = latest_release(download(GNU))
    current = package_version(originals[FORMULA], FORMULA)
    if version_tuple(version) < version_tuple(current):
        raise ValueError("GNU's index is older than the installed tap metadata")
    if version == current:
        # Also validate the matching cask/checksum even when no build is needed.
        update_packages(originals, current, one(CHECKSUM, originals[FORMULA]))
        print(f"Emacs {current} is current; no compilation needed")
        return
    with tempfile.TemporaryDirectory(prefix="emacs-upstream-") as directory:
        archive = Path(directory) / f"emacs-{version}.tar.xz"
        download(f"{GNU}{archive.name}", archive)
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
    updated = update_packages(originals, version, digest)
    for path, content in updated.items():
        Path(path).write_text(content)
    print(f"Prepared official GNU Emacs {version}; both Linux bottles must pass before publication")


if __name__ == "__main__":
    main()

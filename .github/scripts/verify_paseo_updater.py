"""Require the installed release to disable its updater outside AppImage."""

import os
import subprocess
from pathlib import Path


def main():
    prefix = Path(os.environ.get("HOMEBREW_PREFIX") or subprocess.check_output(
        ["brew", "--prefix"], text=True).strip())
    version = os.environ["PASEO_EXPECTED_VERSION"]
    caskroom = prefix / "Caskroom" / "paseo-linux" / version
    archives = list(caskroom.rglob("app.asar"))
    if len(archives) != 1:
        raise RuntimeError(f"Expected one installed app.asar under {caskroom}, got {len(archives)}")
    archive = archives[0].read_bytes()
    guard = b'process.env["APPIMAGE"] == null && !this.forceDevUpdateConfig'
    guard_start = archive.find(guard)
    if guard_start < 0 or b"return false;" not in archive[guard_start:guard_start + 600]:
        raise RuntimeError("Paseo no longer disables electron-updater outside AppImage")
    integration = b"isAppImage: Boolean(process.env.APPIMAGE)"
    if integration not in archive:
        raise RuntimeError("Paseo updater no longer gates app-update behavior on APPIMAGE")
    print(f"Paseo {version} disables its bundled updater outside AppImage")


if __name__ == "__main__":
    main()

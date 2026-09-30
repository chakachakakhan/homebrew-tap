# Linux desktop packaging practices

Checked on 29 September 2026. This is a small comparison of actual recipes,
not a survey of every Linux tap. Older repositories are useful historical
examples, but their old versions are not evidence of current compatibility.

| Tap | Observed practice | Implication for this tap |
| --- | --- | --- |
| [athrunsun/homebrew-linuxbinary](https://github.com/athrunsun/homebrew-linuxbinary/blob/master/Formula/calibre.rb) | Calibre downloads a prebuilt archive, installs it into `libexec`, and links its executable through a formula. The repository last received a push in October 2022. | Binary formulae were a practical workaround; this old recipe provides little desktop integration and is not our maintenance model. |
| [Seryiza/homebrew-linuxtap](https://github.com/Seryiza/homebrew-linuxtap/blob/main/Formula/kitty-binary.rb) | Kitty uses a prebuilt archive, `libexec`, and a linked command. The repository last received a push in April 2022. | Confirms the same historical approach in a small personal tap. |
| [castrojo/homebrew-tap](https://github.com/castrojo/homebrew-tap/blob/main/Casks/lm-studio-linux.rb) | This personal fork of Universal Blue extracts LM Studio’s AppImage and registers its launcher and icon. Its snapshot uses legacy Ruby flight blocks and a version that trails the parent tap. | AppImage extraction is used in practice, but a fork can lag and its implementation should not be copied uncritically. |
| [ublue-os/homebrew-tap](https://github.com/ublue-os/homebrew-tap/blob/main/Casks/lm-studio-linux.rb) | LM Studio uses an extracted AppImage, a command, and desktop artifacts; the current recipe uses structured `preflight_steps`. Its [bump workflow](https://github.com/ublue-os/homebrew-tap/blob/main/.github/workflows/bump.yml) runs Homebrew’s `brew bump` to open PRs. | A useful current Linux desktop reference. Extraction avoids FUSE; managed artifacts give Homebrew install/uninstall ownership. |
| [Homebrew’s Tabby cask](https://github.com/Homebrew/homebrew-cask/blob/main/Casks/t/tabby.rb) | The official cross-platform cask uses the native Linux `app_image` artifact. | Installing an intact AppImage is also a valid current option. It does not by itself add the command and desktop artifacts we want here. |

## Thorium Reader choice

Use EDRLab’s [official stable AppImages](https://github.com/edrlab/thorium-reader/releases/latest)
for Intel and ARM. Extract them in the cask preflight, then register the upstream
`AppRun` launcher, desktop file, and icon using managed artifacts. The runtime
can extract itself, so this recipe does not add an unused `squashfs` dependency.
The original archive is removed from staging after extraction.

The desktop entry points at `thorium-reader` and retains upstream MIME and OPDS
associations. That command name avoids the Thorium browser, which is separately
packaged as [thorium-linux in Universal Blue’s experimental tap](https://github.com/ublue-os/homebrew-experimental-tap/blob/main/Casks/thorium-linux.rb).

Use current structured flight steps as described in the
[Cask Cookbook](https://docs.brew.sh/Cask-Cookbook#stanza-preflight_steps-postflight_steps-uninstall_preflight_steps-uninstall_postflight_steps).
No system package maintainer scripts, privileged system paths, or manual copies
outside Homebrew’s artifact lifecycle are necessary.

The upstream AppRun probes user namespaces and conditionally adds
`--no-sandbox`. The tap retains that behavior, while removing the unconditional
flag from the upstream desktop entry so menu launches use the same AppRun
decision as terminal launches. This is a native application installation; it
does not provide Flatpak’s application sandbox or permission portals.

## Updates and verification

Keep versioned download URLs and SHA-256 verification. Follow stable releases,
wait for complete architecture assets, and validate actual installation and
uninstall behavior. A GUI window check exercises Thorium’s installed launcher
on both architectures. The tap is kept current automatically; local application
upgrades still use `brew update` and `brew upgrade --cask`.

The existing ChatGPT PR workflow provides a narrower update policy than a
general `brew bump` automation: only the branch’s assigned cask, only numeric
version and checksum fields, only an increased version, and only the exact
revision that passed validation. Reuse that policy for Thorium rather than
introducing another access token or mirroring its binaries.

The examples support this approach without making third-party practices an
automatic endorsement. Keep Homebrew’s audit/style checks and actual runtime
checks together: either alone would miss useful failures.

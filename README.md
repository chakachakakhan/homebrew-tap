# Desktop apps for Linux, through Homebrew

[![Installation checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml)
[![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml)

My personal Homebrew tap for ChatGPT and EDRLab's Thorium Reader on Linux.
I made it after the ChatGPT tap I was using stopped getting updates, and wanted
something small that I could keep up to date myself.

This is an unofficial tap, maintained independently of OpenAI, EDRLab, and
Homebrew. Apps are downloaded directly from their publishers; this repo contains
the casks and their update automation.

## Install

You'll need Homebrew on Linux. Both casks support Intel/AMD (`x86_64`) and ARM
(`arm64`); installation checks run on Ubuntu 24.04 for both architectures.

```sh
brew install --cask chakachakakhan/tap/chatgpt-linux
brew install --cask chakachakakhan/tap/thorium-reader-linux
```

Install either app or both. ChatGPT installs the `chatgpt` command, desktop
launcher, icon, and app metadata. Homebrew installs `dpkg` to extract its official
Debian package.

Thorium Reader installs the `thorium-reader` command, desktop launcher, and icon.
The cask extracts the official AppImage into Homebrew’s Caskroom, so launching
does not require FUSE, root access, or a Debian package installation. It preserves
the upstream ebook and OPDS link associations. It is distinct from the Thorium
web browser.

These are native desktop installations, with no Flatpak sandbox or permission
portal. Thorium’s upstream launcher uses Electron’s sandbox when user namespaces
are available and falls back to `--no-sandbox` when they are unavailable.

## Update

```sh
brew update
brew upgrade --cask chakachakakhan/tap/chatgpt-linux
brew upgrade --cask chakachakakhan/tap/thorium-reader-linux
```

The automation keeps the cask current. You still run Homebrew to update the
app on your machine.

## How updates work

- Check OpenAI’s stable package indexes and EDRLab’s latest stable GitHub
  release every six hours.
- Require complete Intel and ARM packages, then open a separate update PR for
  each app with its version and SHA-256 checksums. Thorium skips beta, nightly,
  and draft releases, and uses GitHub’s official release-asset digests.
- Test installation, desktop integration, and uninstall cleanup on both
  architectures before merging automatically. Thorium also opens a real window
  under a virtual display.

Automatic merges are limited to version and checksum changes from the updater
bot. Changes to installation behavior or workflows need manual review.
Temporary failures are retried, and a monthly keepalive prevents the scheduled
checks from stopping during quiet release periods.

You can follow the [update PRs](https://github.com/chakachakakhan/homebrew-tap/pulls)
or check the [latest workflow runs](https://github.com/chakachakakhan/homebrew-tap/actions).

## Projects and settings

Normal upgrades and uninstalls preserve your app data, including Thorium’s
book library in `~/.config/EDRLab.ThoriumReader` (or the corresponding directory
under a custom `XDG_CONFIG_HOME`). Moving from the
`ublue/experimental-tap` cask preserved my projects and settings, though that
is my experience rather than a guarantee for every setup.

```sh
brew uninstall --cask chakachakakhan/tap/chatgpt-linux
brew uninstall --cask chakachakakhan/tap/thorium-reader-linux
```

Adding `--zap` removes the data directories listed in the selected cask. For
Thorium this includes its default book library and configuration. For ChatGPT
it includes ChatGPT and Codex configuration and caches. Use it only if you want
to clear those too; custom data locations are not included in the zap list.

## Something broken?

[Open an issue](https://github.com/chakachakakhan/homebrew-tap/issues/new) with
your Linux distribution, CPU architecture, and the Homebrew error. Please
leave out tokens and private app data. Problems with the app itself belong
with their publisher; installation and tap update problems belong here.

For the details of the automation and how to pause it, see
[maintenance notes](docs/maintenance.md).

For the Linux tap comparison and packaging choices, see
[Linux packaging practices](docs/linux-packaging.md).

# ChatGPT for Linux, through Homebrew

[![Installation checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml)
[![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml)

My personal Homebrew tap for OpenAI's ChatGPT desktop app on Linux. I made it
after the tap I was using stopped getting updates, and wanted something small
that I could keep up to date myself.

This is an unofficial tap, maintained independently of OpenAI and Homebrew.
The app is downloaded directly from OpenAI; this repo contains the cask and
its update automation.

## Install

You'll need Homebrew on Linux. The cask supports Intel/AMD (`x86_64`) and ARM
(`arm64`); installation checks run on Ubuntu 24.04 for both architectures.

```sh
brew install --cask chakachakakhan/tap/chatgpt-linux
```

The cask installs the `chatgpt` command and a desktop launcher, along with its
icon and app metadata. Homebrew also installs `dpkg` to extract the official
Debian package.

## Update

```sh
brew update
brew upgrade --cask chakachakakhan/tap/chatgpt-linux
```

The automation keeps the cask current. You still run Homebrew to update the
app on your machine.

## How updates work

- Check OpenAI's stable package indexes every six hours.
- Wait for matching Intel and ARM versions, then open an update PR with the
  version and SHA-256 checksums.
- Test installation, desktop integration, and uninstall cleanup on both
  architectures before merging automatically.

Automatic merges are limited to version and checksum changes from the updater
bot. Changes to installation behavior or workflows need manual review.
Temporary failures are retried, and a monthly keepalive prevents the scheduled
checks from stopping during quiet release periods.

You can follow the [update PRs](https://github.com/chakachakakhan/homebrew-tap/pulls?q=is%3Apr+head%3Aautomation%2Fupdate-chatgpt)
or check the [latest workflow runs](https://github.com/chakachakakhan/homebrew-tap/actions).

## Projects and settings

Normal upgrades and uninstalls preserve your app data. Moving from the
`ublue/experimental-tap` cask preserved my projects and settings, though that
is my experience rather than a guarantee for every setup.

```sh
brew uninstall --cask chakachakakhan/tap/chatgpt-linux
```

Adding `--zap` also removes the ChatGPT and Codex data directories listed in
the cask, including local configuration and caches. Use it only if you want
to clear those too.

## Something broken?

[Open an issue](https://github.com/chakachakakhan/homebrew-tap/issues/new) with
your Linux distribution, CPU architecture, and the Homebrew error. Please
leave out tokens and private app data. Problems with the app itself belong
with OpenAI; installation and tap update problems belong here.

For the details of the automation and how to pause it, see
[maintenance notes](docs/maintenance.md).

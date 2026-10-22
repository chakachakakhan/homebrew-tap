# My Homebrew tap

[![Install checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml) [![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml) [![Thorium](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml)

[![OpenCodex](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml) [![OMP Desktop](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml) [![Emacs](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-emacs.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-emacs.yml)

Hey, this is my personal tap for a few Linux apps I use. No warranty; packages come from their publishers.

| Package | Install | Linux |
| --- | --- | --- |
| ChatGPT | `brew install --cask chakachakakhan/tap/chatgpt-linux` | x86_64, ARM64 |
| Thorium Reader | `brew install --cask chakachakakhan/tap/thorium-reader-linux` | x86_64, ARM64 |
| OpenCodex desktop | `brew install --cask chakachakakhan/tap/opencodex` | x86_64 |
| OpenCodex CLI | `brew install --formula chakachakakhan/tap/opencodex` | x86_64, ARM64 |
| OMP Desktop | `brew install --cask chakachakakhan/tap/omp-desktop` | x86_64 |
| Emacs desktop integration | `brew install --cask chakachakakhan/tap/emacs-pgtk-linux` | x86_64, ARM64 |
| Emacs formula | `brew install --formula chakachakakhan/tap/emacs` | x86_64, ARM64 |

Launch ChatGPT with `chatgpt`, Thorium Reader with `thorium-reader`, and OpenCodex desktop with `opencodex-desktop`. The OpenCodex CLI provides `ocx` and `opencodex`; its dashboard is at `http://localhost:10100`. OMP Desktop needs the separate `omp` engine: install it with `brew install can1357/tap/omp` or use an existing upstream install, then run `omp-desktop /path/to/project`. Emacs's formula provides `emacs`, `emacsclient`, and the optional daemon; the cask adds desktop entries and an icon.

The fully qualified install names let Homebrew trust only the selected package. See [Tap Trust](https://docs.brew.sh/Tap-Trust) before trusting the whole tap.

## Updates and removal

Run `brew update && brew upgrade` to update installed packages. Ordinary uninstall keeps user data. `--zap` removes the cask's listed data: ChatGPT and Codex settings/caches; OpenCodex's `~/.opencodex` (also used by its CLI); OMP Desktop settings, but not the engine's `~/.omp` data; and Thorium Reader's `~/.config/EDRLab.ThoriumReader`, which includes its default library and settings. Check that Thorium folder before using `--zap`.

Emacs's service is optional: `brew services start chakachakakhan/tap/emacs`, then `emacsclient -c` or `emacsclient -t`. Uninstall the cask and formula separately to remove the desktop integration and Emacs itself.

See [maintenance notes](docs/maintenance.md) for update automation and checks.

## Paseo

Paseo is a desktop app and CLI for managing AI coding agents. The cask supports
Linux on x86_64 and installs `paseo-desktop`, `paseo`, an application-menu
entry, and the `paseo://` URL handler.

```sh
brew install --cask chakachakakhan/tap/paseo-linux
```

Updates come through Homebrew:

```sh
brew upgrade --cask chakachakakhan/tap/paseo-linux
```

Uninstalling the cask preserves `~/.paseo`, including agents, worktrees, and
configuration.

```sh
brew uninstall --cask chakachakakhan/tap/paseo-linux
```

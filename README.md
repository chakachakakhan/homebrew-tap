# My Homebrew tap

[![Install checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml) [![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml) [![Thorium](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml)

[![OpenCodex](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml) [![OMP Desktop](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml) [![Emacs](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-emacs.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-emacs.yml)

A personal tap for Linux apps I use.

| Package | Install | Architecture |
| --- | --- | --- |
| ChatGPT | `brew install --cask chakachakakhan/tap/chatgpt-linux` | x86_64, ARM64 |
| Thorium Reader | `brew install --cask chakachakakhan/tap/thorium-reader-linux` | x86_64, ARM64 |
| OpenCodex desktop | `brew install --cask chakachakakhan/tap/opencodex` | x86_64 |
| OpenCodex CLI | `brew install --formula chakachakakhan/tap/opencodex` | x86_64, ARM64 |
| OMP Desktop | `brew install --cask chakachakakhan/tap/omp-desktop` | x86_64 |
| Paseo | `brew install --cask chakachakakhan/tap/paseo-linux` | x86_64 |
| Emacs + desktop entries | `brew install --cask chakachakakhan/tap/emacs-pgtk-linux` | x86_64, ARM64 |
| Emacs only | `brew install --formula chakachakakhan/tap/emacs` | x86_64, ARM64 |

Update with `brew update && brew upgrade`. Remove a package with `brew uninstall`.

See [notes](docs/maintenance.md) for launch commands, package quirks, and maintenance.

# Tap notes

## Using the apps

| App | Notes |
| --- | --- |
| ChatGPT | Launch with `chatgpt`. |
| Thorium Reader | Launch with `thorium-reader`. `--zap` deletes the default library and settings in `~/.config/EDRLab.ThoriumReader`. |
| OpenCodex | Desktop: `opencodex-desktop`. CLI: `ocx` or `opencodex`; dashboard: `http://localhost:10100`. The cask's `--zap` also removes `~/.opencodex`, shared with the CLI. |
| OMP Desktop | Needs the engine: `brew install can1357/tap/omp`. Launch with `omp-desktop /path/to/project`. |
| Paseo | Desktop: `paseo-desktop`. CLI: `paseo`. Uninstall keeps `~/.paseo`. |
| Emacs | PGTK/Wayland, native compilation, tree-sitter. The cask installs the formula plus menu entries. Remove the cask and formula separately; Emacs and Doom settings are preserved. |

Optional Emacs daemon: `brew services start chakachakakhan/tap/emacs`, then `emacsclient -c` (window) or `emacsclient -t` (terminal).

Ordinary uninstall keeps user data. Use `--zap` only when you want the cask's listed settings and data removed.

## Maintaining the tap

App updates check every six hours; Emacs checks stable releases on GNU's kernel.org mirror daily. Validated updates publish automatically. Disable the relevant merge/publish workflow to pause them.

Emacs builds and tests x86_64 and ARM64 bottles before publication with `brew pr-pull`. For the first release or a packaging fix, run **Publish tested Emacs bottles** with the PR number and exact head SHA after **Validate Emacs** passes. Publication then checks the installed bottles on `main`.

Recipes live in `Casks/` and `Formula/`; checks and updaters live in `.github/`. Local checks:

```sh
brew style Formula/*.rb Casks/*.rb
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```

GitHub's **Validate tap syntax and automation policy** checks the branch; package workflows test installs.

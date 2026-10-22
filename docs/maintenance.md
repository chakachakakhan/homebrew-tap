# Maintenance notes

Recipes are in `Casks/` and `Formula/`; automation and tests are in `.github/workflows/` and `.github/scripts/`.

## Updates

ChatGPT, Thorium Reader, OpenCodex, OMP Desktop, and Paseo check for releases every six hours. Emacs checks GNU's stable source index daily. Updaters verify upstream version and checksums, then open pull requests for expected metadata changes. OpenCodex updates its desktop cask and CLI formula together.

Updaters explicitly dispatch validation and publication with `GITHUB_TOKEN`, so routine updates do not depend on approving workflows for bot-created pull requests. Those workflows verify the exact pull request revision. The ChatGPT updater also refreshes `automation/keepalive` monthly so GitHub does not suspend scheduled checks during quiet periods. See [GitHub's `GITHUB_TOKEN` documentation](https://docs.github.com/en/actions/concepts/security/github_token).

Emacs builds from GNU source. Its workflow builds and validates Linux x86_64 and ARM64 bottles, then publishes the tested revision with Homebrew's `brew pr-pull`. To publish an initial bottle or a reviewed packaging correction, dispatch **Publish tested Emacs bottles** with the pull request number and exact validated head SHA. Publication requires a successful validation run for that revision. Unrelated tap updates do not require rebuilding; changes to the Emacs recipes or validation workflow do.

Disable **Merge validated cask update**, **Merge validated OpenCodex update**, **Merge validated OMP Desktop update**, or **Merge validated Paseo update** to pause those automatic merges. Disable **Publish tested Emacs bottles** to pause Emacs bottle publication.

## Checks

**Validate tap** runs `brew readall`, `brew style`, and the Python policy tests for the whole tap. Package workflows also run audits and install/launch checks; the Emacs workflow builds and tests bottles. For local Python checks:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v
```

`brew readall` examines Homebrew's installed tap; use **Validate tap** for this branch. Local `brew style Formula/*.rb Casks/*.rb` and the Python tests inspect this checkout. Package-specific validation is documented in the corresponding workflow under `.github/workflows/`.

## Packaging references

Homebrew supports Linux casks when their artifact types support Linux. This personal tap also packages upstream binaries and smaller projects; its extraction and desktop integration choices follow examples such as UBlue's Linux casks, while official core acceptance policies remain Homebrew's own.

- Homebrew: [How to Create and Maintain a Tap](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap), [Cask Cookbook](https://docs.brew.sh/Cask-Cookbook), [Formula Cookbook](https://docs.brew.sh/Formula-Cookbook), [Acceptable Casks](https://docs.brew.sh/Acceptable-Casks), and [Tap Trust](https://docs.brew.sh/Tap-Trust).
- Linux cask examples from Universal Blue: [Visual Studio Code](https://github.com/ublue-os/homebrew-tap/blob/main/Casks/visual-studio-code-linux.rb), [LM Studio](https://github.com/ublue-os/homebrew-tap/blob/main/Casks/lm-studio-linux.rb), and their [tests workflow](https://github.com/ublue-os/homebrew-tap/blob/main/.github/workflows/tests.yml).

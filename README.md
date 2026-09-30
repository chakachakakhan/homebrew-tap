# ChatGPT Linux Homebrew tap

Install OpenAI's official Linux desktop app with:

```sh
brew install --cask chakachakakhan/tap/chatgpt-linux
```

## Updates

The updater checks OpenAI's official stable Debian indexes every six hours. It
waits for matching Intel and ARM versions, rejects downgrades, and opens one
update PR with the new version and SHA-256 checksums. The repository owner is
requested as a reviewer, which uses GitHub's participating notification settings.

Validation runs explicitly on the update branch, including real installation,
desktop integration, and uninstall checks on Intel and ARM Linux runners.
Unchanged open PRs are rechecked so temporary download or runner failures recover.

After successful validation, a separate workflow from the trusted default branch
merges the exact tested commit. It accepts only a bot-authored PR from this tap,
with one existing cask changed and only its version and checksum fields modified.
The version must increase. Same-version package rebuilds, application integration
changes, and workflow changes need manual review. Stale validation cannot merge
a newer revision; an update must also include the current main branch.

A monthly empty commit on `automation/keepalive` prevents GitHub from disabling
scheduled workflows after 60 days of repository inactivity. It does not change
the cask or main branch. The updater and merger share a concurrency group.

Enable Email for participating notifications and failed Actions workflows in
[GitHub notification settings](https://github.com/settings/notifications).
There is no separate mail service or expiring personal access token in the updater.
To pause automatic merging, disable **Merge validated ChatGPT update** in Actions;
release checks and PR creation can continue.

## Updating your installed app

Updating this tap makes a release available to Homebrew. Install it locally with:

```sh
brew update
brew upgrade --cask chakachakakhan/tap/chatgpt-linux
```

Normal upgrades and uninstalls preserve app projects and settings. Explicitly
uninstalling with `--zap` removes the app data directories listed in the cask.

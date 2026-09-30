# Maintenance notes

## Release checks and validation

The updater reads OpenAI's official stable Debian indexes every six hours. It
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

The policy tests cover successful updates and rejected changes, including stale
revisions, failed checks, forks, malformed metadata, and changes to app behavior.
Run them locally with:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v
```

## Scheduling and notifications

A monthly empty commit on `automation/keepalive` prevents GitHub from disabling
scheduled workflows after 60 days of repository inactivity. It does not change
the cask or main branch. The updater and merger share a concurrency group.

Enable Email for participating notifications and failed Actions workflows in
[GitHub notification settings](https://github.com/settings/notifications).
There is no separate mail service or expiring personal access token in the updater.
To pause automatic merging, disable **Merge validated ChatGPT update** in Actions;
release checks and PR creation can continue.

## Versions, releases, and packages

This tap keeps one cask for the current stable ChatGPT version. Each upstream
update changes that cask in a PR; the merged PR and Git history record the update.
Homebrew reads the tap's Git repository, so publishing a GitHub Release is not
required to make an update available.

GitHub Packages is not used. App binaries stay on OpenAI's servers. GitHub
Releases could be added later for release announcements and tagged snapshots of
the cask, with notes clearly identifying them as tap updates. They would not
need copies of the app or a separate release workflow to keep Homebrew working.

References: [Homebrew tap maintenance](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap),
[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
and [GitHub Packages](https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages).

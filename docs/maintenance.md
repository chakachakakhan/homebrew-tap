# Maintenance notes

## Packaging choices

ChatGPT extracts the official Debian package without running distro maintainer
scripts. Thorium Reader extracts the official AppImage so launching does not
require FUSE. Both casks register commands and desktop files as Homebrew-managed
artifacts, which handles removal during upgrades and uninstalls. Ordinary
uninstall preserves application data; `--zap` removes the listed data directories.

## Release checks and validation

The ChatGPT updater reads OpenAI's official stable Debian indexes every six hours.
It waits for matching Intel and ARM versions, rejects downgrades, and opens one
update PR with the new version and SHA-256 checksums. ChatGPT PRs mention the
repository owner as an email notification, without requesting review or approval.

The Thorium updater checks EDRLab’s latest stable GitHub release every six hours.
It rejects draft and prerelease tags, downgrades, incomplete or duplicate
architecture assets, unexpected download origins, and missing SHA-256 digests.
Only the version and both architecture checksums are changed. Same-version
rebuilds need manual review.

Validation runs explicitly on the update branch, including real installation,
desktop integration, and uninstall checks on Intel and ARM Linux runners.
Thorium additionally opens a GUI window using Xvfb with isolated app data, and
its uninstall check confirms that the user’s book library is preserved.
Unchanged open PRs are rechecked so temporary download or runner failures recover.

The ChatGPT updater explicitly dispatches the merger on the default branch with
the validation run ID. It waits for that run to finish, then applies the same
checks as the workflow-run handoff. This avoids GitHub suppressing follow-up
events from bot-triggered validation runs.

After successful validation, a separate workflow from the trusted default branch
merges the exact tested commit. It accepts only a bot-authored PR from this tap,
on `automation/update-chatgpt` or `automation/update-thorium-reader`,
with only the existing cask assigned to that branch changed and only its version
and checksum fields modified.
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
the cask or main branch. Both updaters and the merger share a concurrency group
to avoid overlapping
branch updates and merges. The ChatGPT workflow maintains the shared keepalive
branch; if it is disabled, keepalive must be moved to the remaining updater.

Enable Email for participating notifications and failed Actions workflows in
[GitHub notification settings](https://github.com/settings/notifications).
There is no separate mail service or expiring personal access token in the updater.
To pause automatic merging, disable **Merge validated cask update** in Actions;
release checks and PR creation can continue.

## Versions, releases, and packages

This tap keeps one cask for each app’s current stable version. Each upstream
update changes that cask in a PR; the merged PR and Git history record the update.
Homebrew reads the tap's Git repository, so publishing a GitHub Release is not
required to make an update available.

GitHub Packages is not used. App binaries stay at their upstream origins:
OpenAI’s package server for ChatGPT and EDRLab’s GitHub Releases for Thorium.
All tap validation and release checks
run on GitHub-hosted Ubuntu Intel and ARM runners. No tap-side application
compilation or binary mirroring is needed. GitHub
Releases could be added later for release announcements and tagged snapshots of
the cask, with notes clearly identifying them as tap updates. They would not
need copies of the app or a separate release workflow to keep Homebrew working.

References: [Homebrew tap maintenance](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap),
[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
and [GitHub Packages](https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages).

## OpenCodex

`Formula/opencodex.rb` installs the publisher's standalone Bun runtime, dashboard,
and native keyring addon together in libexec. It exposes `ocx` and `opencodex`.
`Casks/opencodex.rb` installs the universal macOS DMG or extracts the Linux
x86_64 AppImage, preserving AppRun and its bundled libraries and sidecar. There is
one AppRun path correction so it resolves its own executable before its parent
directory when invoked through Homebrew's symlink. Extraction fails if upstream
changes that launcher line, requiring a reviewed packaging adjustment.
There is
no Linux ARM desktop asset upstream. Downloads stay on lidge-jun/opencodex Releases.

The separate **Update OpenCodex packages** workflow checks every six hours. It
accepts only a complete stable release with all six expected assets, exact origin
URLs, and GitHub's SHA-256 digests. Both packages advance to the same version.
The existing ChatGPT keepalive also keeps this schedule active.

**Validate OpenCodex** installs and tests the CLI, proxy health, and dashboard
assets on Ubuntu x86_64/ARM and macOS Apple Silicon/Intel. It installs the desktop
where available, checks a Linux desktop window and bundled runtime under Xvfb,
verifies the macOS app signature and bundled CLI, and verifies ordinary uninstall
preserves settings. A macOS GUI window is not exercised by these hosted checks.

The updater explicitly dispatches validation and **Merge validated OpenCodex
update** using the validation run ID. The trusted main-branch merger requires
all five jobs to pass on the exact current PR head, a same-repository bot PR that
includes current main, and only higher versions/checksums in the two existing
recipes. Code, URL, architecture, or installation changes cannot merge under
that policy. Same-version rebuilds are rejected. All updaters and mergers use
the existing shared concurrency group. Disable the OpenCodex merger to pause
its automatic merges without affecting the other apps.

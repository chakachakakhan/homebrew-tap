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
`Casks/opencodex.rb` extracts the Linux x86_64 AppImage, preserving AppRun and its
bundled libraries and sidecar. Both packages require Linux. There is
one AppRun path correction so it resolves its own executable before its parent
directory when invoked through Homebrew's symlink. Extraction fails if upstream
changes that launcher line, requiring a reviewed packaging adjustment.
There is no Linux ARM desktop asset upstream. Downloads stay on lidge-jun/opencodex Releases.

The separate **Update OpenCodex packages** workflow checks every six hours. It
accepts only a stable release with all three expected Linux assets, exact origin
URLs, and GitHub's SHA-256 digests. Both packages advance to the same version.
The existing ChatGPT keepalive also keeps this schedule active.

**Validate OpenCodex** installs and tests the CLI, proxy health, and dashboard
assets on Ubuntu x86_64/ARM. It installs the desktop on x86_64, checks its window
and bundled runtime under Xvfb, and verifies ordinary uninstall preserves settings.

The updater explicitly dispatches validation and **Merge validated OpenCodex
update** using the validation run ID. The trusted main-branch merger requires
all three jobs to pass on the exact current PR head, a same-repository bot PR that
includes current main, and only higher versions/checksums in the two existing
recipes. Code, URL, architecture, or installation changes cannot merge under
that policy. Same-version rebuilds are rejected. All updaters and mergers use
the existing shared concurrency group. Disable the OpenCodex merger to pause
its automatic merges without affecting the other apps.

## OMP Desktop

`Casks/omp-desktop.rb` installs apoc's official Linux x86_64 AppImage after
extraction, keeping its GTK setup and bundled libraries together without
FUSE. The generic AppImage shim's PYTHONHOME and PYTHONPATH keys are replaced
with unused, equally sized APP_PYHOME and APP_PYPATH keys. This retains its
GTK/WebKit library paths and working directory while preventing it from pointing
external Python tools at a nonexistent bundled runtime. CI checks these keys
and uses a normal system-Python RPC proxy to catch environment contamination.
The Homebrew command adds the actual Homebrew prefix to PATH before
running AppRun by its full path; desktop-menu launches can therefore find the
separately installed `omp` from `can1357/tap`.

Tauri's fixed-width `__TAURI_BUNDLE_TYPE_VAR_APP` marker is replaced with
`__TAURI_BUNDLE_TYPE_VAR_UNK` in the extracted executable. This switches the
upstream updater to its existing notify-only path, so it cannot overwrite a
Homebrew-managed payload. The replacement is audited and fails if the marker
changes upstream. This is a packaging adjustment, not an application rebuild.
The recipe registers a command, folder-aware desktop entry, and icon.

The strict Homebrew audit excludes only `github_repository` and
`token_bad_words`: this personal tap accepts the small upstream project and
uses its desktop name to distinguish the separately installed OMP engine.
The remaining recipe and artifact audits still run.

`--zap` targets only `dev.ohMyPi.desktop` application data. It deliberately
does not target `~/.omp`, shared credentials, saved sessions, or named profiles.

The separate updater checks stable releases every six hours and also checks
after this package's setup changes on main. It requires one complete Linux
AppImage at the exact upstream origin with a GitHub SHA-256 digest. Drafts,
prereleases, downgrades, malformed metadata, and same-version rebuilds are
rejected. A bot update can change only the existing cask's version and checksum.

Validation installs the current upstream Homebrew OMP, checks the desktop
integration and notify-only marker, then opens the GUI under Xvfb with a minimal
launcher PATH. A transparent test proxy observes a successful RPC get_state
response from the real OMP engine; it sends no model prompt and uses no provider
credentials. Ordinary uninstall must remove the desktop artifacts while
preserving both desktop settings and OMP data.

The updater explicitly dispatches validation and the trusted main-branch merger.
Only both required jobs passing at the current PR head, a same-repository bot PR,
an unchanged current main base, and a strictly newer metadata-only cask change
permit automatic merging. It shares the existing update concurrency group and
keepalive. Disable **Merge validated OMP Desktop update** to pause its automatic
merges without changing other apps.

import re
import unittest
from pathlib import Path

from update_emacs import (
    CASK, FORMULA, PACKAGES, latest_release, metadata_only, package_version, update_packages,
)


class EmacsUpdateTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.before = {path: (root / path).read_text() for path in PACKAGES}
        self.old = package_version(self.before[FORMULA], FORMULA)
        self.new = f"{int(self.old.split('.')[0]) + 1}.1"
        self.digest = "a" * 64

    def test_stable_source_index_excludes_prereleases_and_other_downloads(self):
        index = '''<a href="emacs-30.2.tar.xz">a</a>
        <a href="emacs-31.1.tar.xz">b</a><a href="emacs-32.0.90.tar.xz">c</a>
        <a href="emacs-33.0.50.tar.xz">d</a><a href="emacs-31.2.tar.xz.sig">e</a>
        <a href="https://example.com/emacs-99.1.tar.xz">f</a>'''
        self.assertEqual(latest_release(index), "31.1")
        with self.assertRaises(ValueError):
            latest_release('<a href="emacs-32.0.90.tar.xz">a</a>')

    def test_both_sources_advance_together_and_old_bottle_is_removed(self):
        self.before[FORMULA] = self.before[FORMULA].replace("  livecheck do", '''  bottle do
    root_url "https://github.com/owner/tap/releases/download/old"
    sha256 x86_64_linux: "bottle-sha"
  end

  livecheck do''', 1)
        after = update_packages(self.before, self.new, self.digest)
        self.assertTrue(metadata_only(self.before, after))
        self.assertNotIn("bottle do", after[FORMULA])
        for path in PACKAGES:
            self.assertEqual(package_version(after[path], path), self.new)
            self.assertIn(self.digest, after[path])

    def test_no_change_preserves_published_bottle_metadata(self):
        digest = re.search(r'^  sha256 "([0-9a-f]{64})"', self.before[FORMULA], re.M)[1]
        self.assertEqual(update_packages(self.before, self.old, digest), self.before)
        self.assertFalse(metadata_only(self.before, self.before))

    def test_downgrade_snapshot_and_same_version_replacement_are_rejected(self):
        for version in ("1.1", "32.0.50", self.old):
            with self.subTest(version=version), self.assertRaises(ValueError):
                update_packages(self.before, version, self.digest)

    def test_behavior_and_bottle_code_cannot_publish_as_metadata(self):
        after = update_packages(self.before, self.new, self.digest)
        for path, change in ((FORMULA, '  system "untrusted"\n'),
                             (FORMULA, '  bottle do\n    system "untrusted"\n  end\n\n'),
                             (CASK, '  zap trash: "~/.config/emacs"\n')):
            candidate = after.copy()
            candidate[path] += change
            self.assertFalse(metadata_only(self.before, candidate))

    def test_mismatched_sources_checksums_and_malformed_fields_are_rejected(self):
        for changes in (
            {CASK: self.before[CASK].replace(f'version "{self.old}"', 'version "99.1"')},
            {CASK: re.sub(r'^  sha256 "[0-9a-f]{64}"', f'  sha256 "{self.digest}"',
                         self.before[CASK], flags=re.M)},
            {FORMULA: self.before[FORMULA].replace("ftpmirror.gnu.org", "example.com")},
            {FORMULA: self.before[FORMULA] + '\n  sha256 "' + self.digest + '"\n'},
        ):
            with self.assertRaises(ValueError):
                update_packages(self.before | changes, self.new, self.digest)


if __name__ == "__main__":
    unittest.main()

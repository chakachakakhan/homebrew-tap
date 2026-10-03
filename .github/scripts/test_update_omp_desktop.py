import copy
import re
import unittest
from pathlib import Path

from update_omp_desktop import ORIGIN, metadata_only, update_cask


class OMPDesktopUpdateTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.before = re.sub(r'^  version "[^"]+"$', '  version "1.0.0"',
                             (root / "Casks/omp-desktop.rb").read_text(), flags=re.MULTILINE)
        self.release = {
            "tag_name": "v1.0.1", "draft": False, "prerelease": False, "assets": [{
                "name": "OMP.Desktop_1.0.1_amd64.AppImage", "state": "uploaded",
                "size": 1024, "digest": "sha256:" + "a" * 64,
                "browser_download_url": f"{ORIGIN}/v1.0.1/OMP.Desktop_1.0.1_amd64.AppImage",
            }],
        }

    def test_complete_release_changes_only_version_and_checksum(self):
        after = update_cask(self.before, self.release)
        self.assertIn('version "1.0.1"', after)
        self.assertIn('sha256 "' + "a" * 64 + '"', after)
        self.assertTrue(metadata_only(self.before, after))

    def test_current_release_is_a_noop(self):
        after = update_cask(self.before, self.release)
        self.assertEqual(after, update_cask(after, self.release))

    def test_republished_checksum_requires_review(self):
        after = update_cask(self.before, self.release)
        self.release["assets"][0]["digest"] = "sha256:" + "b" * 64
        with self.assertRaises(ValueError):
            update_cask(after, self.release)

    def test_draft_prerelease_bad_tag_and_downgrade_are_rejected(self):
        for field, value in (("draft", True), ("prerelease", True),
                             ("tag_name", "v0.9.0"), ("tag_name", "v1.1.0-rc1"),
                             ("tag_name", "1.1.0")):
            release = copy.deepcopy(self.release)
            release[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                update_cask(self.before, release)

    def test_missing_duplicate_or_incomplete_asset_is_rejected(self):
        for assets in ([], self.release["assets"] * 2):
            release = copy.deepcopy(self.release)
            release["assets"] = assets
            with self.assertRaises(ValueError):
                update_cask(self.before, release)
        for field, value in (("state", "new"), ("size", 0), ("digest", None),
                             ("digest", "sha256:bad"),
                             ("browser_download_url", "https://attacker.invalid/desktop")):
            release = copy.deepcopy(self.release)
            release["assets"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                update_cask(self.before, release)

    def test_executable_launcher_url_or_marker_changes_are_not_metadata(self):
        after = update_cask(self.before, self.release)
        for altered in (after + '\nsystem "unexpected"\n',
                        after.replace("apoc/omp-desktop", "attacker/omp-desktop"),
                        after.replace("__TAURI_BUNDLE_TYPE_VAR_UNK", "__TAURI_BUNDLE_TYPE_VAR_APP"),
                        after.replace('exec "{{staged_path}}', 'exec "/tmp/untrusted')):
            self.assertFalse(metadata_only(self.before, altered))

    def test_unchanged_downgraded_or_duplicate_metadata_is_rejected(self):
        after = update_cask(self.before, self.release)
        for altered in (self.before, after.replace('version "1.0.1"', 'version "0.9.0"'),
                        after + '  version "2.0.0"\n',
                        after + '  sha256 "' + "b" * 64 + '"\n',
                        after.replace('sha256 "' + "a" * 64 + '"', 'sha256 "bad"')):
            self.assertFalse(metadata_only(self.before, altered))

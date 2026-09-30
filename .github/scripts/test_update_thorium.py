import copy
import re
import unittest
from pathlib import Path

from update_thorium import ORIGIN, update_cask


class ThoriumUpdateTests(unittest.TestCase):
    def setUp(self):
        self.original = (Path(__file__).resolve().parents[2] / "Casks/thorium-reader-linux.rb").read_text()
        self.original = re.sub(r'^  version "[^\"]+"$', '  version "1.0.0"',
                               self.original, flags=re.MULTILINE)
        self.release = {
            "tag_name": "v1.0.1", "draft": False, "prerelease": False,
            "assets": [
                {"name": f"Thorium-1.0.1-{arch}.AppImage",
                 "browser_download_url": f"{ORIGIN}/v1.0.1/Thorium-1.0.1-{arch}.AppImage",
                 "digest": "sha256:" + digit * 64, "state": "uploaded", "size": 123}
                for arch, digit in (("arm64", "a"), ("x86_64", "b"))
            ],
        }

    def test_complete_stable_release_changes_only_metadata(self):
        from merge_update import metadata_only
        updated = update_cask(self.original, self.release)
        self.assertTrue(metadata_only(self.original, updated))
        self.assertIn('version "1.0.1"', updated)
        self.assertIn('sha256 arm64_linux:  "' + "a" * 64, updated)
        self.assertIn('x86_64_linux: "' + "b" * 64, updated)
        self.assertEqual(update_cask(updated, self.release), updated)

    def test_prerelease_draft_or_invalid_tag_is_rejected(self):
        for field, value in (("draft", True), ("prerelease", True),
                             ("tag_name", "latest-linux-intel"),
                             ("tag_name", "v1.0.1-beta.1")):
            release = copy.deepcopy(self.release)
            release[field] = value
            with self.assertRaises(ValueError):
                update_cask(self.original, release)

    def test_incomplete_or_duplicate_architectures_are_rejected(self):
        for assets in (self.release["assets"][:1],
                       self.release["assets"] + self.release["assets"][:1]):
            release = dict(self.release, assets=assets)
            with self.assertRaises(ValueError):
                update_cask(self.original, release)

    def test_wrong_origin_bad_digest_or_unfinished_upload_is_rejected(self):
        for field, value in (("browser_download_url", "https://other.example/app.AppImage"),
                             ("digest", None), ("digest", "sha256:bad"),
                             ("state", "new"), ("size", 0)):
            release = copy.deepcopy(self.release)
            release["assets"][0][field] = value
            with self.assertRaises(ValueError):
                update_cask(self.original, release)

    def test_downgrade_and_same_version_rebuild_require_review(self):
        for version in ("1.0.1", "2.0.0"):
            current = self.original.replace('version "1.0.0"', f'version "{version}"')
            with self.assertRaises(ValueError):
                update_cask(current, self.release)

    def test_missing_or_duplicate_cask_fields_are_rejected(self):
        for original in (self.original + '\n  version "1.0.0"\n',
                         self.original.replace("sha256 arm64_linux:", "sha256 arm:")):
            with self.assertRaises(ValueError):
                update_cask(original, self.release)


if __name__ == "__main__":
    unittest.main()

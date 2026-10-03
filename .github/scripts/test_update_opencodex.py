import copy
import re
import unittest
from pathlib import Path

from update_opencodex import ORIGIN, PACKAGE_ASSETS, metadata_only, update_packages


class OpenCodexUpdateTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.originals = {
            path: re.sub(r'^  version "[^\"]+"$', '  version "1.0.0"',
                         (root / path).read_text(), flags=re.MULTILINE)
            for path in PACKAGE_ASSETS
        }
        self.release = {
            "tag_name": "v1.0.1", "draft": False, "prerelease": False,
            "assets": [
                {"name": name.format(version="1.0.1"),
                 "browser_download_url": f'{ORIGIN}/v1.0.1/{name.format(version="1.0.1")}',
                 "digest": "sha256:" + str(index + 1) * 64,
                 "state": "uploaded", "size": 123}
                for index, name in enumerate(dict.fromkeys(
                    name for names in PACKAGE_ASSETS.values() for name in names))
            ],
        }

    def test_complete_release_changes_only_metadata_and_is_idempotent(self):
        updated = update_packages(self.originals, self.release)
        for path, content in updated.items():
            self.assertTrue(metadata_only(self.originals[path], content, path))
            self.assertIn('version "1.0.1"', content)
        self.assertEqual(update_packages(updated, self.release), updated)

    def test_incomplete_duplicate_or_wrong_origin_assets_are_rejected(self):
        for change in ("missing", "duplicate", "origin", "digest", "upload", "empty"):
            with self.subTest(change=change):
                release = copy.deepcopy(self.release)
                if change == "missing":
                    release["assets"].pop()
                elif change == "duplicate":
                    release["assets"].append(release["assets"][0])
                else:
                    field, value = {"origin": ("browser_download_url", "https://other.example/app"),
                                    "digest": ("digest", "sha256:bad"),
                                    "upload": ("state", "new"), "empty": ("size", 0)}[change]
                    release["assets"][0][field] = value
                with self.assertRaises(ValueError):
                    update_packages(self.originals, release)

    def test_drafts_prereleases_and_non_numeric_tags_are_rejected(self):
        for field, value in (("draft", True), ("prerelease", True),
                             ("tag_name", "v1.0.1-beta"), ("tag_name", "latest")):
            with self.assertRaises(ValueError):
                update_packages(self.originals, dict(self.release, **{field: value}))

    def test_downgrade_same_version_rebuild_and_inconsistent_versions_are_rejected(self):
        for version in ("1.0.1", "2.0.0"):
            originals = {path: content.replace('version "1.0.0"', f'version "{version}"')
                         for path, content in self.originals.items()}
            with self.assertRaises(ValueError):
                update_packages(originals, self.release)
        originals = dict(self.originals)
        path = next(iter(originals))
        originals[path] = originals[path].replace('version "1.0.0"', 'version "1.0.2"')
        with self.assertRaises(ValueError):
            update_packages(originals, self.release)

    def test_missing_package_or_malformed_checksum_is_rejected(self):
        originals = dict(self.originals)
        originals.pop(next(iter(originals)))
        with self.assertRaises(ValueError):
            update_packages(originals, self.release)
        originals = dict(self.originals)
        path = next(iter(originals))
        originals[path] = originals[path].replace('sha256 "', 'sha256 "bad', 1)
        with self.assertRaises(ValueError):
            update_packages(originals, self.release)

    def test_url_install_code_and_uninstall_changes_are_not_metadata(self):
        updated = update_packages(self.originals, self.release)
        for path in self.originals:
            for before, after in (("https://", "https://other.example/"),
                                  ("\nend\n", '\n  system "unexpected"\nend\n')):
                self.assertFalse(metadata_only(self.originals[path],
                                               updated[path].replace(before, after), path))


if __name__ == "__main__":
    unittest.main()

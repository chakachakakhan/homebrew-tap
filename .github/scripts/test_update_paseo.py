import copy
import unittest

from update_paseo import ORIGIN, metadata_only, update_cask


class PaseoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.original = '''cask "paseo-linux" do
  version "0.12.0"
  sha256 "fa64073325898687e724bce20a5cbe4d0e8bbeb5e4ed58ca0398b3bc066060d4"
  url "https://github.com/getpaseo/paseo/releases/download/v#{version}/Paseo-#{version}-x64.tar.gz"
end
'''
        self.release = {
            "tag_name": "v0.13.0", "draft": False, "prerelease": False,
            "assets": [{
                "name": "Paseo-0.13.0-x64.tar.gz",
                "browser_download_url": f"{ORIGIN}/v0.13.0/Paseo-0.13.0-x64.tar.gz",
                "digest": "sha256:" + "a" * 64,
                "state": "uploaded", "size": 123,
            }],
        }

    def test_release_digest_updates_metadata_and_same_release_is_idempotent(self):
        updated = update_cask(self.original, self.release)
        self.assertTrue(metadata_only(self.original, updated))
        self.assertIn('version "0.13.0"', updated)
        self.assertIn('sha256 "' + "a" * 64 + '"', updated)
        self.assertEqual(update_cask(updated, self.release), updated)

    def test_incomplete_untrusted_or_invalid_assets_are_rejected(self):
        changes = {
            "missing": lambda release: release["assets"].clear(),
            "wrong-origin": lambda release: release["assets"][0].update(
                browser_download_url="https://example.com/paseo.tar.gz"),
            "missing-digest": lambda release: release["assets"][0].update(digest=None),
            "not-uploaded": lambda release: release["assets"][0].update(state="new"),
            "empty": lambda release: release["assets"][0].update(size=0),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                release = copy.deepcopy(self.release)
                change(release)
                with self.assertRaises(ValueError):
                    update_cask(self.original, release)

    def test_drafts_prereleases_downgrades_and_rebuilds_are_rejected(self):
        for field, value in (("draft", True), ("prerelease", True),
                             ("tag_name", "v0.13.0-rc1"), ("tag_name", "latest")):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    update_cask(self.original, dict(self.release, **{field: value}))
        downgrade = copy.deepcopy(self.release)
        downgrade["tag_name"] = "v0.11.0"
        downgrade["assets"][0].update(
            name="Paseo-0.11.0-x64.tar.gz",
            browser_download_url=f"{ORIGIN}/v0.11.0/Paseo-0.11.0-x64.tar.gz")
        with self.assertRaises(ValueError):
            update_cask(self.original, downgrade)
        rebuild = copy.deepcopy(self.release)
        rebuild["tag_name"] = "v0.12.0"
        rebuild["assets"][0].update(
            name="Paseo-0.12.0-x64.tar.gz",
            browser_download_url=f"{ORIGIN}/v0.12.0/Paseo-0.12.0-x64.tar.gz")
        with self.assertRaises(ValueError):
            update_cask(self.original, rebuild)

    def test_metadata_guard_rejects_installer_changes(self):
        updated = update_cask(self.original, self.release)
        self.assertFalse(metadata_only(
            self.original, updated.replace("Paseo-#{version}-x64.tar.gz", "other.tar.gz")))


if __name__ == "__main__":
    unittest.main()

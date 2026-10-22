import base64
import copy
import unittest
from unittest.mock import Mock

from merge_paseo import BRANCH, REQUIRED_JOBS, merge_update


class PaseoMergeTests(unittest.TestCase):
    def setUp(self):
        self.before = '''cask "paseo-linux" do
  version "0.12.0"
  sha256 "''' + "a" * 64 + '''"
  url "https://github.com/getpaseo/paseo/releases/download/v#{version}/Paseo-#{version}-x64.tar.gz"
end
'''
        self.after = self.before.replace('version "0.12.0"', 'version "0.13.0"')
        self.repo = "owner/homebrew-tap"
        self.run = {"id": 42, "event": "workflow_dispatch", "head_branch": BRANCH,
                    "head_repository": {"full_name": self.repo},
                    "head_sha": "tested", "path": ".github/workflows/validate-paseo.yml",
                    "conclusion": "success"}
        self.pr = {"number": 3, "title": "Paseo update", "draft": False, "state": "open",
                   "user": {"login": "github-actions[bot]"}, "changed_files": 1,
                   "head": {"repo": {"full_name": self.repo}, "ref": BRANCH, "sha": "tested"},
                   "base": {"repo": {"full_name": self.repo}, "ref": "main", "sha": "base"}}
        self.comparison = {"merge_base_commit": {"sha": "base"}, "files": [
            {"filename": "Casks/paseo-linux.rb", "status": "modified"}]}
        self.jobs = {"total_count": len(REQUIRED_JOBS), "jobs": [
            {"name": name, "conclusion": "success"} for name in REQUIRED_JOBS]}
        self.request = Mock(side_effect=self.respond)

    def respond(self, path, payload=None):
        if path.endswith("/merge"):
            self.assertEqual(payload["sha"], "tested")
            return {"merged": True}
        if "/jobs?" in path:
            return self.jobs
        if "/pulls?" in path:
            return [{"number": 3}]
        if path.endswith("/pulls/3"):
            return self.pr
        if "/compare/" in path:
            return self.comparison
        source = self.before if path.endswith("ref=base") else self.after
        return {"encoding": "base64", "content": base64.b64encode(source.encode()).decode()}

    def assert_rejected(self):
        with self.assertRaises(ValueError):
            merge_update(self.repo, self.run, self.request)
        self.assertFalse(any(call.args[0].endswith("/merge")
                             for call in self.request.call_args_list))

    def test_merges_the_exact_successfully_validated_commit(self):
        self.assertTrue(merge_update(self.repo, self.run, self.request))

    def test_wrong_workflow_or_failed_or_incomplete_jobs_never_merge(self):
        for field, value in (("event", "pull_request"), ("head_branch", "other"),
                             ("path", ".github/workflows/validate.yml"),
                             ("head_repository", {"full_name": "attacker/fork"})):
            run = copy.deepcopy(self.run)
            run[field] = value
            self.assertFalse(merge_update(self.repo, run, self.request))
        self.run["conclusion"] = "failure"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.request.assert_not_called()
        self.run["conclusion"] = "success"
        self.jobs["jobs"][0]["conclusion"] = "skipped"
        self.assert_rejected()
        self.jobs["jobs"][0]["conclusion"] = "success"
        self.jobs["total_count"] -= 1
        self.assert_rejected()

    def test_changed_head_stale_base_and_extra_files_never_merge(self):
        self.pr["head"]["sha"] = "newer"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.pr["head"]["sha"] = "tested"
        self.comparison["merge_base_commit"]["sha"] = "old"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.comparison["merge_base_commit"]["sha"] = "base"
        self.comparison["files"].append({"filename": "README.md", "status": "modified"})
        self.assert_rejected()

    def test_user_pr_and_installer_change_never_merge(self):
        original = copy.deepcopy(self.pr)
        changes = {
            "human": lambda pr: pr["user"].update(login="human"),
            "fork": lambda pr: pr["head"].update(repo={"full_name": "attacker/fork"}),
            "draft": lambda pr: pr.update(draft=True),
            "base-branch": lambda pr: pr["base"].update(ref="other"),
            "head-branch": lambda pr: pr["head"].update(ref="other"),
            "base-repo": lambda pr: pr["base"].update(repo={"full_name": "attacker/fork"}),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                self.pr = copy.deepcopy(original)
                change(self.pr)
                self.assert_rejected()
        self.pr = copy.deepcopy(original)
        self.after += '\nsystem "unexpected"\n'
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main()

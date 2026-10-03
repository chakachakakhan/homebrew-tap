import base64
import copy
import re
import unittest
from pathlib import Path
from unittest.mock import Mock

from merge_omp_desktop import BRANCH, REQUIRED_JOBS, merge_update
from update_omp_desktop import CASK

PACKAGE_ASSETS = [str(CASK)]


class OMPDesktopMergeTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.before = {path: re.sub(r'^  version "[^\"]+"$', '  version "1.0.0"',
                                   (root / path).read_text(), flags=re.MULTILINE)
                       for path in PACKAGE_ASSETS}
        self.after = {path: content.replace('version "1.0.0"', 'version "1.0.1"')
                      for path, content in self.before.items()}
        self.repo = "owner/homebrew-tap"
        self.run = {"id": 42, "event": "workflow_dispatch", "head_branch": BRANCH,
                    "head_repository": {"full_name": self.repo}, "head_sha": "tested",
                    "path": ".github/workflows/validate-omp-desktop.yml", "conclusion": "success"}
        self.pr = {"number": 3, "title": "OMP Desktop update", "draft": False, "state": "open",
                   "user": {"login": "github-actions[bot]"}, "changed_files": 1,
                   "head": {"repo": {"full_name": self.repo}, "ref": BRANCH, "sha": "tested"},
                   "base": {"repo": {"full_name": self.repo}, "ref": "main", "sha": "base"}}
        self.comparison = {"merge_base_commit": {"sha": "base"}, "files": [
            {"filename": path, "status": "modified"} for path in PACKAGE_ASSETS]}
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
        filename = path.split("/contents/")[1].split("?")[0]
        return {"encoding": "base64", "content": base64.b64encode(source[filename].encode()).decode()}

    def assert_rejected(self):
        with self.assertRaises(ValueError):
            merge_update(self.repo, self.run, self.request)
        self.assertFalse(any(call.args[0].endswith("/merge") for call in self.request.call_args_list))

    def test_desktop_merges_at_exact_tested_commit(self):
        self.assertTrue(merge_update(self.repo, self.run, self.request))

    def test_failed_missing_or_skipped_platform_never_merges(self):
        self.run["conclusion"] = "failure"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.request.assert_not_called()
        self.run["conclusion"] = "success"
        self.jobs["jobs"][0]["conclusion"] = "skipped"
        self.assert_rejected()

    def test_wrong_workflow_event_branch_or_repository_never_merges(self):
        for field, value in (("event", "pull_request"), ("head_branch", "feature"),
                             ("path", ".github/workflows/validate.yml"),
                             ("head_repository", {"full_name": "attacker/fork"})):
            run = copy.deepcopy(self.run)
            run[field] = value
            self.assertFalse(merge_update(self.repo, run, self.request))
        self.request.assert_not_called()

    def test_changed_head_or_stale_base_waits(self):
        self.pr["head"]["sha"] = "newer"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.pr["head"]["sha"] = "tested"
        self.comparison["merge_base_commit"]["sha"] = "older"
        self.assertFalse(merge_update(self.repo, self.run, self.request))
        self.assertFalse(any(call.args[0].endswith("/merge") for call in self.request.call_args_list))

    def test_human_fork_or_draft_pr_is_rejected(self):
        original = copy.deepcopy(self.pr)
        for change in ("human", "fork", "draft"):
            self.pr = copy.deepcopy(original)
            if change == "human":
                self.pr["user"]["login"] = "someone"
            elif change == "fork":
                self.pr["head"]["repo"]["full_name"] = "attacker/fork"
            else:
                self.pr["draft"] = True
            self.assert_rejected()

    def test_extra_or_missing_file_is_rejected(self):
        original = copy.deepcopy(self.comparison["files"])
        for files in ([], original + [{"filename": "README.md", "status": "modified"}]):
            self.comparison["files"] = files
            self.assert_rejected()

    def test_code_or_url_change_is_rejected_even_with_green_checks(self):
        path = "Casks/omp-desktop.rb"
        self.after[path] += '\nsystem "unexpected"\n'
        self.assert_rejected()

    def test_missing_required_job_is_rejected(self):
        self.jobs["jobs"].pop()
        self.jobs["total_count"] -= 1
        self.assert_rejected()

    def test_deleted_or_renamed_cask_is_rejected(self):
        for status in ("deleted", "renamed", "added"):
            self.comparison["files"][0]["status"] = status
            self.assert_rejected()

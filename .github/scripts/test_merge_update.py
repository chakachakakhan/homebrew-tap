import base64
import copy
import unittest
from pathlib import Path
from unittest.mock import Mock

from merge_update import UPDATE_CASKS, REQUIRED_JOBS, merge_update, metadata_only, validation_run


class MergePolicyTests(unittest.TestCase):
    branch = "automation/update-chatgpt"

    def setUp(self):
        cask = UPDATE_CASKS[self.branch]
        self.before = (Path(__file__).resolve().parents[2] / cask).read_text()
        # Fixtures stay valid when the real cask's version advances.
        import re
        self.before = re.sub(r'^  version "[^"]+"$', '  version "1.0.0"',
                             self.before, flags=re.MULTILINE)
        self.after = self.before.replace('version "1.0.0"', 'version "1.0.1"')
        self.repo = "owner/homebrew-tap"
        self.run = {
            "id": 42, "event": "workflow_dispatch", "head_branch": self.branch,
            "head_repository": {"full_name": self.repo}, "head_sha": "tested",
            "path": ".github/workflows/validate.yml", "conclusion": "success",
        }
        self.pr = {
            "number": 3, "title": "ChatGPT update", "draft": False, "state": "open",
            "user": {"login": "github-actions[bot]"}, "changed_files": 1,
            "head": {"repo": {"full_name": self.repo}, "ref": self.branch, "sha": "tested"},
            "base": {"repo": {"full_name": self.repo}, "ref": "main", "sha": "base"},
        }
        self.comparison = {
            "merge_base_commit": {"sha": "base"},
            "files": [{"filename": cask, "status": "modified"}],
        }
        self.jobs = {"total_count": 3, "jobs": [
            {"name": name, "conclusion": "success"} for name in sorted(REQUIRED_JOBS)
        ]}
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
        text = self.before if path.endswith("ref=base") else self.after
        return {"encoding": "base64", "content": base64.b64encode(text.encode()).decode()}

    def merged(self):
        return merge_update(self.repo, self.run, self.request)

    def assert_not_merged(self):
        self.assertFalse(any(call.args[0].endswith("/merge") for call in self.request.call_args_list))

    def test_valid_update_merges_exact_tested_commit(self):
        self.assertTrue(self.merged())

    def test_uninstall_url_or_code_change_requires_manual_review(self):
        for before, after in (("zap trash:", "zap trash: # changed"),
                              ("https://", "https://other.example.com/"),
                              ('  arch arm:', '  system "unexpected"\n  arch arm:')):
            with self.subTest(change=after):
                self.assertFalse(metadata_only(self.before, self.after.replace(before, after)))

    def test_invalid_or_duplicate_metadata_is_rejected(self):
        for after in (self.after + '\n  version "1.0.1"\n',
                      self.after.replace('version "1.0.1"', 'version "latest"'),
                      self.after.replace('sha256 arm64_linux:  "', 'sha256 arm64_linux:  "bad')):
            self.assertFalse(metadata_only(self.before, after))

    def test_unchanged_downgrade_and_same_version_rebuild_are_rejected(self):
        self.assertFalse(metadata_only(self.before, self.before))
        self.assertFalse(metadata_only(self.after, self.before))
        import re
        rebuilt = re.sub(r'(sha256 arm64_linux:  ")[0-9a-f]{64}',
                         r'\g<1>' + '0' * 64, self.before)
        self.assertFalse(metadata_only(self.before, rebuilt))

    def test_new_version_with_new_checksums_is_allowed(self):
        import re
        updated = re.sub(r'(sha256 arm64_linux:  ")[0-9a-f]{64}',
                         r'\g<1>' + '0' * 64, self.after)
        self.assertTrue(metadata_only(self.before, updated))

    def test_failed_or_incomplete_installation_never_merges(self):
        self.run["conclusion"] = "failure"
        self.assertFalse(self.merged())
        self.assert_not_merged()
        self.run["conclusion"] = "success"
        self.jobs["jobs"][0]["conclusion"] = "skipped"
        with self.assertRaises(ValueError):
            self.merged()
        self.assert_not_merged()

    def test_unrelated_run_never_accesses_api(self):
        for field, value in (("event", "pull_request"), ("head_branch", "feature"),
                             ("path", ".github/workflows/other.yml"),
                             ("head_repository", {"full_name": "attacker/fork"})):
            run = copy.deepcopy(self.run)
            run[field] = value
            self.assertFalse(merge_update(self.repo, run, self.request))
        self.request.assert_not_called()

    def test_changed_head_or_stale_base_waits_for_fresh_validation(self):
        self.pr["head"]["sha"] = "newer"
        self.assertFalse(self.merged())
        self.pr["head"]["sha"] = "tested"
        self.comparison["merge_base_commit"]["sha"] = "older"
        self.assertFalse(self.merged())
        self.assert_not_merged()

    def test_human_authored_fork_or_draft_pr_never_merges(self):
        original = copy.deepcopy(self.pr)
        for change in ("human", "fork", "draft"):
            self.pr = copy.deepcopy(original)
            if change == "human":
                self.pr["user"]["login"] = "someone"
            elif change == "fork":
                self.pr["head"]["repo"]["full_name"] = "attacker/fork"
            else:
                self.pr["draft"] = True
            with self.assertRaises(ValueError):
                self.merged()
        self.assert_not_merged()

    def test_extra_file_never_merges(self):
        self.comparison["files"].append({"filename": ".github/workflows/validate.yml", "status": "modified"})
        with self.assertRaises(ValueError):
            self.merged()
        self.assert_not_merged()

    def test_code_change_never_merges_even_after_successful_checks(self):
        self.after += '\nsystem "unexpected"\n'
        with self.assertRaises(ValueError):
            self.merged()
        self.assert_not_merged()

    def test_other_cask_on_update_branch_never_merges(self):
        other = next(cask for branch, cask in UPDATE_CASKS.items() if branch != self.branch)
        self.comparison["files"][0]["filename"] = other
        with self.assertRaises(ValueError):
            self.merged()
        self.assert_not_merged()


class ThoriumMergePolicyTests(MergePolicyTests):
    branch = "automation/update-thorium-reader"


class ValidationDispatchTests(unittest.TestCase):
    def test_completed_dispatch_fetches_real_run(self):
        run = {"status": "completed", "conclusion": "success"}
        request = Mock(return_value=run)
        pause = Mock()
        self.assertIs(validation_run("owner/tap", {"inputs": {"validation_run_id": "42"}},
                                     request, pause), run)
        request.assert_called_once_with("repos/owner/tap/actions/runs/42")
        pause.assert_not_called()

    def test_waits_for_completion_and_preserves_failure(self):
        failed = {"status": "completed", "conclusion": "failure"}
        request = Mock(side_effect=[{"status": "queued"}, {"status": "in_progress"}, failed])
        pause = Mock()
        self.assertIs(validation_run("owner/tap", {"inputs": {"validation_run_id": "42"}},
                                     request, pause), failed)
        self.assertEqual(pause.call_count, 2)

    def test_invalid_id_never_accesses_api(self):
        for run_id in ("", "0", "-1", "42/other", "hello"):
            request = Mock()
            with self.assertRaises(ValueError):
                validation_run("owner/tap", {"inputs": {"validation_run_id": run_id}},
                               request, Mock())
            request.assert_not_called()

    def test_timeout_leaves_pr_for_retry(self):
        request = Mock(return_value={"status": "in_progress"})
        with self.assertRaises(TimeoutError):
            validation_run("owner/tap", {"inputs": {"validation_run_id": "42"}},
                           request, Mock())
        self.assertEqual(request.call_count, 150)

    def test_existing_workflow_run_handoff_is_preserved(self):
        run = {"status": "completed", "conclusion": "success"}
        request = Mock()
        self.assertIs(validation_run("owner/tap", {"workflow_run": run}, request), run)
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()

import base64
import copy
import unittest
from pathlib import Path
from unittest.mock import Mock

from publish_emacs import ARTIFACTS, BRANCH, REQUIRED_JOBS, WORKFLOW, release_candidate
from update_emacs import FORMULA, PACKAGES, package_version, update_packages


class EmacsPublicationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.before = {path: (root / path).read_text() for path in PACKAGES}
        old = package_version(self.before[FORMULA], FORMULA)
        self.after = update_packages(self.before, f"{int(old.split('.')[0]) + 1}.1", "a" * 64)
        self.repo = "owner/homebrew-tap"
        self.sha = "b" * 40
        self.run = {"id": 42, "event": "workflow_dispatch", "head_branch": BRANCH,
                    "head_repository": {"full_name": self.repo}, "head_sha": self.sha,
                    "path": WORKFLOW, "status": "completed", "conclusion": "success"}
        self.pr = {"number": 3, "state": "open", "draft": False, "changed_files": 2,
                   "user": {"login": "github-actions[bot]"},
                   "head": {"repo": {"full_name": self.repo}, "ref": BRANCH, "sha": self.sha},
                   "base": {"repo": {"full_name": self.repo}, "ref": "main", "sha": "base"}}
        self.jobs = {"total_count": 3, "jobs": [
            {"name": name, "conclusion": "success"} for name in REQUIRED_JOBS]}
        self.artifacts = {"artifacts": [{"name": name, "expired": False} for name in ARTIFACTS]}
        self.comparison = {"merge_base_commit": {"sha": "base"}, "files": [
            {"filename": path, "status": "modified"} for path in PACKAGES]}
        self.request = Mock(side_effect=self.respond)

    def respond(self, path):
        if "/jobs?" in path:
            return self.jobs
        if "/artifacts?" in path:
            return self.artifacts
        if "/pulls?" in path:
            return [{"number": 3}]
        if path.endswith("/pulls/3"):
            return self.pr
        if "/compare/" in path:
            return self.comparison
        source = self.before if path.endswith("ref=base") else self.after
        filename = path.split("/contents/")[1].split("?")[0]
        return {"encoding": "base64", "content": base64.b64encode(source[filename].encode()).decode()}

    def reject(self, run=None):
        with self.assertRaises(ValueError):
            release_candidate(self.repo, run or self.run, self.request)

    def test_exact_source_revision_and_both_bottles_can_publish(self):
        self.assertEqual(release_candidate(self.repo, self.run, self.request), {
            "pull_request": "3", "head_sha": self.sha, "run_id": "42",
        })

    def test_failed_skipped_or_missing_platform_cannot_publish(self):
        for conclusion in ("failure", "cancelled"):
            run = self.run | {"conclusion": conclusion}
            self.reject(run)
        self.jobs["jobs"][0]["conclusion"] = "skipped"
        self.reject()

    def test_wrong_event_branch_workflow_or_fork_cannot_publish(self):
        for key, value in (("event", "pull_request"), ("head_branch", "feature"),
                           ("path", ".github/workflows/validate.yml"),
                           ("head_repository", {"full_name": "attacker/fork"})):
            self.reject(self.run | {key: value})

    def test_expired_missing_or_duplicate_bottles_cannot_publish(self):
        saved = copy.deepcopy(self.artifacts)
        self.artifacts["artifacts"][0]["expired"] = True
        self.reject()
        self.artifacts = copy.deepcopy(saved)
        self.artifacts["artifacts"].pop()
        self.reject()
        self.artifacts = copy.deepcopy(saved)
        self.artifacts["artifacts"].append(self.artifacts["artifacts"][0])
        self.reject()

    def test_stale_head_or_main_cannot_publish(self):
        self.pr["head"]["sha"] = "c" * 40
        self.reject()
        self.pr["head"]["sha"] = self.sha
        self.comparison["merge_base_commit"]["sha"] = "old"
        self.reject()

    def test_workflow_changes_or_installation_behavior_cannot_publish_automatically(self):
        self.comparison["files"].append({"filename": WORKFLOW, "status": "modified"})
        self.reject()
        self.comparison["files"].pop()
        self.after[FORMULA] += '\n  system "untrusted"\n'
        self.reject()

    def test_human_and_draft_pr_cannot_publish_automatically(self):
        self.pr["user"]["login"] = "human"
        self.reject()
        self.pr["user"]["login"] = "github-actions[bot]"
        self.pr["draft"] = True
        self.reject()

    def test_manual_publication_still_requires_the_exact_tested_revision(self):
        self.pr["user"]["login"] = "owner"
        run = self.run | {"event": "pull_request", "head_branch": "initial-emacs"}
        result = release_candidate(self.repo, run, self.request, manual_pr="3", expected_sha=self.sha)
        self.assertEqual(result["head_sha"], self.sha)
        with self.assertRaises(ValueError):
            release_candidate(self.repo, run, self.request, manual_pr="3", expected_sha="c" * 40)


if __name__ == "__main__":
    unittest.main()

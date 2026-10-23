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
        self.jobs = {"total_count": len(REQUIRED_JOBS), "jobs": [
            {"name": name, "conclusion": "success", "run_attempt": 1, "id": index}
            for index, name in enumerate(REQUIRED_JOBS, start=1)]}
        self.artifacts = {"artifacts": [{"name": name, "expired": False} for name in ARTIFACTS]}
        self.comparison = {"merge_base_commit": {"sha": "base"}, "files": [
            {"filename": path, "status": "modified"} for path in PACKAGES]}
        self.extra_sources = {}
        self.extra_validation = {}
        root = Path(__file__).resolve().parents[2]
        self.validation_workflow = (root / WORKFLOW).read_text()
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
        ref = path.rsplit("ref=", 1)[-1]
        source = self.extra_sources.get(ref, self.before if ref == "base" else self.after)
        filename = path.split("/contents/")[1].split("?")[0]
        if filename == WORKFLOW:
            content = self.extra_validation.get(ref, self.validation_workflow)
            return {"encoding": "base64",
                    "content": base64.b64encode(content.encode()).decode()}
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

    def test_both_runtime_jobs_must_succeed(self):
        arm_runtime = next(job for job in self.jobs["jobs"]
                           if job["name"] == "Emacs runtime (ubuntu-24.04-arm)")
        arm_runtime["conclusion"] = "failure"
        self.reject()
        arm_runtime["conclusion"] = "success"
        self.jobs["jobs"].remove(arm_runtime)
        self.jobs["total_count"] -= 1
        self.reject()

    def test_partial_rerun_uses_latest_attempt_for_each_job(self):
        arm_runtime = next(job for job in self.jobs["jobs"]
                           if job["name"] == "Emacs runtime (ubuntu-24.04-arm)")
        arm_runtime["conclusion"] = "failure"
        self.jobs["jobs"].append(arm_runtime | {
            "conclusion": "success", "run_attempt": 2, "id": 100,
        })
        self.jobs["total_count"] += 1
        self.assertEqual(release_candidate(self.repo, self.run, self.request)["head_sha"], self.sha)

        arm_runtime["conclusion"] = "success"
        self.jobs["jobs"][-1]["conclusion"] = "failure"
        self.reject()

    def test_unexpected_validation_job_fails_closed(self):
        self.jobs["jobs"].append({"name": "unexpected", "conclusion": "success",
                                  "run_attempt": 1, "id": 100})
        self.jobs["total_count"] += 1
        self.reject()

    def test_skipped_matrix_placeholder_does_not_block_a_successful_retry(self):
        placeholder = {"name": "Emacs runtime (${{ matrix.runner }})",
                       "conclusion": "skipped", "run_attempt": 1, "id": 100}
        self.jobs["jobs"].append(placeholder)
        self.jobs["total_count"] += 1
        self.assertEqual(release_candidate(self.repo, self.run, self.request)["head_sha"], self.sha)
        placeholder["conclusion"] = "failure"
        self.reject()

    def test_both_bottle_builds_must_succeed_for_publication(self):
        arm_build = next(job for job in self.jobs["jobs"]
                         if job["name"] == "Emacs bottle build (ubuntu-24.04-arm)")
        arm_build["conclusion"] = "skipped"
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

    def test_diagnostic_artifacts_do_not_block_publication(self):
        self.artifacts["artifacts"].extend([
            {"name": "emacs-logs_ubuntu-24.04", "expired": False},
            {"name": "emacs-logs_ubuntu-24.04-arm", "expired": False},
        ])
        self.assertEqual(release_candidate(self.repo, self.run, self.request)["head_sha"], self.sha)

    def test_unexpected_bottle_artifacts_fail_closed(self):
        self.artifacts["artifacts"].append({"name": "bottles_unexpected", "expired": False})
        self.reject()

    def test_stale_head_or_main_cannot_publish(self):
        self.pr["head"]["sha"] = "c" * 40
        self.reject()
        self.pr["head"]["sha"] = self.sha
        self.comparison["merge_base_commit"]["sha"] = "old"
        self.reject()

    def test_unrelated_main_changes_do_not_force_rebuilding_emacs(self):
        self.comparison["merge_base_commit"]["sha"] = "old-main"
        self.pr["base"]["sha"] = "current-main"
        self.extra_sources["old-main"] = self.before
        self.extra_sources["current-main"] = self.before.copy()
        self.assertEqual(release_candidate(self.repo, self.run, self.request)["head_sha"], self.sha)

        self.extra_sources["current-main"][FORMULA] += '\n  # unrelated recipe change\n'
        self.reject()

    def test_changed_validation_policy_on_main_requires_revalidation(self):
        self.comparison["merge_base_commit"]["sha"] = "old-main"
        self.pr["base"]["sha"] = "current-main"
        self.extra_sources["old-main"] = self.before
        self.extra_sources["current-main"] = self.before.copy()
        self.extra_validation["current-main"] = self.validation_workflow + "\n# changed validation policy\n"
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

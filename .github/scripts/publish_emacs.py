"""Gate Homebrew's standard pr-pull publisher on tested, current source metadata."""

import argparse
import base64
import json
import os
from pathlib import Path
import re
import time

from merge_update import api
from update_emacs import PACKAGES, metadata_only

BRANCH = "automation/update-emacs"
WORKFLOW = ".github/workflows/validate-emacs.yml"
REQUIRED_JOBS = {
    "Emacs update policy", "Emacs bottle (ubuntu-24.04)", "Emacs bottle (ubuntu-24.04-arm)",
}
ARTIFACTS = {"bottles_ubuntu-24.04", "bottles_ubuntu-24.04-arm"}


def release_candidate(repo, run, request=api, manual_pr=None, expected_sha=None):
    if (run["head_repository"]["full_name"] != repo or run["path"] != WORKFLOW
            or run["status"] != "completed" or run["conclusion"] != "success"):
        raise ValueError("Only a successful Emacs validation in this repository can publish")
    automatic = manual_pr is None
    if automatic and (run["event"] != "workflow_dispatch" or run["head_branch"] != BRANCH):
        raise ValueError("Only the dedicated dispatched Emacs update can publish automatically")
    if run["event"] not in ("pull_request", "workflow_dispatch"):
        raise ValueError("Unexpected validation event")
    prefix = f"repos/{repo}"
    jobs = request(f"{prefix}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")
    if jobs["total_count"] != len(REQUIRED_JOBS) or {
        job["name"] for job in jobs["jobs"] if job["conclusion"] == "success"
    } != REQUIRED_JOBS:
        raise ValueError("Both complete bottle installations and update policy checks must pass")
    artifacts = request(f"{prefix}/actions/runs/{run['id']}/artifacts?per_page=100")
    names = [item["name"] for item in artifacts["artifacts"] if not item["expired"]]
    if len(names) != len(ARTIFACTS) or set(names) != ARTIFACTS:
        raise ValueError("Both tested Linux bottles must be available")

    if manual_pr is not None:
        pr = request(f"{prefix}/pulls/{manual_pr}")
    else:
        owner = repo.split("/")[0]
        prs = request(f"{prefix}/pulls?state=open&base=main&head={owner}:{BRANCH}")
        if len(prs) != 1:
            raise ValueError("Expected exactly one open Emacs update PR")
        pr = request(f"{prefix}/pulls/{prs[0]['number']}")
    if (pr["state"] != "open" or pr["draft"] or pr["base"]["ref"] != "main"
            or pr["base"]["repo"]["full_name"] != repo
            or pr["head"]["repo"]["full_name"] != repo):
        raise ValueError("Only an open, ready, same-repository PR targeting main can publish")
    sha = pr["head"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or sha != run["head_sha"]:
        raise ValueError("The PR head must be the exact tested revision")
    if expected_sha is not None and sha != expected_sha:
        raise ValueError("The PR moved after manual publication was requested")
    comparison = request(f"{prefix}/compare/{pr['base']['sha']}...{sha}")
    if comparison["merge_base_commit"]["sha"] != pr["base"]["sha"]:
        raise ValueError("Main changed; refresh the update and rerun validation")
    if automatic:
        if pr["user"]["login"] != "github-actions[bot]" or pr["head"]["ref"] != BRANCH:
            raise ValueError("Automatic publication requires the same-repository update bot")
        files = comparison["files"]
        if (pr["changed_files"] != len(PACKAGES) or len(files) != len(PACKAGES)
                or {item["filename"] for item in files} != PACKAGES
                or any(item["status"] != "modified" for item in files)):
            raise ValueError("Automatic updates can modify only the existing Emacs recipes")
        contents = []
        for ref in (pr["base"]["sha"], sha):
            source = {}
            for path in PACKAGES:
                item = request(f"{prefix}/contents/{path}?ref={ref}")
                if item["encoding"] != "base64":
                    raise ValueError("Unexpected GitHub content encoding")
                source[path] = base64.b64decode(item["content"]).decode("utf-8")
            contents.append(source)
        if not metadata_only(*contents):
            raise ValueError("Only a newer official source version and matching checksum can publish")
    return {"pull_request": str(pr["number"]), "head_sha": sha, "run_id": str(run["id"])}


def validation_run(repo, run_id, request=api, pause=time.sleep):
    if not re.fullmatch(r"[1-9][0-9]*", str(run_id)):
        raise ValueError("A numeric validation run ID is required")
    for attempt in range(180):
        run = request(f"repos/{repo}/actions/runs/{run_id}")
        if run["status"] == "completed":
            return run
        pause(30)
    raise TimeoutError("Validation did not finish; leave the source PR open for retry")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--manual-pr")
    parser.add_argument("--head-sha")
    args = parser.parse_args()
    repo = os.environ["GH_REPO"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    inputs = event.get("inputs", {})
    run_id = args.run_id or inputs.get("validation_run_id")
    manual_pr = args.manual_pr or inputs.get("pull_request") or None
    expected_sha = args.head_sha or inputs.get("head_sha") or None
    if manual_pr is not None:
        if not re.fullmatch(r"[1-9][0-9]*", manual_pr) or not re.fullmatch(r"[0-9a-f]{40}", expected_sha or ""):
            raise ValueError("Manual publication requires a PR number and its exact SHA")
        if event.get("sender", {}).get("login") != repo.split("/")[0]:
            raise ValueError("Only the repository owner can request manual publication")
    if run_id:
        run = validation_run(repo, run_id)
    elif "workflow_run" in event:
        run = event["workflow_run"]
    elif manual_pr:
        runs = api(f"repos/{repo}/actions/workflows/validate-emacs.yml/runs?head_sha={expected_sha}&per_page=30")
        matches = [item for item in runs["workflow_runs"]
                   if item["status"] == "completed" and item["conclusion"] == "success"]
        if not matches:
            raise ValueError("No successful validation exists for the requested PR revision")
        run = matches[0]
    else:
        raise ValueError("A validation run or explicit manual PR is required")
    result = release_candidate(repo, run, manual_pr=manual_pr, expected_sha=expected_sha)
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        for key, value in result.items():
            output.write(f"{key}={value}\n")
    print(f"Ready to publish PR #{result['pull_request']} at {result['head_sha']}")


if __name__ == "__main__":
    main()

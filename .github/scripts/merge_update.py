"""Merge a bot's metadata-only update after validation of that exact revision."""

import base64
import json
import os
import re
import subprocess
from pathlib import Path

UPDATE_CASKS = {
    "automation/update-chatgpt": "Casks/chatgpt-linux.rb",
    "automation/update-thorium-reader": "Casks/thorium-reader-linux.rb",
}
REQUIRED_JOBS = {
    "Install (ubuntu-24.04)",
    "Install (ubuntu-24.04-arm)",
    "Automation policy tests",
}
FIELDS = (
    r'^  version "(\d+(?:\.\d+)+)"$',
    r'^  sha256 arm64_linux:  "([0-9a-f]{64})",$',
    r'^         x86_64_linux: "([0-9a-f]{64})"$',
)


def api(path, payload=None):
    command = ["gh", "api", path]
    if payload is not None:
        command += ["--method", "PUT", "--input", "-"]
    return json.loads(subprocess.check_output(
        command, input=json.dumps(payload) if payload is not None else None,
        text=True,
    ))


def metadata_only(before, after):
    """Compare entire files while allowing exactly three well-formed fields."""
    versions = []
    normalized = []
    for content in (before, after):
        matches = re.findall(FIELDS[0], content, re.MULTILINE)
        if len(matches) != 1:
            return False
        versions.append(tuple(map(int, matches[0].split("."))))
        for pattern in FIELDS:
            content, count = re.subn(pattern, "<metadata>", content, flags=re.MULTILINE)
            if count != 1:
                return False
        normalized.append(content)
    return before != after and versions[1] > versions[0] and normalized[0] == normalized[1]


def merge_update(repo, run, request=api):
    branch = run["head_branch"]
    cask = UPDATE_CASKS.get(branch)
    if (run["event"] != "workflow_dispatch"
            or cask is None
            or run["head_repository"]["full_name"] != repo
            or run["path"] != ".github/workflows/validate.yml"):
        print("This run is outside the automatic update policy.")
        return False
    if run["conclusion"] != "success":
        print("Validation did not pass. The PR remains open for review/retry.")
        return False

    prefix = f"repos/{repo}"
    jobs = request(f"{prefix}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")
    if jobs["total_count"] != len(REQUIRED_JOBS) or {
        job["name"] for job in jobs["jobs"] if job["conclusion"] == "success"
    } != REQUIRED_JOBS:
        raise ValueError("Both installations and the automation policy tests must pass")

    owner = repo.split("/")[0]
    prs = request(f"{prefix}/pulls?state=open&base=main&head={owner}:{branch}")
    if not prs:
        print("No open update PR; it may already have been merged.")
        return False
    if len(prs) != 1:
        raise ValueError("Expected exactly one update PR")
    pr = request(f"{prefix}/pulls/{prs[0]['number']}")
    if (pr["user"]["login"] != "github-actions[bot]" or pr["draft"]
            or pr["state"] != "open" or pr["base"]["ref"] != "main"
            or pr["base"]["repo"]["full_name"] != repo
            or pr["head"]["repo"]["full_name"] != repo
            or pr["head"]["ref"] != branch):
        raise ValueError("Only the same-repository bot update PR can merge automatically")
    sha = pr["head"]["sha"]
    if sha != run["head_sha"]:
        print("The PR changed after this validation run; wait for its newer checks.")
        return False

    comparison = request(f"{prefix}/compare/{pr['base']['sha']}...{sha}")
    if comparison["merge_base_commit"]["sha"] != pr["base"]["sha"]:
        print("Main changed since this update; the next updater run will refresh it.")
        return False
    files = comparison["files"]
    if pr["changed_files"] != 1 or len(files) != 1 or (
        files[0]["filename"] != cask or files[0]["status"] != "modified"
    ):
        raise ValueError("The update must modify only the existing cask assigned to its branch")

    def content(ref):
        file = request(f"{prefix}/contents/{cask}?ref={ref}")
        if file["encoding"] != "base64":
            raise ValueError("Unexpected GitHub file encoding")
        return base64.b64decode(file["content"]).decode("utf-8")

    if not metadata_only(content(pr["base"]["sha"]), content(sha)):
        raise ValueError("Only a higher version and valid architecture checksums may change")
    result = request(f"{prefix}/pulls/{pr['number']}/merge", {
        "sha": sha, "merge_method": "squash",
        "commit_title": pr["title"],
    })
    if not result.get("merged"):
        raise ValueError(f"GitHub refused to merge: {result.get('message')}")
    print(f"Merged validated update PR #{pr['number']} at {sha}")
    return True


if __name__ == "__main__":
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    merge_update(os.environ["GH_REPO"], event["workflow_run"])

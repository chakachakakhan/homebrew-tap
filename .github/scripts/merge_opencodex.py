"""Merge only the two metadata-only packages validated at the current PR head."""

import base64
import json
import os
from pathlib import Path

from merge_update import api, validation_run
from update_opencodex import PACKAGE_ASSETS, metadata_only, package_version

BRANCH = "automation/update-opencodex"
REQUIRED_JOBS = {"OpenCodex policy tests"} | {
    f"OpenCodex ({runner})" for runner in
    ("ubuntu-24.04", "ubuntu-24.04-arm", "macos-15", "macos-15-intel")
}


def merge_update(repo, run, request=api):
    if (run["event"] != "workflow_dispatch" or run["head_branch"] != BRANCH
            or run["head_repository"]["full_name"] != repo
            or run["path"] != ".github/workflows/validate-opencodex.yml"):
        print("This run is outside the OpenCodex update policy.")
        return False
    if run["conclusion"] != "success":
        print("Validation did not pass; leave the PR open for retry.")
        return False
    prefix = f"repos/{repo}"
    jobs = request(f"{prefix}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")
    if jobs["total_count"] != len(REQUIRED_JOBS) or {
        job["name"] for job in jobs["jobs"] if job["conclusion"] == "success"
    } != REQUIRED_JOBS:
        raise ValueError("All four platform installations and policy tests must pass")
    owner = repo.split("/")[0]
    prs = request(f"{prefix}/pulls?state=open&base=main&head={owner}:{BRANCH}")
    if not prs:
        print("No open OpenCodex update PR; it may already have merged.")
        return False
    if len(prs) != 1:
        raise ValueError("Expected exactly one OpenCodex update PR")
    pr = request(f"{prefix}/pulls/{prs[0]['number']}")
    if (pr["user"]["login"] != "github-actions[bot]" or pr["draft"]
            or pr["state"] != "open" or pr["base"]["ref"] != "main"
            or pr["base"]["repo"]["full_name"] != repo
            or pr["head"]["repo"]["full_name"] != repo or pr["head"]["ref"] != BRANCH):
        raise ValueError("Only the same-repository bot update PR can merge automatically")
    sha = pr["head"]["sha"]
    if sha != run["head_sha"]:
        print("The PR changed; wait for validation of its newer revision.")
        return False
    comparison = request(f"{prefix}/compare/{pr['base']['sha']}...{sha}")
    if comparison["merge_base_commit"]["sha"] != pr["base"]["sha"]:
        print("Main changed; the next updater run will refresh this PR.")
        return False
    files = comparison["files"]
    if (pr["changed_files"] != 2 or len(files) != 2
            or {file["filename"] for file in files} != set(PACKAGE_ASSETS)
            or any(file["status"] != "modified" for file in files)):
        raise ValueError("Only the existing OpenCodex formula and cask may change")
    versions = set()
    for path in PACKAGE_ASSETS:
        contents = []
        for ref in (pr["base"]["sha"], sha):
            file = request(f"{prefix}/contents/{path}?ref={ref}")
            if file["encoding"] != "base64":
                raise ValueError("Unexpected GitHub file encoding")
            contents.append(base64.b64decode(file["content"]).decode("utf-8"))
        if not metadata_only(*contents, path):
            raise ValueError("Only a higher version and valid checksums may change")
        versions.add(package_version(contents[1]))
    if len(versions) != 1:
        raise ValueError("The CLI and desktop must advance to the same version")
    result = request(f"{prefix}/pulls/{pr['number']}/merge", {
        "sha": sha, "merge_method": "squash", "commit_title": pr["title"],
    })
    if not result.get("merged"):
        raise ValueError(f"GitHub refused to merge: {result.get('message')}")
    print(f"Merged OpenCodex PR #{pr['number']} at its validated revision {sha}")
    return True


if __name__ == "__main__":
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    repo = os.environ["GH_REPO"]
    merge_update(repo, validation_run(repo, event))

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Automated branch diagnostic health check tool.

Audits:
1. Working tree cleanliness
2. Git commit history against Conventional Commits & ACP
3. Local test suite execution
4. GitHub Actions CI status
5. Pull Request presence and template/issue conformance
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_\-\./]+\))?: .+$"
)
ISSUE_REF_REGEX = re.compile(
    r"(close[sd]?|resolve[sd]?|fix(e[sd])?)\s+#\d+|[A-Z]+-\d+",
    re.IGNORECASE,
)


def run_cmd(
    cmd: list[str], cwd: Path | None = None, timeout: int = 60
) -> tuple[int, str, str]:
    """Execute a shell command returning (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as err:
        return 1, "", str(err)


def check_working_tree(repo_dir: Path) -> dict[str, Any]:
    """Audit working tree for dirty/untracked files."""
    code, out, _ = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir)
    if code != 0:
        return {"status": "error", "details": "Failed to inspect git status."}

    lines = [line for line in out.splitlines() if line.strip()]
    if not lines:
        return {"status": "pass", "details": "Clean (0 unstaged / untracked files)"}

    untracked = [item for item in lines if item.startswith("??")]
    modified = [item for item in lines if not item.startswith("??")]

    details = f"{len(modified)} modified/staged, {len(untracked)} untracked file(s)"
    return {"status": "warning", "details": details, "files": lines[:10]}


def check_git_history(repo_dir: Path, branch: str) -> dict[str, Any]:
    """Validate commits on branch against Conventional Commits."""
    # Determine base comparison
    base_ref = "origin/main"
    code, _, _ = run_cmd(["git", "rev-parse", "--verify", base_ref], cwd=repo_dir)
    if code != 0:
        base_ref = "main"
        code, _, _ = run_cmd(["git", "rev-parse", "--verify", base_ref], cwd=repo_dir)
        if code != 0:
            base_ref = "HEAD~5"

    cmd = ["git", "log", f"{base_ref}..HEAD", "--oneline"]
    code, out, _ = run_cmd(cmd, cwd=repo_dir)
    if code != 0 or not out:
        code, out, _ = run_cmd(["git", "log", "-5", "--oneline"], cwd=repo_dir)

    commit_lines = [item for item in out.splitlines() if item.strip()]
    if not commit_lines:
        return {"status": "pass", "details": "No recent commits to evaluate."}

    invalid_commits = []
    valid_count = 0

    for line in commit_lines:
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        sha, msg = parts[0], parts[1]
        if CONVENTIONAL_COMMIT_REGEX.match(msg):
            valid_count += 1
        else:
            invalid_commits.append(f"{sha}: {msg}")

    if invalid_commits:
        details = f"{len(invalid_commits)} of {len(commit_lines)} commit(s) violate Conventional Commits."
        return {
            "status": "fail",
            "details": details,
            "invalid_commits": invalid_commits,
            "total": len(commit_lines),
        }

    return {
        "status": "pass",
        "details": f"All {len(commit_lines)} commit(s) adhere to Conventional Commits.",
        "total": len(commit_lines),
    }


def check_local_tests(repo_dir: Path, run_tests: bool = True) -> dict[str, Any]:
    """Detect and optionally execute project tests."""
    test_cmd = None
    runner_name = None

    if (repo_dir / "justfile").is_file():
        code, out, _ = run_cmd(["just", "--list"], cwd=repo_dir)
        if code == 0 and "test" in out:
            test_cmd = ["just", "test"]
            runner_name = "just test"
    elif (repo_dir / "Makefile").is_file():
        code, out, _ = run_cmd(["make", "-n", "test"], cwd=repo_dir)
        if code == 0:
            test_cmd = ["make", "test"]
            runner_name = "make test"
    elif (repo_dir / "pyproject.toml").is_file() or (repo_dir / "uv.lock").is_file():
        test_cmd = ["uv", "run", "pytest"]
        runner_name = "uv run pytest"
    elif (repo_dir / "Cargo.toml").is_file():
        test_cmd = ["cargo", "test"]
        runner_name = "cargo test"
    elif (repo_dir / "package.json").is_file():
        test_cmd = ["npm", "test"]
        runner_name = "npm test"
    elif (repo_dir / "go.mod").is_file():
        test_cmd = ["go", "test", "./..."]
        runner_name = "go test"

    if not test_cmd:
        return {"status": "info", "details": "No standard test runner detected."}

    if not run_tests:
        return {
            "status": "info",
            "details": f"Detected {runner_name} (skipped execution).",
        }

    code, out, err = run_cmd(test_cmd, cwd=repo_dir, timeout=120)
    if code == 0:
        return {"status": "pass", "details": f"Passed via '{runner_name}'."}
    return {
        "status": "fail",
        "details": f"Failed via '{runner_name}' (exit code {code}).",
        "output": (err or out)[-500:],
    }


def check_github_ci(repo_dir: Path, branch: str) -> dict[str, Any]:
    """Check recent GitHub Actions workflow runs."""
    if not shutil.which("gh"):
        return {"status": "info", "details": "gh CLI not installed; CI check skipped."}

    cmd = [
        "gh",
        "run",
        "list",
        "--branch",
        branch,
        "--limit",
        "3",
        "--json",
        "databaseId,name,status,conclusion,url",
    ]
    code, out, _ = run_cmd(cmd, cwd=repo_dir)
    if code != 0 or not out:
        return {
            "status": "info",
            "details": "No GitHub Actions runs found for this branch.",
        }

    try:
        runs = json.loads(out)
    except json.JSONDecodeError:
        return {"status": "info", "details": "Unable to parse gh run list output."}

    if not runs:
        return {
            "status": "info",
            "details": f"No workflow runs found on branch '{branch}'.",
        }

    failing = [r for r in runs if r.get("conclusion") == "failure"]
    in_progress = [r for r in runs if r.get("status") in ("in_progress", "queued")]
    startup_failures = [r for r in runs if r.get("conclusion") == "startup_failure"]

    if startup_failures:
        return {
            "status": "fail",
            "details": f"{len(startup_failures)} workflow(s) failed on startup (check Actions permissions).",
        }
    if failing:
        return {
            "status": "fail",
            "details": f"{len(failing)} of {len(runs)} workflow runs failed.",
            "failing": [f"{r['name']}: {r['url']}" for r in failing],
        }
    if in_progress:
        return {
            "status": "warning",
            "details": f"{len(in_progress)} workflow(s) in progress.",
        }

    return {
        "status": "pass",
        "details": f"All {len(runs)} recent workflow runs succeeded.",
    }


def check_pull_request(repo_dir: Path) -> dict[str, Any]:
    """Audit Pull Request existence and well-formedness."""
    if not shutil.which("gh"):
        return {"status": "info", "details": "gh CLI not installed; PR check skipped."}

    cmd = [
        "gh",
        "pr",
        "view",
        "--json",
        "number,title,body,state,mergeable,reviewDecision,url",
    ]
    code, out, _ = run_cmd(cmd, cwd=repo_dir)
    if code != 0 or not out:
        return {
            "status": "info",
            "details": "No open Pull Request found for current branch.",
        }

    try:
        pr = json.loads(out)
    except json.JSONDecodeError:
        return {"status": "info", "details": "Unable to parse gh pr view output."}

    issues: list[str] = []
    title = pr.get("title", "")
    body = pr.get("body", "")
    number = pr.get("number")
    mergeable = pr.get("mergeable")

    # Title check
    if not CONVENTIONAL_COMMIT_REGEX.match(title):
        issues.append("PR title does not follow Conventional Commits format.")

    # Body check
    if len(body.strip()) < 30:
        issues.append("PR description body is too brief or empty.")

    # Issue reference check
    if not ISSUE_REF_REGEX.search(body):
        issues.append("PR description does not reference an issue (e.g. 'Fixes #123').")

    # Template compliance check
    template_files = [
        repo_dir / ".github" / "PULL_REQUEST_TEMPLATE.md",
        repo_dir / ".github" / "pull_request_template.md",
    ]
    for tmpl in template_files:
        if tmpl.is_file():
            tmpl_content = tmpl.read_text(encoding="utf-8")
            placeholders = re.findall(r"<!--(.*?)-->", tmpl_content)
            for p in placeholders:
                if p in body:
                    issues.append(
                        f"PR contains unedited template placeholder: <!--{p}-->"
                    )

    # Merge conflict check
    if mergeable == "CONFLICTING":
        issues.append("PR has merge conflicts with the target base branch.")

    if issues:
        return {
            "status": "warning",
            "details": f"PR #{number} has {len(issues)} item(s) requiring attention.",
            "pr_url": pr.get("url"),
            "issues": issues,
        }

    return {
        "status": "pass",
        "details": f"PR #{number} is well-formed, mergeable, and properly referenced.",
        "pr_url": pr.get("url"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Branch Doctor diagnostic health check."
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip executing the local test suite",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path("."),
        help="Path to repository root",
    )
    args = parser.parse_args()
    repo_dir = args.repo_dir.resolve()

    code, branch, _ = run_cmd(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir
    )
    if code != 0 or not branch:
        print("Error: Not in a valid git repository.", file=sys.stderr)
        return 1

    print(f"\n🏥 Branch Doctor Report: {branch}")
    print("=" * 60)

    # 1. Working tree
    wt = check_working_tree(repo_dir)
    print(f"Working Tree:      {status_icon(wt['status'])} {wt['details']}")

    # 2. Git history
    gh = check_git_history(repo_dir, branch)
    print(f"Commit History:    {status_icon(gh['status'])} {gh['details']}")

    # 3. Local tests
    lt = check_local_tests(repo_dir, run_tests=not args.no_tests)
    print(f"Local Tests:       {status_icon(lt['status'])} {lt['details']}")

    # 4. GitHub CI
    ci = check_github_ci(repo_dir, branch)
    print(f"GitHub CI:         {status_icon(ci['status'])} {ci['details']}")

    # 5. Pull Request
    pr = check_pull_request(repo_dir)
    print(f"Pull Request:      {status_icon(pr['status'])} {pr['details']}")

    print("=" * 60)

    has_failures = any(res["status"] == "fail" for res in (wt, gh, lt, ci, pr))
    if "issues" in pr:
        print("\nPR Recommendations:")
        for issue in pr["issues"]:
            print(f"  ⚠️  {issue}")

    if "invalid_commits" in gh:
        print("\nNon-compliant Commits:")
        for ic in gh["invalid_commits"][:5]:
            print(f"  ❌ {ic}")

    return 1 if has_failures else 0


def status_icon(status: str) -> str:
    icons = {
        "pass": "✅",
        "warning": "⚠️ ",
        "fail": "❌",
        "info": "ℹ️ ",
        "error": "❌",
    }
    return icons.get(status, "❓")


if __name__ == "__main__":
    sys.exit(main())

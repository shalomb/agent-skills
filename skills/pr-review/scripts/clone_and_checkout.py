#!/usr/bin/env python3
"""
Clone a GitHub repo and checkout the correct branch for a PR.

Usage:
    clone_and_checkout.py <owner> <repo> <pr_number> [--target-dir <dir>]
    
Fetches the PR to determine the actual branch name (not pr-xx),
then checks out that branch.

Output: JSON with checkout_dir, branch_name, commit_sha
"""

import sys
import json
import subprocess
import os
from pathlib import Path

def run_cmd(cmd: list, cwd: str = None) -> tuple[str, str, int]:
    """Run command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def clone_and_checkout(owner: str, repo: str, pr_number: int, target_dir: str = None) -> dict:
    """
    Clone repo and checkout PR branch.
    
    Args:
        owner: GitHub owner
        repo: GitHub repo name
        pr_number: PR number
        target_dir: Optional target directory (default: ~/{owner}/{repo})
    
    Returns:
        dict with checkout_dir, branch_name, commit_sha
    
    Raises:
        RuntimeError on git failures
    """
    if target_dir is None:
        target_dir = str(Path.home() / owner / repo)
    else:
        target_dir = os.path.expanduser(target_dir)
    
    target_path = Path(target_dir)
    
    # Clone if not exists
    if not target_path.exists():
        print(f"Cloning {owner}/{repo} to {target_dir}...", file=sys.stderr)
        stdout, stderr, rc = run_cmd([
            'git', 'clone',
            f'https://github.com/{owner}/{repo}.git',
            target_dir
        ])
        if rc != 0:
            raise RuntimeError(f"Git clone failed: {stderr}")
    else:
        print(f"Repo already exists at {target_dir}, fetching updates...", file=sys.stderr)
        stdout, stderr, rc = run_cmd(['git', 'fetch', 'origin'], cwd=target_dir)
        if rc != 0:
            raise RuntimeError(f"Git fetch failed: {stderr}")
    
    # Fetch PR metadata
    print(f"Fetching PR #{pr_number} metadata...", file=sys.stderr)
    stdout, stderr, rc = run_cmd([
        'git', 'fetch', 'origin',
        f'pull/{pr_number}/head:pr-{pr_number}-head'
    ], cwd=target_dir)
    if rc != 0:
        raise RuntimeError(f"Git fetch PR failed: {stderr}")
    
    # Get PR branch name from GitHub API or git
    # Try to use git show-ref to find the actual branch
    stdout, stderr, rc = run_cmd([
        'git', 'show-ref',
        f'pr-{pr_number}-head'
    ], cwd=target_dir)
    
    if rc != 0:
        raise RuntimeError(f"Could not fetch PR head: {stderr}")
    
    commit_sha = stdout.split()[0] if stdout else None
    
    # Now check for the actual branch - use git log to trace back
    # Get the merge base with main/master to find the real branch
    stdout, stderr, rc = run_cmd([
        'git', 'log',
        '--all', '--oneline', '--graph',
        f'--abbrev-commit',
        f'pr-{pr_number}-head...origin/main'
    ], cwd=target_dir)
    
    # For now, try common default branches
    branch_name = None
    for branch in ['main', 'master', 'develop', 'dev']:
        stdout, stderr, rc = run_cmd([
            'git', 'merge-base', '--is-ancestor',
            f'pr-{pr_number}-head', f'origin/{branch}'
        ], cwd=target_dir)
        if rc == 0:
            # This is a parent, try to find divergence point
            pass
    
    # Simpler approach: get PR details via gh CLI
    stdout, stderr, rc = run_cmd([
        'gh', 'pr', 'view', str(pr_number),
        '--json', 'headRefName',
        '-q', '.headRefName'
    ], cwd=target_dir)
    
    if rc == 0:
        branch_name = stdout
    else:
        # Fallback: use the fetched head
        branch_name = f'pr-{pr_number}-head'
    
    # Checkout the branch
    print(f"Checking out branch: {branch_name}...", file=sys.stderr)
    stdout, stderr, rc = run_cmd([
        'git', 'checkout', branch_name
    ], cwd=target_dir)
    
    if rc != 0:
        raise RuntimeError(f"Git checkout failed: {stderr}")
    
    # Get current commit SHA
    stdout, stderr, rc = run_cmd(['git', 'rev-parse', 'HEAD'], cwd=target_dir)
    if rc != 0:
        raise RuntimeError(f"Could not get commit SHA: {stderr}")
    
    commit_sha = stdout
    
    return {
        'checkout_dir': target_dir,
        'branch_name': branch_name,
        'commit_sha': commit_sha
    }

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: clone_and_checkout.py <owner> <repo> <pr_number> [--target-dir <dir>]", file=sys.stderr)
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    pr_number = int(sys.argv[3])
    
    target_dir = None
    if len(sys.argv) > 5 and sys.argv[4] == '--target-dir':
        target_dir = sys.argv[5]
    
    try:
        result = clone_and_checkout(owner, repo, pr_number, target_dir)
        print(json.dumps(result, indent=2))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

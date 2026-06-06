#!/usr/bin/env python3
"""
Analyze GitHub Actions workflow runs for a PR.

Fetches recent workflow runs related to the PR branch,
identifies failures and their error messages.

Usage:
    analyze_github_actions.py <owner> <repo> <pr_number> [--repo-dir <dir>]

Output: JSON with workflow runs, failures, and error logs
"""

import sys
import json
import subprocess
from typing import Optional

def run_cmd(cmd: list, cwd: str = None, timeout: int = 60) -> tuple[str, str, int]:
    """Run command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def analyze_github_actions(owner: str, repo: str, pr_number: int, repo_dir: Optional[str] = None) -> dict:
    """
    Analyze workflow runs for a PR.
    
    Returns:
        dict with workflow_runs (array of run objects with status/failures)
    """
    
    # Get PR branch name first
    stdout, stderr, rc = run_cmd([
        'gh', 'pr', 'view', str(pr_number),
        '--json', 'headRefName',
        '-q', '.headRefName'
    ], cwd=repo_dir)
    
    if rc != 0:
        return {
            'error': f"Could not fetch PR details: {stderr}",
            'workflow_runs': []
        }
    
    branch_name = stdout
    
    # List workflow runs for this branch (last 10)
    stdout, stderr, rc = run_cmd([
        'gh', 'run', 'list',
        '--repo', f'{owner}/{repo}',
        '--branch', branch_name,
        '--limit', '10',
        '--json', 'number,name,status,conclusion,createdAt,workflowName,databaseId'
    ], cwd=repo_dir)
    
    if rc != 0:
        return {
            'error': f"Could not fetch workflow runs: {stderr}",
            'workflow_runs': []
        }
    
    try:
        runs = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            'error': f"Failed to parse workflow runs",
            'workflow_runs': []
        }
    
    # For each failed run, get job details
    workflow_runs = []
    for run in runs:
        run_detail = {
            'number': run.get('number'),
            'name': run.get('name'),
            'status': run.get('status'),
            'conclusion': run.get('conclusion'),
            'created_at': run.get('createdAt'),
            'workflow_name': run.get('workflowName'),
            'jobs': []
        }
        
        # If failed, get job details
        if run.get('conclusion') == 'failure':
            job_stdout, _, job_rc = run_cmd([
                'gh', 'run', 'view', str(run['number']),
                '--repo', f'{owner}/{repo}',
                '--json', 'jobs',
                '-q', '.jobs[] | select(.conclusion=="failure") | {name, number, conclusion, steps: [.steps[] | select(.conclusion=="failure") | {name, number}]}'
            ], cwd=repo_dir)
            
            if job_rc == 0 and job_stdout:
                # Parse job output
                try:
                    jobs = json.loads('[' + job_stdout.replace('}\n{', '},{') + ']')
                    run_detail['jobs'] = jobs
                except:
                    pass
        
        workflow_runs.append(run_detail)
    
    return {
        'branch': branch_name,
        'workflow_runs': workflow_runs,
        'run_count': len(runs),
        'failed_runs': sum(1 for r in runs if r.get('conclusion') == 'failure')
    }

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: analyze_github_actions.py <owner> <repo> <pr_number> [--repo-dir <dir>]", file=sys.stderr)
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    pr_number = int(sys.argv[3])
    
    repo_dir = None
    if len(sys.argv) > 5 and sys.argv[4] == '--repo-dir':
        repo_dir = sys.argv[5]
    
    try:
        result = analyze_github_actions(owner, repo, pr_number, repo_dir)
        print(json.dumps(result, indent=2))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""
Check if a PR has linked issues and fetch their details.

Usage:
    check_linked_issue.py <owner> <repo> <pr_number> [--repo-dir <dir>]

Output: JSON with linked_issues (array of issue objects) or empty if none
"""

import sys
import json
import subprocess
from typing import Optional

def run_cmd(cmd: list, cwd: str = None) -> tuple[str, str, int]:
    """Run command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_linked_issues(owner: str, repo: str, pr_number: int, repo_dir: Optional[str] = None) -> dict:
    """
    Fetch linked issues for a PR using gh CLI.
    
    Returns:
        dict with:
        - linked_issues: list of issue objects (number, title, url, type)
        - has_linked_issues: boolean
        - body: PR body (may contain issue references)
    """
    
    # Get PR details including body
    query = """
    {
      repository(owner: "%s", name: "%s") {
        pullRequest(number: %d) {
          body
          linkedIssues(first: 10) {
            nodes {
              number
              title
              url
              body
            }
          }
        }
      }
    }
    """ % (owner, repo, pr_number)
    
    stdout, stderr, rc = run_cmd([
        'gh', 'api', 'graphql',
        '-f', f'query={query}'
    ], cwd=repo_dir)
    
    if rc != 0:
        # Fallback to simpler gh command
        stdout, stderr, rc = run_cmd([
            'gh', 'pr', 'view', str(pr_number),
            '--json', 'body,linkedIssues',
            '-q', '.'
        ], cwd=repo_dir)
        
        if rc != 0:
            raise RuntimeError(f"Could not fetch PR details: {stderr}")
    
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse PR details: {stdout}")
    
    # Extract issues
    linked_issues = []
    
    # Method 1: From GraphQL linkedIssues
    if 'repository' in data:
        pr = data['repository']['pullRequest']
        if 'linkedIssues' in pr and pr['linkedIssues']:
            linked_issues = pr['linkedIssues'].get('nodes', [])
    elif 'linkedIssues' in data:
        linked_issues = data['linkedIssues']
    
    # Method 2: Parse issue references from PR body using regex
    # Pattern: #123, owner/repo#456, or Jira-123
    pr_body = data.get('body', '')
    
    # Extract JIRA-style issues (e.g., PROJ-123)
    jira_pattern = r'\b([A-Z][A-Z0-9]*-\d+)\b'
    import re
    jira_issues = re.findall(jira_pattern, pr_body)
    
    return {
        'linked_issues': linked_issues,
        'has_linked_issues': len(linked_issues) > 0,
        'jira_issues': list(set(jira_issues)),  # deduplicate
        'pr_body': pr_body[:500] if pr_body else '',  # first 500 chars
    }

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: check_linked_issue.py <owner> <repo> <pr_number> [--repo-dir <dir>]", file=sys.stderr)
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    pr_number = int(sys.argv[3])
    
    repo_dir = None
    if len(sys.argv) > 5 and sys.argv[4] == '--repo-dir':
        repo_dir = sys.argv[5]
    
    try:
        result = check_linked_issues(owner, repo, pr_number, repo_dir)
        print(json.dumps(result, indent=2))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

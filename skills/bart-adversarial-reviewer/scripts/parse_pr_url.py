#!/usr/bin/env python3
"""
Parse GitHub PR URL and extract metadata.

Usage:
    parse_pr_url.py <pr_url>
    
Output: JSON with owner, repo, pr_number
"""

import sys
import json
import re
from urllib.parse import urlparse

def parse_pr_url(url: str) -> dict:
    """
    Parse GitHub PR URL into components.
    
    Args:
        url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
    
    Returns:
        dict with keys: owner, repo, pr_number
    
    Raises:
        ValueError if URL is invalid
    """
    # Handle various URL formats
    url = url.strip()
    
    # Remove .git suffix if present
    url = url.rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    
    # Match both https:// and git@ formats
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',
        r'git@github\.com:([^/]+)/([^/]+)\.git',  # git@github.com:owner/repo.git (partial)
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            if len(match.groups()) == 3:
                owner, repo, pr_number = match.groups()
                return {
                    'owner': owner,
                    'repo': repo,
                    'pr_number': int(pr_number),
                    'url': url
                }
            elif len(match.groups()) == 2:
                # git@ format without PR number - error
                raise ValueError(f"URL must include PR number: {url}")
    
    raise ValueError(f"Invalid GitHub PR URL: {url}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: parse_pr_url.py <pr_url>", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = parse_pr_url(sys.argv[1])
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

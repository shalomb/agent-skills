#!/usr/bin/env python3
"""
Discover and run tests in a repository.

Automatically detects test framework (pytest, go test, npm test, etc.)
and executes tests, capturing output and failures.

Usage:
    run_tests.py <repo_dir> [--framework <pytest|go|npm|cargo>]

Output: JSON with test results, failures, and exit code
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

def run_cmd(cmd: list, cwd: str = None, timeout: int = 300) -> Tuple[str, str, int]:
    """Run command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Tests timed out", 1
    except Exception as e:
        return "", str(e), 1

def detect_test_framework(repo_dir: str) -> Optional[str]:
    """Detect which test framework the repo uses"""
    repo_path = Path(repo_dir)
    
    # Check for go tests
    if list(repo_path.glob('**/*_test.go')):
        return 'go'
    
    # Check for pytest/python tests
    if (repo_path / 'pytest.ini').exists() or \
       (repo_path / 'setup.cfg').exists() or \
       list(repo_path.glob('**/test_*.py')) or \
       list(repo_path.glob('**/*_test.py')):
        return 'pytest'
    
    # Check for npm/node tests
    if (repo_path / 'package.json').exists():
        return 'npm'
    
    # Check for terraform tests
    if list(repo_path.glob('**/*.tf')) and \
       list(repo_path.glob('**/*_test.tf')):
        return 'terraform'
    
    # Check for cargo/rust tests
    if (repo_path / 'Cargo.toml').exists():
        return 'cargo'
    
    # Check for pytest with setup.py
    if (repo_path / 'setup.py').exists():
        return 'pytest'
    
    return None

def run_tests(repo_dir: str, framework: Optional[str] = None) -> dict:
    """
    Run tests and return results.
    
    Args:
        repo_dir: Path to repository
        framework: Optional test framework (auto-detected if not provided)
    
    Returns:
        dict with test results, failures, and timing
    """
    
    repo_path = Path(repo_dir)
    
    if not repo_path.exists():
        raise ValueError(f"Repository directory not found: {repo_dir}")
    
    # Auto-detect if not specified
    if framework is None:
        framework = detect_test_framework(repo_dir)
    
    if framework is None:
        return {
            'status': 'no_tests_found',
            'framework': None,
            'message': 'Could not detect test framework. Looked for: pytest, go test, npm test, cargo, terraform'
        }
    
    result = {
        'framework': framework,
        'status': 'unknown',
        'exit_code': None,
        'stdout': '',
        'stderr': '',
        'test_count': 0,
        'failure_count': 0,
    }
    
    try:
        if framework == 'go':
            cmd = ['go', 'test', '-v', './...']
        elif framework == 'pytest':
            cmd = ['python', '-m', 'pytest', '-v', '--tb=short']
        elif framework == 'npm':
            cmd = ['npm', 'test']
        elif framework == 'cargo':
            cmd = ['cargo', 'test', '--', '--nocapture']
        elif framework == 'terraform':
            # Terraform testing via terraform test (TF 1.6+) or tftest
            cmd = ['terraform', 'test']
        else:
            raise ValueError(f"Unsupported framework: {framework}")
        
        stdout, stderr, exit_code = run_cmd(cmd, cwd=repo_dir, timeout=600)
        
        result['exit_code'] = exit_code
        result['stdout'] = stdout[-5000:] if len(stdout) > 5000 else stdout  # Last 5000 chars
        result['stderr'] = stderr[-5000:] if len(stderr) > 5000 else stderr
        result['status'] = 'passed' if exit_code == 0 else 'failed'
        
        # Parse failure count from output
        if 'failed' in stdout.lower():
            # Try to extract test count
            import re
            match = re.search(r'(\d+) failed', stdout.lower())
            if match:
                result['failure_count'] = int(match.group(1))
        
        return result
    
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: run_tests.py <repo_dir> [--framework <pytest|go|npm|cargo>]", file=sys.stderr)
        sys.exit(1)
    
    repo_dir = sys.argv[1]
    framework = None
    
    if len(sys.argv) > 3 and sys.argv[2] == '--framework':
        framework = sys.argv[3]
    
    try:
        result = run_tests(repo_dir, framework)
        print(json.dumps(result, indent=2))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

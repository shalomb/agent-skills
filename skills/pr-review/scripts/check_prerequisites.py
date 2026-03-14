#!/usr/bin/env python3
"""
Check all prerequisites for the pr-review skill.

Validates:
- Python version (3.6+)
- Git installation
- gh CLI installation & authentication
- gh pr-review extension installation
- Required Python modules

Usage:
    check_prerequisites.py [--verbose]

Output: JSON with prerequisites status and detailed failures
Exit code: 0 if all pass, 1 if any fail
"""

import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple

def run_cmd(cmd: list, timeout: int = 10) -> Tuple[str, str, int]:
    """Run command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", "Command not found", 127
    except Exception as e:
        return "", str(e), 1

def check_python_version() -> Dict[str, any]:
    """Check Python version >= 3.6"""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    is_valid = version_info >= (3, 6)
    
    return {
        'name': 'Python 3.6+',
        'status': 'pass' if is_valid else 'fail',
        'version': version_str,
        'details': f"Python {version_str} is {'supported' if is_valid else 'too old (need 3.6+)'}",
        'critical': True
    }

def check_git() -> Dict[str, any]:
    """Check git is installed"""
    stdout, stderr, rc = run_cmd(['git', '--version'])
    
    is_valid = rc == 0
    
    return {
        'name': 'Git',
        'status': 'pass' if is_valid else 'fail',
        'version': stdout if is_valid else None,
        'details': stdout if is_valid else 'Git not installed. Install with: brew install git',
        'critical': True,
        'install_command': 'brew install git'
    }

def check_gh_cli() -> Dict[str, any]:
    """Check gh CLI is installed"""
    stdout, stderr, rc = run_cmd(['gh', '--version'])
    
    is_valid = rc == 0
    
    return {
        'name': 'GitHub CLI (gh)',
        'status': 'pass' if is_valid else 'fail',
        'version': stdout if is_valid else None,
        'details': stdout if is_valid else 'gh CLI not installed. Install from: https://cli.github.com/',
        'critical': True,
        'install_command': 'brew install gh'
    }

def check_gh_authenticated() -> Dict[str, any]:
    """Check gh CLI is authenticated"""
    stdout, stderr, rc = run_cmd(['gh', 'auth', 'status'])
    
    is_valid = rc == 0
    
    return {
        'name': 'gh CLI Authentication',
        'status': 'pass' if is_valid else 'fail',
        'details': stdout if is_valid else 'Not authenticated. Run: gh auth login',
        'critical': True,
        'fix_command': 'gh auth login'
    }

def check_gh_pr_review_extension() -> Dict[str, any]:
    """Check gh pr-review extension is installed"""
    stdout, stderr, rc = run_cmd(['gh', 'extension', 'list'])
    
    is_installed = rc == 0 and 'pr-review' in stdout.lower()
    
    details = stdout if rc == 0 else stderr
    
    return {
        'name': 'gh pr-review extension',
        'status': 'pass' if is_installed else 'fail',
        'details': 'Extension installed' if is_installed else 'Extension not found. Install with: gh extension install agynio/gh-pr-review',
        'critical': True,
        'install_command': 'gh extension install agynio/gh-pr-review',
        'reference': 'https://github.com/agynio/gh-pr-review'
    }

def check_python_modules() -> Dict[str, any]:
    """Check required Python stdlib modules"""
    required = ['subprocess', 'json', 'pathlib', 're']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    is_valid = len(missing) == 0
    
    return {
        'name': 'Python Standard Library Modules',
        'status': 'pass' if is_valid else 'fail',
        'modules_checked': required,
        'missing_modules': missing if missing else None,
        'details': 'All required modules available' if is_valid else f'Missing: {", ".join(missing)}',
        'critical': True
    }

def check_uv_cli() -> Dict[str, any]:
    """Check if uv is available (optional, for performance)"""
    stdout, stderr, rc = run_cmd(['uv', '--version'])
    
    is_available = rc == 0
    
    return {
        'name': 'uv (Python runner, optional)',
        'status': 'pass' if is_available else 'not_installed',
        'version': stdout if is_available else None,
        'details': stdout if is_available else 'uv not installed. Install from: https://docs.astral.sh/uv/. Provides faster script execution.',
        'critical': False,
        'install_command': 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    }

def check_repository_access() -> Dict[str, any]:
    """Check basic GitHub API access"""
    stdout, stderr, rc = run_cmd(['gh', 'api', 'user', '-q', '.login'])
    
    is_valid = rc == 0
    
    return {
        'name': 'GitHub API Access',
        'status': 'pass' if is_valid else 'fail',
        'authenticated_user': stdout if is_valid else None,
        'details': f'Authenticated as: {stdout}' if is_valid else 'Cannot access GitHub API. Check authentication: gh auth status',
        'critical': True
    }

def run_all_checks(verbose: bool = False) -> Tuple[Dict, bool]:
    """Run all prerequisite checks"""
    
    checks = [
        check_python_version,
        check_git,
        check_gh_cli,
        check_gh_authenticated,
        check_gh_pr_review_extension,
        check_python_modules,
        check_uv_cli,
        check_repository_access,
    ]
    
    results = {
        'system': platform.platform(),
        'python_executable': sys.executable,
        'checks': [],
        'summary': {
            'total': len(checks),
            'passed': 0,
            'failed': 0,
            'critical_failures': 0,
            'warnings': 0
        },
        'ready_to_use': True
    }
    
    for check_func in checks:
        try:
            result = check_func()
            results['checks'].append(result)
            
            if result['status'] == 'pass':
                results['summary']['passed'] += 1
            elif result['status'] == 'fail':
                results['summary']['failed'] += 1
                if result.get('critical', False):
                    results['summary']['critical_failures'] += 1
                    results['ready_to_use'] = False
            elif result['status'] == 'not_installed':
                results['summary']['warnings'] += 1
        
        except Exception as e:
            results['checks'].append({
                'name': check_func.__name__,
                'status': 'error',
                'error': str(e),
                'critical': True
            })
            results['summary']['critical_failures'] += 1
            results['ready_to_use'] = False
    
    return results, results['ready_to_use']

def print_results(results: Dict, verbose: bool = False) -> None:
    """Pretty-print results"""
    
    if verbose:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*80)
        print("PR-REVIEW SKILL: PREREQUISITE CHECK")
        print("="*80 + "\n")
        
        for check in results['checks']:
            name = check['name']
            status = check['status']
            
            if status == 'pass':
                symbol = '✅'
            elif status == 'fail':
                symbol = '❌'
            else:  # not_installed, warning
                symbol = '⚠️'
            
            print(f"{symbol} {name}")
            
            if 'version' in check and check['version']:
                print(f"   Version: {check['version']}")
            
            if 'authenticated_user' in check and check['authenticated_user']:
                print(f"   User: {check['authenticated_user']}")
            
            if check['details']:
                print(f"   {check['details']}")
            
            if status == 'fail' and 'install_command' in check:
                print(f"   → Install: {check['install_command']}")
            
            if status == 'fail' and 'fix_command' in check:
                print(f"   → Fix: {check['fix_command']}")
            
            if 'reference' in check:
                print(f"   📖 {check['reference']}")
            
            print()
        
        print("="*80)
        summary = results['summary']
        print(f"Summary: {summary['passed']}/{summary['total']} checks passed")
        
        if summary['critical_failures'] > 0:
            print(f"⚠️  {summary['critical_failures']} critical failure(s)")
        
        if summary['warnings'] > 0:
            print(f"ℹ️  {summary['warnings']} optional component(s) not installed")
        
        print("="*80)
        
        if results['ready_to_use']:
            print("\n✅ All prerequisites satisfied. Skill is ready to use!\n")
        else:
            print("\n❌ Some critical prerequisites are missing. Fix above and retry.\n")

if __name__ == '__main__':
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    results, is_ready = run_all_checks(verbose=verbose)
    print_results(results, verbose=verbose)
    
    sys.exit(0 if is_ready else 1)

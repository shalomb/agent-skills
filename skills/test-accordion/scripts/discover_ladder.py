#!/usr/bin/env python3
import os
import subprocess
import json
import argparse
import re
from pathlib import Path

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def discover_ladder():
    results = {
        "task_runner": None,
        "language": None,
        "test_runner": None,
        "orchestrators": [],
        "rungs": [],
        "ladder": []
    }

    # 1. Detect Task Runner & Targets
    if os.path.exists("justfile"):
        results["task_runner"] = "justfile"
        summary = run_cmd("just --summary")
        targets = summary.split() if summary else []
    elif os.path.exists("Makefile"):
        results["task_runner"] = "Makefile"
        raw_targets = run_cmd("make -pRrq | awk -F: '/^[^.%][-A-Za-z0-9_]*:/ { print $1 }'")
        targets = list(set(raw_targets.split())) if raw_targets else []
    else:
        targets = []

    # 2. Detect Language & Test Runner
    if os.path.exists("pyproject.toml") or os.path.exists("requirements.txt"):
        results["language"] = "python"
        results["test_runner"] = "pytest"
    elif os.path.exists("package.json"):
        results["language"] = "javascript/typescript"
        results["test_runner"] = "npm/jest/vitest"

    # 3. Categorize & Sort
    test_patterns = ["test", "lint", "check", "verify", "validation", "uat", "fast", "slow", "changed", "failing"]
    
    # Identify Orchestrators (heuristically)
    # Orchestrators are often 'test', 'uat', 'fast-fail', 'pr-validation'
    orchestrator_keywords = ["test", "uat", "fast-fail", "pr-validation", "validation"]
    
    # Semantic Phase Priority
    priority = [
        "structure", "syntax", # Phase 0.0
        "imports",             # Phase 0.25
        "types",               # Phase 0.35 (Informational)
        "lint", "check",       # Phase 0.5
        "fast", "changed", "failing", # Phase 1.0 (Incremental)
        "unit",                # Phase 2.0
        "integration", "bdd",  # Phase 3.0+
        "slow", "e2e"          # Heavy
    ]

    discovered_test_targets = [t for t in targets if any(p in t.lower() for p in test_patterns)]
    
    for t in discovered_test_targets:
        if t in orchestrator_keywords or t == "test":
            results["orchestrators"].append(t)
        else:
            results["rungs"].append(t)

    # Sort Rungs by Semantic Priority
    results["rungs"] = sorted(results["rungs"], key=lambda x: next((i for i, p in enumerate(priority) if p in x.lower()), 99))
    results["ladder"] = results["rungs"] # For backward compatibility

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover the project's test ladder.")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    ladder_data = discover_ladder()
    if args.json:
        print(json.dumps(ladder_data, indent=2))
    else:
        print(f"🚀 Discovery complete for {os.getcwd()}")
        print(f"📦 Task Runner: {ladder_data['task_runner']}")
        print(f"🛠️  Language: {ladder_data['language']}")
        
        print(f"\n⚡ Orchestrators (Loop Entry Points):")
        for o in ladder_data["orchestrators"]:
            print(f"  - {o}")
            
        print(f"\n🧪 Rungs (Semantic Ladder):")
        for i, cmd in enumerate(ladder_data["rungs"]):
            print(f"  {i+1}. {cmd}")

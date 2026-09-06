---
name: forensics
description: Diagnose codebase health, detect bug hotspots, churn, bus factor, and perform git pickaxe archaeology. Short command alias for git-forensics.
---

# Git Forensics & Code Archaeology (/forensics)

<!-- generated:alias-skill -->
When invoked, load and execute the **`git-forensics`** skill:
1. Follow all instructions and guidelines in [`git-forensics`](../git-forensics/SKILL.md).
2. Analyze codebase health using `uv run scripts/forensics.py`: churn (codebase drag), bus factor (knowledge silos), bug hotspots, velocity, and rollback commits.
3. Perform code archaeology using git pickaxe (`uv run scripts/forensics.py pickaxe '<pattern>'`) to find deleted or modified functions across all branches.
4. Use X-Ray Blame (`uv run scripts/forensics.py xblame <file>`) to ignore whitespace and detect code movement.

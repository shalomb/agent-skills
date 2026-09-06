---
description: Diagnose codebase health, detect bug hotspots, churn, bus factor, and perform git pickaxe archaeology
---

You are tasked with: Diagnose codebase health, detect bug hotspots, churn, bus factor, and perform git pickaxe archaeology.

Follow the instructions in the `git-forensics` skill:
1. Analyze codebase health using `uv run scripts/forensics.py`: churn (codebase drag), bus factor (knowledge silos), bug hotspots, velocity, and rollback commits.
2. Perform code archaeology using git pickaxe (`uv run scripts/forensics.py pickaxe '<pattern>'`) to find deleted or modified functions across all branches.
3. Use X-Ray Blame (`uv run scripts/forensics.py xblame <file>`) to ignore whitespace and detect code movement.

User request:
$ARGUMENTS

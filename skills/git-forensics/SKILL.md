---
name: git-forensics
description: Diagnose codebase health, risk areas, and perform code archaeology using git history. Use when onboarding to a project, assessing technical debt, finding lost code, tracking function evolution, or analyzing "bus factor" risks.
---

# Git Forensics

Analyze git history to identify health patterns (codebase drag, organizational risk) and perform deep code archaeology (finding lost code, tracing lines).

## 1. Codebase Health Assessment

Use these commands for a high-level view of project health and stability.

| Command | Description | Risk Indicated |
| --- | --- | --- |
| `uv run scripts/forensics.py report` | Run full health report | - |
| `uv run scripts/forensics.py churn` | Top 20 most frequently changed files | High Churn ("Codebase drag") |
| `uv run scripts/forensics.py bus` | Contributor commit distribution | Low Bus Factor (Knowledge silos) |
| `uv run scripts/forensics.py bugs` | Files most associated with "fix/bug" | Bug Hotspots |
| `uv run scripts/forensics.py velocity` | Commit counts by month | Declining velocity (Tech debt) |
| `uv run scripts/forensics.py fire` | "hotfix", "revert", "rollback" commits | Deployment/testing instability |

**Interpretation:** Files appearing in BOTH "churn" and "bugs" are the highest risk components in the system and prime candidates for refactoring.

## 2. Code Archaeology

Use these commands to dig into the history of specific code blocks or find lost context, treating the codebase as a crime scene.

### The Pickaxe (Find Lost Code)
Find exactly when a specific string, function name, or variable was added or deleted anywhere in the repository's history (across all branches).
```bash
uv run scripts/forensics.py pickaxe "my_deprecated_key"
uv run scripts/forensics.py pickaxe "^def legacy_.*" --regex
```

### X-Ray Blame
Standard `git blame` is noisy. This ignores whitespace changes (`-w`) and detects if the code was moved/copied from elsewhere (`-M -C`), pointing you to the *true* original author.
```bash
uv run scripts/forensics.py xblame path/to/file.py
```

### Trace Function Evolution
See every diff that modified a specific function or class. (Opens in a pager; press `q` to exit).
```bash
uv run scripts/forensics.py trace "my_function" path/to/file.py
```

### Find Stale Code
List the oldest, untouched files in the repository. High churn is bad, but code that hasn't been touched in 5 years might be dead weight or forgotten legacy systems.
```bash
uv run scripts/forensics.py stale
```

### Find Deleted Files
List recently deleted files across the repository to resurrect lost modules.
```bash
uv run scripts/forensics.py deleted
```

## Credits
Based on concepts from Adam Tornhill's *Your Code as a Crime Scene* and recommendations by [Ally Piechowski](https://piechowski.io/post/git-commands-before-reading-code/).

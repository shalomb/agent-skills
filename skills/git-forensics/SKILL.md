---
name: git-forensics
description: Diagnose codebase health, risk areas, and contributor dynamics using git history. Use when onboarding to a new project, assessing technical debt, identifying high-risk "bug hotspots", or analyzing team velocity and "bus factor" risks.
---

# Git Forensics

Analyze git history to identify patterns that indicate code quality, stability, and organizational risk.

## Forensic Analysis Workflow

When entering an unfamiliar codebase or conducting a health check:

1. **Run Full Report**: Get a high-level overview of churn, bugs, and velocity.
   ```bash
   uv run scripts/forensics.py report
   ```

2. **Identify High-Risk Files**: Files appearing in both "High-Churn" and "Bug Hotspots" are candidates for refactoring.
3. **Assess Bus Factor**: Check if knowledge is siloed among a few contributors.
4. **Detect Stability Trends**: Frequent `hotfix` or `revert` commits indicate deployment or testing instability.

## Capabilities

### 1. High-Churn Files
Identify files that are constantly patched. High churn often indicates "codebase drag" where changes are unpredictable and error-prone.
```bash
uv run scripts/forensics.py churn
```

### 2. Contributor Distribution (Bus Factor)
Rank contributors by commit count to identify knowledge silos.
```bash
uv run scripts/forensics.py bus
```

### 3. Bug Hotspots
Locate files most frequently associated with bug fixes (`fix`, `bug`, `broken` keywords).
```bash
uv run scripts/forensics.py bugs
```

### 4. Project Velocity
Visualize commit counts by month to track if the project is accelerating or losing momentum.
```bash
uv run scripts/forensics.py velocity
```

### 5. Firefighting Patterns
Detect `revert`, `hotfix`, `emergency`, or `rollback` patterns to assess deployment stability.
```bash
uv run scripts/forensics.py fire
```

## Interpreting Results

| Signal | Interpretation |
| --- | --- |
| **Churn + Bugs** | **High Risk.** Target these files for immediate refactoring or increased test coverage. |
| **Low Bus Factor** | **Organizational Risk.** Critical knowledge is held by too few people. |
| **High Firefighting** | **Process Risk.** Indicates unstable CI/CD, poor testing, or high-pressure "crunch" culture. |
| **Declining Velocity** | **Health Risk.** May indicate growing technical debt making changes harder. |

## Credits
Based on recommendations by [Ally Piechowski](https://piechowski.io/post/git-commands-before-reading-code/).

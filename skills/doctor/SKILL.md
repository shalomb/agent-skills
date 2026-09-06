---
name: doctor
description: Audit branch health, working tree cleanliness, conventional commits, local tests, GitHub CI, and PR well-formedness. Short command alias for branch-doctor.
---

# Branch & PR Doctor (/doctor)

<!-- generated:alias-skill -->
When invoked, load and execute the **`branch-doctor`** skill:
1. Follow all instructions and guidelines in [`branch-doctor`](../branch-doctor/SKILL.md).
2. Run the automated diagnostic check: `uv run {SKILLS_DIR}/branch-doctor/scripts/doctor.py`.
3. Inspect the 5 health dimensions: (1) Working tree cleanliness, (2) Git commit history sanity against Conventional Commits & ACP, (3) Local test suite execution, (4) GitHub Actions CI status, (5) PR existence and well-formedness against PR templates and issue references.
4. Provide actionable recommendations for any failing or warning health checks.

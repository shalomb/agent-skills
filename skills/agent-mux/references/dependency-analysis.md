# Dependency Analysis for Wave Planning

## The core question

Before parallelising, identify which TODO items touch the same source files.
Items sharing a hub file must be sequenced or merged into one branch.

## Hub file identification

```bash
# Files imported by 3+ others are hubs — dangerous to touch in parallel
grep -rn "^from \.\|^import " src/ | grep -v "__pycache__" \
  | awk -F: '{print $2}' | sort | uniq -c | sort -rn | head -20
```

## Worked example — terrapyne TODO.md

### Shared file map

| File | Touched by |
|---|---|
| `cli/utils.py` | U2, X2, X4, R3 — ALL in one branch |
| `cli/main.py` | U2, X3, U4, U5, X5, X6, R11 — ALL in one branch |
| `cli/*_cmd.py` (all) | U2 (Console stderr) touches every cmd file |
| `api/runs.py` | #10 (--wait), F3 (discard/cancel) — sequence or merge |
| `api/workspaces.py` | F2, F4, F6 — can parallel (different methods) |
| `api/client.py` | R10 (cached_property), refactor/api-access-pattern |
| `core/plan_parser.py` | R1 (dead code), R2 (split) — R1 first, R2 after |
| `api/workspace_clone.py` | R7, R8, R4 — R7+R8 together, R4 after |

### Resulting waves

```
Wave 0 (no shared files, all independent):
  fix/quick-wins: pyproject.toml, CI yaml, utils.py dedup, client.py cached_property, __init__.py version

Wave 1 (parallel — no overlap between branches):
  feature/cli-ux:        cli/utils.py + cli/main.py + all *_cmd.py  (U2,X2,X3,X4,U4,U5,X5,X6)
  feature/raw-flag:      cli/state_cmd.py only                       (#9)
  feature/run-wait:      cli/run_cmd.py + api/runs.py                (#10)
  feature/code-quality-1: api/workspace_clone.py + cli/utils.py     (R1,R3,R7,R8,R9,R12,R13)
    ⚠ cli/utils.py also touched by cli-ux — sequence or accept conflict

Wave 2 (after Wave 1 lands to main):
  feature/feature-completeness: new commands, no conflicts
  feature/code-quality-2:       core/plan_parser.py split (risky, alone)
  feature/json-format-gaps:     all *_cmd.py (after cli-ux landed)
```

## Conflict detection

```bash
# Check if two branches touch the same file
git diff --name-only origin/main...feature/cli-ux > /tmp/cli-ux-files.txt
git diff --name-only origin/main...feature/code-quality-1 > /tmp/cq1-files.txt
comm -12 <(sort /tmp/cli-ux-files.txt) <(sort /tmp/cq1-files.txt)
# Any output = conflict = must sequence
```

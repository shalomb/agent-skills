---
name: codemap
description: Analyze codebase structure, dependencies, changes, and cross-agent handoffs using codemap. Use when asked about project structure, where code is located, how files connect, what changed, how to hand off between agents, or before starting any coding task. Also triggers when codemap output looks noisy and config needs tuning.
---

# Codemap

Gives instant architectural context: project tree, dependency flow, hub detection, diff, intent classification, and multi-agent handoff.

## Commands

```bash
codemap .                       # Project tree with file counts and top files
codemap --deps .                # Dependency flow + hub files (requires ast-grep)
codemap --diff                  # Changes vs main branch
codemap --diff --ref <branch>   # Changes vs specific branch
codemap --importers <file>      # Who imports this file? Is it a hub?
codemap handoff .               # Build + save cross-agent handoff artifact
codemap handoff --latest .      # Read latest saved handoff
codemap skill list              # Show available skills
codemap skill show <name>       # Load full skill instructions
codemap config show             # Show current project config
codemap context --compact       # Minimal JSON context envelope
```

## First-Use Setup

Before deeper analysis in a new repo:
1. Run `codemap .` — if output is noisy or config is missing, run `codemap skill show config-setup` first
2. Run `codemap --deps .` — dependency graph and hub files
3. Config is repo memory: once tuned, all future calls benefit automatically

## When to use

| Situation | Command |
|---|---|
| Starting any task | `codemap .` |
| "Where is X?" / "What uses Y?" | `codemap --deps .` |
| About to edit a file | `codemap --importers <file>` |
| "What changed?" / before committing | `codemap --diff` |
| Switching agents / resuming work | `codemap handoff .` |
| Config missing or output noisy | `codemap skill show config-setup` |
| Risk warning in hook output | `codemap skill show <matched-skill>` |

## Hook output

The `prompt-submit` hook fires on every message and emits:

```
<!-- codemap:intent {"category":"refactor","risk":"high",...} -->
<!-- codemap:skills [{"name":"hub-safety","score":5},...] -->
Skills matched: hub-safety, refactor — run `codemap skill show <name>` for guidance
```

Skills are pull-based — names are surfaced automatically, full body loaded only when needed.

## Builtin skills

| Skill | When to load |
|---|---|
| `config-setup` | Config missing, boilerplate, or output noisy |
| `hub-safety` | Editing a file with 3+ importers |
| `refactor` | Restructuring, renaming, moving code |
| `test-first` | TDD workflows, writing tests |
| `explore` | Understanding how code works |
| `handoff` | Switching between agents |

## Reference

For MCP tools and HTTP API endpoints, load `references/codemap-api.md`.

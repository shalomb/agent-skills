---
name: smart-squash
description: Clean up a noisy branch history by folding insignificant commits (wip, typo, lint, format, review nits, tiny docs/test tweaks, template syncs) into the next significant commit, keeping feat/fix/perf, tagged, merge and PR commits as markers. Not a flat single-commit squash. Writes a new branch with a byte-identical tree and an old-to-new SHA map; never rewrites in place or pushes. Triggers on 'smart squash', 'squash the noise', 'clean up commit history', 'tidy this branch before PR', 'too many commits'.
---

# Smart Squash

Fold noise, keep markers. Result: a **new branch** with a shorter history whose final tree is **identical** to the source.

Script: `scripts/smart_squash.py` (stdlib only; tests in `tests/`, run `uv run --with pytest pytest tests`).

## Rules (do not bend)

1. **Never rewrite in place, never push.** `apply` only creates `<branch>-smart-squash`. The user decides about force-pushing or replacing a branch.
2. **Default range is branch-only** (commits since the merge-base with the default branch). The default branch itself is refused unless `--allow-default`.
3. **Published branches need a human.** If the branch or its commits are pushed, or a consumer pins it (e.g. `registry.yaml` `version_strategy: branch:<name>` in the IaC reveng repo), say so before the user replaces it.
4. **Always `plan` first**, show the user the groups, wait for a go-ahead, then `apply`.
5. Follow `git-safety-guardrails`: never disable GPG signing (the script passes `-S` when `commit.gpgsign` is true), never skip hooks.

## Workflow

```bash
S=~/.pi/agent/skills/smart-squash/scripts/smart_squash.py
python3 $S plan  --repo <repo> [--branch B] [--base REF] [--json]   # read-only
python3 $S apply --repo <repo> [--branch B] [--out NAME]            # creates the new branch
```

`apply` checks `git rev-parse new^{tree} == source^{tree}` and creates no branch on mismatch. It writes the SHA map to `.git/smart-squash/<out>.json` (outside the worktree).

Exit codes: 0 ok, 2 refused (safety rule), 1 error.

## What counts as an anchor (kept)

Root, merge, **tagged**, `feat|fix|perf|revert` (release-please drives versions from these), breaking change (`!` or `BREAKING CHANGE`), `(#N)` PR reference. Then, for free-form or other conventional types: large (default >= 100 lines) or touching runtime `.tf`/`.tfvars`/`.tpl` outside `tests/ examples/ docs/ .github/`.

Explicit noise patterns win over the weak signals (large, runtime): `wip tmp oops typo lint fmt format fixup! squash! sync`, `ruff format`, `address review`, `whitespace`.

Noise folds into the **next** anchor. Trailing noise folds into the previous anchor, and the squashed commit takes the tip's tree. The squashed commit keeps the anchor's message and author, plus a `Folded commits (N):` list (ACP-compatible).

Flags: `--large-lines N`, `--no-runtime-anchor`, `--allow-default`, `--base REF`, `--out NAME`.

## After applying

- Tags are **not moved**. The `tag_map` in the SHA map shows each tag's new commit; the user retags if they want.
- SHAs quoted in issues, PRs, trackers or commit messages point at old commits: use the SHA map.
- Merge commits keep their second parent (original SHAs); only the first-parent chain is rewritten.

## Known limits

- Reduction is only as good as the signals. On `terraform-aws-S3` branch `54-brownfield-import` it folded 196 to 148: most commits there are genuine `feat`/`fix`. Do not expect 80%.
- `fix:`/`feat:` commits that only touch tests or docs are kept (they drive the changelog, and facade-Python fixes look the same by path). There is no scope-based demotion yet.
- `origin/HEAD` decides the default branch; in a local clone of a local repo it can point at a feature branch. Pass `--base origin/main`.
- Signing path (`-S`) is tested for argument construction only, not with a real key.
- No revert-pair detection, no per-file or time-window grouping.

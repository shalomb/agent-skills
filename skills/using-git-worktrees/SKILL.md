---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from the current checkout, when running several branches or sub-agent writers in parallel, or before executing an implementation plan. Sets up git worktrees inside the repository under a git-ignored .worktrees/ directory, so each repository is self-contained.
---

# Using Git Worktrees

Customised from [obra/superpowers](https://github.com/obra/superpowers) `using-git-worktrees`, which it replaces.

## Overview

Work that needs isolation happens in a git worktree **inside the repository**, under
`.worktrees/`, and that directory is git-ignored. A repository then carries its own
worktrees: nothing lands in sibling or shared directories, and removing the repository
removes everything.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## The convention

| Item | Rule |
|---|---|
| Location | `<repo root>/.worktrees/<dir>` |
| Directory name | The branch name with `/` replaced by `-`: `feat/central-mode` → `.worktrees/feat-central-mode` |
| Ignored | `.worktrees/` in `.git/info/exclude` **and** in the committed `.gitignore` |
| Writers | One writer per worktree, human or agent |
| Base | Branch from the branch the work belongs to, not from `main` by default |

This is a declared preference. Do not ask where to put a worktree, and do not use sibling
directories such as `<repo>-wt` or a shared `../worktrees/` root.

## Step 0: Detect existing isolation

Check first whether you are already in a linked worktree:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
git rev-parse --show-superproject-working-tree 2>/dev/null   # prints a path only inside a submodule
```

- `GIT_DIR != GIT_COMMON` and not a submodule: you are already in a worktree. Do not create
  another one. Go to Step 3.
- Otherwise you are in the main checkout. Continue.

## Step 1: Make sure `.worktrees/` is ignored

```bash
ROOT=$(git rev-parse --show-toplevel)
COMMON=$(git rev-parse --git-common-dir)
git -C "$ROOT" check-ignore -q .worktrees/x || echo "not ignored"
```

If it is not ignored, do both:

1. **Locally, at once:** add `.worktrees/` to `$COMMON/info/exclude`. This file is shared by
   every worktree and applies on every branch, including `main`. It is never committed.
2. **In the repository:** add `.worktrees/` to `.gitignore` and commit it as its own
   Conventional Commit (`chore(git): ignore the .worktrees directory`). A `.gitignore` change on a
   feature branch protects other clones only once it reaches `main`; the `info/exclude` entry
   covers the gap.

Never create a worktree in `.worktrees/` before `git check-ignore` succeeds: an unignored
worktree shows as untracked files and can be committed by accident.

## Step 2: Create the worktree

```bash
BRANCH=feat/central-mode                     # the branch for this work
DIR="$ROOT/.worktrees/${BRANCH//\//-}"
git worktree add "$DIR" -b "$BRANCH" <base-branch>     # new branch
# or, for a branch that already exists:
git worktree add "$DIR" "$BRANCH"
```

To bring an existing worktree that lives elsewhere into the convention, move it rather than
recreating it, after checking that it is clean and that nothing is running in it:

```bash
git -C <old-path> status --porcelain        # must print nothing
git worktree move <old-path> "$ROOT/.worktrees/<dir>"
```

### Sub-agents

The pi-subagents tool's own managed worktrees (`worktree: true`) cannot follow this convention:
it refuses a worktree root inside the repository checkout. For sub-agent writers:

1. Create one worktree per lane with Step 2 yourself.
2. Launch each child with an explicit `cwd` set to its worktree and **without** `worktree: true`.
3. Name the lane's branch for its work (`test/bdd-provider-path`), not after the tool.

## Step 3: Set up and check the baseline

Install what the project needs, then run its fast checks in the new worktree:

```bash
[ -f go.mod ] && go mod download
[ -f package.json ] && npm install
[ -f pyproject.toml ] && uv sync
[ -f justfile ] && just            # or the repo's own fast test target
```

If the baseline fails, report it and ask before continuing. Proceeding past a red baseline
makes every later failure ambiguous.

Report: `Worktree ready at <path> on <branch>; baseline <passing|failing: summary>.`

## Step 4: Finish and clean up

When the work is integrated (merged, or its commits cherry-picked with `-S` onto the target branch):

```bash
git -C "$DIR" status --porcelain            # must print nothing
git cherry <target-branch> "$BRANCH"        # every line must start with '-' (already applied)
git worktree remove "$DIR"
git branch -d "$BRANCH"                     # -D only if the commits were cherry-picked, after the check above
```

Never remove a worktree that has uncommitted changes, or a branch whose commits are not on
another branch, unless the user says to drop them.

## Pitfalls

| Pitfall | What to do |
|---|---|
| A tool walks the file tree without honouring `.gitignore` | It sees a second copy of the repository in `.worktrees/`. `rg`, `fd` and Go's `./...` skip it; check any repository script that uses `glob("**")` or `os.walk` from the root, and anchor it to the directories it means. |
| Formatters, linters or watchers started at the root | Run them per worktree, or scope them to tracked files. |
| `.gitignore` committed only on a feature branch | Covered by the `info/exclude` entry from Step 1. |
| Two writers in one worktree | Never. Give each writer its own worktree. |
| A worktree whose session ended | Check it is clean and its commits are on another branch, then move or remove it. Do not delete blindly. |

## Quick reference

| Situation | Action |
|---|---|
| Already in a linked worktree | Do not create another (Step 0) |
| `.worktrees/` not ignored | `info/exclude` now, `.gitignore` commit too (Step 1) |
| New work | `git worktree add .worktrees/<dir> -b <branch> <base>` |
| Existing worktree elsewhere | `git worktree move` it into `.worktrees/` |
| Sub-agent writer | Create the worktree yourself; launch with `cwd`, not `worktree: true` |
| Baseline fails | Report and ask |
| Work integrated | Check clean and `git cherry`, then remove worktree and branch |

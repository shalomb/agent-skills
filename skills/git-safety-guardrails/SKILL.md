---
name: git-safety-guardrails
description: Git safety guardrails for AI agents. Read before ANY git operation. Ensures GPG signing is never disabled, editors never launch interactively, and prompts are suppressed. Triggers on any git commit, rebase, merge, or tag operation.
---

# Git — Agent Safety Guardrails

## Before any git operation

### 1. GPG signing must stay enabled

**Never run `git config commit.gpgsign false` or `--no-gpg-sign`.**

Check signing is configured:
```bash
git config --get commit.gpgsign  # must be "true"
git config --get user.signingkey  # must be non-empty
```

If the GPG key is locked (commit fails with "no secret key"), unlock it:
```bash
export GPG_TTY=$(tty)
echo "test" | gpg --batch --pinentry-mode loopback -o /dev/null --sign - \
  || echo "⚠️ GPG key locked — ask user to unlock with: gpg --sign /dev/null"
```

Do NOT work around a locked key by disabling signing. Stop and ask.

### 2. Prevent interactive editors

Set these before any rebase, merge, or commit that might launch an editor:

```bash
export GIT_EDITOR=true
export GIT_SEQUENCE_EDITOR=true
export EDITOR=true
export VISUAL=true
```

`true` is the no-op binary — it exits 0 without launching anything.

For interactive rebase, always prepare the todo file and pipe it:

```bash
GIT_SEQUENCE_EDITOR="sed -i 's/^pick \(HASH\)/edit \1/'" git rebase -i HEAD~3
```

### 3. Suppress prompts

```bash
export GIT_TERMINAL_PROMPT=0
export GIT_ASK_YESNO=false
```

### 4. Pager safety

```bash
export GIT_PAGER=cat    # or leave as delta if configured
```

## Quick pre-flight

Copy-paste before a git-heavy session:

```bash
export GPG_TTY=$(tty)
export GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true EDITOR=true VISUAL=true
export GIT_TERMINAL_PROMPT=0 GIT_ASK_YESNO=false
```

## Squash merge gotcha: check the branch base before merging

When squash-merging a PR, GitHub squashes **all commits on the branch that
are not on the base branch** — including any inherited history if the branch
was cut from the wrong point.

**Before every squash merge, verify the diff is only what you intend:**

```bash
# Three-dot diff = only what this branch uniquely adds
git diff origin/main...HEAD --stat

# Count of commits that will be squashed
git log --oneline origin/main..HEAD | wc -l
```

If the branch was accidentally cut from a feature branch instead of `main`,
the squash will swallow everything:

```
# WRONG — feature-branch cut from another feature branch
git checkout -b ci/my-change some-feature-branch  # ← inherits 30 commits

# RIGHT — always cut from the actual base
git checkout -b ci/my-change origin/main
```

If a branch was cut from the wrong base and already has commits, cherry-pick
the meaningful commits onto a fresh branch from `main`:

```bash
# Identify the commits that actually matter
git log --oneline origin/main..HEAD  # these are the commits to cherry-pick

# Create clean branch from correct base
git checkout -b ci/my-change-clean origin/main
git cherry-pick <sha1> <sha2>       # only the real work

# Verify
git diff origin/main...HEAD --stat  # should be minimal and correct
```

## Reverting a bad squash merge from main

If a squash swallowed too much and landed on `main`:

```bash
# Identify the bad commit
git log --oneline origin/main -3

# Reset locally
git checkout main && git pull
git reset --hard <sha-before-bad-commit>

# Force push (confirm no one else has pulled the bad state)
git push origin main --force
```

Always force-push `main` with care — coordinate with the team first.

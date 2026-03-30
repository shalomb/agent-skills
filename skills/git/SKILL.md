---
name: git
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

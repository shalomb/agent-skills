---
name: modern-cli-overrides
description: >
  Use this skill to upgrade and enforce the use of modern Rust/Go CLI equivalents 
  over traditional POSIX coreutils. Trigger this whenever you are about to use 
  grep, find, sed, awk, or ls in a shell command. You MUST read this skill to 
  learn the syntax for rg (ripgrep), fd, sd, sg (ast-grep), eza, and jq, which 
  are significantly faster, safer, and better suited for codebases.
---

# Modern CLI Overrides

As an AI agent, you were likely trained heavily on traditional POSIX tools (`grep`, `find`, `sed`, `awk`, `ls`). However, modern development environments use faster, safer, and more intelligent alternatives. 

**ABSOLUTE RULE: Do not use the traditional tools if a modern equivalent exists in this environment.**

## The Overrides

When generating shell commands or writing scripts, apply the following tool substitutions:

### 1. Use `rg` (ripgrep) instead of `grep`
*   `rg` is drastically faster and respects `.gitignore` by default.
*   **DO NOT USE:** `grep -r "pattern" .`
*   **USE:** `rg "pattern"`

### 2. Use `fd` instead of `find`
*   `fd` has a simpler syntax and respects `.gitignore`.
*   **DO NOT USE:** `find . -name "*.py"`
*   **USE:** `fd -e py`

### 3. Use `sd` or `sg` instead of `sed`
*   `sed` escaping is error-prone and dangerous for code refactoring.
*   For simple string/regex replacement, use `sd`. 
*   **DO NOT USE:** `sed -i 's/old/new/g' file`
*   **USE:** `sd 'old' 'new' file`
*   For codebase-wide structural refactoring, use `sg` (ast-grep). See the `ast-grep` skill.

### 4. Use `eza` instead of `ls`
*   `eza` provides better defaults and git status integration.
*   **DO NOT USE:** `ls -la`
*   **USE:** `eza -la --git`

### 5. Use `jq` instead of `grep`/`awk` for JSON
*   Never attempt to parse or extract values from JSON files using text-processing tools.
*   **DO NOT USE:** `grep '"key":' file.json | awk '{print $2}'`
*   **USE:** `jq '.key' file.json`

## Syntax Reference

For exact flag translations and advanced usage of these modern tools, refer to:
**[references/tool-mappings.md](references/tool-mappings.md)**

---
name: modern-cli-overrides
description: >
  Use this skill to upgrade and enforce the use of modern Rust/Go CLI equivalents 
  over traditional POSIX coreutils. Trigger this whenever you are about to use 
  grep, find, awk, or curl in a shell command. You MUST read this skill to 
  learn the syntax for rg (ripgrep), fd, sg (ast-grep), jq, yq, and httpie, which 
  are significantly faster, safer, and better suited for codebases. Must always apply!
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

### 3. Use `sg` (ast-grep) for codebase-wide refactoring
*   Standard regex replacements (`sed`) are dangerous for code refactoring.
*   For codebase-wide structural refactoring, use `sg` (ast-grep). See the `ast-grep` skill.

### 4. Use `jq` instead of `grep`/`awk` for JSON
*   Never attempt to parse or extract values from JSON files using text-processing tools.
*   **DO NOT USE:** `grep '"key":' file.json | awk '{print $2}'`
*   **USE:** `jq '.key' file.json`

### 5. Use `yq` instead of `grep`/`awk` for YAML
*   Never attempt to parse or extract values from YAML files using text-processing tools.
*   **DO NOT USE:** `grep 'key:' file.yaml`
*   **USE:** `yq '.key' file.yaml`

### 6. Use `httpie` (`http`) instead of `curl`
*   `curl` syntax for JSON payloads is tedious and error-prone. `httpie` provides intuitive syntax, automatic JSON parsing, and avoids escaping hell.
*   **DO NOT USE:** `curl -X POST -H "Content-Type: application/json" -d '{"key":"value"}' api.com`
*   **USE:** `http POST api.com key=value`

## Syntax Reference

For exact flag translations and advanced usage of these modern tools, refer to:
**[references/tool-mappings.md](references/tool-mappings.md)**

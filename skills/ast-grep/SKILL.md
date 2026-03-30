---
name: ast-grep
description: Structural code search, analysis, and rewriting using AST patterns with sg/ast-grep. Use when searching for code patterns across a codebase (not text grep), extracting structured information from code (function names, imports, usages), applying automated refactors or migrations, linting with custom rules, or when a task requires understanding code structure rather than text. Triggers include "find all usages of", "rename this pattern", "refactor all X to Y", "extract all functions that", "lint for pattern", or any structural code analysis task.
---

# ast-grep (sg)

Structural code search and rewriting using AST patterns. Think `grep` but matches syntax, not text. `$VAR` matches any single node; `$$$VARS` matches zero or more nodes.

## Quick patterns

```bash
# Search
sg run -p 'console.log($A)' -l js .
sg run -p 'def $FUNC($$$):' -l python .

# Rewrite (preview diff)
sg run -p 'var $V = $E' -r 'const $V = $E' -l js .

# Apply rewrite to all files
sg run -p 'var $V = $E' -r 'const $V = $E' -l js . --update-all

# JSON output for scripting
sg run -p '$FUNC($$$ARGS)' -l python . --json=stream

# Scan with a YAML rule file
sg scan -r rule.yml .

# Inline rule (no file)
sg scan --inline-rules '
id: no-var
language: javascript
rule:
  pattern: var $V = $E
fix: const $V = $E
message: Use const
severity: warning
' .
```

## Pattern syntax

| Syntax | Matches |
|---|---|
| `$VAR` | Any single AST node (captures as metavariable) |
| `$$$VARS` | Zero or more nodes (ellipsis) |
| `$_` | Any node (anonymous, no capture) |
| Literal code | Exact structural match |

## Key flags (`sg run`)

| Flag | Purpose |
|---|---|
| `-p` | Pattern to match |
| `-r` | Replacement pattern (uses same `$VAR` names) |
| `-l` | Language (js, ts, py, python, go, rust, java, …) |
| `--json=stream` | One JSON object per match on stdout |
| `--json=pretty` | Pretty-printed JSON array |
| `--update-all` | Apply rewrite without confirmation |
| `--stdin` | Read code from stdin |
| `--files-with-matches` | Print only matching file paths |
| `-C <n>` | Show n lines of context |
| `--globs` | Restrict to file glob patterns |

## Rule YAML schema

```yaml
id: rule-id               # required, unique
language: python          # required
rule:                     # required — the matcher
  pattern: $EXPR          # atomic: match by pattern
  # OR:
  kind: function_definition  # atomic: match by AST node type
  regex: "^test_"         # atomic: match by text regex
  # Composites:
  all: [rule1, rule2]     # all must match
  any: [rule1, rule2]     # any must match
  not: {pattern: $X}      # negate
  inside: {pattern: ...}  # relational: node is inside this
  has: {pattern: ...}     # relational: node has descendant
  follows: {pattern: ...} # relational: node follows this
  precedes: {pattern: ...}# relational: node precedes this
fix: "replacement"        # optional rewrite
message: "Human message"  # optional lint message
severity: warning         # hint | info | warning | error
```

## sgconfig.yml (project config)

```yaml
ruleDirs:
  - rules/
testConfigs:
  - testDir: tests/
```

Place at repo root. Run `sg scan .` to apply all rules.

## Common use cases

Load `references/ast-grep-patterns.md` for language-specific pattern examples and metavariable extraction recipes.

## JSON output schema

Each `--json=stream` line:
```json
{
  "text": "matched text",
  "file": "path/to/file.py",
  "range": {"start": {"line": 0, "column": 0}, "end": {...}},
  "metaVariables": {
    "single": {"VAR": {"text": "captured", "range": {...}}},
    "multi": {"VARS": [{"text": "...", "range": {...}}, ...]}
  },
  "language": "Python"
}
```

## Go SDK / vendored module search

Searching Go types in vendored dependencies or Go module cache:

```bash
# Find the cached module path
TYPES=$(find $(go env GOMODCACHE)/github.com/aws/aws-sdk-go-v2/service/elasticloadbalancingv2* \
  -name "types.go" -path "*/types/*")

# Search for a struct definition
sg -p 'type Action struct { $$$ }' "$TYPES"

# Search for a function in provider source
cd ~/projects/hashicorp/terraform-provider-aws
sg -p 'func expandListenerAction($$$) $$${ $$$ }' --lang go internal/service/elbv2/listener.go
```

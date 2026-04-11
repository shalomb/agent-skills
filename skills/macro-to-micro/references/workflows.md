# Macro to Micro Workflows

This reference provides detailed articulation strategies for combining Codemap, LSP, and AST Grep.

## Workflow A: The "Safe Hub Refactor"

When you are asked to modify a widely-used file or perform a codebase-wide structural change, follow this sequence:

### 1. Codemap (Blast Radius)
You are asked to change the parameters of a core authentication function.
1. Run the `codemap` tool or CLI command to map dependencies.
2. Codemap reveals the `auth.py` file is a "Hub File" imported by 45 different modules across the project. It is dangerous to touch blindly.

### 2. LSP Code Analysis (Semantic Tracing)
You need to know how those 45 modules interact with the function you are changing.
1. Run `lsp reference src/auth.py --scope validate_token`.
2. LSP returns the exact line numbers and surrounding syntax of every call site across those 45 modules.
3. You realize they are all passing a legacy string parameter that you now need to remove.

### 3. AST Grep (Structural Rewrite)
Standard text replacement (`sed` or `replace`) is dangerous across 45 files because it might accidentally replace occurrences inside string literals or comments.
1. Use AST Grep to perform a syntax-aware rewrite.
2. Run `sg run -p 'validate_token($TOKEN, $LEGACY)' -r 'validate_token($TOKEN)' --update-all`.
3. The refactoring is executed safely across the entire codebase.

---

## Workflow B: The "Mystery Bug Hunt"

When you encounter an obscure error log or trace that doesn't point to an obvious cause, follow this sequence:

### 1. AST Grep (Pattern Discovery)
You know the bug is related to a specific anti-pattern (e.g., catching a generic `Exception` without logging it, or missing an `await` on a database call).
1. Run `sg run -p 'try { $$$ } except Exception: pass'` to find all structural instances of this anti-pattern.
2. AST Grep returns 3 obscure files deep in the codebase.

### 2. LSP Code Analysis (Data Flow)
You need to know how user input or data reaches that broken code in those 3 files.
1. Run `lsp definition` or `lsp reference` on the functions immediately surrounding the bug.
2. You trace the data flow backwards through the call stack to figure out where the erroneous state originated.

### 3. Codemap (Architectural Context)
You have found the source, but you need to understand *why* the system is designed this way before proposing a fix.
1. Run `codemap` to see the architectural boundaries of the subsystem where the bug lives.
2. You check the git history and fan-out of the module to understand the wider architectural flaw before writing the fix.

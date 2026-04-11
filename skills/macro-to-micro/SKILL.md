---
name: macro-to-micro
description: >
  Use this skill to orchestrate deep codebase exploration and complex structural refactoring by chaining Codemap, LSP Code Analysis, and AST Grep. Trigger this when asked to "safely refactor across the codebase", "trace this bug to its source", "explore the architecture of this subsystem", or whenever a task requires understanding the impact of a change before making it. This acts as a high-road strategy guide over basic grep/read commands.
---

# Macro to Micro: Structural Codebase Mastery

This is a higher-order orchestrator skill that formalizes the "Macro to Micro" toolchain. It teaches you how and when to hand off context between three powerful semantic tools:

1.  **Codemap (The Macro View):** Treats code as a **graph of files**.
2.  **LSP Code Analysis (The Meso View):** Treats code as a **graph of symbols**.
3.  **AST Grep (The Micro View):** Treats code as **syntax trees**.

## The Articulation Strategy

Do not blindly use `grep_search` or `read_file` on large unfamiliar codebases. Follow this hand-off chain:

1.  **Identify the Blast Radius (Codemap)**
    *   Find the files that matter and their dependencies.
    *   *Output:* A list of target files and "hub" files (highly imported files that are dangerous to change).
2.  **Trace the Logic (LSP)**
    *   Take the files from step 1 and use `lsp reference` and `lsp definition` to understand exactly how data flows between them.
    *   *Output:* An understanding of the exact semantic contract (function signatures, usages) that needs to be altered.
3.  **Execute the Transformation (AST Grep)**
    *   Take the semantic understanding from step 2 and use `sg run` to perform a surgical, syntax-aware rewrite across all affected files simultaneously.

## Reference Workflows

Detailed recipes for specific scenarios are available in the references:

*   **[references/workflows.md](references/workflows.md)**: Step-by-step guides for the "Safe Hub Refactor" and the "Mystery Bug Hunt".

## Core Principles

*   **Never skip the Macro step:** If you are asked to change a "core" or "utils" file, use Codemap to check its fan-out first.
*   **Never use `sed` for code:** If you need to rename a parameter across 20 files, use AST Grep or LSP Rename. Text replacement destroys comments and strings.
*   **Don't read massive files:** If a file is 2,000 lines long, use `lsp outline` to see its structure before blindly jumping in.

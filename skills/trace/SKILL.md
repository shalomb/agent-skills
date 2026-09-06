---
name: trace
description: Trace bugs and refactoring blast radius by chaining Codemap, LSP, and AST-grep. Short command alias for macro-to-micro.
---

# Macro-to-Micro Codebase Tracing (/trace)

<!-- generated:alias-skill -->
When invoked, load and execute the **`macro-to-micro`** skill:
1. Follow all instructions and guidelines in [`macro-to-micro`](../macro-to-micro/SKILL.md).
2. Follow the 3-tier articulation chain: Macro (Codemap file graph) -> Meso (LSP symbol graph) -> Micro (AST-grep syntax tree).
3. Identify hub files and dependency blast radius with Codemap before editing.
4. Trace call chains and data flow with LSP (`lsp reference`, `lsp definition`, `lsp outline`).
5. Perform surgical syntax-aware transformations using AST-grep (`sg run`).
